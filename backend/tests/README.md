# IT Budget Manager - Backend Tests

This directory contains automated tests for the IT Budget Manager backend.

## Test Structure

```
tests/
├── __init__.py                      # Tests package
├── conftest.py                      # Pytest fixtures and configuration
├── test_auth.py                     # Authentication and authorization tests (50+ tests)
├── test_kpi_calculations.py         # KPI bonus calculations tests (30+ tests) ✨ NEW
├── test_payroll_calculations.py     # Payroll calculations tests (25+ tests) ✨ NEW
├── test_baseline_bus.py             # Baseline calculation bus tests
├── test_cache_service.py            # Redis caching tests
└── README.md                       # This file
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

### KPI Calculations Tests (`test_kpi_calculations.py`) ✨ NEW
- **Bonus Calculations**: Three bonus types with mathematical formulas
  - `PERFORMANCE_BASED`: bonus = base × (kpi% / 100)
  - `FIXED`: bonus = base (independent of KPI)
  - `MIXED`: fixed_part + performance_part × (kpi% / 100)
- **Goal Achievement**: Calculate achievement percentage
  - 100% achievement (actual = target)
  - Over-achievement (actual > target)
  - Under-achievement (actual < target)
- **Weighted Average KPI**: Multiple goals with different weights
- **Edge Cases**: Zero bonuses, negative KPI, extreme values (>200%)

### Payroll Calculations Tests (`test_payroll_calculations.py`) ✨ NEW
- **Total Compensation**: total_planned = base + monthly + quarterly + annual + other
- **Advance vs Final Payments**: Split payment logic
  - Advance: 50% of base salary (25th of month)
  - Final: 50% of base + 100% bonuses (10th of next month)
- **KPI Integration**: Payroll bonuses calculated from KPI achievements
- **Payment Dates**: Business rules for 10th and 25th
- **Annual Totals**: Yearly compensation calculations
- **Edge Cases**: Zero salary, partial month, pro-rata calculations

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

## Test Coverage Statistics (v0.5.0)

### Current Coverage
- **Overall**: ~75% (target: 70%+) ✅
- **Critical Business Logic**: ~90% (target: 90%+) ✅
  - KPI calculations: 95%+
  - Payroll calculations: 92%+
  - Authentication: 95%+
  - Authorization: 93%+

### Test Count by Category
- Authentication & Security: 50+ tests
- KPI Calculations: 30+ tests
- Payroll Calculations: 25+ tests
- Caching & Performance: 10+ tests
- **Total**: 115+ tests

## Future Test Coverage

Planned test modules:
- `test_expenses.py` - Expense CRUD operations and validation
- `test_budget_planning.py` - Budget planning module (v0.6.0+)
- `test_departments.py` - Department management and isolation
- `test_analytics.py` - Analytics endpoints accuracy
- `test_forecasting.py` - Forecasting algorithms
- `test_api_security.py` - Rate limiting, CORS, headers
- `test_integrations.py` - External system integrations
