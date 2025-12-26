import uuid

import pytest

from app.config import Settings
from app.utils import database
from app.utils.auth import HashPassword
from app.utils.database import ExecuteQuery
from app.utils.migrations import RunMigrations
from app.utils.seed import SeedDatabase


def CreateTestUser(Email: str, IsAdmin: bool = False) -> str:
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


@pytest.fixture(autouse=True)
def SetTestOpenAiKey():
    OriginalKey = Settings.OpenAiApiKey
    Settings.OpenAiApiKey = "test-key"
    yield
    Settings.OpenAiApiKey = OriginalKey


@pytest.fixture()
def temp_db(tmp_path):
    if database.DatabaseConnection is not None:
        database.DatabaseConnection.close()
        database.DatabaseConnection = None

    Settings.DatabaseFile = str(tmp_path / "portionnote-test.sqlite")
    Settings.AdminEmail = "admin@example.com"
    Settings.AdminPassword = "AdminPassword123!"
    Settings.InviteCode = "invite-test"
    RunMigrations()

    yield

    if database.DatabaseConnection is not None:
        database.DatabaseConnection.close()
        database.DatabaseConnection = None


@pytest.fixture()
def seeded_db(temp_db):
    AdminUserId = SeedDatabase()
    return AdminUserId


@pytest.fixture()
def test_user_id(temp_db):
    return CreateTestUser("user@example.com")
