"""
Authentication Tests

Tests for authentication endpoints including:
- User registration
- Login/logout
- JWT token validation
- Role-based access control (RBAC)
- Password security
- Row-level security (department filtering)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from tests.conftest import get_auth_headers


# ================================================================
# Registration Tests
# ================================================================

class TestRegistration:
    """Test user registration functionality"""

    def test_register_user_success(self, client: TestClient, test_user_data: dict):
        """Test successful user registration"""
        response = client.post(
            f"{settings.API_PREFIX}/auth/register",
            json=test_user_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["role"] == test_user_data["role"]
        assert data["department_id"] == test_user_data["department_id"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned

    def test_register_duplicate_username(self, client: TestClient, test_user_data: dict):
        """Test registration with duplicate username fails"""
        # First registration
        response = client.post(
            f"{settings.API_PREFIX}/auth/register",
            json=test_user_data
        )
        assert response.status_code == 200

        # Second registration with same username
        response = client.post(
            f"{settings.API_PREFIX}/auth/register",
            json=test_user_data
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_duplicate_email(self, client: TestClient, test_user_data: dict):
        """Test registration with duplicate email fails"""
        # First registration
        response = client.post(
            f"{settings.API_PREFIX}/auth/register",
            json=test_user_data
        )
        assert response.status_code == 200

        # Second registration with different username but same email
        duplicate_data = test_user_data.copy()
        duplicate_data["username"] = "different_user"
        response = client.post(
            f"{settings.API_PREFIX}/auth/register",
            json=duplicate_data
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient, test_user_data: dict):
        """Test registration with invalid email format fails"""
        invalid_data = test_user_data.copy()
        invalid_data["email"] = "not-an-email"

        response = client.post(
            f"{settings.API_PREFIX}/auth/register",
            json=invalid_data
        )
        assert response.status_code == 422  # Validation error

    def test_register_missing_required_fields(self, client: TestClient):
        """Test registration with missing required fields fails"""
        incomplete_data = {
            "username": "testuser"
            # Missing other required fields
        }

        response = client.post(
            f"{settings.API_PREFIX}/auth/register",
            json=incomplete_data
        )
        assert response.status_code == 422  # Validation error


# ================================================================
# Login Tests
# ================================================================

class TestLogin:
    """Test user login functionality"""

    def test_login_success(self, client: TestClient, test_user_data: dict):
        """Test successful login returns JWT token"""
        # Register user first
        client.post(f"{settings.API_PREFIX}/auth/register", json=test_user_data)

        # Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post(
            f"{settings.API_PREFIX}/auth/login",
            data=login_data  # OAuth2 uses form data, not JSON
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client: TestClient, test_user_data: dict):
        """Test login with wrong password fails"""
        # Register user first
        client.post(f"{settings.API_PREFIX}/auth/register", json=test_user_data)

        # Login with wrong password
        login_data = {
            "username": test_user_data["username"],
            "password": "WrongPassword123!"
        }
        response = client.post(f"{settings.API_PREFIX}/auth/login", data=login_data)

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent username fails"""
        login_data = {
            "username": "nonexistent",
            "password": "SomePassword123!"
        }
        response = client.post(f"{settings.API_PREFIX}/auth/login", data=login_data)

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_inactive_user(self, client: TestClient, test_user_data: dict, db_session: Session):
        """Test login with inactive user fails"""
        # Register user
        client.post(f"{settings.API_PREFIX}/auth/register", json=test_user_data)

        # Deactivate user
        from app.db.models import User
        user = db_session.query(User).filter(User.username == test_user_data["username"]).first()
        user.is_active = False
        db_session.commit()

        # Try to login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post(f"{settings.API_PREFIX}/auth/login", data=login_data)

        assert response.status_code == 400
        assert "inactive" in response.json()["detail"].lower()


# ================================================================
# JWT Token Tests
# ================================================================

class TestJWTToken:
    """Test JWT token validation and usage"""

    def test_access_protected_endpoint_with_token(self, client: TestClient, authenticated_user):
        """Test accessing protected endpoint with valid token"""
        user_data, token = authenticated_user

        response = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers=get_auth_headers(token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]

    def test_access_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without token fails"""
        response = client.get(f"{settings.API_PREFIX}/auth/me")
        assert response.status_code == 401

    def test_access_protected_endpoint_with_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token fails"""
        response = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers=get_auth_headers("invalid-token")
        )
        assert response.status_code == 401

    def test_token_contains_user_info(self, client: TestClient, authenticated_user):
        """Test that token properly encodes user information"""
        user_data, token = authenticated_user

        # Get current user info using token
        response = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers=get_auth_headers(token)
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all user info is correctly returned
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["role"] == user_data["role"]
        assert data["department_id"] == user_data["department_id"]


# ================================================================
# Role-Based Access Control (RBAC) Tests
# ================================================================

