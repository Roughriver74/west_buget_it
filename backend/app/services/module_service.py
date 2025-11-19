"""
Module Service - Business logic for module access control and management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.models import (
    Module,
    OrganizationModule,
    FeatureLimit,
    ModuleEvent,
    ModuleEventTypeEnum,
    Organization,
    User,
)


class ModuleService:
    """Service for managing module access and permissions"""

    def __init__(self, db: Session):
        self.db = db

    def is_module_enabled(
        self,
        organization_id: int,
        module_code: str,
    ) -> bool:
        """
        Check if a module is enabled for an organization
        
        TEMPORARILY DISABLED: Module system is disabled - all modules return True.

        Args:
            organization_id: Organization ID
            module_code: Module code (e.g., "AI_FORECAST")

        Returns:
            True if module is enabled and not expired, False otherwise
        """
        # TEMPORARILY DISABLED: Module system is disabled - allow all access
        return True
        
        # # Get module
        # module = self.db.query(Module).filter_by(
        #     code=module_code,
        #     is_active=True
        # ).first()

        # if not module:
        #     return False

        # # Check if organization has this module
        # org_module = self.db.query(OrganizationModule).join(Module).filter(
        #     and_(
        #         OrganizationModule.organization_id == organization_id,
        #         OrganizationModule.module_id == module.id,
        #         OrganizationModule.is_active == True,
        #         or_(
        #             OrganizationModule.expires_at.is_(None),
        #             OrganizationModule.expires_at > datetime.utcnow()
        #         )
        #     )
        # ).first()

        # return org_module is not None

    def get_enabled_modules(
        self,
        organization_id: int,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get list of enabled modules for an organization

        Args:
            organization_id: Organization ID
            include_expired: Include expired modules

        Returns:
            List of enabled modules with details
        """
        query = self.db.query(OrganizationModule, Module).join(Module).filter(
            OrganizationModule.organization_id == organization_id,
            OrganizationModule.is_active == True,
            Module.is_active == True
        )

        if not include_expired:
            query = query.filter(
                or_(
                    OrganizationModule.expires_at.is_(None),
                    OrganizationModule.expires_at > datetime.utcnow()
                )
            )

        results = query.order_by(Module.sort_order).all()

        modules = []
        for org_module, module in results:
            modules.append({
                "code": module.code,
                "name": module.name,
                "description": module.description,
                "version": module.version,
                "icon": module.icon,
                "enabled_at": org_module.enabled_at,
                "expires_at": org_module.expires_at,
                "limits": org_module.limits or {},
                "is_expired": (
                    org_module.expires_at is not None and
                    org_module.expires_at < datetime.utcnow()
                ),
            })

        return modules

    def check_feature_limit(
        self,
        organization_id: int,
        module_code: str,
        limit_type: str,
    ) -> Dict[str, Any]:
        """
        Check feature limit for a module

        Args:
            organization_id: Organization ID
            module_code: Module code
            limit_type: Type of limit (e.g., "users", "departments", "api_calls")

        Returns:
            Dict with limit information:
            {
                "has_limit": bool,
                "limit_value": int,
                "current_usage": int,
                "is_exceeded": bool,
                "is_warning": bool,
                "usage_percent": float
            }
        """
        # Get module
        module = self.db.query(Module).filter_by(code=module_code).first()
        if not module:
            return {
                "has_limit": False,
                "limit_value": 0,
                "current_usage": 0,
                "is_exceeded": False,
                "is_warning": False,
                "usage_percent": 0.0
            }

        # Get organization module
        org_module = self.db.query(OrganizationModule).filter_by(
            organization_id=organization_id,
            module_id=module.id
        ).first()

        if not org_module:
            return {
                "has_limit": False,
                "limit_value": 0,
                "current_usage": 0,
                "is_exceeded": False,
                "is_warning": False,
                "usage_percent": 0.0
            }

        # Check if limit exists in limits JSON or in feature_limits table
        limit_in_json = org_module.limits and limit_type in org_module.limits

        if limit_in_json:
            # Simple limit in JSON
            limit_value = org_module.limits[limit_type]
            return {
                "has_limit": True,
                "limit_value": limit_value,
                "current_usage": 0,  # Would need separate tracking
                "is_exceeded": False,
                "is_warning": False,
                "usage_percent": 0.0
            }

        # Check feature_limits table
        feature_limit = self.db.query(FeatureLimit).filter_by(
            organization_module_id=org_module.id,
            limit_type=limit_type
        ).first()

        if not feature_limit:
            return {
                "has_limit": False,
                "limit_value": 0,
                "current_usage": 0,
                "is_exceeded": False,
                "is_warning": False,
                "usage_percent": 0.0
            }

        return {
            "has_limit": True,
            "limit_value": feature_limit.limit_value,
            "current_usage": feature_limit.current_usage,
            "is_exceeded": feature_limit.is_exceeded,
            "is_warning": feature_limit.is_warning_threshold_reached,
            "usage_percent": feature_limit.usage_percent
        }

    def increment_usage(
        self,
        organization_id: int,
        module_code: str,
        limit_type: str,
        increment: int = 1
    ) -> bool:
        """
        Increment usage counter for a feature limit

        Args:
            organization_id: Organization ID
            module_code: Module code
            limit_type: Type of limit
            increment: Amount to increment by

        Returns:
            True if successful, False if limit would be exceeded
        """
        # Get module and org_module
        module = self.db.query(Module).filter_by(code=module_code).first()
        if not module:
            return False

        org_module = self.db.query(OrganizationModule).filter_by(
            organization_id=organization_id,
            module_id=module.id
        ).first()

        if not org_module:
            return False

        # Get or create feature limit
        feature_limit = self.db.query(FeatureLimit).filter_by(
            organization_module_id=org_module.id,
            limit_type=limit_type
        ).first()

        if not feature_limit:
            # No limit defined, allow
            return True

        # Check if would exceed
        new_usage = feature_limit.current_usage + increment
        if new_usage > feature_limit.limit_value:
            # Emit limit exceeded event
            self.emit_event(
                organization_id=organization_id,
                module_id=module.id,
                event_type=ModuleEventTypeEnum.LIMIT_EXCEEDED,
                metadata={
                    "limit_type": limit_type,
                    "limit_value": feature_limit.limit_value,
                    "attempted_usage": new_usage
                }
            )
            return False

        # Update usage
        feature_limit.current_usage = new_usage
        feature_limit.last_checked_at = datetime.utcnow()

        # Check warning threshold
        if (
            not feature_limit.warning_sent and
            feature_limit.is_warning_threshold_reached
        ):
            feature_limit.warning_sent = True
            self.emit_event(
                organization_id=organization_id,
                module_id=module.id,
                event_type=ModuleEventTypeEnum.LIMIT_WARNING,
                metadata={
                    "limit_type": limit_type,
                    "limit_value": feature_limit.limit_value,
                    "current_usage": feature_limit.current_usage,
                    "usage_percent": feature_limit.usage_percent
                }
            )

        self.db.commit()
        return True

    def emit_event(
        self,
        organization_id: int,
        module_id: int,
        event_type: ModuleEventTypeEnum,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Emit a module event for auditing

        Args:
            organization_id: Organization ID
            module_id: Module ID
            event_type: Type of event
            metadata: Additional event data
            user_id: User who triggered the event
            ip_address: IP address
            user_agent: User agent string
        """
        event = ModuleEvent(
            organization_id=organization_id,
            module_id=module_id,
            event_type=event_type,
            event_metadata=metadata,
            created_by_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(event)
        self.db.commit()

    def get_module_by_code(self, module_code: str) -> Optional[Module]:
        """Get module by code"""
        return self.db.query(Module).filter_by(
            code=module_code,
            is_active=True
        ).first()

    def get_all_modules(self, active_only: bool = True) -> List[Module]:
        """Get all available modules"""
        query = self.db.query(Module)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Module.sort_order).all()

    def enable_module_for_organization(
        self,
        organization_id: int,
        module_code: str,
        expires_at: Optional[datetime] = None,
        limits: Optional[Dict[str, Any]] = None,
        enabled_by_user_id: Optional[int] = None
    ) -> OrganizationModule:
        """
        Enable a module for an organization

        Args:
            organization_id: Organization ID
            module_code: Module code
            expires_at: Expiration date (None = no expiration)
            limits: Limits dict
            enabled_by_user_id: User ID who enabled the module

        Returns:
            OrganizationModule instance
        """
        # Get module
        module = self.get_module_by_code(module_code)
        if not module:
            raise ValueError(f"Module {module_code} not found")

        # Check if already exists
        org_module = self.db.query(OrganizationModule).filter_by(
            organization_id=organization_id,
            module_id=module.id
        ).first()

        if org_module:
            # Update existing
            org_module.is_active = True
            org_module.expires_at = expires_at
            org_module.limits = limits
            org_module.updated_by_id = enabled_by_user_id
            org_module.updated_at = datetime.utcnow()
        else:
            # Create new
            org_module = OrganizationModule(
                organization_id=organization_id,
                module_id=module.id,
                enabled_at=datetime.utcnow(),
                expires_at=expires_at,
                limits=limits,
                is_active=True,
                enabled_by_id=enabled_by_user_id
            )
            self.db.add(org_module)

        # Emit event
        self.emit_event(
            organization_id=organization_id,
            module_id=module.id,
            event_type=ModuleEventTypeEnum.MODULE_ENABLED,
            metadata={
                "expires_at": expires_at.isoformat() if expires_at else None,
                "limits": limits
            },
            user_id=enabled_by_user_id
        )

        self.db.commit()
        return org_module

    def disable_module_for_organization(
        self,
        organization_id: int,
        module_code: str,
        disabled_by_user_id: Optional[int] = None
    ):
        """
        Disable a module for an organization

        Args:
            organization_id: Organization ID
            module_code: Module code
            disabled_by_user_id: User ID who disabled the module
        """
        module = self.get_module_by_code(module_code)
        if not module:
            raise ValueError(f"Module {module_code} not found")

        org_module = self.db.query(OrganizationModule).filter_by(
            organization_id=organization_id,
            module_id=module.id
        ).first()

        if org_module:
            org_module.is_active = False
            org_module.updated_by_id = disabled_by_user_id
            org_module.updated_at = datetime.utcnow()

            # Emit event
            self.emit_event(
                organization_id=organization_id,
                module_id=module.id,
                event_type=ModuleEventTypeEnum.MODULE_DISABLED,
                user_id=disabled_by_user_id
            )

            self.db.commit()
