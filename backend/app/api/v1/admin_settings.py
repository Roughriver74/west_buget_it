from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.utils.auth import get_current_active_user
from app.db.models import User, UserRoleEnum

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
async def get_admin_config(current_user: User = Depends(get_current_active_user)) -> AdminConfigResponse:
    """
    Возвращает чувствительные настройки для администраторов (только чтение).
    """
    ensure_admin(current_user)

    return AdminConfigResponse(
        app_name=settings.APP_NAME,
        odata_url=settings.ODATA_1C_URL,
        odata_username=settings.ODATA_1C_USERNAME,
        odata_password=settings.ODATA_1C_PASSWORD,
        odata_custom_auth_token=settings.ODATA_1C_CUSTOM_AUTH_TOKEN,
        vsegpt_api_key=settings.VSEGPT_API_KEY,
        vsegpt_base_url=settings.VSEGPT_BASE_URL,
        vsegpt_model=settings.VSEGPT_MODEL,
        credit_portfolio_ftp_host=settings.CREDIT_PORTFOLIO_FTP_HOST,
        credit_portfolio_ftp_user=settings.CREDIT_PORTFOLIO_FTP_USER,
        credit_portfolio_ftp_password=settings.CREDIT_PORTFOLIO_FTP_PASSWORD,
        credit_portfolio_ftp_remote_dir=settings.CREDIT_PORTFOLIO_FTP_REMOTE_DIR,
        credit_portfolio_ftp_local_dir=settings.CREDIT_PORTFOLIO_FTP_LOCAL_DIR,
        scheduler_enabled=settings.SCHEDULER_ENABLED,
        credit_portfolio_import_enabled=settings.CREDIT_PORTFOLIO_IMPORT_ENABLED,
        credit_portfolio_import_hour=settings.CREDIT_PORTFOLIO_IMPORT_HOUR,
        credit_portfolio_import_minute=settings.CREDIT_PORTFOLIO_IMPORT_MINUTE,
    )


@router.put("/config", response_model=AdminConfigResponse, tags=["Admin"])
async def update_admin_config(
    payload: AdminConfigUpdate,
    current_user: User = Depends(get_current_active_user),
) -> AdminConfigResponse:
    """
    Обновляет чувствительные настройки для администраторов (только в памяти).

    Значения не сохраняются между рестартами приложения — это runtime override.
    """
    ensure_admin(current_user)
    updates = payload.model_dump(exclude_unset=True)

    # Map API fields → settings attributes
    mapping = {
        "app_name": "APP_NAME",
        "odata_url": "ODATA_1C_URL",
        "odata_username": "ODATA_1C_USERNAME",
        "odata_password": "ODATA_1C_PASSWORD",
        "odata_custom_auth_token": "ODATA_1C_CUSTOM_AUTH_TOKEN",
        "vsegpt_api_key": "VSEGPT_API_KEY",
        "vsegpt_base_url": "VSEGPT_BASE_URL",
        "vsegpt_model": "VSEGPT_MODEL",
        "credit_portfolio_ftp_host": "CREDIT_PORTFOLIO_FTP_HOST",
        "credit_portfolio_ftp_user": "CREDIT_PORTFOLIO_FTP_USER",
        "credit_portfolio_ftp_password": "CREDIT_PORTFOLIO_FTP_PASSWORD",
        "credit_portfolio_ftp_remote_dir": "CREDIT_PORTFOLIO_FTP_REMOTE_DIR",
        "credit_portfolio_ftp_local_dir": "CREDIT_PORTFOLIO_FTP_LOCAL_DIR",
        "scheduler_enabled": "SCHEDULER_ENABLED",
        "credit_portfolio_import_enabled": "CREDIT_PORTFOLIO_IMPORT_ENABLED",
        "credit_portfolio_import_hour": "CREDIT_PORTFOLIO_IMPORT_HOUR",
        "credit_portfolio_import_minute": "CREDIT_PORTFOLIO_IMPORT_MINUTE",
    }

    for field, value in updates.items():
        attr = mapping.get(field)
        if attr is None:
            continue
        # Simple runtime override; not persisted across restarts
        setattr(settings, attr, value)

    # Return refreshed config snapshot
    return await get_admin_config(current_user)
