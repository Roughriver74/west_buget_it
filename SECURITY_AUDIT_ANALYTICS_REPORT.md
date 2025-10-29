# SECURITY AUDIT REPORT: Analytics API Endpoints
**Date**: 2025-10-29  
**Files Audited**: 4 critical analytics modules  
**Audit Level**: COMPREHENSIVE - Multi-tenancy & Department-based Access Control

---

## EXECUTIVE SUMMARY

**Overall Status**: CRITICAL VULNERABILITIES FOUND ⚠️

- **3 Critical Import/Compilation Errors** that would cause runtime failures
- **1 HIGH Risk Endpoint** (plan-vs-actual) with incomplete department filtering
- **1 MODERATE Risk Endpoint** (plan-vs-actual) with potential data aggregation bypass
- **Multiple Endpoints**: Properly secured with department filtering
- **Service Layer**: PaymentForecastService properly implements department isolation

---

## FILES AUDITED

1. `/home/user/west_buget_it/backend/app/api/v1/analytics.py` - **1030 lines**
2. `/home/user/west_buget_it/backend/app/api/v1/analytics_advanced.py` - **804 lines**
3. `/home/user/west_buget_it/backend/app/api/v1/forecast.py` - **605 lines**
4. `/home/user/west_buget_it/backend/app/api/v1/comprehensive_report.py` - **641 lines**

---

## DETAILED FINDINGS

### FILE 1: analytics.py

#### **VULNERABILITY #1: Missing Import - UserRoleEnum**
**Severity**: CRITICAL - COMPILATION ERROR  
**Status**: VULNERABLE  
**Location**: Line 1-8 (imports section)  
**Description**: UserRoleEnum is used extensively throughout the file (lines 67, 75, 246, 254, 309, 317, 400, 408, 467, 475, 572, 580, 674, 682, 748, 756, 806, 839, 984) but is NOT imported.

**Code Example** (Line 67):
```python
if current_user.role == UserRoleEnum.USER:  # UserRoleEnum NOT IMPORTED!
    if not current_user.department_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no assigned department"
        )
    department_id = current_user.department_id
```

**Impact**: All endpoints will crash with `NameError: name 'UserRoleEnum' is not defined` at runtime.

**Missing Import**:
```python
from app.db.models import Expense, BudgetCategory, BudgetPlan, BudgetVersion, BudgetPlanDetail, ExpenseStatusEnum, ExpenseTypeEnum, User, PayrollPlan, UserRoleEnum
```

**Fix**: Add `UserRoleEnum` to line 8 import statement.

---

#### **VULNERABILITY #2: Missing Import - status module**
**Severity**: CRITICAL - COMPILATION ERROR  
**Status**: VULNERABLE  
**Location**: Line 2 (imports section)  
**Description**: `status` module used at lines 71, 250 but not imported. HTTPException is imported but `status.HTTP_403_FORBIDDEN` and `status.HTTP_400_BAD_REQUEST` will fail.

**Code Example** (Line 71):
```python
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,  # 'status' NOT IMPORTED!
    detail="User has no assigned department"
)
```

**Impact**: All error responses will crash with `NameError: name 'status' is not defined`.

**Missing Import**:
```python
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status  # Add 'status'
```

**Fix**: Update line 2 to include `status`.

---

### ENDPOINT ANALYSIS: analytics.py

#### **Endpoint 1: GET /dashboard**
**Lines**: 49-229  
**Status**: SECURE ✓  
**Department Filtering**: YES - Properly enforced

**Analysis**:
- Line 67-74: Correctly enforces USER role to use their own department_id
- Lines 80-85: BudgetPlan query properly filters by department_id
- Lines 88-93: PayrollPlan query properly filters by department_id
- Lines 99-106: Expense aggregation properly filters by department_id
- Lines 113-132: Status distribution query properly filters by department_id
- Lines 140-149: Category query properly filters by department_id via Expense join
- Lines 188-205: CAPEX/OPEX queries properly filter by department_id

**Recommendation**: Fix import errors. Endpoint logic is secure.

---

