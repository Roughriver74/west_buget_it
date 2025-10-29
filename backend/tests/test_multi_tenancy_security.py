"""
Multi-Tenancy Security Tests

Comprehensive security tests to ensure proper data isolation between departments.
These tests verify that users cannot access, modify, or delete data from other departments.

Test Coverage:
- Expense API
- Budget API
- Attachment API
- Payroll API
- KPI API
- Analytics API
- Contractor/Category API
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
from decimal import Decimal

from app.main import app
from app.db.session import Base, get_db
from app.db.models import (
    User, Department, Expense, BudgetCategory, Contractor, Organization,
    Attachment, BudgetPlan, Employee, PayrollPlan, PayrollActual,
    EmployeeKPI, KPIGoal, UserRoleEnum, ExpenseStatusEnum, ExpenseTypeEnum,
    EmployeeStatusEnum, BonusTypeEnum
)
from app.utils.auth import create_access_token, get_password_hash

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_security.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database and session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_data(db):
    """Create test data: 2 departments, 2 users (one per department), test entities"""
    # Create departments
    dept1 = Department(id=1, name="IT Department", code="IT")
    dept2 = Department(id=2, name="Finance Department", code="FIN")
    db.add_all([dept1, dept2])
    db.flush()

    # Create users
    user1 = User(
        id=1,
        username="user_dept1",
        email="user1@test.com",
        full_name="User Department 1",
        hashed_password=get_password_hash("password"),
        role=UserRoleEnum.USER,
        department_id=1,
        is_active=True
    )
    user2 = User(
        id=2,
        username="user_dept2",
        email="user2@test.com",
        full_name="User Department 2",
        hashed_password=get_password_hash("password"),
        role=UserRoleEnum.USER,
        department_id=2,
        is_active=True
    )
    admin = User(
        id=3,
        username="admin",
        email="admin@test.com",
        full_name="Admin User",
        hashed_password=get_password_hash("password"),
        role=UserRoleEnum.ADMIN,
        department_id=None,
        is_active=True
    )
    db.add_all([user1, user2, admin])
    db.flush()

    # Create shared organization
    org = Organization(id=1, name="Test Organization", legal_name="Test Org LLC")
    db.add(org)
    db.flush()

    # Create categories for each department
    cat1 = BudgetCategory(id=1, name="IT Hardware", type=ExpenseTypeEnum.CAPEX, department_id=1, is_active=True)
    cat2 = BudgetCategory(id=2, name="Finance Software", type=ExpenseTypeEnum.OPEX, department_id=2, is_active=True)
    db.add_all([cat1, cat2])
    db.flush()

    # Create contractors for each department
    contractor1 = Contractor(id=1, name="IT Supplier", department_id=1, is_active=True)
    contractor2 = Contractor(id=2, name="Finance Vendor", department_id=2, is_active=True)
    db.add_all([contractor1, contractor2])
    db.flush()

    # Create expenses for each department
    expense1 = Expense(
        id=1,
        number="EXP-001",
        department_id=1,
        category_id=1,
        contractor_id=1,
        organization_id=1,
        amount=Decimal("1000.00"),
        request_date=datetime.now(),
        status=ExpenseStatusEnum.PENDING
    )
    expense2 = Expense(
        id=2,
        number="EXP-002",
        department_id=2,
        category_id=2,
        contractor_id=2,
        organization_id=1,
        amount=Decimal("2000.00"),
        request_date=datetime.now(),
        status=ExpenseStatusEnum.PENDING
    )
    db.add_all([expense1, expense2])
    db.flush()

    # Create budget plans
    budget1 = BudgetPlan(
        id=1,
        year=2025,
        month=1,
        department_id=1,
        category_id=1,
        planned_amount=Decimal("10000.00"),
        capex_planned=Decimal("10000.00"),
        opex_planned=Decimal("0.00")
    )
    budget2 = BudgetPlan(
        id=2,
        year=2025,
        month=1,
        department_id=2,
        category_id=2,
        planned_amount=Decimal("20000.00"),
        capex_planned=Decimal("0.00"),
        opex_planned=Decimal("20000.00")
    )
    db.add_all([budget1, budget2])
    db.flush()

    # Create employees
    emp1 = Employee(
        id=1,
        full_name="John Doe",
        position="Developer",
        base_salary=Decimal("100000.00"),
        monthly_bonus_base=Decimal("10000.00"),
        department_id=1,
        status=EmployeeStatusEnum.ACTIVE
    )
    emp2 = Employee(
        id=2,
        full_name="Jane Smith",
        position="Accountant",
        base_salary=Decimal("80000.00"),
        monthly_bonus_base=Decimal("8000.00"),
        department_id=2,
        status=EmployeeStatusEnum.ACTIVE
    )
    db.add_all([emp1, emp2])
    db.flush()

    # Create payroll plans
    payroll1 = PayrollPlan(
        id=1,
        year=2025,
        month=1,
        employee_id=1,
        department_id=1,
        base_salary=Decimal("100000.00"),
        monthly_bonus=Decimal("10000.00"),
        quarterly_bonus=Decimal("0.00"),
        annual_bonus=Decimal("0.00"),
        other_payments=Decimal("0.00"),
        total_planned=Decimal("110000.00")
    )
    payroll2 = PayrollPlan(
        id=2,
        year=2025,
        month=1,
        employee_id=2,
        department_id=2,
        base_salary=Decimal("80000.00"),
        monthly_bonus=Decimal("8000.00"),
        quarterly_bonus=Decimal("0.00"),
        annual_bonus=Decimal("0.00"),
        other_payments=Decimal("0.00"),
        total_planned=Decimal("88000.00")
    )
    db.add_all([payroll1, payroll2])
    db.flush()

    # Create KPI goals
    goal1 = KPIGoal(
        id=1,
        name="IT Performance Goal",
        description="Test goal for IT",
        category="Performance",
        metric_name="Tasks Completed",
        metric_unit="tasks",
        target_value=Decimal("100.00"),
        weight=Decimal("100.00"),
        year=2025,
        department_id=1
    )
    goal2 = KPIGoal(
        id=2,
        name="Finance Performance Goal",
        description="Test goal for Finance",
        category="Performance",
        metric_name="Reports Filed",
        metric_unit="reports",
        target_value=Decimal("50.00"),
        weight=Decimal("100.00"),
        year=2025,
        department_id=2
    )
    db.add_all([goal1, goal2])
    db.flush()

    db.commit()

    return {
        "dept1": dept1,
        "dept2": dept2,
        "user1": user1,
        "user2": user2,
        "admin": admin,
        "org": org,
        "cat1": cat1,
        "cat2": cat2,
        "contractor1": contractor1,
        "contractor2": contractor2,
        "expense1": expense1,
        "expense2": expense2,
        "budget1": budget1,
        "budget2": budget2,
        "emp1": emp1,
        "emp2": emp2,
        "payroll1": payroll1,
        "payroll2": payroll2,
        "goal1": goal1,
        "goal2": goal2
    }


def get_auth_headers(user_id: int, username: str, department_id: int = None, role: str = "USER"):
    """Generate authentication headers for test requests"""
    token = create_access_token(data={
        "sub": username,
        "user_id": user_id,
        "department_id": department_id,
        "role": role
    })
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# EXPENSE API SECURITY TESTS
# ============================================================================

def test_user_cannot_view_other_department_expenses(client, test_data):
    """USER from dept1 should NOT see expenses from dept2"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    # Try to get expense from dept2
    response = client.get("/api/v1/expenses/2", headers=headers)

    assert response.status_code == 403
    assert "only view expenses from your own department" in response.json()["detail"]


