import uuid

from app.models.schemas import AdminUserSummary
from app.services.auth_service import NormalizeEmail
from app.utils.auth import HashPassword
from app.utils.database import ExecuteQuery, FetchAll, FetchOne


def _BuildAdminUser(Row: dict) -> AdminUserSummary:
    return AdminUserSummary(
        UserId=Row["UserId"],
        Email=Row["Email"],
        FirstName=Row.get("FirstName"),
        LastName=Row.get("LastName"),
        AuthProvider=Row["AuthProvider"],
        IsAdmin=bool(Row["IsAdmin"]),
        CreatedAt=Row.get("CreatedAt")
    )


def ListUsers() -> list[AdminUserSummary]:
    Rows = FetchAll(
        """
        SELECT
            UserId AS UserId,
            Email AS Email,
            FirstName AS FirstName,
            LastName AS LastName,
            AuthProvider AS AuthProvider,
            IsAdmin AS IsAdmin,
            CreatedAt AS CreatedAt
        FROM Users
        ORDER BY CreatedAt DESC;
        """
    )
    return [_BuildAdminUser(Row) for Row in Rows]


def CreateLocalUser(
    Email: str,
    Password: str,
    FirstName: str,
    LastName: str | None,
    IsAdmin: bool
) -> AdminUserSummary:
    NormalizedEmail = NormalizeEmail(Email)
    Existing = FetchOne(
        "SELECT UserId AS UserId FROM Users WHERE Email = ?;",
        [NormalizedEmail]
    )
    if Existing is not None:
        raise ValueError("User already exists.")

    UserId = str(uuid.uuid4())
    PasswordHash = HashPassword(Password)

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
            NormalizedEmail,
            FirstName.strip(),
            LastName.strip() if LastName else None,
            PasswordHash,
            "Local",
            1 if IsAdmin else 0
        ]
    )

    Row = FetchOne(
        """
        SELECT
            UserId AS UserId,
            Email AS Email,
            FirstName AS FirstName,
            LastName AS LastName,
            AuthProvider AS AuthProvider,
            IsAdmin AS IsAdmin,
            CreatedAt AS CreatedAt
        FROM Users
        WHERE UserId = ?;
        """,
        [UserId]
    )
    if Row is None:
        raise ValueError("Failed to load user.")

    return _BuildAdminUser(Row)


def UpdateUserAdmin(UserId: str, IsAdmin: bool) -> AdminUserSummary:
    ExecuteQuery(
        "UPDATE Users SET IsAdmin = ? WHERE UserId = ?;",
        [1 if IsAdmin else 0, UserId]
    )

    Row = FetchOne(
        """
        SELECT
            UserId AS UserId,
            Email AS Email,
            FirstName AS FirstName,
            LastName AS LastName,
            AuthProvider AS AuthProvider,
            IsAdmin AS IsAdmin,
            CreatedAt AS CreatedAt
        FROM Users
        WHERE UserId = ?;
        """,
        [UserId]
    )
    if Row is None:
        raise ValueError("User not found.")

    return _BuildAdminUser(Row)
