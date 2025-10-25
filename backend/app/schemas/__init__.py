from .expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseInDB,
    ExpenseList,
    ExpenseStatusUpdate,
)
from .category import BudgetCategoryCreate, BudgetCategoryUpdate, BudgetCategoryInDB
from .contractor import ContractorCreate, ContractorUpdate, ContractorInDB
from .organization import OrganizationCreate, OrganizationUpdate, OrganizationInDB
from .budget import BudgetPlanCreate, BudgetPlanUpdate, BudgetPlanInDB
from .attachment import (
    AttachmentCreate,
    AttachmentUpdate,
    AttachmentInDB,
    AttachmentList,
)
from .dashboard import (
    DashboardConfigCreate,
    DashboardConfigUpdate,
    DashboardConfigInDB,
    DashboardConfigList,
)
from .user import (
    User,
    UserCreate,
    UserUpdate,
    UserPasswordChange,
    UserListItem,
    Token,
    TokenData,
    UserLogin,
    UserLoginResponse,
)
from .department import (
    Department,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentListItem,
    DepartmentWithStats,
)
from .audit import (
    AuditLogCreate,
    AuditLogInDB,
    AuditLogWithUser,
)
from .payroll import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeInDB,
    EmployeeWithSalaryHistory,
    SalaryHistoryCreate,
    SalaryHistoryInDB,
    PayrollPlanCreate,
    PayrollPlanUpdate,
    PayrollPlanInDB,
    PayrollPlanWithEmployee,
    PayrollActualCreate,
    PayrollActualUpdate,
    PayrollActualInDB,
    PayrollActualWithEmployee,
    PayrollSummary,
    EmployeePayrollStats,
    DepartmentPayrollStats,
)

# Rebuild models to resolve forward references
ExpenseInDB.model_rebuild()
ExpenseList.model_rebuild()

__all__ = [
    # Expense
    "ExpenseCreate",
    "ExpenseUpdate",
    "ExpenseInDB",
    "ExpenseList",
    "ExpenseStatusUpdate",
    # Category
    "BudgetCategoryCreate",
    "BudgetCategoryUpdate",
    "BudgetCategoryInDB",
    # Contractor
    "ContractorCreate",
    "ContractorUpdate",
    "ContractorInDB",
    # Organization
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationInDB",
    # Budget Plan
    "BudgetPlanCreate",
    "BudgetPlanUpdate",
    "BudgetPlanInDB",
    # Attachment
    "AttachmentCreate",
    "AttachmentUpdate",
    "AttachmentInDB",
    "AttachmentList",
    # Dashboard Config
    "DashboardConfigCreate",
    "DashboardConfigUpdate",
    "DashboardConfigInDB",
    "DashboardConfigList",
    # User
    "User",
    "UserCreate",
    "UserUpdate",
    "UserPasswordChange",
    "UserListItem",
    "Token",
    "TokenData",
    "UserLogin",
    "UserLoginResponse",
    # Department
    "Department",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentListItem",
    "DepartmentWithStats",
    # Audit Log
    "AuditLogCreate",
    "AuditLogInDB",
    "AuditLogWithUser",
    # Payroll (Employee)
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeInDB",
    "EmployeeWithSalaryHistory",
    "SalaryHistoryCreate",
    "SalaryHistoryInDB",
    # Payroll Plan
    "PayrollPlanCreate",
    "PayrollPlanUpdate",
    "PayrollPlanInDB",
    "PayrollPlanWithEmployee",
    # Payroll Actual
    "PayrollActualCreate",
    "PayrollActualUpdate",
    "PayrollActualInDB",
    "PayrollActualWithEmployee",
    # Payroll Analytics
    "PayrollSummary",
    "EmployeePayrollStats",
    "DepartmentPayrollStats",
]
