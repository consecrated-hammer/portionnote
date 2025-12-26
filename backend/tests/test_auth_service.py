import uuid

import pytest
from starlette.requests import Request
from app.config import Settings
from app.services.auth_service import (
    AuthenticateUser,
    CreateInviteForEmail,
    GetUserFromRequest,
    RegisterGoogleUser,
    RegisterLocalUser
)
from app.utils.database import ExecuteQuery, FetchOne
from app.utils.seed import SeedDatabase


def test_register_and_authenticate_local_user(temp_db):
    AdminUserId = SeedDatabase()
    InviteRow = CreateInviteForEmail("user@gmail.com", AdminUserId)
    UserItem, Created = RegisterLocalUser(
        Email="user@gmail.com",
        Password="Password123",
        FirstName="Taylor",
        LastName="Green",
        InviteCode=InviteRow["InviteCode"]
    )

    assert Created is True
    assert UserItem.Email == "user@gmail.com"

    Authenticated = AuthenticateUser("user@gmail.com", "Password123")
    assert Authenticated.UserId == UserItem.UserId


def test_register_local_user_requires_invite(temp_db):
    AdminUserId = SeedDatabase()
    CreateInviteForEmail("blocked@gmail.com", AdminUserId)
    with pytest.raises(ValueError):
        RegisterLocalUser(
            Email="blocked@gmail.com",
            Password="Password123",
            FirstName="Blocked",
            LastName="User",
            InviteCode="wrong-code"
        )


def test_register_google_user_with_invite(temp_db):
    AdminUserId = SeedDatabase()
    InviteRow = CreateInviteForEmail("google@gmail.com", AdminUserId)
    UserItem, Created = RegisterGoogleUser(
        Email="google@gmail.com",
        FirstName="Jules",
        LastName="Adams",
        GoogleSubject="sub-123",
        InviteCode=InviteRow["InviteCode"]
    )

    assert Created is True
    assert UserItem.Email == "google@gmail.com"

    Existing, CreatedAgain = RegisterGoogleUser(
        Email="google@gmail.com",
        FirstName="Jules",
        LastName="Adams",
        GoogleSubject="sub-123",
        InviteCode=None
    )

    assert CreatedAgain is False
    assert Existing.UserId == UserItem.UserId


def test_google_registration_rejects_local_account(temp_db):
    AdminUserId = SeedDatabase()
    InviteRow = CreateInviteForEmail("local@gmail.com", AdminUserId)
    RegisterLocalUser(
        Email="local@gmail.com",
        Password="Password123",
        FirstName="Local",
        LastName="Account",
        InviteCode=InviteRow["InviteCode"]
    )

    with pytest.raises(ValueError):
        RegisterGoogleUser(
            Email="local@gmail.com",
            FirstName="Local",
            LastName="Account",
            GoogleSubject="sub-999",
            InviteCode=None
        )


def test_get_user_from_request(temp_db):
    AdminUserId = SeedDatabase()
    InviteRow = CreateInviteForEmail("request@gmail.com", AdminUserId)
    UserItem, Created = RegisterLocalUser(
        Email="request@gmail.com",
        Password="Password123",
        FirstName="Request",
        LastName="Session",
        InviteCode=InviteRow["InviteCode"]
    )

    assert Created is True

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "session": {"UserId": UserItem.UserId}
    }
    request = Request(scope)

    Loaded = GetUserFromRequest(request)
    assert Loaded is not None
    assert Loaded.UserId == UserItem.UserId


def test_create_invite_requires_gmail(temp_db):
    AdminUserId = SeedDatabase()
    with pytest.raises(ValueError):
        CreateInviteForEmail("user@example.com", AdminUserId)


def test_google_login_links_missing_subject(temp_db):
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
            GoogleSubject,
            IsAdmin
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        [
            UserId,
            "seed@gmail.com",
            None,
            None,
            None,
            "Google",
            None,
            1
        ]
    )

    UserItem, Created = RegisterGoogleUser(
        Email="seed@gmail.com",
        FirstName="Seed",
        LastName="Admin",
        GoogleSubject="sub-seed",
        InviteCode=None
    )

    assert Created is False
    assert UserItem.UserId == UserId

    Row = FetchOne(
        "SELECT GoogleSubject AS GoogleSubject FROM Users WHERE UserId = ?;",
        [UserId]
    )
    assert Row is not None
    assert Row["GoogleSubject"] == "sub-seed"


def test_seeded_google_admin_logs_in_without_invite(temp_db):
    OriginalAdmins = Settings.SeedGoogleAdmins
    OriginalUsers = Settings.SeedGoogleUsers
    Settings.SeedGoogleAdmins = "adminseed@gmail.com"
    Settings.SeedGoogleUsers = ""

    try:
        UserItem, Created = RegisterGoogleUser(
            Email="adminseed@gmail.com",
            FirstName="Seeded",
            LastName="Admin",
            GoogleSubject="sub-admin",
            InviteCode=None
        )

        assert Created is True
        assert UserItem.IsAdmin is True
    finally:
        Settings.SeedGoogleAdmins = OriginalAdmins
        Settings.SeedGoogleUsers = OriginalUsers


def test_seeded_google_admin_converts_local_account(temp_db):
    AdminUserId = SeedDatabase()
    InviteRow = CreateInviteForEmail("convert@gmail.com", AdminUserId)
    RegisterLocalUser(
        Email="convert@gmail.com",
        Password="Password123",
        FirstName="Convert",
        LastName="User",
        InviteCode=InviteRow["InviteCode"]
    )

    OriginalAdmins = Settings.SeedGoogleAdmins
    OriginalUsers = Settings.SeedGoogleUsers
    Settings.SeedGoogleAdmins = "convert@gmail.com"
    Settings.SeedGoogleUsers = ""

    try:
        UserItem, Created = RegisterGoogleUser(
            Email="convert@gmail.com",
            FirstName="Convert",
            LastName="User",
            GoogleSubject="sub-convert",
            InviteCode=None
        )

        assert Created is False
        assert UserItem.IsAdmin is True

        Row = FetchOne(
            "SELECT AuthProvider AS AuthProvider FROM Users WHERE UserId = ?;",
            [UserItem.UserId]
        )
        assert Row is not None
        assert Row["AuthProvider"] == "Google"
    finally:
        Settings.SeedGoogleAdmins = OriginalAdmins
        Settings.SeedGoogleUsers = OriginalUsers