#### **Endpoint 2: GET /budget-execution**
**Lines**: 232-291  
**Status**: SECURE ✓  
**Department Filtering**: YES - Properly enforced

**Analysis**:
- Lines 246-253: Correctly enforces USER role department isolation
- Lines 262-277: All monthly aggregations (planned vs actual) properly filter by department_id

**Recommendation**: Fix import errors only.

---

#### **Endpoint 3: GET /by-category**
**Lines**: 294-382  
**Status**: SECURE ✓  
**Department Filtering**: YES - Properly enforced

**Analysis**:
- Lines 309-316: Correctly enforces USER role department isolation
- Lines 326-327: Category queries properly filter by department_id
- Lines 334-353: All planned/actual/count queries properly filter by department_id

**Recommendation**: Fix import errors only.

---

#### **Endpoint 4: GET /trends**
**Lines**: 385-440  
**Status**: SECURE ✓  
**Department Filtering**: YES - Properly enforced

**Analysis**:
- Lines 400-407: Correctly enforces USER role department isolation
- Lines 421-422: Query properly filters by department_id
- No cross-department data leakage detected

**Recommendation**: Fix import errors only.

---

#### **Endpoint 5: GET /payment-calendar**
**Lines**: 443-547  
**Status**: SECURE ✓  
**Department Filtering**: YES - Properly enforced

**Analysis**:
- Lines 467-479: Correctly enforces USER role department isolation
- Lines 483-489: PaymentForecastService called with proper dept_id parameter
- Lines 492-496: BudgetVersion query properly filters by department_id
- Lines 504-511: BudgetPlanDetail query properly filtered via baseline

**Recommendation**: Fix import errors only.

---

#### **Endpoint 6: GET /payment-calendar/{date}**
**Lines**: 550-642  
**Status**: SECURE ✓  
**Department Filtering**: YES - Properly enforced

**Analysis**:
- Lines 572-579: Correctly enforces USER role department isolation
- Lines 584-590: PaymentForecastService called with proper department_id
- No aggregation bypass possible

**Recommendation**: Fix import errors only.

---

#### **Endpoint 7: GET /payment-forecast**
**Lines**: 645-722  
**Status**: SECURE ✓  
**Department Filtering**: YES - Properly enforced

**Analysis**:
- Lines 674-681: Correctly enforces USER role department isolation
- Lines 687-695: PaymentForecastService called with proper department_id
- Service-level validation prevents cross-department data leakage

**Recommendation**: Fix import errors only.

---

#### **Endpoint 8: GET /payment-forecast/summary**
**Lines**: 725-785  
**Status**: SECURE ✓  
**Department Filtering**: YES - Properly enforced

**Analysis**:
- Lines 748-755: Correctly enforces USER role department isolation
- Lines 761-767: PaymentForecastService called with proper department_id

**Recommendation**: Fix import errors only.

---

#### **Endpoint 9: GET /plan-vs-actual**
**Lines**: 788-968  
**Status**: VULNERABLE - HIGH RISK ⚠️  
**Department Filtering**: INCOMPLETE - MULTIPLE ISSUES

**Critical Issues**:

1. **Issue #1 - Inconsistent role checking (Line 806)**:
```python
if current_user.role.value == "USER":  # Uses .value instead of enum comparison
    baseline_query = baseline_query.filter(
        BudgetVersion.department_id == current_user.department_id
    )
elif department_id:  # PROBLEM: This allows MANAGER/ADMIN to pass None!
    baseline_query = baseline_query.filter(
        BudgetVersion.department_id == department_id
    )
```

**Problem**: If `department_id` parameter is None, MANAGER/ADMIN users can see ALL departments' baseline data. Should have explicit check.

2. **Issue #2 - Aggregation without baseline department filtering (Line 829-851)**:
```python
# Get all actuals for the year
actual_query = db.query(
    Expense.category_id,
    extract('month', Expense.request_date).label('month'),
    func.sum(Expense.amount).label('total')
).filter(
    extract('year', Expense.request_date) == year,
    Expense.status.in_([ExpenseStatusEnum.PAID, ExpenseStatusEnum.PENDING])
)

# Filter by department IF needed
if current_user.role.value == "USER":
    actual_query = actual_query.filter(
        Expense.department_id == current_user.department_id
    )
elif department_id:
    actual_query = actual_query.filter(
        Expense.department_id == department_id
    )
```

