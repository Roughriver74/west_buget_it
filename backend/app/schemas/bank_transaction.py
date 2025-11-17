"""
Pydantic schemas for Bank Transactions
"""
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field
from app.db.models import PaymentSourceEnum, BankTransactionTypeEnum


class BankTransactionBase(BaseModel):
    """Base schema for bank transaction"""
    transaction_date: date
    amount: Decimal
    transaction_type: str = Field(..., description="DEBIT or CREDIT")
    payment_source: Optional[PaymentSourceEnum] = Field(default=PaymentSourceEnum.BANK, description="Payment source: BANK or CASH")
    counterparty_name: Optional[str] = None
    counterparty_inn: Optional[str] = None
    counterparty_kpp: Optional[str] = None
    counterparty_account: Optional[str] = None
    counterparty_bank: Optional[str] = None
    counterparty_bik: Optional[str] = None
    payment_purpose: Optional[str] = None
    business_operation: Optional[str] = Field(None, description="ХозяйственнаяОперация from 1C for auto-categorization")
    organization_id: Optional[int] = None
    account_number: Optional[str] = None
    document_number: Optional[str] = None
    document_date: Optional[date] = None
    notes: Optional[str] = None


class BankTransactionCreate(BankTransactionBase):
    """Schema for creating bank transaction"""
    department_id: int


class BankTransactionUpdate(BaseModel):
    """Schema for updating bank transaction"""
    category_id: Optional[int] = None
    expense_id: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    is_regular_payment: Optional[bool] = None


class BankTransactionCategorize(BaseModel):
    """Schema for categorizing transaction"""
    category_id: int
    notes: Optional[str] = None


class BankTransactionLink(BaseModel):
    """Schema for linking transaction to expense"""
    expense_id: int
    notes: Optional[str] = None


class BankTransactionInDB(BankTransactionBase):
    """Schema for bank transaction from database"""
    id: int
    department_id: int

    # Classification
    category_id: Optional[int] = None
    category_confidence: Optional[Decimal] = None
    suggested_category_id: Optional[int] = None

    # Matching
    expense_id: Optional[int] = None
    matching_score: Optional[Decimal] = None
    suggested_expense_id: Optional[int] = None

    # Status
    status: str
    is_regular_payment: bool
    regular_payment_pattern_id: Optional[int] = None

    # Audit
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None

    # Import
    import_source: Optional[str] = None
    import_file_name: Optional[str] = None
    imported_at: Optional[datetime] = None
    external_id_1c: Optional[str] = None

    # System fields
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BankTransactionWithRelations(BankTransactionInDB):
    """Bank transaction with related entities"""
    category_name: Optional[str] = None
    suggested_category_name: Optional[str] = None
    expense_number: Optional[str] = None
    suggested_expense_number: Optional[str] = None
    organization_name: Optional[str] = None
    reviewed_by_name: Optional[str] = None
    department_name: Optional[str] = None


class BankTransactionList(BaseModel):
    """List of bank transactions with pagination"""
    total: int
    items: List[BankTransactionWithRelations]
    page: int
    page_size: int
    pages: int


class BankTransactionStats(BaseModel):
    """Statistics for bank transactions"""
    total_transactions: int
    total_amount: Decimal  # Deprecated: use total_credit_amount and total_debit_amount
    total_credit_amount: Decimal = Field(default=Decimal('0'), description="Total sum of CREDIT (приход) transactions")
    total_debit_amount: Decimal = Field(default=Decimal('0'), description="Total sum of DEBIT (расход) transactions")
    new_count: int
    categorized_count: int
    matched_count: int
    approved_count: int
    needs_review_count: int
    avg_category_confidence: Optional[float] = None
    avg_matching_score: Optional[float] = None


class BankTransactionImportResult(BaseModel):
    """Result of bank transaction import"""
    total_rows: int
    imported: int
    skipped: int
    errors: List[dict]
    warnings: List[dict]


class MatchingSuggestion(BaseModel):
    """Suggestion for matching transaction to expense"""
    expense_id: int
    expense_number: str
    expense_amount: Decimal
    expense_date: date
    expense_category_id: Optional[int] = None
    expense_contractor_name: Optional[str] = None
    matching_score: float
    match_reasons: List[str]


class CategorySuggestion(BaseModel):
    """AI suggestion for transaction category"""
    category_id: int
    category_name: str
    confidence: float
    reasoning: List[str]


class RegularPaymentPattern(BaseModel):
    """Pattern for regular payments"""
    id: int
    counterparty_inn: Optional[str] = None
    counterparty_name: Optional[str] = None
    category_id: int
    category_name: str
    avg_amount: Decimal
    frequency_days: int  # Average days between payments
    last_payment_date: date
    transaction_count: int


class BulkCategorizeRequest(BaseModel):
    """Request for bulk categorization"""
    transaction_ids: List[int]
    category_id: int
    notes: Optional[str] = None


class BulkLinkRequest(BaseModel):
    """Request for bulk linking to expenses"""
    links: List[dict]  # [{"transaction_id": 1, "expense_id": 10}, ...]


