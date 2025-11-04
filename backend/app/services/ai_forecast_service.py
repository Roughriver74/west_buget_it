"""
AI-powered forecast service using external AI API
"""
import httpx
import logging
import math
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from app.db.models import (
    Expense, BudgetCategory, Contractor, ExpenseStatusEnum,
    BudgetVersion, BudgetPlanDetail, BudgetVersionStatusEnum
)
from app.core.config import settings

# Module-level logger
logger = logging.getLogger(__name__)


class AIForecastService:
    """Service for generating AI-powered expense forecasts"""

    MIN_AI_ITEMS = 10
    DEFAULT_RANGE_DELTA = 0.15  # +/-15% for fallback ranges

    # vsegpt.ru API configuration
    AI_API_URL = "https://api.vsegpt.ru/v1/chat/completions"
    AI_MODEL = "openai/gpt-4o-mini"
    AI_API_KEY = "sk-or-vv-e3d1733d71226f04372d5bd90843b3615228e15f4bc3936371f97198d986b01a"

    def __init__(self, db: Session):
        self.db = db

    def get_historical_expenses(
        self,
        department_id: int,
        lookback_months: int = 24,
        category_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get historical expenses for AI context

        Args:
            department_id: Department ID to filter by
            lookback_months: Number of months to look back (default: 18)
            category_id: Optional category filter

        Returns:
            List of expense records with category and contractor info
        """
        # Calculate date range (24 months by default для более богатого контекста)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_months * 30)

        # Build query
        query = (
            self.db.query(
                Expense.id,
                Expense.category_id,
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
                "category_id": exp.category_id,
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
        # Get expenses for the last 18 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=18 * 30)

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

    def get_approved_budget_plans(
        self,
        department_id: int,
        year: int,
        month: int,
        category_id: Optional[int] = None,
    ) -> Dict:
        """
        Get approved budget plans for the target month

        Args:
            department_id: Department ID
            year: Target year
            month: Target month (1-12)
            category_id: Optional category filter

        Returns:
            Dict with approved budget plan data
        """
        # Find approved budget version for the target year
        approved_version = (
            self.db.query(BudgetVersion)
            .filter(
                BudgetVersion.department_id == department_id,
                BudgetVersion.year == year,
                BudgetVersion.status == BudgetVersionStatusEnum.APPROVED,
            )
            .order_by(BudgetVersion.approved_at.desc())
            .first()
        )

        if not approved_version:
            return {
                "has_approved_plan": False,
                "total_planned": 0,
                "categories": [],
            }

        # Get plan details for the target month
        query = (
            self.db.query(
                BudgetPlanDetail.category_id,
                BudgetCategory.name.label("category_name"),
                BudgetPlanDetail.planned_amount,
                BudgetPlanDetail.type,
                BudgetPlanDetail.justification,
                BudgetPlanDetail.calculation_method,
            )
            .join(BudgetCategory, BudgetPlanDetail.category_id == BudgetCategory.id)
            .filter(
                BudgetPlanDetail.version_id == approved_version.id,
                BudgetPlanDetail.month == month,
            )
        )

        if category_id:
            query = query.filter(BudgetPlanDetail.category_id == category_id)

        plan_details = query.all()

        if not plan_details:
            return {
                "has_approved_plan": False,
                "total_planned": 0,
                "categories": [],
            }

        categories = [
            {
                "category_id": detail.category_id,
                "category_name": detail.category_name,
                "planned_amount": float(detail.planned_amount),
                "type": detail.type,
                "justification": detail.justification,
                "calculation_method": detail.calculation_method,
            }
            for detail in plan_details
        ]

        total_planned = sum(float(detail.planned_amount) for detail in plan_details)

        return {
            "has_approved_plan": True,
            "version_id": approved_version.id,
            "version_name": approved_version.version_name or f"Версия {approved_version.version_number}",
            "approved_at": approved_version.approved_at.isoformat() if approved_version.approved_at else None,
            "total_planned": total_planned,
            "categories": categories,
        }

    def calculate_baseline_metrics(
        self,
        statistics: Dict,
        year: int,
        month: int,
    ) -> Dict:
        """Calculate simple, moving and seasonal baselines for the forecast"""
        monthly_data = statistics.get("monthly_data", [])
        totals = [m.get("total") or 0 for m in monthly_data]

        simple_avg = sum(totals) / len(totals) if totals else 0

        moving_avg = None
        if len(totals) >= 3:
            recent = totals[-3:]
            moving_avg = sum(recent) / len(recent)

        seasonal_reference = None
        for m in monthly_data:
            if m.get("month") == month and m.get("year") == year - 1:
                seasonal_reference = m.get("total") or 0
                break

        last_12_total = sum(totals[-12:]) if len(totals) >= 12 else sum(totals)

        return {
            "simple_average": simple_avg,
            "moving_average": moving_avg,
            "seasonal_reference": seasonal_reference,
            "last_12_months_total": last_12_total,
        }

    @staticmethod
    def round_to_hundreds(value: Optional[float]) -> int:
        """Round numeric value to nearest hundred (bankers rounding avoided)"""
        if value is None:
            return 0
        try:
            dec_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            dec_value = Decimal(0)
        rounded = (dec_value / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("100")
        return int(rounded)

    def detect_anomalies(self, statistics: Dict) -> Dict:
        """Detect outlier months in historical data based on standard deviation"""
        monthly_data = statistics.get("monthly_data", [])
        totals = [m.get("total") or 0 for m in monthly_data]

        if len(totals) < 6:
            return {"items": [], "mean": None, "std": None, "threshold": None}

        mean_value = sum(totals) / len(totals)
        variance = sum((value - mean_value) ** 2 for value in totals) / len(totals)
        std_dev = math.sqrt(variance)

        # If variance is extremely small, skip anomaly detection
        if std_dev < 1:
            return {"items": [], "mean": mean_value, "std": std_dev, "threshold": std_dev * 1.5}

        threshold = std_dev * 1.5
        anomalies = []

        for m in monthly_data:
            total = m.get("total") or 0
            deviation = total - mean_value
            if abs(deviation) >= threshold:
                deviation_percent = (deviation / mean_value * 100) if mean_value else 0
                anomalies.append(
                    {
                        "year": int(m.get("year")),
                        "month": int(m.get("month")),
                        "total": total,
                        "deviation_percent": deviation_percent,
                    }
                )

        return {
            "items": anomalies,
            "mean": mean_value,
            "std": std_dev,
            "threshold": threshold,
        }

    def extract_plan_events(self, approved_plans: Dict) -> List[Dict]:
        """Extract notable events or justifications from approved plan (if available)"""
        if not approved_plans.get("has_approved_plan"):
            return []

        events = []
        for cat in approved_plans.get("categories", []):
            justification = (cat.get("justification") or "").strip()
            calculation_method = cat.get("calculation_method")
            if justification:
                events.append(
                    {
                        "category_name": cat.get("category_name"),
                        "planned_amount": cat.get("planned_amount"),
                        "justification": justification,
                        "calculation_method": calculation_method,
                    }
                )
            elif calculation_method and calculation_method != "manual":
                events.append(
                    {
                        "category_name": cat.get("category_name"),
                        "planned_amount": cat.get("planned_amount"),
                        "justification": None,
                        "calculation_method": calculation_method,
                    }
                )
        return events

    def format_baseline_metrics(self, baseline_metrics: Dict) -> Dict:
        """Normalize baseline metrics for API/Frontend"""
        simple = baseline_metrics.get("simple_average")
        moving = baseline_metrics.get("moving_average")
        seasonal = baseline_metrics.get("seasonal_reference")
        last_12 = baseline_metrics.get("last_12_months_total")
        return {
            "simple_average": self.round_to_hundreds(simple) if simple is not None else None,
            "moving_average": self.round_to_hundreds(moving) if moving is not None else None,
            "seasonal_reference": self.round_to_hundreds(seasonal) if seasonal is not None else None,
            "last_12_months_total": self.round_to_hundreds(last_12) if last_12 is not None else None,
        }

    def format_anomaly_summary(self, anomaly_summary: Optional[Dict]) -> Dict:
        """Normalize anomaly summary for API/Frontend"""
        if not anomaly_summary:
            return {"items": [], "mean": None, "std": None, "threshold": None}

        items_output = []
        for anomaly in anomaly_summary.get("items", []):
            items_output.append(
                {
                    "year": anomaly.get("year"),
                    "month": anomaly.get("month"),
                    "total": self.round_to_hundreds(anomaly.get("total")),
                    "deviation_percent": round(anomaly.get("deviation_percent", 0), 1),
                }
            )

        return {
            "items": items_output,
            "mean": self.round_to_hundreds(anomaly_summary.get("mean")) if anomaly_summary.get("mean") is not None else None,
            "std": self.round_to_hundreds(anomaly_summary.get("std")) if anomaly_summary.get("std") is not None else None,
            "threshold": self.round_to_hundreds(anomaly_summary.get("threshold")) if anomaly_summary.get("threshold") is not None else None,
        }

    def format_plan_context(self, plan_events: List[Dict]) -> List[Dict]:
        """Normalize plan context events"""
        context = []
        for event in plan_events:
            planned_amount = event.get("planned_amount")
            context.append(
                {
                    "category_name": event.get("category_name"),
                    "planned_amount": self.round_to_hundreds(planned_amount) if planned_amount is not None else None,
                    "justification": event.get("justification"),
                    "calculation_method": event.get("calculation_method"),
                }
            )
        return context

    @staticmethod
    def build_category_stats_index(stats_list: List[Dict]) -> Dict[str, Dict]:
        """Build lookup index for category statistics by name and id"""
        index: Dict[str, Dict] = {}
        for stats in stats_list:
            name = (stats.get("category_name") or "").lower()
            if name:
                index[name] = stats
            category_id = stats.get("category_id")
            if category_id is not None:
                index[str(category_id)] = stats
        return index

    def prepare_historical_category_stats(
        self,
        historical_data: List[Dict],
    ) -> List[Dict]:
        """Aggregate historical expenses by category for fallback item generation"""
        category_stats: Dict[str, Dict] = {}
        for exp in historical_data:
            category_id = exp.get("category_id")
            category_name = exp.get("category") or "Без категории"
            amount = exp.get("amount") or 0
            request_date = exp.get("request_date")

            key = str(category_id) if category_id is not None else category_name.lower()
            stats = category_stats.setdefault(
                key,
                {
                    "category_id": category_id,
                    "category_name": category_name,
                    "total": 0.0,
                    "count": 0,
                    "recent_amounts": [],
                    "last_dates": [],
                    "max_amount": 0.0,
                },
            )
            stats["total"] += amount
            stats["count"] += 1
            if amount:
                stats["recent_amounts"].append(amount)
                stats["max_amount"] = max(stats["max_amount"], amount)
            if request_date:
                stats["last_dates"].append(request_date)

        for stats in category_stats.values():
            stats["average"] = (stats["total"] / stats["count"]) if stats["count"] else 0
            stats["recent_amounts"] = sorted(stats["recent_amounts"][-5:])
            stats["last_dates"] = sorted(stats["last_dates"][-3:])

        return sorted(category_stats.values(), key=lambda x: x["total"], reverse=True)

    def augment_items_with_history(
        self,
        items: List[Dict],
        historical_data: List[Dict],
        approved_plans: Dict,
        historical_stats: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """If AI returned too few items, enrich with top historical categories"""
        if len(items) >= self.MIN_AI_ITEMS:
            return items

        if historical_stats is None:
            historical_stats = self.prepare_historical_category_stats(historical_data)
        if not historical_stats:
            return items

        existing_descriptions = {item.get("description", "").lower() for item in items}
        plan_categories = {
            (cat.get("category_name") or "").lower(): cat
            for cat in approved_plans.get("categories", [])
        }

        enriched_items = list(items)

        for stats in historical_stats:
            if len(enriched_items) >= self.MIN_AI_ITEMS:
                break

            category_name = stats.get("category_name")
            if not category_name:
                continue

            category_lower = category_name.lower()
            if category_lower in existing_descriptions:
                continue

            avg_amount = stats.get("average") or 0
            if avg_amount <= 0:
                continue

            rounded_amount = self.round_to_hundreds(avg_amount)
            if rounded_amount <= 0:
                continue

            range_delta = max(int(rounded_amount * self.DEFAULT_RANGE_DELTA), 100)
            range_min = max(0, rounded_amount - range_delta)
            range_max = rounded_amount + range_delta

            history_count = stats.get("count", 0)
            reasoning_parts = [
                f"Средний расход по категории за {history_count} операций: {rounded_amount:,.0f} ₽"
            ]
            if stats.get("last_dates"):
                last_dates = ", ".join(stats["last_dates"])
                reasoning_parts.append(f"Последние операции: {last_dates}")

            plan_entry = plan_categories.get(category_lower)
            if plan_entry and plan_entry.get("planned_amount"):
                reasoning_parts.append(
                    f"Утверждённый план: {plan_entry['planned_amount']:,.0f} ₽"
                )

            enriched_items.append(
                {
                    "description": category_name,
                    "amount": rounded_amount,
                    "range_min": range_min,
                    "range_max": range_max,
                    "reasoning": "На основе истории: " + "; ".join(reasoning_parts),
                    "source": "history",
                    "confidence": 60 if history_count >= 6 else 45,
                    "category_hint": stats.get("category_id"),
                }
            )

        return enriched_items

    def apply_statistical_guards(
        self,
        items: List[Dict],
        category_stats_index: Dict[str, Dict],
        approved_plans: Dict,
    ) -> List[Dict]:
        """Clamp anomalous amounts using historical stats and approved plan"""
        plan_by_name = {}
        if approved_plans.get("has_approved_plan"):
            for cat in approved_plans.get("categories", []):
                name = (cat.get("category_name") or "").lower()
                if name:
                    plan_by_name[name] = cat.get("planned_amount") or 0

        adjusted_items = []
        for item in items:
            description = str(item.get("description", "")).strip()
            if not description:
                adjusted_items.append(item)
                continue

            desc_lower = description.lower()
            category_hint = item.get("category_hint")

            stats = None
            if category_hint is not None and str(category_hint) in category_stats_index:
                stats = category_stats_index[str(category_hint)]
            if stats is None:
                stats = category_stats_index.get(desc_lower)

            plan_amount = plan_by_name.get(desc_lower)

            # Downgrade plan source if нет плана
            if item.get("source") == "plan" and plan_amount is None:
                item["source"] = "history"
                if "план" in item.get("reasoning", "").lower():
                    item["reasoning"] = item["reasoning"].replace(
                        "Из утверждённого плана", "На основе истории"
                    )

            if stats:
                avg = stats.get("average") or 0
                max_amount = stats.get("max_amount") or 0
                recent_amounts = stats.get("recent_amounts") or []
                recent_max = max(recent_amounts) if recent_amounts else max_amount
                # Allow небольшое увеличение относительно среднего, но ограничиваем крайними значениями
                allowed_history = max(avg * 1.5, recent_max, max_amount)
                allowed_history = self.round_to_hundreds(allowed_history)

                upper_bound = allowed_history if allowed_history else None

                if plan_amount:
                    plan_bound = self.round_to_hundreds(plan_amount * 1.05)
                    upper_bound = plan_bound if upper_bound is None else min(upper_bound, plan_bound)

                if upper_bound and upper_bound > 0 and item["amount"] > upper_bound:
                    previous_amount = item["amount"]
                    item["amount"] = upper_bound
                    range_delta = max(int(item["amount"] * self.DEFAULT_RANGE_DELTA), 100)
                    item["range_min"] = max(0, item["amount"] - range_delta)
                    item["range_max"] = item["amount"] + range_delta

                    adjustment_note = (
                        f"Ограничено планом {self.round_to_hundreds(plan_amount):,.0f} ₽"
                        if plan_amount
                        else f"Скорректировано до {upper_bound:,.0f} ₽ по историческим данным"
                    )
                    if adjustment_note not in item.get("reasoning", ""):
                        item["reasoning"] = (item.get("reasoning", "") + "; " + adjustment_note).strip("; ")

                    logger.info(
                        "AI forecast amount adjusted for %s: %s -> %s (upper_bound=%s, plan=%s)",
                        description,
                        previous_amount,
                        item["amount"],
                        upper_bound,
                        plan_amount,
                    )

            adjusted_items.append(item)

        return adjusted_items

    def build_ai_prompt(
        self,
        historical_data: List[Dict],
        statistics: Dict,
        approved_plans: Dict,
        year: int,
        month: int,
        category_name: Optional[str] = None,
        baseline_metrics: Optional[Dict] = None,
        anomaly_summary: Optional[Dict] = None,
        plan_events: Optional[List[Dict]] = None,
    ) -> str:
        """
        Build AI prompt for expense forecasting

        Args:
            historical_data: List of historical expenses
            statistics: Statistical summary
            approved_plans: Approved budget plans data
            year: Target forecast year
            month: Target forecast month
            category_name: Optional category name for context
            baseline_metrics: Calculated statistical baselines
            anomaly_summary: Detected anomalies information
            plan_events: Notable external events from approved plan

        Returns:
            Formatted prompt string for AI
        """
        category_context = f" для категории '{category_name}'" if category_name else ""

        baseline_metrics = baseline_metrics or self.calculate_baseline_metrics(statistics, year, month)
        anomaly_summary = anomaly_summary or self.detect_anomalies(statistics)
        plan_events = plan_events or self.extract_plan_events(approved_plans)

        # Format ALL monthly statistics (not just last 6)
        monthly_text = "\n".join(
            [
                f"- {m['year']}-{m['month']:02d}: {m['count']} расходов, сумма {m['total']:,.0f} ₽, средний {m['average']:,.0f} ₽"
                for m in statistics["monthly_data"]
            ]
        )

        # Baseline metrics summary (simple average, moving average, seasonal reference)
        baseline_lines = []
        simple_avg = baseline_metrics.get("simple_average")
        if simple_avg:
            baseline_lines.append(f"- Simple average (средняя сумма в месяц): {simple_avg:,.0f} ₽")

        moving_avg = baseline_metrics.get("moving_average")
        if moving_avg:
            baseline_lines.append(f"- Moving average (последние 3 месяца): {moving_avg:,.0f} ₽")

        seasonal_reference = baseline_metrics.get("seasonal_reference")
        if seasonal_reference:
            baseline_lines.append(f"- Seasonal (тот же месяц прошлого года): {seasonal_reference:,.0f} ₽")
        else:
            baseline_lines.append("- Seasonal: нет данных по этому месяцу прошлого года")

        last_12_total = baseline_metrics.get("last_12_months_total")
        if last_12_total:
            baseline_lines.append(f"- Total last 12 months: {last_12_total:,.0f} ₽")

        baseline_text = "\n".join(baseline_lines)

        # Anomaly summary
        anomaly_lines = []
        anomaly_items = anomaly_summary.get("items", []) if anomaly_summary else []
        if anomaly_items:
            for anomaly in anomaly_items[:5]:
                deviation = anomaly.get("deviation_percent") or 0
                deviation_sign = "+" if deviation >= 0 else "-"
                anomaly_lines.append(
                    f"- {anomaly['year']}-{anomaly['month']:02d}: {anomaly['total']:,.0f} ₽ ({deviation_sign}{abs(deviation):.1f}% к среднему)"
                )
        else:
            anomaly_lines.append("- Существенных выбросов не обнаружено (порог ±1.5σ)")

        anomalies_text = "\n".join(anomaly_lines)

        # Plan events (justifications, external drivers)
        plan_event_lines = []
        if plan_events:
            for event in plan_events[:10]:
                justification = event.get("justification")
                method = event.get("calculation_method")
                parts = [f"{event.get('category_name')}: {event.get('planned_amount'):,.0f} ₽"]
                if justification:
                    parts.append(f"Обоснование: {justification}")
                if method and method != "manual":
                    parts.append(f"Метод расчета: {method}")
                plan_event_lines.append("- " + " | ".join(parts))
        else:
            plan_event_lines.append("- В утвержденном плане нет дополнительных обоснований или событий")

        plan_events_text = "\n".join(plan_event_lines)

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

        # Format approved budget plans (if available)
        approved_plans_text = ""
        if approved_plans.get("has_approved_plan"):
            categories_list = "\n".join(
                [
                    f"- {cat['category_name']}: {cat['planned_amount']:,.0f} ₽ ({cat['type']}){'  | Обоснование: ' + cat['justification'] if cat['justification'] else ''}"
                    for cat in approved_plans["categories"]
                ]
            )
            approved_plans_text = f"""

💼 УТВЕРЖДЁННЫЙ БЮДЖЕТНЫЙ ПЛАН НА {month:02d}.{year}:

Версия: {approved_plans['version_name']}
Утверждён: {approved_plans['approved_at'][:10] if approved_plans['approved_at'] else 'N/A'}
Общая сумма плана: {approved_plans['total_planned']:,.0f} ₽

Детализация по категориям:
{categories_list}

⚠️ ВАЖНО: Утверждённый бюджетный план имеет ПРИОРИТЕТ при формировании прогноза!
Используй данные из плана как базовую основу и дополни их историческими данными для категорий, не указанных в плане."""

        prompt = f"""Ты - эксперт по финансовому прогнозированию.

ЗАДАЧА: Сгенерируй детальный прогноз расходов{category_context} на {month:02d}.{year} на основе утверждённого бюджета, статистических бенчмарков и исторических данных.

📊 ИСТОРИЧЕСКИЕ ДАННЫЕ ЗА 24 МЕСЯЦА:

Помесячная статистика:
{monthly_text}

Средний расход в месяц: {statistics['overall_average']:,.0f} ₽
Всего расходов за период: {statistics['total_expenses']}
{seasonality_text}
{trend_text}

Топ категорий расходов:
{category_text}

📌 Базовые статистические ориентиры:
{baseline_text}

🚨 Аномалии и выбросы:
{anomalies_text}

🗓️ Внешние события и обоснования (из утверждённого плана):
{plan_events_text}
{approved_plans_text}

📋 ИНСТРУКЦИИ:
1. ПРИОРИТЕТ: Если есть утверждённый бюджетный план - используй суммы из него как базовую основу
2. Для категорий из утверждённого плана обязательно укажи в reasoning источник "Из утверждённого плана"
3. Дополни прогноз категориями из исторических данных, которых нет в плане, отмечая источник "На основе истории"
4. Учти помесячную динамику: тренды роста/снижения, стабильность, сезонность
5. Обязательно учитывай данные за {month:02d}.{year-1} (если есть) как сезонный ориентир
6. Укажи новые или разовые события (проекты, найм, скачки) и их влияние
7. Сгенерируй 7-15 статей расходов, укажи `source` (plan/history/other) и `confidence` (0-100)
8. Для каждой статьи укажи диапазон `range_min`/`range_max` (округляя до сотен) и обоснование
9. Верни массив `scenarios` минимум из 3 сценариев: base, optimistic, pessimistic. Для каждого: `name`, `label`, `probability` (в сумме ≈100), `total`, `range_min`, `range_max`, `description`
10. `forecast_total` должен совпадать с total базового сценария
11. Добавь `correlations` (0-5 элементов) с полями `driver`, `impact`, `confidence`, `lag_months` (если есть задержка)
12. Добавь `recommendations` (0-5 элементов) с `title`, `description`, `potential_saving` (в ₽, если применимо)
13. Включи `quality_notes` (как оцениваешь надежность прогноза, какие риски/пробелы в данных)
14. Поле `confidence` (0-100) должно отражать уверенность в базовом сценарии
15. ⚠️ Округляй ВСЕ суммы (total, amount, range_min, range_max, potential_saving) до сотен (например: 120000, 85300)

ФОРМАТ ОТВЕТА (JSON):
{{
  "forecast_total": 1200000,
  "confidence": 85,
  "scenarios": [
    {{
      "name": "base",
      "label": "Базовый",
      "probability": 60,
      "total": 1200000,
      "range_min": 1150000,
      "range_max": 1250000,
      "description": "Рост по текущему тренду и плановые платежи."
    }},
    {{
      "name": "optimistic",
      "label": "Оптимистичный",
      "probability": 20,
      "total": 1100000,
      "range_min": 1060000,
      "range_max": 1140000,
      "description": "Скоращение аутсорса и оптимизация облака."
    }},
    {{
      "name": "pessimistic",
      "label": "Пессимистичный",
      "probability": 20,
      "total": 1320000,
      "range_min": 1280000,
      "range_max": 1360000,
      "description": "Продление проекта и рост аутсорса."
    }}
  ],
  "items": [
    {{
      "description": "Лицензии Microsoft 365",
      "amount": 450000,
      "range_min": 440000,
      "range_max": 460000,
      "reasoning": "Из утверждённого плана: 450000 ₽. Годовой платеж в марте.",
      "source": "plan",
      "confidence": 90
    }},
    {{
      "description": "Аутсорс разработки",
      "amount": 320000,
      "range_min": 300000,
      "range_max": 340000,
      "reasoning": "На основе истории: рост +8-10% последние 4 месяца из-за нового проекта.",
      "source": "history",
      "confidence": 75
    }}
  ],
  "correlations": [
    {{
      "driver": "Аутсорс разработки",
      "impact": "+15% к расходам на облако через 1 месяц",
      "confidence": 70,
      "lag_months": 1
    }}
  ],
  "recommendations": [
    {{
      "title": "Оптимизация облака",
      "description": "Закрепить Reserved Instances и отключить неиспользуемые ресурсы.",
      "potential_saving": 90000
    }}
  ],
  "summary": "Прогноз основан на утверждённом плане и подтверждённых трендах. Учитываем сезонный платеж по лицензиям и рост аутсорса.",
  "quality_notes": "Высокая уверенность: 18 месяцев данных, нет экстремальных выбросов. Риск: новые проекты с непредсказуемыми затратами."
}}

⚠️ ВАЖНО:
- Используй числа БЕЗ подчеркиваний и пробелов (например: 1200000, а не 1_200_000)
- Округляй ВСЕ суммы и диапазоны до сотен
- Отвечай ТОЛЬКО валидным JSON без дополнительного текста."""

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
        # Get historical data (24 months обеспечивает лучшую сезонность и тренды)
        historical_expenses = self.get_historical_expenses(
            department_id=department_id,
            lookback_months=24,
            category_id=category_id,
        )

        # Get statistics
        statistics = self.get_expense_statistics(
            department_id=department_id, category_id=category_id
        )

        # Get approved budget plans for the target month
        approved_plans = self.get_approved_budget_plans(
            department_id=department_id,
            year=year,
            month=month,
            category_id=category_id,
        )

        # Baselines, anomalies и события для использования в промпте и последующем UI
        baseline_metrics = self.calculate_baseline_metrics(statistics, year, month)
        anomaly_summary = self.detect_anomalies(statistics)
        plan_events = self.extract_plan_events(approved_plans)
        formatted_baselines = self.format_baseline_metrics(baseline_metrics)
        formatted_anomalies = self.format_anomaly_summary(anomaly_summary)
        formatted_plan_context = self.format_plan_context(plan_events)
        category_stats_list = self.prepare_historical_category_stats(historical_expenses)
        category_stats_index = self.build_category_stats_index(category_stats_list)

        if not historical_expenses and not approved_plans.get("has_approved_plan"):
            summary_text = "Недостаточно исторических данных и нет утверждённого плана для формирования AI-прогноза."
            base_total = (
                formatted_baselines["simple_average"]
                or formatted_baselines["seasonal_reference"]
                or formatted_baselines["moving_average"]
                or 0
            )
            return {
                "success": False,
                "error": "Недостаточно данных для AI прогноза",
                "forecast_total": base_total,
                "confidence": 30,
                "items": [],
                "scenarios": [
                    {
                        "name": "base",
                        "label": "Базовый",
                        "probability": 100,
                        "total": base_total,
                        "range_min": base_total,
                        "range_max": base_total,
                        "description": "Средний расход за период используется как единственный сценарий из-за отсутствия входных данных.",
                    }
                ],
                "correlations": [],
                "recommendations": [],
                "summary": summary_text,
                "quality_notes": "Накопите 6-12 месяцев истории или утвердите бюджетный план для AI прогноза.",
                "baseline_metrics": formatted_baselines,
                "anomaly_summary": formatted_anomalies,
                "plan_context": formatted_plan_context,
            }

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
            approved_plans=approved_plans,
            year=year,
            month=month,
            category_name=category_name,
            baseline_metrics=baseline_metrics,
            anomaly_summary=anomaly_summary,
            plan_events=plan_events,
        )

        # Call AI API
        logger.info(f"Calling AI API for forecast: year={year}, month={month}, department_id={department_id}")

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

                logger.info(f"AI API response status: {response.status_code}")

                if response.status_code != 200:
                    logger.error(f"AI API error - Status {response.status_code}, Response: {response.text[:500]}")
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

                logger.info(f"AI raw response: {ai_content}")

                # Try to extract JSON from markdown code blocks if present
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_content, re.DOTALL)
                if json_match:
                    ai_content = json_match.group(1)
                    logger.info(f"Extracted JSON from markdown: {ai_content}")

                # Remove underscores from numeric literals (e.g., 1_200_000 -> 1200000)
                # This handles Python/JS style number formatting that AI might use
                ai_content = re.sub(r'(\d)_(\d)', r'\1\2', ai_content)
                ai_content = re.sub(r'(\d)_(\d)', r'\1\2', ai_content)  # Run twice for multiple underscores
                logger.info(f"Cleaned JSON: {ai_content[:200]}...")

                try:
                    forecast_data = json.loads(ai_content)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {e}, content: {ai_content}")
                    # Fallback: use statistical average
                    fallback_total = (
                        formatted_baselines["simple_average"]
                        or formatted_baselines["seasonal_reference"]
                        or formatted_baselines["moving_average"]
                        or 0
                    )
                    return {
                        "success": False,
                        "error": f"AI response parsing failed: {str(e)}",
                        "forecast_total": fallback_total,
                        "confidence": 50,
                        "items": [],
                        "scenarios": [
                            {
                                "name": "base",
                                "label": "Базовый",
                                "probability": 100,
                                "total": fallback_total,
                                "range_min": fallback_total,
                                "range_max": fallback_total,
                                "description": "Автоматический сценарий по среднему расходу (AI не вернул данные).",
                            }
                        ],
                        "correlations": [],
                        "recommendations": [],
                        "summary": f"Ошибка парсинга AI ответа. Используется средний расход: {statistics['overall_average']:,.0f} ₽",
                        "quality_notes": "AI ответ не разобран, использовано статистическое среднее.",
                        "baseline_metrics": formatted_baselines,
                        "anomaly_summary": formatted_anomalies,
                        "plan_context": formatted_plan_context,
                    }

                if not isinstance(forecast_data, dict):
                    logger.error(f"AI response is not a JSON object: {type(forecast_data)}")
                    raise ValueError("AI response must be a JSON object")

                # Normalize forecast total and confidence
                forecast_total = self.round_to_hundreds(forecast_data.get("forecast_total"))
                if forecast_total == 0 and forecast_data.get("forecast_total"):
                    forecast_total = self.round_to_hundreds(forecast_data["forecast_total"])

                try:
                    confidence_value = int(forecast_data.get("confidence", 50))
                except (TypeError, ValueError):
                    confidence_value = 50
                confidence_value = max(0, min(100, confidence_value))

                # Normalize items
                normalized_items = []
                for item in forecast_data.get("items", []):
                    if not isinstance(item, dict):
                        continue
                    normalized_item = dict(item)
                    normalized_item["description"] = str(normalized_item.get("description", "")).strip()
                    normalized_item["reasoning"] = str(normalized_item.get("reasoning", "")).strip()

                    try:
                        normalized_item_confidence = int(normalized_item.get("confidence", confidence_value))
                    except (TypeError, ValueError):
                        normalized_item_confidence = confidence_value
                    normalized_item["confidence"] = max(0, min(100, normalized_item_confidence))

                    reasoning_lower = normalized_item["reasoning"].lower()
                    source_value = normalized_item.get("source")
                    if not source_value:
                        if "утвержд" in reasoning_lower or "план" in reasoning_lower:
                            source_value = "plan"
                        elif "истори" in reasoning_lower or "средн" in reasoning_lower:
                            source_value = "history"
                        else:
                            source_value = "history"
                    normalized_item["source"] = str(source_value).lower()

                    normalized_item["amount"] = self.round_to_hundreds(normalized_item.get("amount"))
                    normalized_item["range_min"] = self.round_to_hundreds(
                        normalized_item.get("range_min", normalized_item["amount"])
                    )
                    normalized_item["range_max"] = self.round_to_hundreds(
                        normalized_item.get("range_max", normalized_item["amount"])
                    )
                    if normalized_item.get("category_hint") is None:
                        stats = category_stats_index.get(normalized_item["description"].lower())
                        if stats and stats.get("category_id") is not None:
                            normalized_item["category_hint"] = stats.get("category_id")
                    normalized_items.append(normalized_item)
                normalized_items = self.augment_items_with_history(
                    normalized_items,
                    historical_expenses,
                    approved_plans,
                    historical_stats=category_stats_list,
                )
                normalized_items = self.apply_statistical_guards(
                    normalized_items,
                    category_stats_index,
                    approved_plans,
                )
                forecast_data["items"] = normalized_items

                # Normalize scenarios
                normalized_scenarios = []
                for scenario in forecast_data.get("scenarios", []):
                    if not isinstance(scenario, dict):
                        continue
                    normalized = dict(scenario)
                    name = str(normalized.get("name", "")).lower().strip()
                    if not name:
                        name = "base"
                    normalized["name"] = name
                    normalized["label"] = str(normalized.get("label", "") or name.title()).strip()
                    normalized["description"] = str(normalized.get("description", "")).strip()

                    try:
                        probability = int(normalized.get("probability", 0))
                    except (TypeError, ValueError):
                        probability = 0
                    normalized["probability"] = max(0, min(100, probability))

                    normalized["total"] = self.round_to_hundreds(normalized.get("total", forecast_total))
                    normalized["range_min"] = self.round_to_hundreds(
                        normalized.get("range_min", normalized["total"])
                    )
                    normalized["range_max"] = self.round_to_hundreds(
                        normalized.get("range_max", normalized["total"])
                    )
                    normalized_scenarios.append(normalized)

                if not normalized_scenarios:
                    base_total = forecast_total or self.round_to_hundreds(statistics["overall_average"])
                    normalized_scenarios.append(
                        {
                            "name": "base",
                            "label": "Базовый",
                            "probability": 100,
                            "total": base_total,
                            "range_min": base_total,
                            "range_max": base_total,
                            "description": "Автоматически добавленный базовый сценарий.",
                        }
                    )

                forecast_data["scenarios"] = normalized_scenarios
                base_scenario = next(
                    (s for s in normalized_scenarios if s.get("name") in {"base", "baseline"}),
                    normalized_scenarios[0],
                )
                forecast_total = base_scenario.get("total", forecast_total)
                forecast_data["forecast_total"] = forecast_total

                # Normalize correlations
                normalized_correlations = []
                for corr in forecast_data.get("correlations", []):
                    if not isinstance(corr, dict):
                        continue
                    driver = str(corr.get("driver", "")).strip()
                    impact = str(corr.get("impact", "")).strip()
                    if not driver or not impact:
                        continue
                    try:
                        corr_confidence = int(corr.get("confidence", 50))
                    except (TypeError, ValueError):
                        corr_confidence = 50
                    normalized_correlations.append(
                        {
                            "driver": driver,
                            "impact": impact,
                            "confidence": max(0, min(100, corr_confidence)),
                            "lag_months": corr.get("lag_months"),
                        }
                    )
                forecast_data["correlations"] = normalized_correlations

                # Normalize recommendations
                normalized_recommendations = []
                for rec in forecast_data.get("recommendations", []):
                    if not isinstance(rec, dict):
                        continue
                    title = str(rec.get("title", "")).strip()
                    description = str(rec.get("description", "")).strip()
                    if not title and not description:
                        continue
                    normalized_rec = {"title": title, "description": description}
                    if rec.get("potential_saving") is not None:
                        normalized_rec["potential_saving"] = self.round_to_hundreds(rec.get("potential_saving"))
                    normalized_recommendations.append(normalized_rec)
                forecast_data["recommendations"] = normalized_recommendations

                forecast_data["summary"] = str(forecast_data.get("summary", "")).strip()
                forecast_data["quality_notes"] = str(forecast_data.get("quality_notes", "")).strip()
                forecast_data["confidence"] = confidence_value

                # Attach baseline/anomaly/plan context for UI transparency
                forecast_data["baseline_metrics"] = formatted_baselines
                forecast_data["anomaly_summary"] = formatted_anomalies
                forecast_data["plan_context"] = formatted_plan_context

                # Add success flag and metadata
                forecast_data["success"] = True
                forecast_data["ai_model"] = self.AI_MODEL
                forecast_data["generated_at"] = datetime.now().isoformat()
                forecast_data["historical_months"] = len(statistics["monthly_data"])
                forecast_data["has_approved_plan"] = approved_plans.get("has_approved_plan", False)
                if approved_plans.get("has_approved_plan"):
                    forecast_data["approved_plan_total"] = self.round_to_hundreds(approved_plans.get("total_planned", 0))
                    forecast_data["approved_plan_version"] = approved_plans.get("version_name", "")

                return forecast_data

        except Exception as e:
            # Log the actual error for debugging
            logger.error(f"AI forecast service error: {str(e)}", exc_info=True)

            # Fallback to statistical average on any error
            fallback_total = (
                formatted_baselines["simple_average"]
                or formatted_baselines["seasonal_reference"]
                or formatted_baselines["moving_average"]
                or 0
            )

            return {
                "success": False,
                "error": str(e),
                "forecast_total": fallback_total,
                "confidence": 45,
                "items": [],
                "scenarios": [
                    {
                        "name": "base",
                        "label": "Базовый",
                        "probability": 100,
                        "total": fallback_total,
                        "range_min": fallback_total,
                        "range_max": fallback_total,
                        "description": "Средний расход за период. AI недоступен.",
                    }
                ],
                "correlations": [],
                "recommendations": [],
                "summary": f"Ошибка подключения к AI. Используется средний расход: {statistics['overall_average']:,.0f} ₽",
                "quality_notes": "AI не ответил, возвращены статистические значения.",
                "baseline_metrics": formatted_baselines,
                "anomaly_summary": formatted_anomalies,
                "plan_context": formatted_plan_context,
            }
