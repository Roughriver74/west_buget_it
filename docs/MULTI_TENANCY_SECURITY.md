# Multi-Tenancy Security Architecture

**Date**: 2025-10-30
**Status**: Security Audit Completed (Partial)
**Priority**: 🔴🔴🔴 CRITICAL

## Executive Summary

This document outlines the multi-tenancy security architecture of the IT Budget Manager system. The system uses **department-level isolation** to ensure that data from one department is never visible to users from another department.

**Key Principle**: ONE DEPARTMENT MUST NEVER SEE DATA FROM ANOTHER DEPARTMENT (except Organizations, which are shared).

---

## Security Model

### Role-Based Access Control (RBAC)

The system has three roles with different access levels:

| Role | Access Level | Department Access |
|------|-------------|------------------|
| **USER** | Limited | Only their assigned department |
| **MANAGER** | Extended | All departments (with filtering) |
| **ADMIN** | Full | All departments + system management |

### Department Isolation Rules

1. **USER Role:**
   - Can ONLY see/create/update/delete data from their assigned `department_id`
   - Cannot access data from other departments (returns 404, not 403)
   - Cannot change `department_id` when creating/updating records
   - Cannot use references (category, contractor) from other departments

2. **MANAGER Role:**
   - Can access data from all departments
   - Can optionally filter by specific department
   - Used for cross-department reporting and analytics

3. **ADMIN Role:**
   - Full system access
   - Can manage users, departments, and all data
   - Can perform bulk operations across departments

---

## Database Architecture

### Tables with Direct `department_id`

All core entities have a `department_id` foreign key for multi-tenancy:

✅ **Verified Tables** (14 tables):
- `departments` - Department definitions
- `budget_categories` - Expense categories
- `contractors` - Vendors/suppliers
- `expenses` - Expense requests
- `forecast_expenses` - Forecasted expenses
- `budget_plans` - Budget planning
- `budget_scenarios` - Budget scenarios
- `budget_versions` - Budget version control
- `users` - User accounts (nullable for ADMIN)
- `employees` - Employee records
- `payroll_plans` - Payroll planning
- `payroll_actuals` - Actual payroll payments
- `kpi_goals` - KPI goals
- `employee_kpis` - Employee KPI tracking

### Tables WITHOUT `department_id` (By Design)

✅ **Shared Entity**:
- `organizations` - Shared across all departments (ВЕСТ ООО, ВЕСТ ГРУПП ООО)

### Tables with Indirect `department_id` (Through Foreign Keys)

⚠️ **Require Careful API Filtering**:
- `attachments` → via `expense.department_id`
- `dashboard_configs` → via `user.department_id`
- `salary_history` → via `employee.department_id`
- `budget_plan_details` → via `version.department_id`
- `budget_approval_log` → via `version.department_id`
- `employee_kpi_goals` → via `employee.department_id` and `goal.department_id`

⚠️ **Special Case**:
- `audit_logs` - Has nullable `department_id` (system logs may have NULL department)

---

## API Security Audit Results

### ✅ SECURE - Fully Audited & Fixed

#### 1. Attachments API (`/api/v1/attachments/*`)

**Security Measures Implemented:**
- All endpoints check `expense.department_id` via helper function `check_expense_access()`
- USER role can only access attachments from their department
- Returns 404 instead of 403 to prevent information disclosure
- MANAGER/ADMIN can access all attachments

**Fixed Issues:**
- ✅ Added department filtering to all 6 endpoints:
  - `POST /{expense_id}/attachments` - Upload attachment
  - `GET /{expense_id}/attachments` - List attachments
  - `GET /attachments/{attachment_id}` - Get attachment
  - `GET /attachments/{attachment_id}/download` - Download file
  - `PATCH /attachments/{attachment_id}` - Update metadata
  - `DELETE /attachments/{attachment_id}` - Delete attachment

**Code Reference**: [backend/app/api/v1/attachments.py](../backend/app/api/v1/attachments.py)

---

#### 2. Audit Logs API (`/api/v1/audit/*`)

