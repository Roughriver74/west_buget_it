"""
Tests for Module System - Module Access Control

Tests cover:
- Module enabling/disabling
- Access checks
- Feature limits
- Event logging
"""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import Module, OrganizationModule, ModuleEvent, FeatureLimit
from app.services.module_service import ModuleService


@pytest.fixture
def module_service(db: Session):
    """Create ModuleService instance"""
    return ModuleService(db)


@pytest.fixture
def test_module(db: Session):
    """Create test module"""
    module = Module(
        code="TEST_MODULE",
        name="Test Module",
        description="Module for testing",
        version="1.0.0",
        is_active=True
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


@pytest.fixture
def test_organization(db: Session):
    """Create test organization"""
    from app.db.models import Organization, Department

    org = Organization(
        full_name="Test Organization",
        short_name="TestOrg",
        inn="1234567890"
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # Create department for organization
    dept = Department(
        name="Test Department",
        organization_id=org.id
    )
    db.add(dept)
    db.commit()

    return org


class TestModuleEnabling:
    """Test module enabling and disabling"""

    def test_enable_module_for_organization(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test enabling a module for an organization"""
        # Enable module
        org_module = module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            enabled_by_user_id=1
        )

        # Verify
        assert org_module is not None
        assert org_module.organization_id == test_organization.id
        assert org_module.module_id == test_module.id
        assert org_module.is_active is True

    def test_enable_module_with_expiration(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test enabling a module with expiration date"""
        expires_at = datetime.utcnow() + timedelta(days=365)

        org_module = module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            expires_at=expires_at,
            enabled_by_user_id=1
        )

        assert org_module.expires_at is not None
        assert org_module.expires_at == expires_at

    def test_enable_module_with_limits(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test enabling a module with feature limits"""
        limits = {
            "max_records": 1000,
            "api_calls_per_month": 10000
        }

        org_module = module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            limits=limits,
            enabled_by_user_id=1
        )

        assert org_module.limits == limits

    def test_disable_module_for_organization(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test disabling a module"""
        # First enable
        module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            enabled_by_user_id=1
        )

        # Then disable
        module_service.disable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            disabled_by_user_id=1
        )

        # Verify disabled
        assert not module_service.is_module_enabled(
            test_organization.id,
            test_module.code
        )

    def test_enable_nonexistent_module(
        self,
        module_service: ModuleService,
        test_organization
    ):
        """Test enabling a module that doesn't exist"""
        with pytest.raises(ValueError, match="Module with code .* not found"):
            module_service.enable_module_for_organization(
                organization_id=test_organization.id,
                module_code="NONEXISTENT_MODULE",
                enabled_by_user_id=1
            )


class TestModuleAccessChecks:
    """Test module access checking"""

    def test_is_module_enabled_active(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test checking if module is enabled"""
        # Enable module
        module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            enabled_by_user_id=1
        )

        # Check access
        assert module_service.is_module_enabled(
            test_organization.id,
            test_module.code
        ) is True

    def test_is_module_enabled_not_enabled(
        self,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test checking module that is not enabled"""
        assert module_service.is_module_enabled(
            test_organization.id,
            test_module.code
        ) is False

    def test_is_module_enabled_expired(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test checking module that has expired"""
        # Enable with past expiration
        expires_at = datetime.utcnow() - timedelta(days=1)
        module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            expires_at=expires_at,
            enabled_by_user_id=1
        )

        # Should be disabled because expired
        assert module_service.is_module_enabled(
            test_organization.id,
            test_module.code
        ) is False

    def test_get_enabled_modules(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test getting list of enabled modules"""
        # Enable module
        module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            enabled_by_user_id=1
        )

        # Get enabled modules
        enabled = module_service.get_enabled_modules(
            organization_id=test_organization.id
        )

        assert len(enabled) > 0
        assert any(m["code"] == test_module.code for m in enabled)

    def test_get_enabled_modules_exclude_expired(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test that expired modules are excluded by default"""
        # Enable expired module
        expires_at = datetime.utcnow() - timedelta(days=1)
        module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            expires_at=expires_at,
            enabled_by_user_id=1
        )

        # Get enabled modules (should exclude expired)
        enabled = module_service.get_enabled_modules(
            organization_id=test_organization.id,
            include_expired=False
        )

        assert not any(m["code"] == test_module.code for m in enabled)


class TestFeatureLimits:
    """Test feature limit enforcement"""

    def test_check_feature_limit_no_limit(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test checking limit when no limit is set"""
        # Enable without limits
        module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            enabled_by_user_id=1
        )

        # Should not raise error
        module_service.check_feature_limit(
            organization_id=test_organization.id,
            module_code=test_module.code,
            limit_type="api_calls"
        )

    def test_check_feature_limit_within_limit(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test checking limit when within limit"""
        # Enable with limit
        module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            limits={"api_calls": 100},
            enabled_by_user_id=1
        )

        # Should not raise error (0 < 100)
        module_service.check_feature_limit(
            organization_id=test_organization.id,
            module_code=test_module.code,
            limit_type="api_calls"
        )

    def test_check_feature_limit_exceeded(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test checking limit when exceeded"""
        # Enable with small limit
        org_module = module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            limits={"api_calls": 10},
            enabled_by_user_id=1
        )

        # Create feature limit record
        feature_limit = FeatureLimit(
            organization_module_id=org_module.id,
            limit_type="api_calls",
            limit_value=10,
            current_usage=15  # Exceeded
        )
        db.add(feature_limit)
        db.commit()

        # Should raise error
        with pytest.raises(HTTPException) as exc_info:
            module_service.check_feature_limit(
                organization_id=test_organization.id,
                module_code=test_module.code,
                limit_type="api_calls"
            )

        assert exc_info.value.status_code == 403
        assert "limit exceeded" in str(exc_info.value.detail).lower()

    def test_increment_usage(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test incrementing usage counter"""
        # Enable with limit
        org_module = module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            limits={"api_calls": 100},
            enabled_by_user_id=1
        )

        # Create feature limit
        feature_limit = FeatureLimit(
            organization_module_id=org_module.id,
            limit_type="api_calls",
            limit_value=100,
            current_usage=0
        )
        db.add(feature_limit)
        db.commit()

        # Increment
        module_service.increment_usage(
            organization_id=test_organization.id,
            module_code=test_module.code,
            limit_type="api_calls",
            increment=5
        )

        # Verify
        db.refresh(feature_limit)
        assert feature_limit.current_usage == 5


class TestModuleEvents:
    """Test module event logging"""

    def test_event_logged_on_enable(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test that event is logged when module is enabled"""
        module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            enabled_by_user_id=1
        )

        # Check event was logged
        event = db.query(ModuleEvent).filter_by(
            organization_id=test_organization.id,
            module_id=test_module.id,
            event_type="MODULE_ENABLED"
        ).first()

        assert event is not None
        assert event.created_by_id == 1

    def test_event_logged_on_disable(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test that event is logged when module is disabled"""
        # First enable
        module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            enabled_by_user_id=1
        )

        # Then disable
        module_service.disable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            disabled_by_user_id=1
        )

        # Check event was logged
        event = db.query(ModuleEvent).filter_by(
            organization_id=test_organization.id,
            module_id=test_module.id,
            event_type="MODULE_DISABLED"
        ).first()

        assert event is not None

    def test_event_logged_on_limit_exceeded(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test that event is logged when limit is exceeded"""
        # Enable with small limit
        org_module = module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            limits={"api_calls": 10},
            enabled_by_user_id=1
        )

        # Create exceeded limit
        feature_limit = FeatureLimit(
            organization_module_id=org_module.id,
            limit_type="api_calls",
            limit_value=10,
            current_usage=15
        )
        db.add(feature_limit)
        db.commit()

        # Try to check limit (will fail and log event)
        try:
            module_service.check_feature_limit(
                organization_id=test_organization.id,
                module_code=test_module.code,
                limit_type="api_calls"
            )
        except HTTPException:
            pass

        # Check event was logged
        event = db.query(ModuleEvent).filter_by(
            organization_id=test_organization.id,
            module_id=test_module.id,
            event_type="LIMIT_EXCEEDED"
        ).first()

        assert event is not None


class TestModuleIntegration:
    """Integration tests for complete workflows"""

    def test_complete_module_lifecycle(
        self,
        db: Session,
        module_service: ModuleService,
        test_module: Module,
        test_organization
    ):
        """Test complete lifecycle: enable -> use -> disable"""
        # 1. Enable module
        org_module = module_service.enable_module_for_organization(
            organization_id=test_organization.id,
            module_code=test_module.code,
            expires_at=datetime.utcnow() + timedelta(days=365),
            limits={"api_calls": 1000},
            enabled_by_user_id=1
        )
        assert org_module is not None

        # 2. Check access
        assert module_service.is_module_enabled(
            test_organization.id,
            test_module.code
        ) is True

        # 3. Use feature (increment usage)
        module_service.increment_usage(
            test_organization.id,
            test_module.code,
            "api_calls",
            10
        )

        # 4. Check limit
        module_service.check_feature_limit(
            test_organization.id,
            test_module.code,
            "api_calls"
        )

        # 5. Disable module
        module_service.disable_module_for_organization(
            test_organization.id,
            test_module.code,
            disabled_by_user_id=1
        )

        # 6. Verify disabled
        assert module_service.is_module_enabled(
            test_organization.id,
            test_module.code
        ) is False

        # 7. Check events logged
        events = db.query(ModuleEvent).filter_by(
            organization_id=test_organization.id,
            module_id=test_module.id
        ).all()

        assert len(events) >= 2  # At least ENABLED and DISABLED
        event_types = [e.event_type for e in events]
        assert "MODULE_ENABLED" in event_types
        assert "MODULE_DISABLED" in event_types
