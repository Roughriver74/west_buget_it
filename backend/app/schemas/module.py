"""
Pydantic schemas for Module system
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ==================== Module Schemas ====================

class ModuleBase(BaseModel):
    """Base schema for Module"""

    code: str = Field(..., min_length=1, max_length=50, description="Unique module code")
    name: str = Field(..., min_length=1, max_length=255, description="Module name")
    description: Optional[str] = Field(None, description="Module description")
    version: Optional[str] = Field(None, max_length=20, description="Module version")
    dependencies: Optional[List[str]] = Field(None, description="List of module codes this module depends on")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name (Ant Design icon)")
    sort_order: Optional[int] = Field(None, description="Sort order in UI")


class ModuleCreate(ModuleBase):
    """Schema for creating a Module"""

    is_active: bool = Field(True, description="Whether module is active")


class ModuleUpdate(BaseModel):
    """Schema for updating a Module"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    version: Optional[str] = Field(None, max_length=20)
    dependencies: Optional[List[str]] = None
    is_active: Optional[bool] = None
    icon: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[int] = None


class ModuleInDB(ModuleBase):
    """Schema for Module in database"""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== OrganizationModule Schemas ====================

class OrganizationModuleBase(BaseModel):
    """Base schema for OrganizationModule"""

    organization_id: int = Field(..., description="Organization ID")
    module_id: int = Field(..., description="Module ID")
    expires_at: Optional[datetime] = Field(None, description="Expiration date (None = no expiration)")
    limits: Optional[Dict[str, Any]] = Field(None, description="Custom limits for this organization")


class OrganizationModuleCreate(OrganizationModuleBase):
    """Schema for creating OrganizationModule"""

    is_active: bool = Field(True, description="Whether module is active for this organization")


class OrganizationModuleUpdate(BaseModel):
    """Schema for updating OrganizationModule"""

    expires_at: Optional[datetime] = None
    limits: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class OrganizationModuleInDB(OrganizationModuleBase):
    """Schema for OrganizationModule in database"""

    id: int
    enabled_at: datetime
    is_active: bool
    enabled_by_id: Optional[int]
    updated_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Module Enable/Disable Requests ====================

class ModuleEnableRequest(BaseModel):
    """Schema for enabling a module for an organization"""

    module_code: str = Field(..., description="Module code to enable")
    organization_id: int = Field(..., description="Organization ID")
    expires_at: Optional[datetime] = Field(None, description="Expiration date (None = no expiration)")
    limits: Optional[Dict[str, Any]] = Field(
        None,
        description="Custom limits (e.g., {'users': 100, 'departments': 5})",
    )


class ModuleDisableRequest(BaseModel):
    """Schema for disabling a module for an organization"""

    module_code: str = Field(..., description="Module code to disable")
    organization_id: int = Field(..., description="Organization ID")


# ==================== Enabled Modules Response ====================

class EnabledModuleInfo(BaseModel):
    """Schema for enabled module information"""

    code: str
    name: str
    description: Optional[str]
    version: Optional[str]
    icon: Optional[str]
    enabled_at: datetime
    expires_at: Optional[datetime]
    is_expired: bool
    limits: Dict[str, Any]


class EnabledModulesResponse(BaseModel):
    """Schema for response with enabled modules"""

    modules: List[EnabledModuleInfo]
    organization_id: int
    organization_name: str


# ==================== Feature Limit Schemas ====================

class FeatureLimitBase(BaseModel):
    """Base schema for FeatureLimit"""

    organization_module_id: int
    limit_type: str = Field(..., max_length=50, description="Type of limit (users, departments, api_calls)")
    limit_value: int = Field(..., ge=0, description="Maximum allowed value")
    warning_threshold: Optional[int] = Field(None, ge=0, description="Threshold for warning (optional)")


class FeatureLimitCreate(FeatureLimitBase):
    """Schema for creating FeatureLimit"""

    current_usage: int = Field(0, ge=0, description="Current usage count")


class FeatureLimitUpdate(BaseModel):
    """Schema for updating FeatureLimit"""

    limit_value: Optional[int] = Field(None, ge=0)
    warning_threshold: Optional[int] = Field(None, ge=0)
    current_usage: Optional[int] = Field(None, ge=0)


class FeatureLimitInDB(FeatureLimitBase):
    """Schema for FeatureLimit in database"""

    id: int
    current_usage: int
    last_checked_at: Optional[datetime]
    warning_sent: bool
    created_at: datetime
    updated_at: datetime

    # Computed properties
    usage_percent: float
    is_exceeded: bool
    is_warning_threshold_reached: bool

    class Config:
        from_attributes = True


# ==================== Module Event Schemas ====================

class ModuleEventBase(BaseModel):
    """Base schema for ModuleEvent"""

    organization_id: int
    module_id: int
    event_type: str = Field(..., description="Type of event (MODULE_ENABLED, LIMIT_EXCEEDED, etc.)")
    event_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional event data")


class ModuleEventCreate(ModuleEventBase):
    """Schema for creating ModuleEvent"""

    created_by_id: Optional[int] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)


class ModuleEventInDB(ModuleEventBase):
    """Schema for ModuleEvent in database"""

    id: int
    created_by_id: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Statistics & Analytics ====================

class ModuleStatistics(BaseModel):
    """Schema for module usage statistics"""

    module_code: str
    module_name: str
    total_organizations: int
    active_organizations: int
    expired_organizations: int
    total_events: int


class OrganizationModuleStatus(BaseModel):
    """Schema for organization module status summary"""

    organization_id: int
    organization_name: str
    total_modules: int
    enabled_modules: int
    expired_modules: int
    modules: List[EnabledModuleInfo]
