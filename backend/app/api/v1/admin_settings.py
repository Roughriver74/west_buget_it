from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.config import settings
from app.utils.auth import get_current_active_user
from app.db.models import User, UserRoleEnum
from app.services.admin_settings_service import AdminSettingsService

router = APIRouter()


class AdminConfigResponse(BaseModel):
    app_name: str

    odata_url: str
    odata_username: str
    odata_password: str
    odata_custom_auth_token: str

    vsegpt_api_key: str | None
    vsegpt_base_url: str
    vsegpt_model: str

    credit_portfolio_ftp_host: str
    credit_portfolio_ftp_user: str
    credit_portfolio_ftp_password: str
    credit_portfolio_ftp_remote_dir: str
    credit_portfolio_ftp_local_dir: str

    scheduler_enabled: bool
    credit_portfolio_import_enabled: bool
    credit_portfolio_import_hour: int
    credit_portfolio_import_minute: int


class AdminConfigUpdate(BaseModel):
    app_name: str | None = None

    odata_url: str | None = None
    odata_username: str | None = None
    odata_password: str | None = None
    odata_custom_auth_token: str | None = None

    vsegpt_api_key: str | None = None
    vsegpt_base_url: str | None = None
    vsegpt_model: str | None = None

    credit_portfolio_ftp_host: str | None = None
    credit_portfolio_ftp_user: str | None = None
    credit_portfolio_ftp_password: str | None = None
    credit_portfolio_ftp_remote_dir: str | None = None
    credit_portfolio_ftp_local_dir: str | None = None

    scheduler_enabled: bool | None = None
    credit_portfolio_import_enabled: bool | None = None
    credit_portfolio_import_hour: int | None = None
    credit_portfolio_import_minute: int | None = None


def ensure_admin(current_user: User) -> None:
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can view admin configuration",
        )


@router.get("/config", response_model=AdminConfigResponse, tags=["Admin"])
async def get_admin_config(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> AdminConfigResponse:
    """
    Возвращает чувствительные настройки для администраторов из БД.
    Настройки сохраняются между перезапусками.
    """
    ensure_admin(current_user)

    # Get settings from DB (with .env fallback)
    admin_settings = AdminSettingsService.get_or_create(db)

    return AdminConfigResponse(
        app_name=admin_settings.app_name or settings.APP_NAME,
        odata_url=admin_settings.odata_url or settings.ODATA_1C_URL,
        odata_username=admin_settings.odata_username or settings.ODATA_1C_USERNAME,
        odata_password=admin_settings.odata_password or settings.ODATA_1C_PASSWORD,
        odata_custom_auth_token=admin_settings.odata_custom_auth_token or settings.ODATA_1C_CUSTOM_AUTH_TOKEN,
        vsegpt_api_key=admin_settings.vsegpt_api_key or settings.VSEGPT_API_KEY,
        vsegpt_base_url=admin_settings.vsegpt_base_url or settings.VSEGPT_BASE_URL,
        vsegpt_model=admin_settings.vsegpt_model or settings.VSEGPT_MODEL,
        credit_portfolio_ftp_host=admin_settings.credit_portfolio_ftp_host or settings.CREDIT_PORTFOLIO_FTP_HOST,
        credit_portfolio_ftp_user=admin_settings.credit_portfolio_ftp_user or settings.CREDIT_PORTFOLIO_FTP_USER,
        credit_portfolio_ftp_password=admin_settings.credit_portfolio_ftp_password or settings.CREDIT_PORTFOLIO_FTP_PASSWORD,
        credit_portfolio_ftp_remote_dir=admin_settings.credit_portfolio_ftp_remote_dir or settings.CREDIT_PORTFOLIO_FTP_REMOTE_DIR,
        credit_portfolio_ftp_local_dir=admin_settings.credit_portfolio_ftp_local_dir or settings.CREDIT_PORTFOLIO_FTP_LOCAL_DIR,
        scheduler_enabled=admin_settings.scheduler_enabled,
        credit_portfolio_import_enabled=admin_settings.credit_portfolio_import_enabled,
        credit_portfolio_import_hour=admin_settings.credit_portfolio_import_hour,
        credit_portfolio_import_minute=admin_settings.credit_portfolio_import_minute,
    )


@router.put("/config", response_model=AdminConfigResponse, tags=["Admin"])
async def update_admin_config(
    payload: AdminConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> AdminConfigResponse:
    """
    Обновляет чувствительные настройки для администраторов в БД.

    ✅ Значения сохраняются между перезапусками!
    """
    ensure_admin(current_user)
    updates = payload.model_dump(exclude_unset=True)

    # Save to database
    AdminSettingsService.update(db, updates, current_user)

    # Return refreshed config snapshot
    return await get_admin_config(current_user, db)
