import os
import uuid
import mimetypes
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Expense, ExpenseAttachment
from app.schemas.attachment import AttachmentInDB, AttachmentList, AttachmentUpdate

router = APIRouter()

# Директория для хранения файлов
UPLOAD_DIR = Path("./uploads/attachments")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Максимальный размер файла (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Разрешенные типы файлов
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/tiff",
    "text/plain",
]


@router.post("/", response_model=AttachmentInDB, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    expense_id: int = Form(...),
    file_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Загрузить файл для заявки
    """
    # Проверка существования заявки
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Проверка размера файла
    file.file.seek(0, 2)  # Переход в конец файла
    file_size = file.file.tell()  # Получение позиции (размера)
    file.file.seek(0)  # Возврат в начало

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.0f}MB"
        )

    # Определение MIME типа
    mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]

    # Проверка типа файла
    if mime_type and mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {mime_type} is not allowed"
        )

    # Генерация уникального имени файла
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    # Сохранение файла
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Создание записи в БД
    db_attachment = ExpenseAttachment(
        expense_id=expense_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=mime_type,
        file_type=file_type,
        description=description,
        uploaded_by=uploaded_by,
    )
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)

    return db_attachment


@router.get("/expense/{expense_id}", response_model=AttachmentList)
def get_expense_attachments(
    expense_id: int,
    db: Session = Depends(get_db),
):
    """
    Получить список файлов для заявки
    """
    # Проверка существования заявки
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    attachments = (
        db.query(ExpenseAttachment)
        .filter(ExpenseAttachment.expense_id == expense_id)
        .order_by(ExpenseAttachment.created_at.desc())
        .all()
    )

    return {"total": len(attachments), "items": attachments}


@router.get("/{attachment_id}", response_model=AttachmentInDB)
def get_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
):
    """
    Получить информацию о файле
    """
    attachment = db.query(ExpenseAttachment).filter(ExpenseAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return attachment


@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
):
    """
    Скачать файл
    """
    attachment = db.query(ExpenseAttachment).filter(ExpenseAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    file_path = Path(attachment.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=file_path,
        filename=attachment.filename,
        media_type=attachment.mime_type or "application/octet-stream",
    )


@router.patch("/{attachment_id}", response_model=AttachmentInDB)
def update_attachment(
    attachment_id: int,
    attachment_update: AttachmentUpdate,
    db: Session = Depends(get_db),
):
    """
    Обновить метаданные файла
    """
    attachment = db.query(ExpenseAttachment).filter(ExpenseAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Обновление полей
    update_data = attachment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(attachment, field, value)

    db.commit()
    db.refresh(attachment)

    return attachment


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
):
    """
    Удалить файл
    """
    attachment = db.query(ExpenseAttachment).filter(ExpenseAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Удаление файла с диска
    file_path = Path(attachment.file_path)
    if file_path.exists():
        try:
            os.remove(file_path)
        except Exception as e:
            # Логируем ошибку, но продолжаем удаление из БД
            print(f"Failed to delete file from disk: {str(e)}")

    # Удаление записи из БД
    db.delete(attachment)
    db.commit()

    return None
