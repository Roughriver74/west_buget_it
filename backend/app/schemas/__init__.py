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
from .analytics import (
    DashboardData,
    DashboardTotals,
    DashboardCapexVsOpex,
    DashboardStatusDistribution,
    DashboardTopCategory,
    DashboardRecentExpense,
    CategoryAnalytics,
    CategoryAnalyticsItem,
    Trends,
    TrendItem,
    PaymentCalendar,
    PaymentCalendarDay,
    PaymentsByDay,
    PaymentDetail,
    PaymentForecast,
    PaymentForecastPeriod,
    PaymentForecastSummary,
    PaymentForecastPoint,
    ForecastSummary,
    ForecastSummaryPeriod,
    ForecastSummaryMethods,
    ForecastSummaryMethodStats,
    ForecastMethodEnum,
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
from .budget_planning import (
    # Scenario
    BudgetScenarioCreate,
    BudgetScenarioUpdate,
    BudgetScenarioInDB,
    # Version
    BudgetVersionCreate,
    BudgetVersionUpdate,
    BudgetVersionInDB,
    BudgetVersionWithDetails,
    # Plan Details
    BudgetPlanDetailCreate,
    BudgetPlanDetailUpdate,
    BudgetPlanDetailInDB,
    # Approval Log
    BudgetApprovalLogCreate,
    BudgetApprovalLogInDB,
    # Calculator
    CalculateByAverageRequest,
    CalculateByGrowthRequest,
    CalculateByDriverRequest,
    CalculateBySeasonalRequest,
    CalculationResult,
    BaselineSummary,
    VersionComparison,
    VersionComparisonResult,
)
from .kpi import (
    # KPI Goals
    KPIGoalCreate,
    KPIGoalUpdate,
    KPIGoalInDB,
    # Employee KPI
    EmployeeKPICreate,
    EmployeeKPIUpdate,
    EmployeeKPIInDB,
    EmployeeKPIWithGoals,
    # Employee KPI Goals
    EmployeeKPIGoalCreate,
    EmployeeKPIGoalUpdate,
    EmployeeKPIGoalInDB,
    EmployeeKPIGoalWithDetails,
    # KPI Analytics
    KPIEmployeeSummary,
    KPIDepartmentSummary,
    KPIGoalProgress,
)

# Rebuild models to resolve forward references
ExpenseInDB.model_rebuild()
ExpenseList.model_rebuild()
EmployeeWithSalaryHistory.model_rebuild()
EmployeeKPIWithGoals.model_rebuild()
EmployeeKPIGoalWithDetails.model_rebuild()

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
    # Analytics
    "DashboardData",
    "DashboardTotals",
    "DashboardCapexVsOpex",
    "DashboardStatusDistribution",
    "DashboardTopCategory",
    "DashboardRecentExpense",
    "CategoryAnalytics",
    "CategoryAnalyticsItem",
    "Trends",
    "TrendItem",
    "PaymentCalendar",
    "PaymentCalendarDay",
    "PaymentsByDay",
    "PaymentDetail",
    "PaymentForecast",
    "PaymentForecastPeriod",
    "PaymentForecastSummary",
    "PaymentForecastPoint",
    "ForecastSummary",
    "ForecastSummaryPeriod",
    "ForecastSummaryMethods",
    "ForecastSummaryMethodStats",
    "ForecastMethodEnum",
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
    # Budget 2026 - Scenarios
    "BudgetScenarioCreate",
    "BudgetScenarioUpdate",
    "BudgetScenarioInDB",
    # Budget 2026 - Versions
    "BudgetVersionCreate",
    "BudgetVersionUpdate",
    "BudgetVersionInDB",
    "BudgetVersionWithDetails",
    # Budget 2026 - Plan Details
    "BudgetPlanDetailCreate",
    "BudgetPlanDetailUpdate",
    "BudgetPlanDetailInDB",
    # Budget 2026 - Approval Log
    "BudgetApprovalLogCreate",
    "BudgetApprovalLogInDB",
    # Budget 2026 - Calculator
    "CalculateByAverageRequest",
    "CalculateByGrowthRequest",
    "CalculateByDriverRequest",
    "CalculateBySeasonalRequest",
    "CalculationResult",
    "BaselineSummary",
    "VersionComparison",
    "VersionComparisonResult",
    # KPI Goals
    "KPIGoalCreate",
    "KPIGoalUpdate",
    "KPIGoalInDB",
    # Employee KPI
    "EmployeeKPICreate",
    "EmployeeKPIUpdate",
    "EmployeeKPIInDB",
    "EmployeeKPIWithGoals",
    # Employee KPI Goals
    "EmployeeKPIGoalCreate",
    "EmployeeKPIGoalUpdate",
    "EmployeeKPIGoalInDB",
    "EmployeeKPIGoalWithDetails",
    # KPI Analytics
    "KPIEmployeeSummary",
    "KPIDepartmentSummary",
    "KPIGoalProgress",
]
