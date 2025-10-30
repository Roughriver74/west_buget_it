"""
AI-powered forecast service using external AI API
"""
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from decimal import Decimal

from app.db.models import Expense, BudgetCategory, Contractor, ExpenseStatusEnum
from app.core.config import settings


class AIForecastService:
    """Service for generating AI-powered expense forecasts"""

    # vsegpt.ru API configuration
    AI_API_URL = "https://api.vsegpt.ru/v1/chat/completions"
    AI_MODEL = "openai/gpt-4o-mini"
    AI_API_KEY = "sk-or-vv-e3d1733d71226f04372d5bd90843b3615228e15f4bc3936371f97198d986b01a"

    def __init__(self, db: Session):
        self.db = db

    def get_historical_expenses(
        self,
        department_id: int,
        lookback_months: int = 12,
        category_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get historical expenses for AI context

        Args:
            department_id: Department ID to filter by
            lookback_months: Number of months to look back
            category_id: Optional category filter

        Returns:
            List of expense records with category and contractor info
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_months * 30)

        # Build query
        query = (
            self.db.query(
                Expense.id,
                Expense.comment,
                Expense.amount,
                Expense.request_date,
                Expense.payment_date,
                Expense.status,
                BudgetCategory.name.label("category_name"),
                Contractor.name.label("contractor_name"),
            )
            .join(BudgetCategory, Expense.category_id == BudgetCategory.id)
            .outerjoin(Contractor, Expense.contractor_id == Contractor.id)
            .filter(
                Expense.department_id == department_id,
                Expense.request_date >= start_date,
                Expense.request_date <= end_date,
            )
        )

        if category_id:
            query = query.filter(Expense.category_id == category_id)

        # Execute and format results
        expenses = query.all()
        return [
            {
                "id": exp.id,
                "description": exp.comment or "Без комментария",
                "amount": float(exp.amount),
                "request_date": exp.request_date.isoformat() if exp.request_date else None,
                "payment_date": exp.payment_date.isoformat() if exp.payment_date else None,
                "status": exp.status,
                "category": exp.category_name,
                "contractor": exp.contractor_name,
            }
            for exp in expenses
        ]

    def get_expense_statistics(
        self, department_id: int, category_id: Optional[int] = None
    ) -> Dict:
        """
        Get statistical summary of historical expenses

        Returns:
            Dict with monthly averages, trends, and patterns
        """
        # Get expenses for the last 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        query = self.db.query(
            extract("year", Expense.request_date).label("year"),
            extract("month", Expense.request_date).label("month"),
            func.count(Expense.id).label("count"),
            func.sum(Expense.amount).label("total"),
            func.avg(Expense.amount).label("average"),
        ).filter(
            Expense.department_id == department_id,
            Expense.request_date >= start_date,
            Expense.request_date <= end_date,
        )

        if category_id:
            query = query.filter(Expense.category_id == category_id)

        query = query.group_by(
            extract("year", Expense.request_date), extract("month", Expense.request_date)
        ).order_by(
            extract("year", Expense.request_date), extract("month", Expense.request_date)
        )

        monthly_stats = query.all()

        return {
            "monthly_data": [
                {
                    "year": int(stat.year),
                    "month": int(stat.month),
                    "count": stat.count,
                    "total": float(stat.total or 0),
                    "average": float(stat.average or 0),
                }
                for stat in monthly_stats
            ],
            "overall_average": float(
                sum(s.total or 0 for s in monthly_stats) / max(len(monthly_stats), 1)
            ),
            "total_expenses": sum(s.count for s in monthly_stats),
        }

    def build_ai_prompt(
        self,
        historical_data: List[Dict],
        statistics: Dict,
        year: int,
        month: int,
        category_name: Optional[str] = None,
    ) -> str:
        """
        Build AI prompt for expense forecasting

        Args:
            historical_data: List of historical expenses
            statistics: Statistical summary
            year: Target forecast year
            month: Target forecast month
            category_name: Optional category name for context

        Returns:
            Formatted prompt string for AI
        """
        category_context = f" для категории '{category_name}'" if category_name else ""

        # Format ALL monthly statistics (not just last 6)
        monthly_text = "\n".join(
            [
                f"- {m['year']}-{m['month']:02d}: {m['count']} расходов, сумма {m['total']:,.0f} ₽, средний {m['average']:,.0f} ₽"
                for m in statistics["monthly_data"]
            ]
        )

        # Find same month in previous year for seasonality analysis
        same_month_last_year = None
        for m in statistics["monthly_data"]:
            if m['month'] == month and m['year'] == year - 1:
                same_month_last_year = m
                break

        seasonality_text = ""
        if same_month_last_year:
            seasonality_text = f"\nДанные за {month:02d}.{year-1} (прошлый год, тот же месяц): {same_month_last_year['count']} расходов, сумма {same_month_last_year['total']:,.0f} ₽"

        # Calculate trend (comparing last 3 months vs previous 3 months)
        trend_text = ""
        if len(statistics["monthly_data"]) >= 6:
            recent_3 = statistics["monthly_data"][-3:]
            previous_3 = statistics["monthly_data"][-6:-3]
            recent_avg = sum(m['total'] for m in recent_3) / 3
            previous_avg = sum(m['total'] for m in previous_3) / 3

            if previous_avg > 0:
                trend_percent = ((recent_avg - previous_avg) / previous_avg) * 100
                trend_direction = "рост" if trend_percent > 0 else "снижение"
                trend_text = f"\nТренд: {trend_direction} на {abs(trend_percent):.1f}% (последние 3 месяца vs предыдущие 3)"

        # Group expenses by category for better context
        category_breakdown = {}
        for exp in historical_data:
            cat = exp.get('category', 'Без категории')
            if cat not in category_breakdown:
                category_breakdown[cat] = {'count': 0, 'total': 0}
            category_breakdown[cat]['count'] += 1
            category_breakdown[cat]['total'] += exp['amount']

        category_text = "\n".join(
            [
                f"- {cat}: {data['count']} расходов, {data['total']:,.0f} ₽"
                for cat, data in sorted(category_breakdown.items(), key=lambda x: x[1]['total'], reverse=True)[:10]
            ]
        )

        prompt = f"""Ты - эксперт по финансовому прогнозированию для IT отдела.

ЗАДАЧА: Сгенерируй детальный прогноз расходов{category_context} на {month:02d}.{year} на основе исторических данных.

📊 ИСТОРИЧЕСКИЕ ДАННЫЕ ЗА ГОД:

Помесячная статистика за весь период:
{monthly_text}

Средний расход в месяц: {statistics['overall_average']:,.0f} ₽
Всего расходов за период: {statistics['total_expenses']}
{seasonality_text}
{trend_text}

Топ категорий расходов:
{category_text}

📋 ИНСТРУКЦИИ:
1. ОБЯЗАТЕЛЬНО проанализируй месячную динамику выше - есть ли рост, падение или стабильность
2. ОБЯЗАТЕЛЬНО учти данные за {month:02d}.{year-1} (если есть) - это показывает сезонность
3. ОБЯЗАТЕЛЬНО учти текущий тренд последних месяцев
4. Примени выявленные паттерны к прогнозу на {month:02d}.{year}
5. Сгенерируй 3-7 конкретных статей расходов с обоснованием каждой
6. В reasoning для каждой статьи укажи, на основе каких исторических данных сделан прогноз

ФОРМАТ ОТВЕТА (JSON):
{{
  "forecast_total": <общая сумма прогноза>,
  "confidence": <уверенность в прогнозе от 0 до 100>,
  "items": [
    {{
      "description": "<описание расхода>",
      "amount": <сумма>,
      "reasoning": "<обоснование на основе исторических данных>"
    }}
  ],
  "summary": "<краткая сводка: учтённые тренды, сезонность и ключевые факторы>"
}}

Отвечай ТОЛЬКО валидным JSON без дополнительного текста."""

        return prompt

    async def generate_ai_forecast(
        self,
        department_id: int,
        year: int,
        month: int,
        category_id: Optional[int] = None,
    ) -> Dict:
        """
        Generate AI-powered expense forecast

        Args:
            department_id: Department ID
            year: Target year
            month: Target month
            category_id: Optional category filter

        Returns:
            Dict with AI forecast data
        """
        # Get historical data
        historical_expenses = self.get_historical_expenses(
            department_id=department_id,
            lookback_months=12,
            category_id=category_id,
        )

        if not historical_expenses:
            return {
                "success": False,
                "error": "No historical data available for AI forecast",
                "forecast_total": 0,
                "confidence": 0,
                "items": [],
                "summary": "Недостаточно исторических данных для прогноза",
            }

        # Get statistics
        statistics = self.get_expense_statistics(
            department_id=department_id, category_id=category_id
        )

        # Get category name if provided
        category_name = None
        if category_id:
            category = self.db.query(BudgetCategory).filter_by(id=category_id).first()
            if category:
                category_name = category.name

        # Build AI prompt
        prompt = self.build_ai_prompt(
            historical_data=historical_expenses,
            statistics=statistics,
            year=year,
            month=month,
            category_name=category_name,
        )

        # Call AI API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.AI_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.AI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.AI_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are a financial forecasting expert. Always respond with valid JSON only."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1500,
                    },
                )

                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"AI API error: {response.status_code}",
                        "forecast_total": statistics["overall_average"],
                        "confidence": 50,
                        "items": [],
                        "summary": f"Ошибка AI API. Используется средний расход: {statistics['overall_average']:,.0f} ₽",
                    }

                ai_response = response.json()
                ai_content = ai_response["choices"][0]["message"]["content"]

                # Parse AI response (it should be JSON)
                import json
                import re
                import logging

                logger = logging.getLogger(__name__)
                logger.info(f"AI raw response: {ai_content}")

                # Try to extract JSON from markdown code blocks if present
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_content, re.DOTALL)
                if json_match:
                    ai_content = json_match.group(1)
                    logger.info(f"Extracted JSON from markdown: {ai_content}")

                try:
                    forecast_data = json.loads(ai_content)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {e}, content: {ai_content}")
                    # Fallback: use statistical average
                    return {
                        "success": False,
                        "error": f"AI response parsing failed: {str(e)}",
                        "forecast_total": statistics["overall_average"],
                        "confidence": 50,
                        "items": [],
                        "summary": f"Ошибка парсинга AI ответа. Используется средний расход: {statistics['overall_average']:,.0f} ₽",
                    }

                # Add success flag and metadata
                forecast_data["success"] = True
                forecast_data["ai_model"] = self.AI_MODEL
                forecast_data["generated_at"] = datetime.now().isoformat()
                forecast_data["historical_months"] = len(statistics["monthly_data"])

                return forecast_data

        except Exception as e:
            # Fallback to statistical average on any error
            return {
                "success": False,
                "error": str(e),
                "forecast_total": statistics["overall_average"],
                "confidence": 50,
                "items": [],
                "summary": f"Ошибка подключения к AI. Используется средний расход: {statistics['overall_average']:,.0f} ₽",
            }
