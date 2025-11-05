"""
API endpoints for AI Invoice Processing
Supports: Upload → OCR → AI Parse → Create Expense workflow
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import tempfile
import shutil
from loguru import logger

from app.db.session import get_db
from app.db.models import (
    ProcessedInvoice,
    User,
    UserRoleEnum,
    InvoiceProcessingStatusEnum
)
from app.schemas.invoice_processing import (
    InvoiceUploadResponse,
    InvoiceProcessRequest,
    InvoiceProcessResponse,
    ProcessedInvoiceListItem,
    ProcessedInvoiceDetail,
    ProcessedInvoiceUpdate,
    CreateExpenseFromInvoiceRequest,
    CreateExpenseFromInvoiceResponse,
    InvoiceProcessingStats,
    OCRResult,
)
from app.utils.auth import get_current_active_user
from app.services.invoice_processor import InvoiceProcessorService


router = APIRouter(prefix="/invoice-processing", tags=["invoice-processing"])


# ==================== File Upload ====================

@router.post("/upload", response_model=InvoiceUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice_file(
    file: UploadFile = File(..., description="PDF or Image file of invoice"),
    department_id: Optional[int] = Query(None, description="Department ID (optional, defaults to user's department)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Загрузка файла счета

    Поддерживаемые форматы: PDF, JPG, PNG, TIFF, BMP
    Максимальный размер: 10MB

    Process:
    1. Сохранение файла
    2. Создание записи в БД со статусом PENDING
    3. Возврат invoice_id для последующей обработки
    """
    # Проверка формата файла
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый формат файла. Поддерживаются: {', '.join(allowed_extensions)}"
        )

    # Проверка размера (макс 10MB)
    max_size_bytes = 10 * 1024 * 1024  # 10MB
    file.file.seek(0, 2)  # Перейти в конец
    file_size = file.file.tell()
    file.file.seek(0)  # Вернуться в начало

    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Размер файла превышает 10MB (текущий: {file_size / 1024 / 1024:.1f}MB)"
        )

    try:
        # Определяем department_id для загрузки
        target_department_id = department_id if department_id is not None else current_user.department_id

        # Проверка прав: USER может загружать только в свой департамент
        if current_user.role == UserRoleEnum.USER and target_department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав для загрузки файлов в другой департамент"
            )

        # Создаем директорию для хранения файлов
        # Структура: uploads/invoices/{department_id}/{year}/{filename}
        from datetime import datetime
        year = datetime.now().year
        upload_dir = Path(f"uploads/invoices/{target_department_id}/{year}")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = upload_dir / safe_filename

        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Файл сохранен: {file_path} для department_id={target_department_id}")

        # Создаем запись в БД
        processor = InvoiceProcessorService(db)
        invoice = await processor.create_invoice_record(
            file_path=str(file_path),
            original_filename=file.filename,
            file_size_kb=int(file_size / 1024),
            department_id=target_department_id,
            uploaded_by=current_user.id
        )

        return InvoiceUploadResponse(
            success=True,
            invoice_id=invoice.id,
            filename=file.filename,
            message=f"Файл успешно загружен. ID записи: {invoice.id}"
        )

    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )


# ==================== Process Invoice ====================