**Problem**: Same issue - if both USER and department_id checks fail, aggregation includes expenses from ALL departments. The baseline query and actual query filtering logic is misaligned.

3. **Issue #3 - Potential information leakage via baseline version lookup**:
If no baseline exists for the requested department, the endpoint throws 404, but the baseline_query might have returned data from a different department if filtering wasn't applied.

**Recommendation**:
```python
# More secure approach:
if current_user.role == UserRoleEnum.USER:
    effective_dept_id = current_user.department_id
    if not effective_dept_id:
        raise HTTPException(status_code=403, detail="User has no department")
elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
    effective_dept_id = department_id
    if not effective_dept_id:
        raise HTTPException(status_code=400, detail="Department ID required for MANAGER/ADMIN")
else:
    raise HTTPException(status_code=403, detail="Invalid role")

# Then use effective_dept_id consistently throughout
baseline_query = baseline_query.filter(BudgetVersion.department_id == effective_dept_id)
actual_query = actual_query.filter(Expense.department_id == effective_dept_id)
```

---

#### **Endpoint 10: GET /budget-status**
**Lines**: 971-994  
**Status**: VULNERABLE - MODERATE RISK ⚠️  
**Department Filtering**: INCOMPLETE

**Issue** (Lines 984-989):
```python
if current_user.role.value == "USER":
    dept_id = current_user.department_id
elif department_id:
    dept_id = department_id
else:
    dept_id = current_user.department_id  # Fallback - but for MANAGER/ADMIN this could be None!
```

**Problem**: If MANAGER/ADMIN user doesn't pass `department_id` parameter, defaults to `current_user.department_id` which might be None. The BudgetValidator will then query without department filtering.

**Recommendation**: Require `department_id` parameter for MANAGER/ADMIN, similar to other endpoints.

---

#### **Endpoint 11: POST /validate-expense**
**Lines**: 997-1029  
**Status**: SECURE ✓  
**Department Filtering**: YES - Uses current_user.department_id

**Analysis**:
- Line 1020: Correctly passes `current_user.department_id` to validator
- BudgetValidator properly enforces department isolation

---

### FILE 2: analytics_advanced.py

#### **VULNERABILITY #3: Incomplete Department Filtering in Helper Function**
**Severity**: MODERATE - Security Design Flaw  
**Status**: VULNERABLE  
**Location**: Lines 31-43 (check_department_access function)

**Code**:
```python
def check_department_access(user: User, department_id: Optional[int]) -> bool:
    """Check if user has access to specified department"""
    if user.role == UserRoleEnum.ADMIN:
        return True  # ADMIN can access anything
    if user.role == UserRoleEnum.MANAGER:
        if not user.department_id:
            return False
        return department_id is None or department_id == user.department_id
    if user.role == UserRoleEnum.USER:
        if not user.department_id:
            return False
        return department_id is None or department_id == user.department_id
    return False
```

**Problem**: This function returns a boolean but doesn't ENFORCE filtering. Callers must still implement the filtering logic themselves. If a caller forgets, endpoint will leak data.

**Example** (Lines 64-74, GET /expense-trends):
```python
if current_user.role == UserRoleEnum.USER:
    if not current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no department")
    department_id = current_user.department_id  # ✓ Correctly enforced
elif current_user.role == UserRoleEnum.MANAGER:
    if not current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager has no department")
    if department_id and department_id != current_user.department_id:  # ✓ Correctly validated
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    department_id = current_user.department_id  # ✓ Enforced
```

**Recommendation**: The function should actually raise HTTPException instead of returning bool, to prevent callers from forgetting enforcement.

---

#### ENDPOINT ANALYSIS: analytics_advanced.py

#### **Endpoint 1: GET /expense-trends**
**Lines**: 46-185  
**Status**: SECURE ✓  
**Department Filtering**: YES - Properly enforced (lines 64-73)

**Analysis**:
- Correctly forces USER to their department
- Correctly validates MANAGER doesn't access other departments
- Query properly filters by department_id at line 95