class BulkStatusUpdateRequest(BaseModel):
    """Request for bulk status update"""
    transaction_ids: List[int]
    status: str


class ODataSyncRequest(BaseModel):
    """Request for OData sync from 1C"""
    odata_url: str = Field(
        default="http://10.10.100.77/trade/odata/standard.odata",
        description="1C OData base URL"
    )
    username: str = Field(default="odata.user", description="1C username")
    password: str = Field(default="ak228Hu2hbs28", description="1C password")
    department_id: int = Field(..., description="Department ID for imported transactions")
    date_from: date = Field(..., description="Start date for sync")
    date_to: date = Field(..., description="End date for sync")
    auto_classify: bool = Field(default=True, description="Apply AI classification automatically")
    batch_size: int = Field(default=100, description="Batch size for fetching from 1C", ge=1, le=1000)


class ODataSyncResult(BaseModel):
    """Result of OData sync operation"""
    success: bool
    total_fetched: int = Field(description="Total records fetched from 1C")
    total_processed: int = Field(description="Total records processed")
    created: int = Field(description="New records created")
    updated: int = Field(description="Existing records updated")
    skipped: int = Field(description="Records skipped (duplicates)")
    auto_categorized: int = Field(description="Records auto-categorized by AI")
    errors: List[str] = Field(default_factory=list, description="List of errors")
    message: Optional[str] = None
    error: Optional[str] = None


class ODataTestConnectionRequest(BaseModel):
    """Request for testing OData connection"""
    odata_url: str
    username: str
    password: str
    timeout: int = 30


class ODataTestConnectionResult(BaseModel):
    """Result of OData connection test"""
    success: bool
    message: str
    status_code: Optional[int] = None
    url: Optional[str] = None
    error: Optional[str] = None


# Analytics Schemas

class BankTransactionKPIs(BaseModel):
    """Key Performance Indicators for bank transactions"""
    # Financial metrics
    total_debit_amount: Decimal = Field(description="Общая сумма расходов (DEBIT)")
    total_credit_amount: Decimal = Field(description="Общая сумма поступлений (CREDIT)")
    net_flow: Decimal = Field(description="Чистый поток (Credit - Debit)")
    total_transactions: int = Field(description="Общее количество транзакций")

    # Comparison with previous period
    debit_change_percent: Optional[float] = Field(None, description="% изменения расходов vs предыдущий период")
    credit_change_percent: Optional[float] = Field(None, description="% изменения поступлений vs предыдущий период")
    net_flow_change_percent: Optional[float] = Field(None, description="% изменения чистого потока")
    transactions_change: Optional[int] = Field(None, description="Изменение кол-ва транзакций")

    # Status distribution
    new_count: int = Field(description="Количество NEW транзакций")
    categorized_count: int = Field(description="Количество CATEGORIZED")
    matched_count: int = Field(description="Количество MATCHED")
    approved_count: int = Field(description="Количество APPROVED")
    needs_review_count: int = Field(description="Количество NEEDS_REVIEW")
    ignored_count: int = Field(description="Количество IGNORED")

    # Status percentages
    new_percent: float = Field(description="% NEW транзакций")
    categorized_percent: float = Field(description="% CATEGORIZED")
    matched_percent: float = Field(description="% MATCHED")
    approved_percent: float = Field(description="% APPROVED")
    needs_review_percent: float = Field(description="% NEEDS_REVIEW")
    ignored_percent: float = Field(description="% IGNORED")

    # AI metrics
    avg_category_confidence: Optional[float] = Field(None, description="Средняя уверенность AI")
    auto_categorized_count: int = Field(description="Авто-категоризированные")
    auto_categorized_percent: float = Field(description="% авто-категоризированных")
    regular_payments_count: int = Field(description="Регулярные платежи")
    regular_payments_percent: float = Field(description="% регулярных платежей")


class MonthlyFlowData(BaseModel):
    """Monthly cash flow data for time series chart"""
    year: int
    month: int
    month_name: str = Field(description="Название месяца (напр. 'Январь 2025')")
    debit_amount: Decimal = Field(description="Сумма расходов за месяц")
    credit_amount: Decimal = Field(description="Сумма поступлений за месяц")
    net_flow: Decimal = Field(description="Чистый поток за месяц")
    transaction_count: int = Field(description="Количество транзакций")
    avg_confidence: Optional[float] = Field(None, description="Средняя уверенность AI")


class CategoryBreakdown(BaseModel):
    """Breakdown by category"""
    category_id: int
    category_name: str
    category_type: Optional[str] = Field(None, description="OPEX/CAPEX/etc")
    transaction_count: int
    total_amount: Decimal
    avg_amount: Decimal
    avg_confidence: Optional[float] = Field(None, description="Средняя уверенность AI")
    percent_of_total: float = Field(description="% от общей суммы")


