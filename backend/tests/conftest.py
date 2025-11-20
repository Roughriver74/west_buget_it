"""
Pytest configuration and fixtures for IT Budget Manager tests

This module provides common fixtures and configuration for all tests:
- Database setup/teardown
- Test client
- Authentication helpers
- Test data factories
"""

import os
import sys
import types
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Keep external integrations disabled for tests
os.environ["DEBUG"] = "True"
os.environ.setdefault("SCHEDULER_ENABLED", "False")
os.environ.setdefault("USE_REDIS", "False")
os.environ.setdefault("ENABLE_PROMETHEUS", "False")
os.environ.setdefault("C1_ENABLED", "False")

# Lightweight stubs for optional heavy deps to keep unit tests fast
if "pytesseract" not in sys.modules:
    sys.modules["pytesseract"] = types.SimpleNamespace(image_to_string=lambda *args, **kwargs: "")
if "pdf2image" not in sys.modules:
    pdf2image_module = types.ModuleType("pdf2image")
    pdf2image_module.convert_from_path = lambda *args, **kwargs: []
    sys.modules["pdf2image"] = pdf2image_module
if "PIL" not in sys.modules:
    pil_module = types.ModuleType("PIL")
    image_module = types.ModuleType("PIL.Image")
    image_module.open = lambda *args, **kwargs: None
    pil_module.Image = image_module
    sys.modules["PIL"] = pil_module
    sys.modules["PIL.Image"] = image_module

# Provide placeholder KPITask model to satisfy imports (task feature deprecated)
import importlib
models_module = importlib.import_module("app.db.models")
if not hasattr(models_module, "KPITask"):
    class KPITaskPlaceholder:
        ...
    models_module.KPITask = KPITaskPlaceholder
if not hasattr(models_module, "KPITaskStatusEnum"):
    import enum
    class KPITaskStatusEnum(str, enum.Enum):
        TODO = "TODO"
        IN_PROGRESS = "IN_PROGRESS"
        IN_REVIEW = "IN_REVIEW"
        DONE = "DONE"
    models_module.KPITaskStatusEnum = KPITaskStatusEnum
if not hasattr(models_module, "KPITaskPriorityEnum"):
    import enum
    class KPITaskPriorityEnum(str, enum.Enum):
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
    models_module.KPITaskPriorityEnum = KPITaskPriorityEnum

# Stub removed task complexity calculator module to satisfy imports in deprecated endpoints
if "app.services.task_complexity_bonus" not in sys.modules:
    task_complexity_module = types.ModuleType("app.services.task_complexity_bonus")

    class TaskComplexityBonusCalculator:
        def __init__(self, *args, **kwargs):
            ...

        def calculate_complexity_bonus(self, *args, **kwargs):
            return {"complexity_bonus": 0}

    task_complexity_module.TaskComplexityBonusCalculator = TaskComplexityBonusCalculator
    sys.modules["app.services.task_complexity_bonus"] = task_complexity_module

from app.main import app
from app.db.models import Base
from app.db.session import get_db
from app.core.config import settings


# ================================================================
# Database Fixtures
# ================================================================

@pytest.fixture(scope="function")
def db_engine():
    """
    Create an in-memory SQLite database engine for testing

    Uses StaticPool to maintain connection across test lifecycle.
    Database is created fresh for each test function.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    Create a database session for testing

    Each test gets a fresh database with all tables created.
    Session is rolled back and closed after each test.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with test database

    Overrides the get_db dependency to use the test database session.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


# ================================================================
# Test Data Fixtures
# ================================================================

@pytest.fixture
def test_department(db_session: Session):
    """
    Create a test department

    Returns:
        Department object with id, name, and code
    """
    from app.db.models import Department

    department = Department(
        name="Test IT Department",
        code="TEST-IT",
        description="Test department for unit tests",
        is_active=True
    )
    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)
    return department


@pytest.fixture
def test_user_data(test_department):
    """
    Test user data for registration/login

    Returns:
        Dictionary with user credentials and department
    """
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "department_id": test_department.id,
        "role": "USER"
    }


@pytest.fixture
def test_admin_data(test_department):
    """
    Test admin user data

    Returns:
        Dictionary with admin credentials and department
    """
    return {
        "username": "testadmin",
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "full_name": "Test Admin",
        "department_id": test_department.id,
        "role": "ADMIN"
    }


@pytest.fixture
def test_manager_data(test_department):
    """
    Test manager user data

    Returns:
        Dictionary with manager credentials and department
    """
    return {
        "username": "testmanager",
        "email": "manager@example.com",
        "password": "ManagerPassword123!",
        "full_name": "Test Manager",
        "department_id": test_department.id,
        "role": "MANAGER"
    }


# ================================================================
# Authentication Fixtures
# ================================================================

@pytest.fixture
def authenticated_user(client: TestClient, test_user_data: dict):
    """
    Create and authenticate a test user

    Returns:
        Tuple of (user_data, access_token)
    """
    # Register user
    response = client.post(f"{settings.API_PREFIX}/auth/register", json=test_user_data)
    assert response.status_code == 200, f"Registration failed: {response.json()}"

    # Login to get token
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    response = client.post(f"{settings.API_PREFIX}/auth/login", data=login_data)
    assert response.status_code == 200, f"Login failed: {response.json()}"

    token_data = response.json()
    return test_user_data, token_data["access_token"]


@pytest.fixture
def authenticated_admin(client: TestClient, test_admin_data: dict):
    """
    Create and authenticate a test admin user

    Returns:
        Tuple of (admin_data, access_token)
    """
    # Register admin
    response = client.post(f"{settings.API_PREFIX}/auth/register", json=test_admin_data)
    assert response.status_code == 200, f"Admin registration failed: {response.json()}"

    # Login to get token
    login_data = {
        "username": test_admin_data["username"],
        "password": test_admin_data["password"]
    }
    response = client.post(f"{settings.API_PREFIX}/auth/login", data=login_data)
    assert response.status_code == 200, f"Admin login failed: {response.json()}"

    token_data = response.json()
    return test_admin_data, token_data["access_token"]


@pytest.fixture
def authenticated_manager(client: TestClient, test_manager_data: dict):
    """
    Create and authenticate a test manager user

    Returns:
        Tuple of (manager_data, access_token)
    """
    # Register manager
    response = client.post(f"{settings.API_PREFIX}/auth/register", json=test_manager_data)
    assert response.status_code == 200, f"Manager registration failed: {response.json()}"

    # Login to get token
    login_data = {
        "username": test_manager_data["username"],
        "password": test_manager_data["password"]
    }
    response = client.post(f"{settings.API_PREFIX}/auth/login", data=login_data)
    assert response.status_code == 200, f"Manager login failed: {response.json()}"

    token_data = response.json()
    return test_manager_data, token_data["access_token"]


# ================================================================
# Helper Functions
# ================================================================

def get_auth_headers(token: str) -> dict:
    """
    Get authorization headers with Bearer token

    Args:
        token: JWT access token

    Returns:
        Dictionary with Authorization header
    """
    return {"Authorization": f"Bearer {token}"}