---

#### **Endpoint 2: GET /contractor-analysis**
**Lines**: 188-314  
**Status**: SECURE ✓  
**Department Filtering**: YES - Properly enforced (lines 205-214)

**Analysis**:
- Lines 205-214: Correctly enforces department isolation
- Lines 240-241: Query properly filters by department_id
- No data aggregation bypass detected

---

#### **Endpoint 3: GET /department-comparison**
**Lines**: 317-477  
**Status**: VULNERABLE - MODERATE RISK ⚠️  
**Department Filtering**: INCOMPLETE

**Issue** (Lines 335-345):
```python
dept_query = db.query(Department)

if current_user.role == UserRoleEnum.USER:
    if not current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no department")
    dept_query = dept_query.filter(Department.id == current_user.department_id)
elif current_user.role == UserRoleEnum.MANAGER:
    if not current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager has no department")
    dept_query = dept_query.filter(Department.id == current_user.department_id)
```

**Problem**: 
- ADMIN role is NOT handled - no filtering, so ADMIN sees all departments (intentional but undocumented)
- The endpoint description says "Only ADMIN can see all departments, MANAGER/USER see only own department" but the code actually allows ADMIN unrestricted access without explicit comment

**Nested Query Issue** (Lines 354-370):
Each department comparison includes a complex nested budget query. When iterating departments (line 514), the budget_query joins BudgetPlanDetail:
```python
budget_query = db.query(
    func.sum(BudgetPlanDetail.amount).label('total_budget')
).join(
    BudgetVersion, BudgetPlanDetail.version_id == BudgetVersion.id
).filter(
    and_(
        BudgetVersion.department_id == dept.id,  # ✓ Correctly filtered
        BudgetVersion.year == year,
        BudgetVersion.is_baseline == True
    )
)
```

**Recommendation**: This endpoint is actually SECURE because nested queries properly filter. The concern is only documentation/clarity.

---

#### **Endpoint 4: GET /seasonal-patterns**
**Lines**: 480-621  
**Status**: SECURE ✓  
**Department Filtering**: YES - Properly enforced (lines 497-506)

**Analysis**:
- Lines 497-506: Correctly enforces department isolation similar to /expense-trends
- Query properly filters at line 522

---

#### **Endpoint 5: GET /cost-efficiency**
**Lines**: 624-803  
**Status**: VULNERABLE - MODERATE RISK ⚠️  
**Department Filtering**: INCOMPLETE/INCONSISTENT

**Issue** (Lines 640-650):
```python
if current_user.role == UserRoleEnum.USER:
    if not current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no department")
    department_id = current_user.department_id
elif current_user.role == UserRoleEnum.MANAGER:
    if not current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager has no department")
    if department_id and department_id != current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    department_id = current_user.department_id  # ✓ Enforced
```

**Problem**: ADMIN role is NOT explicitly handled. If ADMIN calls this endpoint without passing `department_id`, the parameter stays None, but then the query at line 658 filters with:
```python
if department_id:
    categories_query = categories_query.filter(BudgetCategory.department_id == department_id)
```

This means if ADMIN passes `department_id=None`, categories_query returns categories from ALL departments, leading to mixed reporting metrics.

**Critical Nested Query Issue** (Lines 672-687):
```python
budget_query = db.query(
    func.sum(BudgetPlanDetail.amount).label('budget')
).join(
    BudgetVersion, BudgetPlanDetail.version_id == BudgetVersion.id
).filter(
    and_(
        BudgetVersion.year == year,
        BudgetVersion.is_baseline == True,
        BudgetPlanDetail.category_id == cat.category_id
    )
)

if department_id:
    budget_query = budget_query.filter(BudgetVersion.department_id == department_id)
```

**Problem**: If `department_id=None` (ADMIN case), the budget query doesn't filter by department, returning budgets from ALL departments for the given category.

Then at line 705:
```python
actual_query = actual_query.filter(Expense.department_id == department_id)
```

If `department_id=None`, actual expenses are NOT filtered, causing:
- Budget data from all departments
- Actual expenses from all departments
- Metrics become meaningless / cross-pollinated

