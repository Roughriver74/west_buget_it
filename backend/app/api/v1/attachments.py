import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.db import get_db
from app.db.models import User, Attachment, Expense, UserRoleEnum
from app.schemas.attachment import AttachmentCreate, AttachmentUpdate, AttachmentInDB, AttachmentList
from app.utils.auth import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])

# Directory to store uploaded files
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.jpg', '.jpeg', '.png', '.gif', '.tiff',
    '.txt', '.csv', '.zip', '.rar'
}

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return Path(filename).suffix.lower()


def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def check_expense_department_access(expense: Expense, current_user: User) -> None:
    """
    Check if current user has access to this expense's department.

    - USER: Can only access expenses from their own department
    - MANAGER/ADMIN: Can access expenses from any department

    Raises HTTPException if access denied.
    """
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        if expense.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access attachments from your own department"
            )


@router.post("/{expense_id}/attachments", response_model=AttachmentInDB, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    expense_id: int,
    file: UploadFile = File(...),
    file_type: str = Form(None),
    uploaded_by: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file attachment for an expense"""

    # Check if expense exists
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )

    # Check department access (SECURITY: prevent cross-department file uploads)
    check_expense_department_access(expense, current_user)

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # Generate unique filename to prevent collisions
    file_extension = get_file_extension(file.filename)
    unique_filename = f"{expense_id}_{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file to disk
    with open(file_path, "wb") as f:
        f.write(content)

    # Create database record
    db_attachment = Attachment(
        expense_id=expense_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type,
        file_type=file_type,
        uploaded_by=uploaded_by
    )

    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)

    return db_attachment


@router.get("/{expense_id}/attachments", response_model=AttachmentList)
def get_expense_attachments(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all attachments for an expense"""

    # Check if expense exists
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )

    # Check department access (SECURITY: prevent viewing attachments from other departments)
    check_expense_department_access(expense, current_user)

    attachments = db.query(Attachment).filter(Attachment.expense_id == expense_id).all()

    return AttachmentList(
        items=attachments,
        total=len(attachments)
    )


@router.get("/attachments/{attachment_id}", response_model=AttachmentInDB)
def get_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get attachment by ID"""

    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment with id {attachment_id} not found"
        )

    # Check department access through parent expense (SECURITY: critical data leak prevention)
    expense = db.query(Expense).filter(Expense.id == attachment.expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated expense not found"
        )
    check_expense_department_access(expense, current_user)

    return attachment


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download an attachment file"""

    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment with id {attachment_id} not found"
        )

    # Check department access through parent expense (SECURITY: prevent downloading confidential files from other departments)
    expense = db.query(Expense).filter(Expense.id == attachment.expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated expense not found"
        )
    check_expense_department_access(expense, current_user)

    file_path = Path(attachment.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )

    return FileResponse(
        path=file_path,
        filename=attachment.filename,
        media_type=attachment.mime_type or 'application/octet-stream'
    )


@router.patch("/attachments/{attachment_id}", response_model=AttachmentInDB)
def update_attachment(
    attachment_id: int,
    attachment_update: AttachmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update attachment metadata (filename or file_type)"""

    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment with id {attachment_id} not found"
        )

    # Check department access through parent expense (SECURITY: prevent modifying attachments from other departments)
    expense = db.query(Expense).filter(Expense.id == attachment.expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated expense not found"
        )
    check_expense_department_access(expense, current_user)

    # Update fields
    update_data = attachment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(attachment, field, value)

    db.commit()
    db.refresh(attachment)

    return attachment


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an attachment"""

    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment with id {attachment_id} not found"
        )

    # Check department access through parent expense (SECURITY: prevent deleting attachments from other departments)
    expense = db.query(Expense).filter(Expense.id == attachment.expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated expense not found"
        )
    check_expense_department_access(expense, current_user)

    # Delete file from disk
    file_path = Path(attachment.file_path)
    if file_path.exists():
        try:
            os.remove(file_path)
        except Exception as e:
            # Log error but continue with database deletion
            print(f"Error deleting file {file_path}: {e}")

    # Delete database record
    db.delete(attachment)
    db.commit()

    return None
