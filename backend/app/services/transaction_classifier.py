"""
AI-powered Transaction Classifier
Automatically suggests categories for bank transactions based on payment purpose and counterparty
"""
from typing import Optional, Tuple, List, Dict
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import (
    BankTransaction,
    BudgetCategory,
    ExpenseTypeEnum,
)


class TransactionClassifier:
    """
    AI-powered classifier for bank transactions
    Uses rule-based system with keyword matching and historical data
    Can be enhanced with ML model in the future
    """

    # Keyword mapping for Russian categories (OPEX)
    OPEX_KEYWORDS = {
        'Аренда помещений': [
            'аренда', 'арендная плата', 'арендные платежи', 'rent', 'rental',
            'помещение', 'офис', 'склад', 'площадь'
        ],
        'Услуги связи': [
            'связь', 'интернет', 'телефон', 'мобильная связь', 'телеком',
            'internet', 'telephone', 'mobile', 'сотовая', 'телефония',
            'домен', 'хостинг', 'vpn'
        ],
        'Канцтовары': [
            'канцтовары', 'канцелярия', 'бумага', 'ручки', 'папки',
            'stationery', 'office supplies', 'офисные принадлежности'
        ],
        'Коммунальные услуги': [
            'коммунальные', 'электроэнергия', 'электричество', 'вода', 'отопление',
            'utilities', 'electricity', 'water', 'heating', 'свет', 'газ'
        ],
        'Программное обеспечение': [
            'по ', 'программное обеспечение', 'лицензия', 'software', 'license',
            'subscription', 'подписка', 'saas', 'облако', 'cloud'
        ],
        'Реклама и маркетинг': [
            'реклама', 'маркетинг', 'продвижение', 'advertising', 'marketing',
            'seo', 'контекстная реклама', 'яндекс директ', 'google ads'
        ],
        'Транспортные расходы': [
            'транспорт', 'бензин', 'топливо', 'гсм', 'парковка', 'такси',
            'transport', 'fuel', 'parking', 'taxi', 'uber', 'яндекс такси'
        ],
        'Обучение персонала': [
            'обучение', 'тренинг', 'курсы', 'семинар', 'training', 'education',
            'повышение квалификации', 'образование'
        ],
        'Банковские услуги': [
            'комиссия банка', 'банковская комиссия', 'рко', 'обслуживание счета',
            'bank commission', 'bank fee', 'эквайринг'
        ],
        'Юридические услуги': [
            'юридические услуги', 'юрист', 'адвокат', 'legal services',
            'нотариус', 'правовые услуги'
        ],
        'Бухгалтерские услуги': [
            'бухгалтерские услуги', 'бухгалтер', 'accounting', '1с',
            'отчетность', 'аудит'
        ],
    }

    # CAPEX keywords
    CAPEX_KEYWORDS = {
        'Оборудование': [
            'оборудование', 'станок', 'машина', 'equipment', 'hardware',
            'сервер', 'компьютер', 'ноутбук', 'принтер', 'мебель'
        ],
        'Программное обеспечение (CAPEX)': [
            'внедрение', 'разработка по', 'erp', 'crm система',
            'implementation', 'development'
        ],
    }

    # Tax keywords
    TAX_KEYWORDS = {
        'Налоги': [
            'налог', 'ндфл', 'ндс', 'налог на прибыль', 'страховые взносы',
            'tax', 'усн', 'енвд', 'пени', 'штраф'
        ],
    }

    def __init__(self, db: Session):
        self.db = db

    def classify(
        self,
        payment_purpose: Optional[str],
        counterparty_name: Optional[str],
        counterparty_inn: Optional[str],
        amount: Decimal,
        department_id: int
    ) -> Tuple[Optional[int], float, str]:
        """
        Classify transaction and return (category_id, confidence, reasoning)

        Returns:
            - category_id: Suggested category ID or None
            - confidence: Confidence score 0.0-1.0
            - reasoning: Human-readable explanation
        """
        # 1. Check historical data first (highest confidence)
        historical = self._get_historical_category(counterparty_inn, department_id)
        if historical:
            return historical['category_id'], 0.95, f"Исторические данные: контрагент всегда относится к категории '{historical['category_name']}' ({historical['count']} транзакций)"

        # 2. Analyze payment purpose text
        if payment_purpose:
            text_based = self._analyze_text(payment_purpose, department_id)
            if text_based:
                return text_based

        # 3. Analyze counterparty name
        if counterparty_name:
            name_based = self._analyze_text(counterparty_name, department_id)
            if name_based:
                category_id, confidence, reasoning = name_based
                return category_id, confidence * 0.8, f"По имени контрагента: {reasoning}"

        # No match found
        return None, 0.0, "Не удалось автоматически определить категорию"

    def _get_historical_category(
        self,
        counterparty_inn: Optional[str],
        department_id: int
    ) -> Optional[Dict]:
        """
        Get most common category for this counterparty from historical data
        """
        if not counterparty_inn:
            return None

        # Find most common category for this INN
        result = self.db.query(
            BankTransaction.category_id,
            BudgetCategory.name,
            func.count(BankTransaction.id).label('count')
        ).join(
            BudgetCategory,
            BankTransaction.category_id == BudgetCategory.id
        ).filter(
            BankTransaction.counterparty_inn == counterparty_inn,
            BankTransaction.department_id == department_id,
            BankTransaction.category_id.isnot(None),
            BankTransaction.is_active == True
        ).group_by(
            BankTransaction.category_id,
            BudgetCategory.name
        ).order_by(
            func.count(BankTransaction.id).desc()
        ).first()

        if result and result.count >= 2:  # At least 2 historical transactions
            return {
                'category_id': result.category_id,
                'category_name': result.name,
                'count': result.count
            }

        return None

    def _analyze_text(
        self,
        text: str,
        department_id: int
    ) -> Optional[Tuple[int, float, str]]:
        """
        Analyze text and match against keyword dictionaries
        Returns (category_id, confidence, reasoning)
        """
        text_lower = text.lower()

        # Check all keyword groups
        all_keywords = {
            **self.OPEX_KEYWORDS,
            **self.CAPEX_KEYWORDS,
            **self.TAX_KEYWORDS
        }

        matches = []
        for category_pattern, keywords in all_keywords.items():
            match_count = 0
            matched_keywords = []

            for keyword in keywords:
                if keyword.lower() in text_lower:
                    match_count += 1
                    matched_keywords.append(keyword)

            if match_count > 0:
                # Calculate confidence based on number of matches
                confidence = min(0.7 + (match_count * 0.1), 0.95)
                matches.append({
                    'pattern': category_pattern,
                    'count': match_count,
                    'confidence': confidence,
                    'keywords': matched_keywords
                })

        if not matches:
            return None

        # Sort by match count and confidence
        matches.sort(key=lambda x: (x['count'], x['confidence']), reverse=True)
        best_match = matches[0]

        # Find category in database
        category = self.db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department_id,
            BudgetCategory.name.ilike(f"%{best_match['pattern']}%"),
            BudgetCategory.is_active == True
        ).first()

        if not category:
            # Try to find by partial match
            category = self.db.query(BudgetCategory).filter(
                BudgetCategory.department_id == department_id,
                BudgetCategory.is_active == True
            ).all()

            # Find best match
            for cat in category:
                if any(kw.lower() in cat.name.lower() for kw in best_match['keywords']):
                    category = cat
                    break

        if category:
            reasoning = f"Найдены ключевые слова: {', '.join(best_match['keywords'][:3])}"
            return category.id, best_match['confidence'], reasoning

        return None

    def get_category_suggestions(
        self,
        payment_purpose: Optional[str],
        counterparty_name: Optional[str],
        counterparty_inn: Optional[str],
        amount: Decimal,
        department_id: int,
        top_n: int = 3
    ) -> List[Dict]:
        """
        Get multiple category suggestions with explanations
        """
        suggestions = []

        # Historical data
        historical = self._get_historical_category(counterparty_inn, department_id)
        if historical:
            suggestions.append({
                'category_id': historical['category_id'],
                'category_name': historical['category_name'],
                'confidence': 0.95,
                'reasoning': [f"Исторические данные ({historical['count']} транзакций)"]
            })

        # Text analysis
        if payment_purpose:
            text_result = self._analyze_text(payment_purpose, department_id)
            if text_result:
                cat_id, conf, reason = text_result
                cat = self.db.query(BudgetCategory).filter(BudgetCategory.id == cat_id).first()
                if cat:
                    suggestions.append({
                        'category_id': cat_id,
                        'category_name': cat.name,
                        'confidence': conf,
                        'reasoning': [reason]
                    })

        # Deduplicate by category_id
        seen = set()
        unique_suggestions = []
        for sugg in suggestions:
            if sugg['category_id'] not in seen:
                seen.add(sugg['category_id'])
                unique_suggestions.append(sugg)

        # Sort by confidence
        unique_suggestions.sort(key=lambda x: x['confidence'], reverse=True)

        return unique_suggestions[:top_n]


