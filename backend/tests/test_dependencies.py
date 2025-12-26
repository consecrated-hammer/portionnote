import uuid

import pytest
from starlette.requests import Request

from fastapi import HTTPException
from app.dependencies import RequireAdmin, RequireUser
from app.models.schemas import User
from app.utils.auth import HashPassword
from app.utils.database import ExecuteQuery


def CreateUser(Email: str, IsAdmin: bool) -> str:
    UserId = str(uuid.uuid4())
    ExecuteQuery(
        """
        INSERT INTO Users (
            UserId,
            Email,
            FirstName,
            LastName,
            PasswordHash,
            AuthProvider,
            IsAdmin
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        [
            UserId,
            Email,
            "Test",
            "User",
            HashPassword("Password123"),
            "Local",
            1 if IsAdmin else 0
        ]
    )
    return UserId


def BuildRequest(UserId: str | None) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "session": {"UserId": UserId} if UserId else {}
    }
    return Request(scope)


def test_require_user_unauthenticated(temp_db):
    request = BuildRequest(None)
    with pytest.raises(HTTPException):
        RequireUser(request)


def test_require_admin_blocks_non_admin(temp_db):
    UserId = CreateUser("basic@example.com", False)
    request = BuildRequest(UserId)
    with pytest.raises(HTTPException):
        RequireAdmin(request)


def test_require_admin_allows_admin(temp_db):
    AdminId = CreateUser("admin@example.com", True)
    request = BuildRequest(AdminId)
    user = RequireAdmin(request)
    assert isinstance(user, User)
    assert user.IsAdmin is True
