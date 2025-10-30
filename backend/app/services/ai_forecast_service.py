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
                Expense.description,
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
                "description": exp.description,
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

        # Format recent expenses for context
        recent_expenses = historical_data[-10:]  # Last 10 expenses
        expenses_text = "\n".join(
            [
                f"- {exp['request_date']}: {exp['description']} - {exp['amount']:,.0f} ₽ ({exp['category']})"
                for exp in recent_expenses
            ]
        )

        # Format monthly statistics
        monthly_text = "\n".join(
            [
                f"- {m['year']}-{m['month']:02d}: {m['count']} расходов, сумма {m['total']:,.0f} ₽, средний {m['average']:,.0f} ₽"
                for m in statistics["monthly_data"][-6:]  # Last 6 months
            ]
        )

        prompt = f"""Ты - эксперт по финансовому прогнозированию для IT отдела.

ЗАДАЧА: Сгенерируй прогноз расходов{category_context} на {month:02d}.{year}.

ИСТОРИЧЕСКИЕ ДАННЫЕ:

Последние расходы:
{expenses_text}

Помесячная статистика за последние 6 месяцев:
{monthly_text}

Средний расход в месяц: {statistics['overall_average']:,.0f} ₽
Всего расходов за год: {statistics['total_expenses']}

ИНСТРУКЦИИ:
1. Проанализируй паттерны расходов (сезонность, тренды, частота)
2. Учти типичные категории расходов IT отдела
3. Сгенерируй реалистичный прогноз на {month:02d}.{year}
4. Предложи 3-5 конкретных статей расходов с суммами
5. Дай краткое обоснование каждой статьи

ФОРМАТ ОТВЕТА (JSON):
{{
  "forecast_total": <общая сумма прогноза>,
  "confidence": <уверенность в прогнозе от 0 до 100>,
  "items": [
    {{
      "description": "<описание расхода>",
      "amount": <сумма>,
      "reasoning": "<обоснование>"
    }}
  ],
  "summary": "<краткая сводка прогноза и ключевые факторы>"
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

                try:
                    forecast_data = json.loads(ai_content)
                except json.JSONDecodeError:
                    # Fallback: use statistical average
                    return {
                        "success": False,
                        "error": "AI response parsing failed",
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