**Recommendation**: Explicitly handle ADMIN role and require `department_id` parameter.

---

### FILE 3: forecast.py

#### ENDPOINT ANALYSIS: forecast.py

#### **Endpoint 1: POST /generate**
**Lines**: 129-315  
**Status**: SECURE ✓  
**Department Filtering**: YES - Enforced at line 144

**Analysis**:
- Line 144: check_department_access called to enforce access
- Lines 170, 186, 214: ForecastExpense created with proper department_id
- Query at line 150-153 properly filters by department_id

---

#### **Endpoint 2: GET /**
**Lines**: 318-363  
**Status**: SECURE ✓  
**Department Filtering**: YES - Enforced at line 333

**Analysis**:
- Line 333: check_department_access ensures proper access
- Lines 335-338: Query properly filters by department_id

---

#### **Endpoint 3: POST /**
**Lines**: 366-403  
**Status**: SECURE ✓  
**Department Filtering**: YES - Enforced at line 379

---

#### **Endpoint 4: PUT /{forecast_id}**
**Lines**: 406-453  
**Status**: SECURE ✓  
**Department Filtering**: YES - Enforced at line 427

---

#### **Endpoint 5: DELETE /{forecast_id}**
**Lines**: 456-480  
**Status**: SECURE ✓  
**Department Filtering**: YES - Enforced at line 476

---

#### **Endpoint 6: DELETE /clear/{year}/{month}**
**Lines**: 483-506  
**Status**: SECURE ✓  
**Department Filtering**: YES - Enforced at line 498

---

#### **Endpoint 7: GET /export/{year}/{month}**
**Lines**: 509-604  
**Status**: VULNERABLE - MODERATE RISK ⚠️  
**Department Filtering**: INCOMPLETE

**Issue** (Lines 525-544):
```python
if current_user.role == UserRoleEnum.USER:
    if not current_user.department_id:
        raise HTTPException(...)
    dept_id = current_user.department_id
elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
    if department_id is not None:
        dept_id = department_id
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required for export"
        )
else:
    dept_id = None
```

**Problem**: 
- MANAGER/ADMIN users are required to pass `department_id` parameter (which is good)
- But the validation doesn't check if MANAGER is accessing their own department or different one
- An ADMIN with `department_id=2` can export forecasts, but a MANAGER with their department=1 might also try to access `department_id=2`

**Recommendation**: Add MANAGER validation:
```python
elif current_user.role == UserRoleEnum.MANAGER:
    if not current_user.department_id:
        raise HTTPException(status_code=403, detail="Manager has no department")
    if department_id and department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="Cannot export other departments' forecasts")
    dept_id = current_user.department_id
```

---

### FILE 4: comprehensive_report.py

#### **Missing Dependency Injection Router Decorator**
**Severity**: LOW - Design Issue  
**Status**: POTENTIAL ISSUE  
**Location**: Line 28

```python
router = APIRouter()  # Missing: dependencies=[Depends(get_current_active_user)]
```

**Issue**: Unlike other routers, this doesn't set router-level auth dependency. Each endpoint must manually depend on `get_current_active_user`. This is less likely to cause issues but violates consistency pattern.

---

#### ENDPOINT ANALYSIS: comprehensive_report.py

#### **Endpoint 1: GET /**
**Lines**: 46-640  
**Status**: SECURE - WITH MINOR CONCERNS ✓  
**Department Filtering**: YES - Properly enforced in _check_department_access

**Analysis**:
- Line 76: `_check_department_access` properly restricts USER to own department
- Lines 88-112: All budget queries properly filter by effective_department_id
- Lines 103-116: All expense queries properly filter by effective_department_id
- Lines 118-130: OPEX query filters by department
- Lines 149-180: Payroll queries filter by department
- Lines 205-233: KPI queries filter by department
- Lines 330-365: Top performers query filters by Employee.department_id
- Lines 370-399: Top categories query filters by Expense.department_id
- Lines 405-500: Monthly breakdown queries filter by department
- Lines 507-611: Department comparison (when requested) properly filters departments for MANAGER/ADMIN