@router.post("/process", response_model=InvoiceProcessResponse)
async def process_invoice(
    request: InvoiceProcessRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Запуск обработки загруженного счета (OCR + AI парсинг)

    Process:
    1. OCR распознавание текста
    2. AI-парсинг структурированных данных
    3. Валидация
    4. Сохранение результатов

    Status после обработки:
    - PROCESSED - успешно
    - MANUAL_REVIEW - требует проверки
    - ERROR - ошибка
    """
    # Проверяем существование записи
    invoice = db.query(ProcessedInvoice).filter(
        ProcessedInvoice.id == request.invoice_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Счет с ID {request.invoice_id} не найден"
        )

    # Проверка прав доступа
    if current_user.role == UserRoleEnum.USER:
        if invoice.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа к счету другого отдела"
            )

    # Проверяем статус
    if invoice.status not in [InvoiceProcessingStatusEnum.PENDING, InvoiceProcessingStatusEnum.ERROR]:
        logger.warning(f"Попытка повторной обработки invoice ID={request.invoice_id} в статусе {invoice.status}")
        # Разрешаем переобработку только для PENDING и ERROR

    try:
        processor = InvoiceProcessorService(db)
        result = await processor.process_invoice(request.invoice_id)

        return InvoiceProcessResponse(
            success=result["success"],
            invoice_id=request.invoice_id,
            status=invoice.status.value,
            ocr_result=result.get("ocr_result"),
            parsed_data=result.get("parsed_data"),
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            processing_time_total_sec=result.get("processing_time_sec")
        )

    except Exception as e:
        logger.error(f"Ошибка при обработке invoice ID={request.invoice_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обработке: {str(e)}"
        )


# ==================== List & Get ====================

@router.get("/", response_model=List[ProcessedInvoiceListItem])
async def get_invoices(
    department_id: Optional[int] = Query(None, description="Фильтр по отделу"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Список обработанных счетов с фильтрацией

    Role-based access:
    - USER: только свой отдел
    - MANAGER/ADMIN: может фильтровать по отделам
    """
    query = db.query(ProcessedInvoice).filter(ProcessedInvoice.is_active == True)

    # Role-based filtering
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(ProcessedInvoice.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(ProcessedInvoice.department_id == department_id)

    # Фильтр по статусу
    if status:
        try:
            status_enum = InvoiceProcessingStatusEnum(status)
            query = query.filter(ProcessedInvoice.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверный статус: {status}"
            )

    # Сортировка по дате загрузки (новые сверху)
    query = query.order_by(ProcessedInvoice.uploaded_at.desc())

    # Пагинация
    invoices = query.offset(skip).limit(limit).all()

    # Преобразование в response schema
    result = []
    for invoice in invoices:
        uploaded_by_name = "Unknown"
        if invoice.uploaded_by_rel:
            uploaded_by_name = invoice.uploaded_by_rel.full_name or invoice.uploaded_by_rel.email

        result.append(ProcessedInvoiceListItem(
            id=invoice.id,
            original_filename=invoice.original_filename,
            uploaded_at=invoice.uploaded_at,
            uploaded_by_name=uploaded_by_name,
            status=invoice.status.value,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            supplier_name=invoice.supplier_name,
            supplier_inn=invoice.supplier_inn,
            total_amount=invoice.total_amount,
            expense_id=invoice.expense_id,
            contractor_id=invoice.contractor_id,
            has_errors=bool(invoice.errors),
            has_warnings=bool(invoice.warnings)
        ))

    return result


@router.get("/{invoice_id}", response_model=ProcessedInvoiceDetail)
async def get_invoice_detail(
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Детальная информация о счете
    """
    invoice = db.query(ProcessedInvoice).filter(
        ProcessedInvoice.id == invoice_id,
        ProcessedInvoice.is_active == True
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Счет с ID {invoice_id} не найден"
        )

    # Проверка прав доступа
    if current_user.role == UserRoleEnum.USER:
        if invoice.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа к счету другого отдела"
            )

    uploaded_by_name = "Unknown"
    if invoice.uploaded_by_rel:
        uploaded_by_name = invoice.uploaded_by_rel.full_name or invoice.uploaded_by_rel.email

    return ProcessedInvoiceDetail(
        id=invoice.id,
        department_id=invoice.department_id,
        original_filename=invoice.original_filename,
        file_path=invoice.file_path,
        file_size_kb=invoice.file_size_kb,
        uploaded_by=invoice.uploaded_by,
        uploaded_by_name=uploaded_by_name,
        uploaded_at=invoice.uploaded_at,
        ocr_text=invoice.ocr_text,
        ocr_confidence=invoice.ocr_confidence,
        ocr_processing_time_sec=invoice.ocr_processing_time_sec,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        supplier_name=invoice.supplier_name,
        supplier_inn=invoice.supplier_inn,
        supplier_kpp=invoice.supplier_kpp,
        supplier_bank_name=invoice.supplier_bank_name,
        supplier_bik=invoice.supplier_bik,
        supplier_account=invoice.supplier_account,
        amount_without_vat=invoice.amount_without_vat,
        vat_amount=invoice.vat_amount,
        total_amount=invoice.total_amount,
        payment_purpose=invoice.payment_purpose,
        contract_number=invoice.contract_number,
        contract_date=invoice.contract_date,
        status=invoice.status.value,
        processed_at=invoice.processed_at,
        expense_id=invoice.expense_id,
        contractor_id=invoice.contractor_id,
        expense_created_at=invoice.expense_created_at,
        parsed_data=invoice.parsed_data,
        ai_processing_time_sec=invoice.ai_processing_time_sec,
        ai_model_used=invoice.ai_model_used,
        errors=invoice.errors,
        warnings=invoice.warnings,
        is_active=invoice.is_active,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at
    )


# ==================== Update & Delete ====================

@router.put("/{invoice_id}", response_model=ProcessedInvoiceDetail)
async def update_invoice(
    invoice_id: int,
    update_data: ProcessedInvoiceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Обновление распознанных данных счета (ручная корректировка)
    """
    invoice = db.query(ProcessedInvoice).filter(
        ProcessedInvoice.id == invoice_id,
        ProcessedInvoice.is_active == True
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Счет с ID {invoice_id} не найден"
        )

    # Проверка прав доступа
    if current_user.role == UserRoleEnum.USER:
        if invoice.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа к счету другого отдела"
            )

    # Обновляем поля
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(invoice, field, value)

    db.commit()
    db.refresh(invoice)

    logger.info(f"Invoice ID={invoice_id} обновлен пользователем {current_user.id}")

    # Возвращаем обновленные данные
    return await get_invoice_detail(invoice_id, current_user, db)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Удаление записи о счете (soft delete)
    """
    invoice = db.query(ProcessedInvoice).filter(
        ProcessedInvoice.id == invoice_id,
        ProcessedInvoice.is_active == True
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Счет с ID {invoice_id} не найден"
        )

    # Проверка прав доступа
    if current_user.role == UserRoleEnum.USER:
        if invoice.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа к счету другого отдела"
            )

    # Проверяем, не создан ли уже expense
    if invoice.expense_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Невозможно удалить счет - уже создан расход ID={invoice.expense_id}"
        )

    # Soft delete
    invoice.is_active = False
    db.commit()

    logger.info(f"Invoice ID={invoice_id} удален пользователем {current_user.id}")
    return None


# ==================== Create Expense ====================

@router.post("/create-expense", response_model=CreateExpenseFromInvoiceResponse)
async def create_expense_from_invoice(
    request: CreateExpenseFromInvoiceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Создание expense из обработанного счета

    Process:
    1. Поиск/создание контрагента по ИНН
    2. Создание expense в статусе DRAFT
    3. Обновление статуса счета на EXPENSE_CREATED
    """
    invoice = db.query(ProcessedInvoice).filter(
        ProcessedInvoice.id == request.invoice_id,
        ProcessedInvoice.is_active == True
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Счет с ID {request.invoice_id} не найден"
        )

    # Проверка прав доступа
    if current_user.role == UserRoleEnum.USER:
        if invoice.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа к счету другого отдела"
            )

    # Проверяем, не создан ли уже expense
    if invoice.expense_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Расход уже создан (ID={invoice.expense_id})"
        )

    try:
        processor = InvoiceProcessorService(db)
        result = await processor.create_expense_from_invoice(
            invoice_id=request.invoice_id,
            category_id=request.category_id,
            amount_override=request.amount_override,
            description_override=request.description_override,
            contractor_id_override=request.contractor_id_override
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )

        return CreateExpenseFromInvoiceResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании expense из invoice ID={request.invoice_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании расхода: {str(e)}"
        )