**Security Measures Implemented:**
- USER can view audit logs from their department
- MANAGER/ADMIN can view all audit logs
- Handles nullable `department_id` for system logs

**Fixed Issues:**
- ✅ Removed contradictory permission check that blocked USER from viewing logs
- ✅ Changed 403 to 404 in `get_audit_log` to prevent information disclosure
- ✅ Updated documentation to clarify USER access to audit logs

**Endpoints (3 total):**
- `GET /audit/` - List audit logs with filters
- `GET /audit/{audit_log_id}` - Get specific audit log
- `GET /audit/entity/{entity_type}/{entity_id}` - Get entity history

**Code Reference**: [backend/app/api/v1/audit.py](../backend/app/api/v1/audit.py)

---

#### 3. Expenses API (`/api/v1/expenses/*`)

**Security Measures Implemented:**
- Comprehensive department filtering on all endpoints
- USER can only access expenses from their department
- Validates that `category` and `contractor` belong to same department
- Returns 404 instead of 403 to prevent information disclosure

**Fixed Issues:**
- ✅ Added validation in `create_expense` to check category department
- ✅ Added validation in `create_expense` to check contractor department
- ✅ Added validation in `update_expense` for new category/contractor
- ✅ Prevents USER from using references from other departments

**Endpoints (10 total):**
- `GET /expenses/export` - Export to Excel
- `GET /expenses/` - List expenses with pagination
- `GET /expenses/{expense_id}` - Get specific expense
- `POST /expenses/` - Create expense
- `PUT /expenses/{expense_id}` - Update expense
- `PATCH /expenses/{expense_id}/status` - Update status
- `PATCH /expenses/{expense_id}/mark-reviewed` - Mark as reviewed
- `DELETE /expenses/{expense_id}` - Delete expense
- `POST /expenses/bulk-delete` - Bulk delete (ADMIN only)
- `GET /expenses/stats/totals` - Get totals
- `POST /expenses/import/ftp` - Import from FTP (ADMIN only)

**Code Reference**: [backend/app/api/v1/expenses.py](../backend/app/api/v1/expenses.py)

---

### ⚠️ PENDING AUDIT - To Be Reviewed

The following API modules still require security audit:

1. **Budget API** (`/api/v1/budget/*`)
   - Budget plans
   - Budget versions
   - Budget plan details
   - Budget approval workflow

2. **Budget Categories API** (`/api/v1/budget-categories/*`)
   - Category CRUD operations
   - Bulk operations

3. **Contractors API** (`/api/v1/contractors/*`)
   - Contractor CRUD operations
   - Bulk operations

4. **Departments API** (`/api/v1/departments/*`)
   - Department management (ADMIN only)

5. **Payroll API** (`/api/v1/payroll/*`)
   - Payroll plans
   - Payroll actuals
   - Analytics

6. **KPI API** (`/api/v1/kpi/*`)
   - KPI goals
   - Employee KPIs
   - Goal achievements
   - Analytics

7. **Analytics API** (`/api/v1/analytics/*`)
   - Dashboard data
   - Budget execution
   - Plan vs actual
   - Payment calendar
   - Forecasting

8. **Organizations API** (`/api/v1/organizations/*`)
   - Should be accessible to all (shared entity)

9. **Users API** (`/api/v1/users/*`)
   - User management (ADMIN only)
   - Profile management

---

## Security Testing Requirements

### Critical Security Tests Needed

Create `backend/tests/test_multi_tenancy_security.py` with the following test scenarios:

#### 1. Cross-Department Access Tests

```python
def test_user_cannot_access_expense_from_other_department():
    """USER from Department A cannot GET expense from Department B"""
    # Returns 404, not 403

def test_user_cannot_update_expense_from_other_department():
    """USER from Department A cannot UPDATE expense from Department B"""

def test_user_cannot_delete_expense_from_other_department():
    """USER from Department A cannot DELETE expense from Department B"""

def test_user_cannot_create_expense_with_foreign_department_id():
    """USER cannot create expense with department_id != their own"""
```

#### 2. Reference Validation Tests

