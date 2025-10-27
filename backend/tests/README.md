# IT Budget Manager - Backend Tests

This directory contains automated tests for the IT Budget Manager backend.

## Test Structure

```
tests/
├── __init__.py           # Tests package
├── conftest.py           # Pytest fixtures and configuration
├── test_auth.py          # Authentication and authorization tests
├── test_rbac.py          # Role-based access control tests (future)
├── test_departments.py   # Multi-tenancy tests (future)
└── README.md            # This file
```

## Running Tests

### Run all tests
```bash
cd backend
pytest
```

### Run specific test file
```bash
pytest tests/test_auth.py
```

### Run specific test class
```bash
pytest tests/test_auth.py::TestLogin
```

### Run specific test function
```bash
pytest tests/test_auth.py::TestLogin::test_login_success
```

### Run tests with coverage
```bash
# Install pytest-cov first
pip install pytest-cov

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing
```

### Run tests with markers
```bash
# Run only authentication tests
pytest -m auth

# Run only security tests
pytest -m security

# Run all except slow tests
pytest -m "not slow"
```

## Test Categories

### Authentication Tests (`test_auth.py`)
- **Registration**: User registration, validation, duplicate handling
- **Login**: Authentication, JWT token generation, password verification
- **JWT Token**: Token validation, protected endpoints, token expiry
- **RBAC**: Role-based access control (USER, MANAGER, ADMIN)
- **Row-Level Security**: Department-based data isolation (multi-tenancy)
- **Password Security**: Hashing, secure storage

## Writing New Tests

### 1. Use Fixtures

Fixtures are defined in `conftest.py`:

```python
def test_example(client: TestClient, authenticated_user):
    """Test with authenticated user"""
    user_data, token = authenticated_user

    response = client.get(
        "/api/v1/endpoint",
        headers=get_auth_headers(token)
    )
    assert response.status_code == 200
```

### 2. Follow Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### 3. Use Descriptive Names

```python
# Good
def test_user_cannot_access_other_department_data(self):
    pass

# Bad
def test_user_access(self):
    pass
```

### 4. Add Docstrings

```python
def test_login_success(self, client: TestClient, test_user_data: dict):
    """Test successful login returns JWT token"""
    # Test implementation
```

### 5. Use Markers

```python
@pytest.mark.auth
@pytest.mark.security
def test_password_hashing(self):
    """Test passwords are properly hashed"""
    pass
```

## Available Fixtures

### Database Fixtures
- `db_engine`: In-memory SQLite database engine
- `db_session`: Database session for tests
- `client`: FastAPI test client with test database

### Test Data Fixtures
- `test_department`: Test department object
- `test_user_data`: User registration data (dict)
- `test_admin_data`: Admin registration data (dict)
- `test_manager_data`: Manager registration data (dict)

### Authentication Fixtures
- `authenticated_user`: Registered and authenticated user (returns user_data, token)
- `authenticated_admin`: Registered and authenticated admin (returns admin_data, token)
- `authenticated_manager`: Registered and authenticated manager (returns manager_data, token)

### Helper Functions
- `get_auth_headers(token)`: Returns headers with Bearer token

## Test Database

Tests use an in-memory SQLite database that is:
- Created fresh for each test function
- Isolated from the production PostgreSQL database
- Automatically cleaned up after each test

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    cd backend
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml
```

## Code Coverage Goals

- **Critical paths**: 90%+ coverage (authentication, authorization, data access)
- **Business logic**: 80%+ coverage
- **Overall**: 70%+ coverage

## Best Practices

1. **Isolation**: Each test should be independent
2. **Clarity**: Test one thing at a time
3. **Completeness**: Test both success and failure cases
4. **Speed**: Keep tests fast (use in-memory DB)
5. **Documentation**: Add docstrings and comments
6. **Assertions**: Use descriptive assertions
7. **Cleanup**: Use fixtures for setup/teardown

## Troubleshooting

### Import Errors
Make sure you're in the backend directory:
```bash
cd backend
pytest
```

### Database Errors
Tests use in-memory SQLite, not PostgreSQL. If you see connection errors, check that `conftest.py` properly overrides `get_db`.

### Token Errors
Make sure your `.env` file has a valid `SECRET_KEY` set.

## Future Test Coverage

Planned test modules:
- `test_expenses.py` - Expense CRUD operations
- `test_budget.py` - Budget planning and tracking
- `test_departments.py` - Department management and multi-tenancy
- `test_analytics.py` - Analytics endpoints
- `test_rbac.py` - Comprehensive RBAC tests
- `test_api_security.py` - API security (rate limiting, headers, etc.)