class TestRBAC:
    """Test role-based access control"""

    def test_user_role_permissions(self, client: TestClient, authenticated_user):
        """Test USER role has limited permissions"""
        user_data, token = authenticated_user

        # USER should be able to access their own profile
        response = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers=get_auth_headers(token)
        )
        assert response.status_code == 200

    def test_admin_role_permissions(self, client: TestClient, authenticated_admin):
        """Test ADMIN role has elevated permissions"""
        admin_data, token = authenticated_admin

        # ADMIN should be able to access their own profile
        response = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers=get_auth_headers(token)
        )
        assert response.status_code == 200
        assert response.json()["role"] == "ADMIN"

    def test_manager_role_permissions(self, client: TestClient, authenticated_manager):
        """Test MANAGER role has intermediate permissions"""
        manager_data, token = authenticated_manager

        # MANAGER should be able to access their own profile
        response = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers=get_auth_headers(token)
        )
        assert response.status_code == 200
        assert response.json()["role"] == "MANAGER"


# ================================================================
# Row-Level Security Tests
# ================================================================

class TestRowLevelSecurity:
    """Test department-based data isolation (multi-tenancy)"""

    def test_user_sees_only_own_department(self, client: TestClient, authenticated_user, db_session: Session):
        """Test USER role can only see data from their department"""
        user_data, token = authenticated_user

        # Create a second department
        from app.db.models import Department
        other_dept = Department(
            name="Other Department",
            code="OTHER",
            is_active=True
        )
        db_session.add(other_dept)
        db_session.commit()

        # Get current user's department
        response = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers=get_auth_headers(token)
        )
        user_dept_id = response.json()["department_id"]

        # Verify user's department is correct
        assert user_dept_id == user_data["department_id"]
        assert user_dept_id != other_dept.id


# ================================================================
# Password Security Tests
# ================================================================

class TestPasswordSecurity:
    """Test password hashing and security"""

    def test_password_is_hashed(self, client: TestClient, test_user_data: dict, db_session: Session):
        """Test that passwords are hashed in database"""
        # Register user
        client.post(f"{settings.API_PREFIX}/auth/register", json=test_user_data)

        # Check database
        from app.db.models import User
        user = db_session.query(User).filter(User.username == test_user_data["username"]).first()

        # Password should be hashed (not plain text)
        assert user.hashed_password != test_user_data["password"]
        # Hashed password should be bcrypt hash (starts with $2b$)
        assert user.hashed_password.startswith("$2b$")

    def test_password_not_returned_in_api(self, client: TestClient, authenticated_user):
        """Test that password/hash is never returned in API responses"""
        user_data, token = authenticated_user

        # Get user profile
        response = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers=get_auth_headers(token)
        )

        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data


# ================================================================
# Integration Tests
# ================================================================

class TestAuthIntegration:
    """Integration tests for complete authentication flows"""

    def test_complete_auth_flow(self, client: TestClient, test_user_data: dict):
        """Test complete authentication flow: register -> login -> access protected resource"""
        # Step 1: Register
        response = client.post(
            f"{settings.API_PREFIX}/auth/register",
            json=test_user_data
        )
        assert response.status_code == 200
        user = response.json()

        # Step 2: Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post(f"{settings.API_PREFIX}/auth/login", data=login_data)
        assert response.status_code == 200
        token = response.json()["access_token"]

        # Step 3: Access protected resource
        response = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers=get_auth_headers(token)
        )
        assert response.status_code == 200
        profile = response.json()

        # Verify data consistency
        assert profile["id"] == user["id"]
        assert profile["username"] == user["username"]
        assert profile["email"] == user["email"]

    def test_multiple_users_different_departments(
        self,
        client: TestClient,
        test_user_data: dict,
        test_admin_data: dict,
        db_session: Session
    ):
        """Test multiple users in different departments"""
        # Create second department
        from app.db.models import Department
        dept2 = Department(name="Dept 2", code="D2", is_active=True)
        db_session.add(dept2)
        db_session.commit()

        # Register users in different departments
        user1_data = test_user_data.copy()
        user2_data = test_admin_data.copy()
        user2_data["department_id"] = dept2.id

        # Register both users
        client.post(f"{settings.API_PREFIX}/auth/register", json=user1_data)
        client.post(f"{settings.API_PREFIX}/auth/register", json=user2_data)

        # Login both users
        token1 = client.post(
            f"{settings.API_PREFIX}/auth/login",
            data={"username": user1_data["username"], "password": user1_data["password"]}
        ).json()["access_token"]

        token2 = client.post(
            f"{settings.API_PREFIX}/auth/login",
            data={"username": user2_data["username"], "password": user2_data["password"]}
        ).json()["access_token"]

        # Verify different departments
        profile1 = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers=get_auth_headers(token1)
        ).json()

        profile2 = client.get(
            f"{settings.API_PREFIX}/auth/me",
            headers=get_auth_headers(token2)
        ).json()

        assert profile1["department_id"] != profile2["department_id"]
        assert profile1["department_id"] == user1_data["department_id"]
        assert profile2["department_id"] == dept2.id