```python
def test_user_cannot_create_expense_with_category_from_other_department():
    """USER cannot use category from another department"""
    # Returns 404, not 403

def test_user_cannot_create_expense_with_contractor_from_other_department():
    """USER cannot use contractor from another department"""
    # Returns 404, not 403

def test_user_cannot_update_expense_with_category_from_other_department():
    """USER cannot change category to one from another department"""

def test_user_cannot_update_expense_with_contractor_from_other_department():
    """USER cannot change contractor to one from another department"""
```

#### 3. Attachment Security Tests

```python
def test_user_cannot_upload_attachment_to_expense_from_other_department():
    """USER cannot upload file to expense from another department"""

def test_user_cannot_download_attachment_from_other_department():
    """USER cannot download attachment belonging to another department"""

def test_user_cannot_delete_attachment_from_other_department():
    """USER cannot delete attachment from another department"""
```

#### 4. Audit Log Security Tests

```python
def test_user_can_view_own_department_audit_logs():
    """USER can view audit logs from their department"""

def test_user_cannot_view_audit_log_from_other_department():
    """USER cannot view audit log from another department"""
    # Returns 404, not 403
```

#### 5. Manager/Admin Access Tests

```python
def test_manager_can_access_all_departments():
    """MANAGER can access data from any department"""

def test_manager_can_filter_by_department():
    """MANAGER can optionally filter by specific department"""

def test_admin_can_access_all_departments():
    """ADMIN has full access to all departments"""

def test_admin_can_bulk_delete_across_departments():
    """ADMIN can perform bulk operations across departments"""
```

**Target**: Minimum 100+ security tests covering all critical scenarios

---

## Frontend Security Requirements

### React Query Cache Isolation

⚠️ **CRITICAL**: Ensure `department_id` is included in React Query cache keys:

```typescript
// ❌ WRONG - Department data may leak between cache entries
const { data } = useQuery({
  queryKey: ['expenses'],
  queryFn: () => api.getExpenses()
})

// ✅ CORRECT - Cache is isolated by department
const { data } = useQuery({
  queryKey: ['expenses', selectedDepartment?.id],
  queryFn: () => api.getExpenses({
    department_id: selectedDepartment?.id
  })
})
```

### Department Context Usage

All pages MUST use `useDepartment()` hook:

```typescript
import { useDepartment } from '@/contexts/DepartmentContext'

const MyPage = () => {
  const { selectedDepartment } = useDepartment()

  // All API calls must include department_id
  const { data } = useQuery({
    queryKey: ['items', selectedDepartment?.id],
    queryFn: () => api.getItems({
      department_id: selectedDepartment?.id
    })
  })
}
```

### Pages Requiring Audit

⚠️ The following frontend pages need to be audited for correct `department_id` usage:

1. `DashboardPage.tsx`
2. `ExpensesPage.tsx`
3. `BudgetPlanPage.tsx`
4. `BudgetPlanDetailsPage.tsx`
5. `PayrollPlanPage.tsx`
6. `PayrollActualsPage.tsx`
7. `KpiManagementPage.tsx`
8. `EmployeesPage.tsx`
9. `ForecastPage.tsx`
10. `AnalyticsPage.tsx`
11. All other data-displaying pages

---

## Common Security Patterns

### Backend Pattern: Department Filtering

```python
from app.db.models import UserRoleEnum

@router.get("/items")
def get_items(
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Item)

    # Department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER sees only their department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Item.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER/ADMIN can filter by department
        if department_id is not None:
            query = query.filter(Item.department_id == department_id)

    return query.all()
```

### Backend Pattern: Access Check for Single Item

```python
@router.get("/items/{item_id}")
def get_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    # SECURITY: Check department access for USER role
    # Return 404 instead of 403 to prevent information disclosure
    if current_user.role == UserRoleEnum.USER:
        if item.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {item_id} not found"
            )

    return item
```

### Backend Pattern: Auto-assign Department on Create

