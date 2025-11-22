import pytest
from fastapi import HTTPException

from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    authenticate_user,
    get_current_user,
)
from app.db.models import User, Department, UserRoleEnum


def test_password_hash_and_verify():
    password = "StrongPass123!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token_roundtrip():
    token = create_access_token({"sub": "123"})
    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "123"
    assert "exp" in payload


def test_authenticate_user_and_last_login(db_session):
    department = Department(name="QA", code="QA", is_active=True)
    db_session.add(department)
    db_session.flush()

    user = User(
        username="qa",
        email="qa@example.com",
        full_name="QA User",
        hashed_password=get_password_hash("secret"),
        role=UserRoleEnum.USER,
        department_id=department.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    authenticated = authenticate_user(db_session, "qa", "secret")
    assert authenticated is not None
    assert authenticated.id == user.id
    assert authenticated.last_login is not None


@pytest.mark.asyncio
async def test_get_current_user_inactive_rejected(db_session):
    department = Department(name="Support", code="SUP", is_active=True)
    db_session.add(department)
    db_session.flush()

    inactive_user = User(
        username="inactive",
        email="inactive@example.com",
        full_name="Inactive User",
        hashed_password=get_password_hash("pass"),
        role=UserRoleEnum.USER,
        department_id=department.id,
        is_active=False,
    )
    db_session.add(inactive_user)
    db_session.commit()
    db_session.refresh(inactive_user)

    token = create_access_token({"sub": str(inactive_user.id)})

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=db_session)  # type: ignore[arg-type]

    assert exc.value.status_code == 403
