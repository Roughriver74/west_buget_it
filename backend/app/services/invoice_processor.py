"""
Invoice Processor - Orchestrator service for invoice processing workflow
Coordinates: File upload → OCR → AI Parsing → Database storage → Expense creation
"""
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from loguru import logger

from app.db.models import ProcessedInvoice, Contractor, Expense, User, InvoiceProcessingStatusEnum, ExpenseStatusEnum
from app.schemas.invoice_processing import (
    ParsedInvoiceData,
    OCRResult,
    ProcessingError
)
from app.services.invoice_ocr import InvoiceOCRService
from app.services.invoice_ai_parser import InvoiceAIParser


class InvoiceProcessorService:
    """
    Orchestrator сервис для обработки счетов

    Workflow:
    1. Загрузка файла и создание записи в БД
    2. OCR распознавание
    3. AI-парсинг данных
    4. Сохранение результатов
    5. (Опционально) Создание Expense
    """

    def __init__(self, db: Session):
        self.db = db
        self.ocr_service = InvoiceOCRService()
        self.ai_parser = InvoiceAIParser()

    async def create_invoice_record(
        self,
        file_path: str,
        original_filename: str,
        file_size_kb: int,
        department_id: int,
        uploaded_by: int
    ) -> ProcessedInvoice:
        """
        Создание записи о загруженном счете в БД

        Args:
            file_path: Путь к сохраненному файлу
            original_filename: Оригинальное имя файла
            file_size_kb: Размер файла в КБ
            department_id: ID отдела
            uploaded_by: ID пользователя

        Returns:
            ProcessedInvoice: Созданная запись
        """
        invoice = ProcessedInvoice(
            department_id=department_id,
            uploaded_by=uploaded_by,
            original_filename=original_filename,
            file_path=file_path,
            file_size_kb=file_size_kb,
            status=InvoiceProcessingStatusEnum.PENDING
        )
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)

        logger.info(f"Создана запись ProcessedInvoice ID={invoice.id} для файла {original_filename}")
        return invoice

    async def process_invoice(self, invoice_id: int) -> Dict[str, Any]:
        """
        Полная обработка счета: OCR + AI парсинг

        Args:
            invoice_id: ID записи ProcessedInvoice

        Returns:
            Dict с результатами обработки:
                - success: bool
                - ocr_result: OCRResult или None
                - parsed_data: ParsedInvoiceData или None
                - errors: List[ProcessingError]
                - warnings: List[ProcessingError]
                - processing_time_sec: float
        """
        invoice = self.db.query(ProcessedInvoice).filter(
            ProcessedInvoice.id == invoice_id
        ).first()

        if not invoice:
            raise ValueError(f"ProcessedInvoice с ID {invoice_id} не найден")

        # Обновляем статус
        invoice.status = InvoiceProcessingStatusEnum.PROCESSING
        self.db.commit()

        errors: List[ProcessingError] = []
        warnings: List[ProcessingError] = []
        ocr_result: Optional[OCRResult] = None
        parsed_data: Optional[ParsedInvoiceData] = None

        start_time = time.time()

        try:
            # Шаг 1: OCR
            logger.info(f"Начинаю OCR для invoice ID={invoice_id}")
            ocr_start = time.time()
            ocr_text = self.ocr_service.process_file(invoice.file_path)
            ocr_time = time.time() - ocr_start

            if len(ocr_text.strip()) < 50:
                errors.append(ProcessingError(
                    field="ocr",
                    message="Распознано слишком мало текста (< 50 символов)",
                    severity="error"
                ))
                invoice.status = InvoiceProcessingStatusEnum.ERROR
                invoice.errors = [e.model_dump() for e in errors]
                self.db.commit()
                return {
                    "success": False,
                    "ocr_result": None,
                    "parsed_data": None,
                    "errors": errors,
                    "warnings": warnings,
                    "processing_time_sec": time.time() - start_time
                }

            # Сохраняем OCR результат
            invoice.ocr_text = ocr_text
            invoice.ocr_processing_time_sec = Decimal(str(round(ocr_time, 2)))
            self.db.commit()

            ocr_result = OCRResult(
                text=ocr_text,
                confidence=None,  # Tesseract не возвращает confidence
                processing_time_sec=ocr_time
            )

            # Шаг 2: AI парсинг
            logger.info(f"Начинаю AI парсинг для invoice ID={invoice_id}")
            ai_start = time.time()
            parsed_data = self.ai_parser.parse_invoice(ocr_text, invoice.original_filename)
            ai_time = time.time() - ai_start

            # Сохраняем распознанные данные
            self._save_parsed_data(invoice, parsed_data, ai_time)

            # Валидация
            validation_errors = self._validate_parsed_data(parsed_data)
            if validation_errors:
                errors.extend(validation_errors)
                if any(e.severity == "error" for e in validation_errors):
                    invoice.status = InvoiceProcessingStatusEnum.MANUAL_REVIEW
                else:
                    invoice.status = InvoiceProcessingStatusEnum.PROCESSED
            else:
                invoice.status = InvoiceProcessingStatusEnum.PROCESSED

            invoice.processed_at = datetime.utcnow()
            invoice.errors = [e.model_dump() for e in errors] if errors else None
            invoice.warnings = [w.model_dump() for w in warnings] if warnings else None
            self.db.commit()

            logger.info(f"Обработка invoice ID={invoice_id} завершена успешно. Статус: {invoice.status}")

            return {
                "success": len([e for e in errors if e.severity == "error"]) == 0,
                "ocr_result": ocr_result,
                "parsed_data": parsed_data,
                "errors": errors,
                "warnings": warnings,
                "processing_time_sec": time.time() - start_time
            }

        except Exception as e:
            logger.error(f"Ошибка при обработке invoice ID={invoice_id}: {e}", exc_info=True)
            invoice.status = InvoiceProcessingStatusEnum.ERROR
            error = ProcessingError(
                field="processing",
                message=f"Критическая ошибка: {str(e)}",
                severity="error"
            )
            errors.append(error)
            invoice.errors = [e.model_dump() for e in errors]
            self.db.commit()

            return {
                "success": False,
                "ocr_result": ocr_result,
                "parsed_data": parsed_data,
                "errors": errors,
                "warnings": warnings,
                "processing_time_sec": time.time() - start_time
            }

    def _save_parsed_data(
        self,
        invoice: ProcessedInvoice,
        parsed_data: ParsedInvoiceData,
        ai_time: float
    ):
        """Сохранение распознанных данных в БД"""
        invoice.invoice_number = parsed_data.invoice_number
        invoice.invoice_date = parsed_data.invoice_date

        if parsed_data.supplier:
            invoice.supplier_name = parsed_data.supplier.name
            invoice.supplier_inn = parsed_data.supplier.inn
            invoice.supplier_kpp = parsed_data.supplier.kpp
            invoice.supplier_bank_name = parsed_data.supplier.bank_name
            invoice.supplier_bik = parsed_data.supplier.bik
            invoice.supplier_account = parsed_data.supplier.account

        invoice.amount_without_vat = parsed_data.amount_without_vat
        invoice.vat_amount = parsed_data.vat_amount
        invoice.total_amount = parsed_data.total_amount
        invoice.payment_purpose = parsed_data.payment_purpose
        invoice.contract_number = parsed_data.contract_number
        invoice.contract_date = parsed_data.contract_date

        # Полный JSON с табличной частью
        invoice.parsed_data = parsed_data.model_dump(mode='json')
        invoice.ai_processing_time_sec = Decimal(str(round(ai_time, 2)))
        invoice.ai_model_used = self.ai_parser.model

    def _validate_parsed_data(self, parsed_data: ParsedInvoiceData) -> List[ProcessingError]:
        """Валидация распознанных данных"""
        errors: List[ProcessingError] = []

        # Обязательные поля
        if not parsed_data.invoice_number:
            errors.append(ProcessingError(
                field="invoice_number",
                message="Не удалось распознать номер счета",
                severity="error"
            ))

        if not parsed_data.invoice_date:
            errors.append(ProcessingError(
                field="invoice_date",
                message="Не удалось распознать дату счета",
                severity="error"
            ))

        if not parsed_data.supplier or not parsed_data.supplier.inn:
            errors.append(ProcessingError(
                field="supplier.inn",
                message="Не удалось распознать ИНН поставщика",
                severity="error"
            ))

        if not parsed_data.total_amount or parsed_data.total_amount <= 0:
            errors.append(ProcessingError(
                field="total_amount",
                message="Некорректная сумма счета",
                severity="error"
            ))

        # Предупреждения
        if not parsed_data.supplier or not parsed_data.supplier.name:
            errors.append(ProcessingError(
                field="supplier.name",
                message="Не удалось распознать наименование поставщика",
                severity="warning"
            ))

        if not parsed_data.items or len(parsed_data.items) == 0:
            errors.append(ProcessingError(
                field="items",
                message="Табличная часть не распознана",
                severity="warning"
            ))

        return errors

    async def create_expense_from_invoice(
        self,
        invoice_id: int,
        category_id: int,
        amount_override: Optional[Decimal] = None,
        description_override: Optional[str] = None,
        contractor_id_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Создание expense из обработанного счета

        Args:
            invoice_id: ID обработанного счета
            category_id: ID категории бюджета
            amount_override: Переопределить сумму
            description_override: Переопределить описание
            contractor_id_override: Переопределить контрагента

        Returns:
            Dict с результатами:
                - success: bool
                - expense_id: int или None
                - contractor_id: int или None
                - contractor_created: bool
                - message: str
        """
        invoice = self.db.query(ProcessedInvoice).filter(
            ProcessedInvoice.id == invoice_id
        ).first()

        if not invoice:
            return {
                "success": False,
                "expense_id": None,
                "contractor_id": None,
                "contractor_created": False,
                "message": f"ProcessedInvoice с ID {invoice_id} не найден"
            }

        if invoice.status != InvoiceProcessingStatusEnum.PROCESSED:
            return {
                "success": False,
                "expense_id": None,
                "contractor_id": None,
                "contractor_created": False,
                "message": f"Счет должен быть в статусе PROCESSED (текущий: {invoice.status})"
            }

        try:
            # Ищем или создаем контрагента
            contractor_id = contractor_id_override
            contractor_created = False

            if not contractor_id and invoice.supplier_inn:
                # Поиск по ИНН
                contractor = self.db.query(Contractor).filter(
                    Contractor.inn == invoice.supplier_inn,
                    Contractor.department_id == invoice.department_id,
                    Contractor.is_active == True
                ).first()

                if contractor:
                    contractor_id = contractor.id
                    logger.info(f"Найден существующий контрагент ID={contractor_id} по ИНН {invoice.supplier_inn}")
                else:
                    # Создаем нового контрагента
                    contractor = Contractor(
                        name=invoice.supplier_name or f"Контрагент (ИНН {invoice.supplier_inn})",
                        inn=invoice.supplier_inn,
                        kpp=invoice.supplier_kpp,
                        department_id=invoice.department_id,
                        is_active=True
                    )
                    self.db.add(contractor)
                    self.db.flush()
                    contractor_id = contractor.id
                    contractor_created = True
                    logger.info(f"Создан новый контрагент ID={contractor_id} для ИНН {invoice.supplier_inn}")

            # Создаем expense
            amount = amount_override or invoice.total_amount
            description = description_override or (invoice.payment_purpose or f"Счет №{invoice.invoice_number}")

            expense = Expense(
                department_id=invoice.department_id,
                category_id=category_id,
                contractor_id=contractor_id,
                amount=amount,
                description=description,
                expense_date=invoice.invoice_date or datetime.utcnow().date(),
                status=ExpenseStatusEnum.DRAFT,
                is_active=True
            )
            self.db.add(expense)
            self.db.flush()

            # Обновляем invoice
            invoice.expense_id = expense.id
            invoice.contractor_id = contractor_id
            invoice.status = InvoiceProcessingStatusEnum.EXPENSE_CREATED
            invoice.expense_created_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Создан Expense ID={expense.id} из ProcessedInvoice ID={invoice_id}")

            return {
                "success": True,
                "expense_id": expense.id,
                "contractor_id": contractor_id,
                "contractor_created": contractor_created,
                "message": "Расход успешно создан"
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при создании expense из invoice ID={invoice_id}: {e}", exc_info=True)
            return {
                "success": False,
                "expense_id": None,
                "contractor_id": None,
                "contractor_created": False,
                "message": f"Ошибка создания расхода: {str(e)}"
            }