```python
@router.post("/items")
def create_item(
    item: ItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    item_data = item.model_dump()

    # Auto-assign department based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER always creates in their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        item_data['department_id'] = current_user.department_id
    else:
        # MANAGER/ADMIN can specify department or use their own
        if 'department_id' not in item_data:
            item_data['department_id'] = current_user.department_id

    db_item = Item(**item_data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

---

## Error Response Strategy

**IMPORTANT**: Always return `404 Not Found` instead of `403 Forbidden` when USER tries to access data from another department.

**Why?**
- Returning 403 confirms the resource exists but user has no access
- This is an **information disclosure vulnerability**
- Returning 404 prevents attackers from enumerating resources

**Example:**

```python
# ✅ CORRECT - Returns 404
if current_user.role == UserRoleEnum.USER:
    if expense.department_id != current_user.department_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )

# ❌ WRONG - Returns 403 (information leak)
if current_user.role == UserRoleEnum.USER:
    if expense.department_id != current_user.department_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this department"
        )
```

---

## Metrics for Success

✅ **Security Audit Completion Criteria:**

- [ ] 100% of tables have `department_id` or justified exception
- [ ] 100% of API endpoints implement department filtering
- [ ] 100% of USER role endpoints return 404 (not 403) for cross-department access
- [ ] 100+ security tests pass successfully
- [ ] Zero cross-department data leaks in production
- [ ] All frontend pages use `useDepartment()` correctly
- [ ] All React Query cache keys include `department_id`
- [ ] Documentation is complete and up-to-date

**Current Progress:**
- ✅ Database models audited (14/14 core tables verified)
- ✅ Attachments API secured (6/6 endpoints)
- ✅ Audit Logs API secured (3/3 endpoints)
- ✅ Expenses API secured (10/10 endpoints)
- ⚠️ Budget API - pending audit
- ⚠️ Payroll API - pending audit
- ⚠️ KPI API - pending audit
- ⚠️ Analytics API - pending audit
- ⚠️ Security tests - not yet written
- ⚠️ Frontend audit - not yet started

---

## Next Steps

### Immediate Actions (High Priority)

1. **Complete API Audit:**
   - Audit Budget API endpoints (budget plans, versions, details)
   - Audit Payroll API endpoints (plans, actuals, analytics)
   - Audit KPI API endpoints (goals, employee KPIs, achievements)
   - Audit Analytics API endpoints (dashboard, reports, forecasting)

2. **Write Security Tests:**
   - Create `test_multi_tenancy_security.py`
   - Implement 100+ security test scenarios
   - Add to CI/CD pipeline

3. **Frontend Audit:**
   - Audit all pages for `useDepartment()` usage
   - Check React Query cache keys include `department_id`
   - Test department switching behavior

4. **Penetration Testing:**
   - Manual testing with different user roles
   - Attempt to access cross-department data
   - Verify 404 responses (not 403)

### Medium Priority

5. **Performance Optimization:**
   - Add database indexes on `department_id` columns
   - Optimize queries with `joinedload()` for related entities
   - Cache department-specific data appropriately

6. **Monitoring:**
   - Log all cross-department access attempts
   - Alert on suspicious patterns
   - Track department isolation metrics

### Low Priority

7. **Documentation:**
   - Update API documentation with security notes
   - Create security training materials
   - Document incident response procedures

---

## References

- Project Documentation: [DEVELOPMENT_PRINCIPLES.md](./DEVELOPMENT_PRINCIPLES.md)
- Multi-Tenancy Architecture: [MULTI_TENANCY_ARCHITECTURE.md](./MULTI_TENANCY_ARCHITECTURE.md)
- Code Examples: [CLAUDE.md](../CLAUDE.md)
- Database Models: [backend/app/db/models.py](../backend/app/db/models.py)

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-30 | Claude | Initial security audit and documentation |
| 2025-10-30 | Claude | Fixed Attachments API (6 endpoints) |
| 2025-10-30 | Claude | Fixed Audit Logs API (3 endpoints) |
| 2025-10-30 | Claude | Fixed Expenses API (10 endpoints) |

---

**Document Owner**: Development Team
**Last Updated**: 2025-10-30
**Next Review**: Before Production Deployment
