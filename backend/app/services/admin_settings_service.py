"""
Admin Settings Service
Manages persistent admin settings stored in database with fallback to .env
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models import AdminSettings, User
from app.core.config import settings as env_settings


class AdminSettingsService:
    """Service for managing admin settings with DB persistence"""

    @staticmethod
    def get_or_create(db: Session) -> AdminSettings:
        """
        Get admin settings singleton (id=1) or create with .env defaults

        Returns:
            AdminSettings: The singleton admin settings record
        """
        admin_settings = db.query(AdminSettings).filter(AdminSettings.id == 1).first()

        if not admin_settings:
            # Create with .env defaults
            admin_settings = AdminSettings(
                id=1,  # Singleton
                app_name=env_settings.APP_NAME,
                odata_url=env_settings.ODATA_1C_URL,
                odata_username=env_settings.ODATA_1C_USERNAME,
                odata_password=env_settings.ODATA_1C_PASSWORD,
                odata_custom_auth_token=env_settings.ODATA_1C_CUSTOM_AUTH_TOKEN,
                vsegpt_api_key=env_settings.VSEGPT_API_KEY,
                vsegpt_base_url=env_settings.VSEGPT_BASE_URL,
                vsegpt_model=env_settings.VSEGPT_MODEL,
                credit_portfolio_ftp_host=env_settings.CREDIT_PORTFOLIO_FTP_HOST,
                credit_portfolio_ftp_user=env_settings.CREDIT_PORTFOLIO_FTP_USER,
                credit_portfolio_ftp_password=env_settings.CREDIT_PORTFOLIO_FTP_PASSWORD,
                credit_portfolio_ftp_remote_dir=env_settings.CREDIT_PORTFOLIO_FTP_REMOTE_DIR,
                credit_portfolio_ftp_local_dir=env_settings.CREDIT_PORTFOLIO_FTP_LOCAL_DIR,
                scheduler_enabled=env_settings.SCHEDULER_ENABLED,
                credit_portfolio_import_enabled=env_settings.CREDIT_PORTFOLIO_IMPORT_ENABLED,
                credit_portfolio_import_hour=env_settings.CREDIT_PORTFOLIO_IMPORT_HOUR,
                credit_portfolio_import_minute=env_settings.CREDIT_PORTFOLIO_IMPORT_MINUTE,
            )
            db.add(admin_settings)
            db.commit()
            db.refresh(admin_settings)

        return admin_settings

    @staticmethod
    def update(
        db: Session,
        updates: dict,
        current_user: Optional[User] = None
    ) -> AdminSettings:
        """
        Update admin settings

        Args:
            db: Database session
            updates: Dictionary of fields to update
            current_user: User making the update (for audit trail)

        Returns:
            AdminSettings: Updated settings
        """
        admin_settings = AdminSettingsService.get_or_create(db)

        # Update fields
        for field, value in updates.items():
            if hasattr(admin_settings, field):
                setattr(admin_settings, field, value)

        # Update metadata
        admin_settings.updated_at = datetime.utcnow()
        if current_user:
            admin_settings.updated_by_id = current_user.id

        db.commit()
        db.refresh(admin_settings)

        return admin_settings

    @staticmethod
    def get_vsegpt_api_key(db: Session) -> Optional[str]:
        """
        Get VseGPT API key from DB with fallback to .env

        Args:
            db: Database session

        Returns:
            str: API key or None
        """
        try:
            admin_settings = AdminSettingsService.get_or_create(db)
            # Use DB value if set, otherwise fallback to .env
            return admin_settings.vsegpt_api_key or env_settings.VSEGPT_API_KEY
        except Exception:
            # Fallback to .env if DB access fails
            return env_settings.VSEGPT_API_KEY

    @staticmethod
    def get_vsegpt_config(db: Session) -> dict:
        """
        Get full VseGPT configuration from DB with .env fallback

        Args:
            db: Database session

        Returns:
            dict: Configuration with api_key, base_url, model
        """
        try:
            admin_settings = AdminSettingsService.get_or_create(db)
            return {
                "api_key": admin_settings.vsegpt_api_key or env_settings.VSEGPT_API_KEY,
                "base_url": admin_settings.vsegpt_base_url or env_settings.VSEGPT_BASE_URL,
                "model": admin_settings.vsegpt_model or env_settings.VSEGPT_MODEL,
            }
        except Exception:
            # Fallback to .env if DB access fails
            return {
                "api_key": env_settings.VSEGPT_API_KEY,
                "base_url": env_settings.VSEGPT_BASE_URL,
                "model": env_settings.VSEGPT_MODEL,
            }

    @staticmethod
    def get_odata_config(db: Session) -> dict:
        """
        Get 1C OData configuration from DB with .env fallback

        Args:
            db: Database session

        Returns:
            dict: Configuration with url, username, password, custom_auth_token
        """
        try:
            admin_settings = AdminSettingsService.get_or_create(db)
            return {
                "url": admin_settings.odata_url or env_settings.ODATA_1C_URL,
                "username": admin_settings.odata_username or env_settings.ODATA_1C_USERNAME,
                "password": admin_settings.odata_password or env_settings.ODATA_1C_PASSWORD,
                "custom_auth_token": admin_settings.odata_custom_auth_token or env_settings.ODATA_1C_CUSTOM_AUTH_TOKEN,
            }
        except Exception:
            # Fallback to .env if DB access fails
            return {
                "url": env_settings.ODATA_1C_URL,
                "username": env_settings.ODATA_1C_USERNAME,
                "password": env_settings.ODATA_1C_PASSWORD,
                "custom_auth_token": env_settings.ODATA_1C_CUSTOM_AUTH_TOKEN,
            }