def test_user_cannot_create_expense_in_other_department(client, test_data):
    """USER from dept1 should NOT create expenses in dept2"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    expense_data = {
        "number": "EXP-003",
        "department_id": 2,  # Trying to create in dept2
        "category_id": 2,
        "contractor_id": 2,
        "organization_id": 1,
        "amount": 5000.00,
        "request_date": datetime.now().isoformat(),
        "status": "PENDING"
    }

    response = client.post("/api/v1/expenses/", json=expense_data, headers=headers)

    # Should succeed but force dept1 (not dept2)
    assert response.status_code == 201
    created_expense = response.json()
    assert created_expense["department_id"] == 1  # Forced to user's dept


def test_user_cannot_update_other_department_expense(client, test_data):
    """USER from dept1 should NOT update expense from dept2"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    update_data = {
        "amount": 9999.99,
        "comment": "Hacked!"
    }

    response = client.put("/api/v1/expenses/2", json=update_data, headers=headers)

    assert response.status_code == 403
    assert "only update expenses from your own department" in response.json()["detail"]


def test_user_cannot_delete_other_department_expense(client, test_data):
    """USER from dept1 should NOT delete expense from dept2"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    response = client.delete("/api/v1/expenses/2", headers=headers)

    assert response.status_code == 403
    assert "only delete expenses from your own department" in response.json()["detail"]


# ============================================================================
# ATTACHMENT API SECURITY TESTS
# ============================================================================

def test_user_cannot_view_attachments_from_other_department(client, test_data):
    """USER from dept1 should NOT view attachments from dept2's expense"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    # Try to view attachments of expense from dept2
    response = client.get("/api/v1/attachments/2/attachments", headers=headers)

    assert response.status_code == 403
    assert "only access attachments from your own department" in response.json()["detail"]


def test_user_cannot_upload_attachment_to_other_department_expense(client, test_data):
    """USER from dept1 should NOT upload files to dept2's expense"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    data = {"file_type": "invoice"}

    response = client.post("/api/v1/attachments/2/attachments", files=files, data=data, headers=headers)

    assert response.status_code == 403
    assert "only access attachments from your own department" in response.json()["detail"]


# ============================================================================
# BUDGET API SECURITY TESTS
# ============================================================================

def test_user_cannot_view_other_department_budget(client, test_data):
    """USER from dept1 should NOT see budget from dept2"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    # Try to get budget from dept2
    response = client.get("/api/v1/budget/plans/2", headers=headers)

    assert response.status_code == 403