class RegularPaymentDetector:
    """
    Detect regular payments (subscriptions, rent, utilities, etc.)
    """

    def __init__(self, db: Session):
        self.db = db

    def detect_patterns(self, department_id: int) -> List[Dict]:
        """
        Detect regular payment patterns for a department
        Returns list of patterns with frequency and last payment date
        """
        # Find transactions with same counterparty_inn that occur regularly
        from datetime import datetime, timedelta

        patterns = []

        # Group by counterparty INN
        transactions_by_inn = self.db.query(
            BankTransaction.counterparty_inn,
            BankTransaction.counterparty_name,
            BankTransaction.category_id,
            func.count(BankTransaction.id).label('count'),
            func.avg(BankTransaction.amount).label('avg_amount'),
            func.max(BankTransaction.transaction_date).label('last_date')
        ).filter(
            BankTransaction.department_id == department_id,
            BankTransaction.counterparty_inn.isnot(None),
            BankTransaction.is_active == True,
            BankTransaction.transaction_type == 'DEBIT'
        ).group_by(
            BankTransaction.counterparty_inn,
            BankTransaction.counterparty_name,
            BankTransaction.category_id
        ).having(
            func.count(BankTransaction.id) >= 3  # At least 3 transactions
        ).all()

        for group in transactions_by_inn:
            # Get all transaction dates for this INN
            dates = self.db.query(BankTransaction.transaction_date).filter(
                BankTransaction.counterparty_inn == group.counterparty_inn,
                BankTransaction.department_id == department_id,
                BankTransaction.is_active == True
            ).order_by(BankTransaction.transaction_date).all()

            if len(dates) < 3:
                continue

            # Calculate average days between payments
            date_list = [d.transaction_date for d in dates]
            intervals = []
            for i in range(1, len(date_list)):
                delta = (date_list[i] - date_list[i-1]).days
                intervals.append(delta)

            avg_interval = sum(intervals) / len(intervals)
            interval_std = (sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)) ** 0.5

            # If interval is consistent (low variance), it's a regular payment
            if interval_std < avg_interval * 0.3:  # Less than 30% variation
                category = None
                if group.category_id:
                    category = self.db.query(BudgetCategory).filter(
                        BudgetCategory.id == group.category_id
                    ).first()

                patterns.append({
                    'counterparty_inn': group.counterparty_inn,
                    'counterparty_name': group.counterparty_name,
                    'category_id': group.category_id,
                    'category_name': category.name if category else None,
                    'avg_amount': float(group.avg_amount),
                    'frequency_days': int(avg_interval),
                    'last_payment_date': group.last_date.isoformat(),
                    'transaction_count': group.count,
                    'is_monthly': 25 <= avg_interval <= 35,  # ~monthly
                    'is_quarterly': 85 <= avg_interval <= 95,  # ~quarterly
                })

        return patterns

    def mark_regular_payments(self, department_id: int) -> int:
        """
        Mark transactions as regular payments based on detected patterns
        Returns number of transactions marked
        """
        patterns = self.detect_patterns(department_id)
        marked_count = 0

        for pattern in patterns:
            # Mark all transactions from this counterparty as regular
            updated = self.db.query(BankTransaction).filter(
                BankTransaction.counterparty_inn == pattern['counterparty_inn'],
                BankTransaction.department_id == department_id,
                BankTransaction.is_active == True
            ).update({
                'is_regular_payment': True
            })

            marked_count += updated

        self.db.commit()
        return marked_count