class CounterpartyBreakdown(BaseModel):
    """Breakdown by counterparty"""
    counterparty_inn: Optional[str] = None
    counterparty_name: str
    transaction_count: int
    total_amount: Decimal
    avg_amount: Decimal
    first_transaction_date: date
    last_transaction_date: date
    is_regular: bool = Field(description="Признак регулярного контрагента")


class RegionalData(BaseModel):
    """Regional distribution"""
    region: str = Field(description="MOSCOW/SPB/REGIONS/FOREIGN")
    transaction_count: int
    total_amount: Decimal
    percent_of_total: float


class SourceDistribution(BaseModel):
    """Distribution by payment source (BANK/CASH)"""
    payment_source: str = Field(description="BANK or CASH")
    year: int
    month: int
    month_name: str
    transaction_count: int
    total_amount: Decimal


class ProcessingFunnelStage(BaseModel):
    """One stage in processing funnel"""
    status: str
    count: int
    amount: Decimal
    percent_of_total: float = Field(description="% от общего количества")
    avg_processing_hours: Optional[float] = Field(None, description="Среднее время обработки (часы)")


class ProcessingFunnelData(BaseModel):
    """Processing funnel data"""
    stages: List[ProcessingFunnelStage]
    total_count: int
    conversion_rate_to_approved: float = Field(description="% конверсии в APPROVED")


class ConfidenceBracket(BaseModel):
    """AI confidence bracket"""
    bracket: str = Field(description="High/Medium/Low/Very Low")
    min_confidence: float
    max_confidence: float
    count: int
    total_amount: Decimal
    percent_of_total: float


class AIPerformanceData(BaseModel):
    """AI performance metrics"""
    confidence_distribution: List[ConfidenceBracket]
    avg_confidence: float
    high_confidence_count: int = Field(description="Количество с confidence >= 0.9")
    high_confidence_percent: float
    low_confidence_count: int = Field(description="Количество с confidence < 0.7")
    low_confidence_percent: float


class ExhibitionData(BaseModel):
    """Exhibition/event related transaction"""
    transaction_id: int
    transaction_date: date
    exhibition: str = Field(description="Название выставки/мероприятия")
    counterparty_name: str
    amount: Decimal
    category_name: Optional[str] = None


class LowConfidenceItem(BaseModel):
    """Transaction with low AI confidence"""
    transaction_id: int
    transaction_date: date
    counterparty_name: str
    amount: Decimal
    payment_purpose: Optional[str] = None
    suggested_category_name: Optional[str] = None
    category_confidence: float
    status: str


class RegularPaymentSummary(BaseModel):
    """Summary of regular payment pattern"""
    counterparty_inn: Optional[str] = None
    counterparty_name: str
    category_name: str
    avg_amount: Decimal
    amount_variance: Decimal = Field(description="Стандартное отклонение суммы")
    payment_count: int
    avg_days_between: Optional[float] = Field(None, description="Среднее количество дней между платежами")
    last_payment_date: date
    next_expected_date: Optional[date] = Field(None, description="Ожидаемая дата следующего платежа")


class DailyFlowData(BaseModel):
    """Daily cash flow details"""
    date: date
    debit_amount: Decimal
    credit_amount: Decimal
    net_flow: Decimal
    transaction_count: int


class ActivityHeatmapPoint(BaseModel):
    """Bucket for day-of-week/hour activity"""
    day_of_week: int = Field(ge=0, le=6, description="0=Monday ... 6=Sunday")
    hour: int = Field(ge=0, le=23)
    transaction_count: int
    total_amount: Decimal
    avg_amount: Decimal


class StatusTimelinePoint(BaseModel):
    """Daily timeline of statuses"""
    date: date
    new_count: int
    categorized_count: int
    matched_count: int
    approved_count: int
    needs_review_count: int
    ignored_count: int


class ConfidenceScatterPoint(BaseModel):
    """Single point for confidence vs amount scatter view"""
    transaction_id: int
    transaction_date: date
    counterparty_name: Optional[str] = None
    amount: Decimal
    category_confidence: Optional[float] = None
    status: str
    transaction_type: BankTransactionTypeEnum
    is_regular_payment: bool


class BankTransactionAnalytics(BaseModel):
    """Complete analytics data for bank transactions"""
    kpis: BankTransactionKPIs
    monthly_flow: List[MonthlyFlowData]
    daily_flow: List[DailyFlowData]
    top_categories: List[CategoryBreakdown]
    category_type_distribution: List[CategoryBreakdown] = Field(description="OPEX vs CAPEX breakdown")
    top_counterparties: List[CounterpartyBreakdown]
    regional_distribution: List[RegionalData]
    source_distribution: List[SourceDistribution]
    processing_funnel: ProcessingFunnelData
    ai_performance: AIPerformanceData
    low_confidence_items: List[LowConfidenceItem]
    activity_heatmap: List[ActivityHeatmapPoint]
    status_timeline: List[StatusTimelinePoint]
    confidence_scatter: List[ConfidenceScatterPoint]
    regular_payments: List[RegularPaymentSummary]
    exhibitions: List[ExhibitionData]
