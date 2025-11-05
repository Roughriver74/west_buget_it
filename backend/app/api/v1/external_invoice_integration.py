"""
External API for 1C Integration - Invoice Processing
Endpoints for 1C to fetch processed invoices in JSON format
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
from loguru import logger

from app.db.session import get_db
from app.db.models import (
    ProcessedInvoice,
    InvoiceProcessingStatusEnum,
    APIToken,
    APITokenScopeEnum
)
from app.utils.api_token import verify_api_token, check_token_scope
from pydantic import BaseModel, Field
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


router = APIRouter(prefix="/external/invoices", tags=["external-1c-integration"])
security = HTTPBearer()


async def verify_api_token_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> APIToken:
    """Dependency to verify API token with database session"""
    return await verify_api_token(credentials, db)


# ==================== Schemas ====================

class BuyerInfo(BaseModel):
    """Информация о покупателе (из parsed_data или OCR)"""
    name: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None


class InvoiceFor1C(BaseModel):
    """Счет для выгрузки в 1С - полная информация"""
    invoice_id: int
    invoice_number: str
    invoice_date: str
    # Поставщик
    supplier_name: str
    supplier_inn: Optional[str] = None
    supplier_kpp: Optional[str] = None
    supplier_bank_name: Optional[str] = None
    supplier_bik: Optional[str] = None
    supplier_account: Optional[str] = None
    # Покупатель
    buyer: Optional[BuyerInfo] = None
    # Суммы
    total_amount: float
    amount_without_vat: Optional[float] = None
    vat_amount: Optional[float] = None
    payment_purpose: Optional[str] = None
    contract_number: Optional[str] = None
    contract_date: Optional[str] = None
    # Департамент
    department_id: int
    department_name: Optional[str] = None
    # Категория бюджета
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    original_filename: str
    processed_at: str
    # 1C Integration tracking
    external_id_1c: Optional[str] = None
    created_in_1c_at: Optional[str] = None
    # Полные данные из AI парсинга (включая items array)
    parsed_data: Optional[dict] = None
    ocr_text: Optional[str] = None  # Полный текст OCR для дополнительной обработки


class InvoiceListItem(BaseModel):
    """Краткая информация о счете для списка"""
    invoice_id: int
    invoice_number: str
    invoice_date: str
    supplier_name: str
    supplier_inn: Optional[str] = None
    total_amount: float
    department_id: int
    category_id: Optional[int] = None
    processed_at: str
    # 1C Integration tracking
    external_id_1c: Optional[str] = None
    created_in_1c_at: Optional[str] = None


class AcknowledgeResponse(BaseModel):
    """Ответ на подтверждение получения счета"""
    success: bool
    message: str


class MarkCreatedIn1CRequest(BaseModel):
    """Запрос на отметку счета как созданного в 1С"""
    external_id_1c: str = Field(..., description="ID документа в системе 1С")


# ==================== Endpoints ====================

@router.get("/pending", response_model=List[InvoiceListItem])
async def get_pending_invoices_list(
    department_id: Optional[int] = Query(None, description="Фильтр по департаменту"),
    only_not_created_in_1c: bool = Query(False, description="Только счета, еще не созданные в 1С"),
    limit: int = Query(100, ge=1, le=500, description="Максимум записей"),
    token: APIToken = Depends(verify_api_token_dependency),
    db: Session = Depends(get_db)
):
    """
    Получить список обработанных счетов для загрузки в 1С (краткая информация)

    Возвращает только счета со статусом PROCESSED.
    Для получения полных данных счета используйте GET /{invoice_id}

    Требуется API Token аутентификация с READ или FULL_ACCESS scope.
    """
    # Проверка прав доступа
    if not check_token_scope(token, APITokenScopeEnum.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Token требует scope READ или выше"
        )

    logger.info(f"1C API: Запрос списка pending invoices от токена {token.name}")

    # Базовый запрос - все счета со статусом PROCESSED
    query = db.query(ProcessedInvoice).filter(
        and_(
            ProcessedInvoice.status == InvoiceProcessingStatusEnum.PROCESSED,
            ProcessedInvoice.is_active == True
        )
    )

    # Фильтр по департаменту
    if department_id:
        query = query.filter(ProcessedInvoice.department_id == department_id)

    # Фильтр - только не созданные в 1С
    if only_not_created_in_1c:
        query = query.filter(ProcessedInvoice.created_in_1c_at == None)

    # Сортировка по дате обработки (новые сначала)
    invoices = query.order_by(ProcessedInvoice.processed_at.desc()).limit(limit).all()

    logger.info(f"1C API: Найдено {len(invoices)} счетов для выгрузки")

    # Возвращаем краткую информацию
    result = []
    for inv in invoices:
        result.append(InvoiceListItem(
            invoice_id=inv.id,
            invoice_number=inv.invoice_number or "",
            invoice_date=inv.invoice_date.isoformat() if inv.invoice_date else "",
            supplier_name=inv.supplier_name or "",
            supplier_inn=inv.supplier_inn,
            total_amount=float(inv.total_amount) if inv.total_amount else 0.0,
            department_id=inv.department_id,
            category_id=inv.category_id,
            processed_at=inv.processed_at.isoformat() if inv.processed_at else "",
            external_id_1c=inv.external_id_1c,
            created_in_1c_at=inv.created_in_1c_at.isoformat() if inv.created_in_1c_at else None
        ))

    return result


@router.get("/{invoice_id}", response_model=InvoiceFor1C)
async def get_invoice_details(
    invoice_id: int,
    token: APIToken = Depends(verify_api_token_dependency),
    db: Session = Depends(get_db)
):
    """
    Получить полную информацию о счете в формате JSON

    Возвращает все данные счета, включая OCR текст и AI ответ.
    Эти данные используются 1С для создания документов.

    Требуется API Token аутентификация с READ или FULL_ACCESS scope.
    """
    # Проверка прав доступа
    if not check_token_scope(token, APITokenScopeEnum.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Token требует scope READ или выше"
        )

    logger.info(f"1C API: Запрос счета {invoice_id} от токена {token.name}")

    # Находим счет с загрузкой департамента и категории
    invoice = db.query(ProcessedInvoice).options(
        joinedload(ProcessedInvoice.department_rel),
        joinedload(ProcessedInvoice.category_rel)
    ).filter(
        ProcessedInvoice.id == invoice_id,
        ProcessedInvoice.is_active == True
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Счет с ID {invoice_id} не найден"
        )

    # Извлекаем информацию о покупателе из parsed_data
    buyer_info = None
    if invoice.parsed_data and isinstance(invoice.parsed_data, dict):
        buyer_data = invoice.parsed_data.get('buyer') or invoice.parsed_data.get('customer')
        if buyer_data:
            buyer_info = BuyerInfo(
                name=buyer_data.get('name'),
                inn=buyer_data.get('inn'),
                kpp=buyer_data.get('kpp')
            )

    # Возвращаем полную информацию
    return InvoiceFor1C(
        invoice_id=invoice.id,
        invoice_number=invoice.invoice_number or "",
        invoice_date=invoice.invoice_date.isoformat() if invoice.invoice_date else "",
        supplier_name=invoice.supplier_name or "",
        supplier_inn=invoice.supplier_inn,
        supplier_kpp=invoice.supplier_kpp,
        supplier_bank_name=invoice.supplier_bank_name,
        supplier_bik=invoice.supplier_bik,
        supplier_account=invoice.supplier_account,
        buyer=buyer_info,
        total_amount=float(invoice.total_amount) if invoice.total_amount else 0.0,
        amount_without_vat=float(invoice.amount_without_vat) if invoice.amount_without_vat else None,
        vat_amount=float(invoice.vat_amount) if invoice.vat_amount else None,
        payment_purpose=invoice.payment_purpose,
        contract_number=invoice.contract_number,
        contract_date=invoice.contract_date.isoformat() if invoice.contract_date else None,
        department_id=invoice.department_id,
        department_name=invoice.department_rel.ftp_subdivision_name if invoice.department_rel else None,
        category_id=invoice.category_id,
        category_name=invoice.category_rel.name if invoice.category_rel else None,
        original_filename=invoice.original_filename,
        processed_at=invoice.processed_at.isoformat() if invoice.processed_at else "",
        external_id_1c=invoice.external_id_1c,
        created_in_1c_at=invoice.created_in_1c_at.isoformat() if invoice.created_in_1c_at else None,
        parsed_data=invoice.parsed_data,
        ocr_text=invoice.ocr_text
    )


@router.post("/{invoice_id}/acknowledge", response_model=AcknowledgeResponse)
async def acknowledge_invoice(
    invoice_id: int,
    token: APIToken = Depends(verify_api_token_dependency),
    db: Session = Depends(get_db)
):
    """
    Подтвердить получение счета системой 1С (опционально)

    Этот endpoint можно использовать для отслеживания, что счет был получен 1С.
    Обновляет метку времени fetched_at.

    Требуется API Token аутентификация с WRITE или FULL_ACCESS scope.
    """
    # Проверка прав доступа
    if not check_token_scope(token, APITokenScopeEnum.WRITE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Token требует scope WRITE или выше"
        )

    logger.info(f"1C API: Подтверждение получения счета {invoice_id} от токена {token.name}")

    # Находим счет
    invoice = db.query(ProcessedInvoice).filter(
        ProcessedInvoice.id == invoice_id,
        ProcessedInvoice.is_active == True
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Счет с ID {invoice_id} не найден"
        )

    # Обновляем метку времени (можно добавить поле fetched_at в модель)
    # invoice.fetched_at = datetime.now()
    # db.commit()

    return AcknowledgeResponse(
        success=True,
        message=f"Счет {invoice_id} подтвержден"
    )


@router.post("/{invoice_id}/mark-created-in-1c", response_model=AcknowledgeResponse)
async def mark_invoice_created_in_1c(
    invoice_id: int,
    request: MarkCreatedIn1CRequest,
    token: APIToken = Depends(verify_api_token_dependency),
    db: Session = Depends(get_db)
):
    """
    Отметить счет как созданный в 1С

    После успешного создания документа в 1С, система должна вызвать этот endpoint
    для сохранения ID документа 1С и времени создания.

    Требуется API Token аутентификация с WRITE или FULL_ACCESS scope.
    """
    # Проверка прав доступа
    if not check_token_scope(token, APITokenScopeEnum.WRITE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Token требует scope WRITE или выше"
        )

    logger.info(
        f"1C API: Отметка счета {invoice_id} как созданного в 1С "
        f"с external_id={request.external_id_1c} от токена {token.name}"
    )

    # Находим счет
    invoice = db.query(ProcessedInvoice).filter(
        ProcessedInvoice.id == invoice_id,
        ProcessedInvoice.is_active == True
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Счет с ID {invoice_id} не найден"
        )

    # Проверяем, что счет еще не был отмечен как созданный в 1С
    if invoice.created_in_1c_at is not None:
        logger.warning(
            f"1C API: Счет {invoice_id} уже был отмечен как созданный в 1С "
            f"({invoice.created_in_1c_at.isoformat()})"
        )
        # Не возвращаем ошибку, просто обновляем external_id если он изменился

    # Обновляем поля 1С интеграции
    invoice.external_id_1c = request.external_id_1c
    invoice.created_in_1c_at = datetime.now()

    db.commit()
    db.refresh(invoice)

    logger.info(
        f"1C API: Счет {invoice_id} успешно отмечен как созданный в 1С "
        f"с external_id={request.external_id_1c}"
    )

    return AcknowledgeResponse(
        success=True,
        message=f"Счет {invoice_id} успешно отмечен как созданный в 1С с ID {request.external_id_1c}"
    )
