"""
Pydantic schemas for invoice processing with AI OCR and parsing
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date as DateType, datetime
from decimal import Decimal


# ==================== Supplier & Buyer Data ====================

class SupplierData(BaseModel):
    """Данные поставщика из счета"""
    name: str = Field(..., description="Наименование организации")
    inn: Optional[str] = Field(None, description="ИНН", min_length=10, max_length=12)
    kpp: Optional[str] = Field(None, description="КПП", min_length=9, max_length=9)
    bank_name: Optional[str] = Field(None, description="Наименование банка")
    bik: Optional[str] = Field(None, description="БИК банка", min_length=9, max_length=9)
    account: Optional[str] = Field(None, description="Расчетный счет", min_length=20, max_length=20)
    corr_account: Optional[str] = Field(None, description="Корр. счет")

    @field_validator('inn')
    @classmethod
    def validate_inn(cls, v):
        if v and not v.isdigit():
            raise ValueError('ИНН должен содержать только цифры')
        if v and len(v) not in [10, 12]:
            raise ValueError('ИНН должен быть 10 или 12 цифр')
        return v


class BuyerData(BaseModel):
    """Данные покупателя из счета"""
    name: Optional[str] = Field(None, description="Наименование организации")
    inn: Optional[str] = Field(None, description="ИНН", min_length=10, max_length=12)
    kpp: Optional[str] = Field(None, description="КПП", min_length=9, max_length=9)

    @field_validator('inn')
    @classmethod
    def validate_inn(cls, v):
        if v and not v.isdigit():
            raise ValueError('ИНН должен содержать только цифры')
        if v and len(v) not in [10, 12]:
            raise ValueError('ИНН должен быть 10 или 12 цифр')
        return v


class InvoiceItem(BaseModel):
    """Позиция счета (табличная часть)"""
    description: str = Field(..., description="Наименование товара/услуги")
    quantity: Decimal = Field(default=Decimal("1"), description="Количество")
    unit: Optional[str] = Field(default="-", description="Единица измерения")
    price: Decimal = Field(..., description="Цена за единицу")
    amount: Decimal = Field(..., description="Сумма")


# ==================== Parsed Invoice Data ====================

class ParsedInvoiceData(BaseModel):
    """Распознанные данные счета (результат AI-парсинга)"""
    invoice_number: Optional[str] = Field(None, description="Номер счета")
    invoice_date: Optional[DateType] = Field(None, description="Дата счета")

    supplier: Optional[SupplierData] = Field(None, description="Данные поставщика")
    buyer: Optional[BuyerData] = Field(None, description="Данные покупателя")

    # Суммы
    amount_without_vat: Optional[Decimal] = Field(None, description="Сумма без НДС")
    vat_amount: Optional[Decimal] = Field(None, description="Сумма НДС")
    total_amount: Optional[Decimal] = Field(None, description="Всего к оплате")

    # Дополнительно
    payment_purpose: Optional[str] = Field(None, description="Назначение платежа")
    contract_number: Optional[str] = Field(None, description="Номер договора")
    contract_date: Optional[DateType] = Field(None, description="Дата договора")

    # Табличная часть
    items: List[InvoiceItem] = Field(default_factory=list, description="Позиции счета")


# ==================== Processing Results ====================

class OCRResult(BaseModel):
    """Результат OCR распознавания"""
    text: str = Field(..., description="Распознанный текст")
    confidence: Optional[float] = Field(None, description="Уверенность OCR (0-100%)")
    processing_time_sec: Optional[float] = Field(None, description="Время обработки в секундах")


class ProcessingError(BaseModel):
    """Ошибка обработки"""
    field: str = Field(..., description="Поле с ошибкой")
    message: str = Field(..., description="Описание ошибки")
    severity: str = Field(default="error", description="error | warning")


# ==================== Request/Response Schemas ====================

class InvoiceUploadResponse(BaseModel):
    """Ответ при загрузке файла счета"""
    success: bool
    invoice_id: int = Field(..., description="ID созданной записи")
    filename: str
    message: str


class InvoiceProcessRequest(BaseModel):
    """Запрос на обработку счета"""
    invoice_id: int = Field(..., description="ID загруженного счета")


class InvoiceProcessResponse(BaseModel):
    """Ответ после обработки счета"""
    success: bool
    invoice_id: int
    status: str = Field(..., description="PENDING | PROCESSING | PROCESSED | ERROR")

    ocr_result: Optional[OCRResult] = None
    parsed_data: Optional[ParsedInvoiceData] = None

    errors: List[ProcessingError] = Field(default_factory=list)
    warnings: List[ProcessingError] = Field(default_factory=list)

    processing_time_total_sec: Optional[float] = None


class CreateExpenseFromInvoiceRequest(BaseModel):
    """Запрос на создание expense из счета"""
    invoice_id: int = Field(..., description="ID обработанного счета")
    category_id: int = Field(..., description="ID категории бюджета")

    # Опциональные корректировки
    amount_override: Optional[Decimal] = Field(None, description="Переопределить сумму")
    description_override: Optional[str] = Field(None, description="Переопределить описание")
    contractor_id_override: Optional[int] = Field(None, description="Переопределить контрагента")


class CreateExpenseFromInvoiceResponse(BaseModel):
    """Ответ после создания expense"""
    success: bool
    expense_id: Optional[int] = None
    contractor_id: Optional[int] = None
    contractor_created: bool = False  # Был ли создан новый контрагент
    message: str


# ==================== List & Detail Schemas ====================

class ProcessedInvoiceListItem(BaseModel):
    """Элемент списка обработанных счетов"""
    id: int
    original_filename: str
    uploaded_at: datetime
    uploaded_by_name: str

    status: str
    invoice_number: Optional[str] = None
    invoice_date: Optional[DateType] = None
    supplier_name: Optional[str] = None
    supplier_inn: Optional[str] = None
    total_amount: Optional[Decimal] = None

    expense_id: Optional[int] = None
    contractor_id: Optional[int] = None

    # 1C Integration
    external_id_1c: Optional[str] = None
    created_in_1c_at: Optional[datetime] = None

    has_errors: bool = False
    has_warnings: bool = False

    class Config:
        from_attributes = True


class ProcessedInvoiceDetail(BaseModel):
    """Детальная информация об обработанном счете"""
    id: int
    department_id: int

    # Файл
    original_filename: str
    file_path: Optional[str] = None
    file_size_kb: Optional[int] = None
    uploaded_by: int
    uploaded_by_name: str
    uploaded_at: datetime

    # OCR
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[Decimal] = None
    ocr_processing_time_sec: Optional[Decimal] = None

    # Parsed data
    invoice_number: Optional[str] = None
    invoice_date: Optional[DateType] = None
    supplier_name: Optional[str] = None
    supplier_inn: Optional[str] = None
    supplier_kpp: Optional[str] = None
    supplier_bank_name: Optional[str] = None
    supplier_bik: Optional[str] = None
    supplier_account: Optional[str] = None
    amount_without_vat: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    payment_purpose: Optional[str] = None
    contract_number: Optional[str] = None
    contract_date: Optional[DateType] = None

    # Status
    status: str
    processed_at: Optional[datetime] = None

    # Relations
    expense_id: Optional[int] = None
    contractor_id: Optional[int] = None
    expense_created_at: Optional[datetime] = None

    # 1C Integration
    external_id_1c: Optional[str] = None
    created_in_1c_at: Optional[datetime] = None

    # AI metadata
    parsed_data: Optional[dict] = None  # Полный JSON
    ai_processing_time_sec: Optional[Decimal] = None
    ai_model_used: Optional[str] = None

    # Errors
    errors: Optional[List[dict]] = None
    warnings: Optional[List[dict]] = None

    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProcessedInvoiceUpdate(BaseModel):
    """Обновление данных счета (ручная корректировка)"""
    invoice_number: Optional[str] = None
    invoice_date: Optional[DateType] = None
    supplier_name: Optional[str] = None
    supplier_inn: Optional[str] = None
    supplier_kpp: Optional[str] = None
    total_amount: Optional[Decimal] = None
    payment_purpose: Optional[str] = None

    # Можно обновить связь с contractor
    contractor_id: Optional[int] = None


# ==================== Statistics & Analytics ====================

class InvoiceProcessingStats(BaseModel):
    """Статистика обработки счетов"""
    total_invoices: int
    by_status: dict = Field(default_factory=dict, description="Количество по статусам")

    total_amount_processed: Decimal = Decimal("0")
    expenses_created: int = 0

    avg_ocr_time_sec: Optional[float] = None
    avg_ai_time_sec: Optional[float] = None
    avg_total_time_sec: Optional[float] = None

    success_rate: float = Field(description="Процент успешно обработанных")
    error_rate: float = Field(description="Процент с ошибками")


# ==================== 1C Integration Schemas ====================

class Invoice1CValidationRequest(BaseModel):
    """Запрос на валидацию счета перед отправкой в 1С"""
    invoice_id: int = Field(..., description="ID обработанного счета")


class Invoice1CFoundData(BaseModel):
    """Найденные данные из 1С при валидации"""
    counterparty: Optional[dict] = Field(None, description="Контрагент {guid, name}")
    organization: Optional[dict] = Field(None, description="Организация {guid, name}")
    cash_flow_category: Optional[dict] = Field(None, description="Статья ДДС {guid, name}")


class Invoice1CValidationResponse(BaseModel):
    """Результат валидации счета перед отправкой в 1С"""
    is_valid: bool = Field(..., description="Прошла ли валидация")
    errors: List[str] = Field(default_factory=list, description="Список ошибок")
    warnings: List[str] = Field(default_factory=list, description="Предупреждения")
    found_data: Invoice1CFoundData = Field(..., description="Найденные данные в 1С")


class Create1CExpenseRequestRequest(BaseModel):
    """Запрос на создание заявки на расход в 1С"""
    invoice_id: int = Field(..., description="ID обработанного счета")
    upload_attachment: bool = Field(default=True, description="Загружать ли прикрепленный файл")


class Create1CExpenseRequestResponse(BaseModel):
    """Ответ после создания заявки в 1С"""
    success: bool
    external_id_1c: Optional[str] = Field(None, description="GUID созданной заявки в 1С")
    message: str
    created_at: Optional[datetime] = None


class SuggestCategoryRequest(BaseModel):
    """Запрос на AI-предложение категории"""
    invoice_id: int = Field(..., description="ID обработанного счета")


class SuggestCategoryResponse(BaseModel):
    """Ответ с предложенной категорией"""
    suggested_category_id: Optional[int] = Field(None, description="ID предложенной категории")
    category_name: Optional[str] = None
    confidence: Optional[float] = Field(None, description="Уверенность в предложении (0-100%)")
    reasoning: Optional[str] = Field(None, description="Обоснование выбора")


class CashFlowCategoryListItem(BaseModel):
    """Элемент списка статей ДДС для выбора"""
    id: int
    name: str
    code: Optional[str] = None
    external_id_1c: str = Field(..., description="GUID в 1С")
    parent_id: Optional[int] = None
    is_folder: bool
    order_index: Optional[int] = None

    class Config:
        from_attributes = True


class InvoiceUpdateCategoryRequest(BaseModel):
    """Запрос на обновление категории счета"""
    category_id: int = Field(..., description="ID категории бюджета (статьи ДДС)")