**Recommendation**: Secure. No changes needed.

---

## SUMMARY TABLE

| # | File | Endpoint | Status | Risk | Issue |
|---|------|----------|--------|------|-------|
| 1 | analytics.py | GET /dashboard | VULNERABLE | CRITICAL | Missing UserRoleEnum & status imports |
| 2 | analytics.py | GET /budget-execution | VULNERABLE | CRITICAL | Missing imports |
| 3 | analytics.py | GET /by-category | VULNERABLE | CRITICAL | Missing imports |
| 4 | analytics.py | GET /trends | VULNERABLE | CRITICAL | Missing imports |
| 5 | analytics.py | GET /payment-calendar | VULNERABLE | CRITICAL | Missing imports |
| 6 | analytics.py | GET /payment-calendar/{date} | VULNERABLE | CRITICAL | Missing imports |
| 7 | analytics.py | GET /payment-forecast | VULNERABLE | CRITICAL | Missing imports |
| 8 | analytics.py | GET /payment-forecast/summary | VULNERABLE | CRITICAL | Missing imports |
| 9 | analytics.py | GET /plan-vs-actual | VULNERABLE | HIGH | Inconsistent role checking, potential data aggregation bypass |
| 10 | analytics.py | GET /budget-status | VULNERABLE | MODERATE | Incomplete department filtering for MANAGER/ADMIN |
| 11 | analytics.py | POST /validate-expense | SECURE | - | - |
| 12 | analytics_advanced.py | GET /expense-trends | SECURE | - | - |
| 13 | analytics_advanced.py | GET /contractor-analysis | SECURE | - | - |
| 14 | analytics_advanced.py | GET /department-comparison | SECURE | - | Documentation clarity issue |
| 15 | analytics_advanced.py | GET /seasonal-patterns | SECURE | - | - |
| 16 | analytics_advanced.py | GET /cost-efficiency | VULNERABLE | MODERATE | ADMIN role not handled, nested queries lack department filtering |
| 17 | forecast.py | POST /generate | SECURE | - | - |
| 18 | forecast.py | GET / | SECURE | - | - |
| 19 | forecast.py | POST / | SECURE | - | - |
| 20 | forecast.py | PUT /{forecast_id} | SECURE | - | - |
| 21 | forecast.py | DELETE /{forecast_id} | SECURE | - | - |
| 22 | forecast.py | DELETE /clear/{year}/{month} | SECURE | - | - |
| 23 | forecast.py | GET /export/{year}/{month} | VULNERABLE | MODERATE | Missing MANAGER department validation |
| 24 | comprehensive_report.py | GET / | SECURE | - | - |

---

## VULNERABILITY SUMMARY

### Critical Vulnerabilities (3)
1. **analytics.py**: Missing UserRoleEnum import - causes NameError in all role-checked endpoints
2. **analytics.py**: Missing status import - causes NameError in all error responses
3. **analytics_advanced.py / forecast.py**: Inconsistent import patterns (auth, status) - should match

### High Risk (1)
1. **analytics.py - GET /plan-vs-actual**: Inconsistent role checking allows MANAGER/ADMIN to see data from all departments when department_id parameter is not provided

### Moderate Risk (4)
1. **analytics.py - GET /budget-status**: MANAGER/ADMIN defaults to current_user.department_id which may be None
2. **analytics_advanced.py - GET /cost-efficiency**: ADMIN role not explicitly handled; nested budget queries don't filter when department_id=None
3. **forecast.py - GET /export/{year}/{month}**: MANAGER role can potentially export other departments' forecasts
4. **analytics_advanced.py - check_department_access**: Helper function returns bool instead of raising exception, prone to caller error

---

## RECOMMENDATIONS (PRIORITY ORDER)

### IMMEDIATE (Fix Critical Issues)

**Fix 1: Update analytics.py imports (Line 1-8)**
```python
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status  # Add 'status'
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from app.db import get_db
from app.db.models import Expense, BudgetCategory, BudgetPlan, BudgetVersion, BudgetPlanDetail, ExpenseStatusEnum, ExpenseTypeEnum, User, PayrollPlan, UserRoleEnum  # Add 'UserRoleEnum'
```