# ==================== Statistics ====================

@router.get("/stats/summary", response_model=InvoiceProcessingStats)
async def get_processing_stats(
    department_id: Optional[int] = Query(None, description="Фильтр по отделу"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Статистика обработки счетов
    """
    from sqlalchemy import func
    from decimal import Decimal

    query = db.query(ProcessedInvoice).filter(ProcessedInvoice.is_active == True)

    # Role-based filtering
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(ProcessedInvoice.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(ProcessedInvoice.department_id == department_id)

    total_invoices = query.count()

    # Подсчет по статусам
    by_status = {}
    for status in InvoiceProcessingStatusEnum:
        count = query.filter(ProcessedInvoice.status == status).count()
        by_status[status.value] = count

    # Суммы
    total_amount_result = query.filter(
        ProcessedInvoice.total_amount.isnot(None)
    ).with_entities(func.sum(ProcessedInvoice.total_amount)).scalar()
    total_amount_processed = Decimal(str(total_amount_result or 0))

    # Количество созданных expenses
    expenses_created = query.filter(ProcessedInvoice.expense_id.isnot(None)).count()

    # Средние времена обработки
    avg_ocr_time = query.filter(
        ProcessedInvoice.ocr_processing_time_sec.isnot(None)
    ).with_entities(func.avg(ProcessedInvoice.ocr_processing_time_sec)).scalar()

    avg_ai_time = query.filter(
        ProcessedInvoice.ai_processing_time_sec.isnot(None)
    ).with_entities(func.avg(ProcessedInvoice.ai_processing_time_sec)).scalar()

    avg_total_time = None
    if avg_ocr_time and avg_ai_time:
        avg_total_time = float(avg_ocr_time) + float(avg_ai_time)

    # Success rate
    processed_count = by_status.get(InvoiceProcessingStatusEnum.PROCESSED.value, 0) + \
                     by_status.get(InvoiceProcessingStatusEnum.EXPENSE_CREATED.value, 0)
    error_count = by_status.get(InvoiceProcessingStatusEnum.ERROR.value, 0)

    success_rate = (processed_count / total_invoices * 100) if total_invoices > 0 else 0
    error_rate = (error_count / total_invoices * 100) if total_invoices > 0 else 0

    return InvoiceProcessingStats(
        total_invoices=total_invoices,
        by_status=by_status,
        total_amount_processed=total_amount_processed,
        expenses_created=expenses_created,
        avg_ocr_time_sec=float(avg_ocr_time) if avg_ocr_time else None,
        avg_ai_time_sec=float(avg_ai_time) if avg_ai_time else None,
        avg_total_time_sec=avg_total_time,
        success_rate=round(success_rate, 2),
        error_rate=round(error_rate, 2)
    )