def test_user_cannot_initialize_other_department_budget(client, test_data):
    """USER from dept1 should NOT initialize budget for dept2"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    # Try to initialize budget for dept2
    response = client.post("/api/v1/budget/plans/year/2026/init?department_id=2", headers=headers)

    # Should succeed but only for dept1 (ignoring department_id parameter)
    assert response.status_code == 200
    result = response.json()
    assert result["department_id"] == 1  # Forced to user's dept


def test_user_cannot_copy_budget_from_other_department(client, test_data):
    """USER from dept1 should NOT copy budget for dept2"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    copy_data = {"coefficient": 1.1}

    # Try to copy budget for dept2
    response = client.post(
        "/api/v1/budget/plans/year/2026/copy-from/2025?department_id=2",
        json=copy_data,
        headers=headers
    )

    # Should succeed but only for dept1 (ignoring department_id parameter)
    assert response.status_code == 200
    result = response.json()
    assert result["department_id"] == 1  # Forced to user's dept


# ============================================================================
# PAYROLL API SECURITY TESTS
# ============================================================================

def test_user_cannot_view_other_department_employees(client, test_data):
    """USER from dept1 should NOT see employees from dept2"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    # Try to get employee from dept2
    response = client.get("/api/v1/employees/2", headers=headers)

    assert response.status_code == 403


def test_user_cannot_view_other_department_payroll(client, test_data):
    """USER from dept1 should NOT see payroll from dept2"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    # Try to get payroll plan from dept2
    response = client.get("/api/v1/payroll/plans/2", headers=headers)

    assert response.status_code == 403


# ============================================================================
# KPI API SECURITY TESTS
# ============================================================================

def test_user_cannot_view_other_department_kpi_goals(client, test_data):
    """USER from dept1 should NOT see KPI goals from dept2"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    # Try to get goal from dept2
    response = client.get("/api/v1/kpi/goals/2", headers=headers)

    assert response.status_code == 403


# ============================================================================
# ANALYTICS API SECURITY TESTS
# ============================================================================

def test_user_analytics_only_shows_own_department(client, test_data):
    """USER analytics should only show data from their own department"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    # Get dashboard analytics
    response = client.get("/api/v1/analytics/dashboard?year=2025", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Verify totals are only from dept1 (expense1 = 1000.00)
    assert float(data["totals"]["total_expenses"]) == 1000.00
    assert float(data["totals"]["total_budget"]) == 110000.00  # Budget + Payroll from dept1


def test_user_cannot_filter_analytics_by_other_department(client, test_data):
    """USER should NOT be able to filter analytics by other department"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    # Try to get analytics for dept2 (should be ignored and show dept1)
    response = client.get("/api/v1/analytics/dashboard?year=2025&department_id=2", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Should still show only dept1 data (parameter ignored for USER)
    assert float(data["totals"]["total_expenses"]) == 1000.00


# ============================================================================
# CONTRACTOR & CATEGORY API SECURITY TESTS
# ============================================================================

def test_user_cannot_view_other_department_contractors(client, test_data):
    """USER from dept1 should NOT see contractors from dept2"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    # Get all contractors (should only see dept1)
    response = client.get("/api/v1/contractors/", headers=headers)

    assert response.status_code == 200
    contractors = response.json()["items"]

    # Should only have contractor1 (dept1)
    assert len(contractors) == 1
    assert contractors[0]["id"] == 1
    assert contractors[0]["name"] == "IT Supplier"


def test_user_cannot_view_other_department_categories(client, test_data):
    """USER from dept1 should NOT see categories from dept2"""
    headers = get_auth_headers(1, "user_dept1", 1, "USER")

    # Get all categories (should only see dept1)
    response = client.get("/api/v1/budget-categories/", headers=headers)

    assert response.status_code == 200
    categories = response.json()["items"]

    # Should only have cat1 (dept1)
    assert len(categories) == 1
    assert categories[0]["id"] == 1
    assert categories[0]["name"] == "IT Hardware"


# ============================================================================
# ADMIN & MANAGER ROLE TESTS
# ============================================================================

def test_admin_can_view_all_departments(client, test_data):
    """ADMIN should be able to view data from all departments"""
    headers = get_auth_headers(3, "admin", None, "ADMIN")

    # Get all expenses
    response = client.get("/api/v1/expenses/", headers=headers)

    assert response.status_code == 200
    expenses = response.json()["items"]

    # Should see both expenses
    assert len(expenses) == 2


def test_admin_can_filter_by_department(client, test_data):
    """ADMIN should be able to filter by specific department"""
    headers = get_auth_headers(3, "admin", None, "ADMIN")

    # Filter by dept2
    response = client.get("/api/v1/expenses/?department_id=2", headers=headers)

    assert response.status_code == 200
    expenses = response.json()["items"]

    # Should only see dept2 expense
    assert len(expenses) == 1
    assert expenses[0]["id"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