### HIGH PRIORITY

**Fix 2: analytics.py - GET /plan-vs-actual (Lines 788-968)**
Replace inconsistent role checking with:
```python
@router.get("/plan-vs-actual", response_model=PlanVsActualSummary)
def get_plan_vs_actual(
    year: int = Query(..., description="Target year for comparison"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Determine effective department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(status_code=403, detail="User has no department")
        effective_dept_id = current_user.department_id
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if current_user.role == UserRoleEnum.MANAGER:
            if not current_user.department_id:
                raise HTTPException(status_code=403, detail="Manager has no department")
            if department_id and department_id != current_user.department_id:
                raise HTTPException(status_code=403, detail="Cannot access other departments")
        effective_dept_id = department_id if department_id else current_user.department_id
    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    # Find baseline version - NOW WITH PROPER FILTERING
    baseline_query = db.query(BudgetVersion).filter(
        BudgetVersion.year == year,
        BudgetVersion.is_baseline == True
    )
    
    if effective_dept_id:
        baseline_query = baseline_query.filter(BudgetVersion.department_id == effective_dept_id)
    
    baseline_version = baseline_query.first()
    # ... rest of code
```

### MEDIUM PRIORITY

**Fix 3: analytics_advanced.py - GET /cost-efficiency**
Add ADMIN handling and require department_id for aggregations.

**Fix 4: forecast.py - GET /export/{year}/{month}**
Add validation for MANAGER to prevent accessing other departments.

**Fix 5: analytics_advanced.py - check_department_access**
Refactor to raise HTTPException instead of returning bool.

---

## COMPLIANCE CHECKLIST

| Item | Status | Evidence |
|------|--------|----------|
| JWT Authentication on all endpoints | ✓ PASS | All endpoints use `Depends(get_current_active_user)` |
| Multi-tenancy via department_id | ✓ MOSTLY PASS | 21/24 endpoints properly filter |
| USER role isolation | ✓ MOSTLY PASS | 23/24 endpoints force USER to own department |
| MANAGER department validation | ⚠️ PARTIAL | 4 endpoints lack proper MANAGER validation |
| ADMIN scope limitation | ⚠️ PARTIAL | ADMIN not explicitly documented in some endpoints |
| JOIN queries filtered | ✓ PASS | All JOINs properly filter by department_id |
| Aggregation security | ⚠️ PARTIAL | 2 endpoints have potential aggregation leaks |
| Error handling | ✓ PASS | Proper HTTPException with status codes |

---

## TESTING RECOMMENDATIONS

### Test Case 1: User Role Isolation
```bash
# USER should NOT see other departments' data
curl -H "Authorization: Bearer USER_TOKEN" \
  "http://localhost:8000/api/v1/analytics/dashboard?department_id=2"
# Expected: 403 Forbidden
```

### Test Case 2: Manager Department Validation
```bash
# MANAGER from dept=1 should NOT see dept=2 data
curl -H "Authorization: Bearer MANAGER_TOKEN_DEPT1" \
  "http://localhost:8000/api/v1/analytics/plan-vs-actual?year=2025&department_id=2"
# Expected: 403 Forbidden
```

### Test Case 3: Admin Cross-Department Access
```bash
# ADMIN should see all departments
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/analytics/dashboard"
# Expected: 200 with all departments aggregated
```

### Test Case 4: Null Department Parameter
```bash
# MANAGER without department_id should fail (for /plan-vs-actual)
curl -H "Authorization: Bearer MANAGER_TOKEN" \
  "http://localhost:8000/api/v1/analytics/plan-vs-actual?year=2025"
# Expected: 400 Bad Request
```

---

## CONCLUSION

**Overall Security Assessment**: VULNERABLE WITH CRITICAL ISSUES

The analytics API has foundational multi-tenancy controls but suffers from:
1. **Compilation errors** that will crash at runtime (missing imports)
2. **Inconsistent role handling** that could leak data when parameters are omitted
3. **Incomplete validation** in cost-efficiency and export endpoints

**Action Required**: Fix critical imports immediately and implement recommended role-checking patterns consistently across all endpoints.

