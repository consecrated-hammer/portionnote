import secrets
import uuid

from fastapi import Request

from app.config import Settings
from app.models.schemas import User
from app.utils.auth import HashPassword, VerifyPassword
from app.utils.database import ExecuteQuery, FetchOne


def NormalizeEmail(Email: str) -> str:
    return Email.strip().lower()


def BuildUserFromRow(Row: dict) -> User:
    return User(
        UserId=Row["UserId"],
        Email=Row["Email"],
        FirstName=Row.get("FirstName"),
        LastName=Row.get("LastName"),
        BirthDate=Row.get("BirthDate"),
        HeightCm=Row.get("HeightCm"),
        WeightKg=Row.get("WeightKg"),
        ActivityLevel=Row.get("ActivityLevel"),
        IsAdmin=bool(Row["IsAdmin"])
    )


def GetUserFromRequest(RequestValue: Request) -> User | None:
    SessionData = RequestValue.scope.get("session", {})
    UserId = SessionData.get("UserId")
    if not UserId:
        return None

    Row = FetchOne(
        """
        SELECT
            UserId AS UserId,
            Email AS Email,
            FirstName AS FirstName,
            LastName AS LastName,
            BirthDate AS BirthDate,
            HeightCm AS HeightCm,
            WeightKg AS WeightKg,
            ActivityLevel AS ActivityLevel,
            IsAdmin AS IsAdmin
        FROM Users
        WHERE UserId = ?;
        """,
        [UserId]
    )

    if Row is None:
        return None

    return BuildUserFromRow(Row)


def IsGmailAddress(Email: str) -> bool:
    Normalized = NormalizeEmail(Email)
    return Normalized.endswith("@gmail.com")


def ParseSeedEmailSet(RawEmails: str) -> set[str]:
    if not RawEmails:
        return set()
    return {NormalizeEmail(Email) for Email in RawEmails.split(",") if Email.strip()}


def GetSeededGoogleRoles(NormalizedEmail: str) -> tuple[bool, bool]:
    SeedAdmins = ParseSeedEmailSet(Settings.SeedGoogleAdmins)
    SeedUsers = ParseSeedEmailSet(Settings.SeedGoogleUsers)
    IsAdminSeed = NormalizedEmail in SeedAdmins
    IsUserSeed = IsAdminSeed or NormalizedEmail in SeedUsers
    return IsUserSeed, IsAdminSeed


def GenerateInviteCode() -> str:
    for _ in range(5):
        Code = secrets.token_urlsafe(16)
        Existing = FetchOne(
            "SELECT InviteCode FROM InviteCodes WHERE InviteCode = ?;",
            [Code]
        )
        if Existing is None:
            return Code
    raise ValueError("Failed to generate invite code.")


def EnsureInviteForEmail(InviteCode: str | None, Email: str) -> dict:
    if InviteCode is None or not InviteCode.strip():
        raise ValueError("Invite required.")

    NormalizedEmail = NormalizeEmail(Email)
    Row = FetchOne(
        """
        SELECT
            InviteCodeId AS InviteCodeId,
            InviteEmail AS InviteEmail,
            UsedAt AS UsedAt,
            RequireGmail AS RequireGmail
        FROM InviteCodes
        WHERE InviteCode = ?;
        """,
        [InviteCode.strip()]
    )

    if Row is None:
        raise ValueError("Invite not found.")

    if Row["UsedAt"] is not None:
        raise ValueError("Invite already used.")

    InviteEmail = NormalizeEmail(Row["InviteEmail"])
    if InviteEmail != NormalizedEmail:
        raise ValueError("Invite email does not match.")

    if Row["RequireGmail"] and not IsGmailAddress(Email):
        raise ValueError("Invite requires a gmail.com address.")

    return Row


def MarkInviteUsed(InviteCodeId: str, UserId: str) -> None:
    ExecuteQuery(
        """
        UPDATE InviteCodes
        SET
            UsedByUserId = ?,
            UsedAt = CURRENT_TIMESTAMP
        WHERE InviteCodeId = ? AND UsedAt IS NULL;
        """,
        [UserId, InviteCodeId]
    )


def CreateInviteForEmail(Email: str, CreatedByUserId: str) -> dict:
    NormalizedEmail = NormalizeEmail(Email)
    if not IsGmailAddress(NormalizedEmail):
        raise ValueError("Invite must use a gmail.com address.")

    ExistingUser = FetchOne(
        "SELECT UserId AS UserId FROM Users WHERE Email = ?;",
        [NormalizedEmail]
    )
    if ExistingUser is not None:
        raise ValueError("User already exists.")

    PendingInvite = FetchOne(
        """
        SELECT InviteCode AS InviteCode
        FROM InviteCodes
        WHERE InviteEmail = ? AND UsedAt IS NULL;
        """,
        [NormalizedEmail]
    )
    if PendingInvite is not None:
        ExistingRow = FetchOne(
            """
            SELECT
                InviteCode AS InviteCode,
                InviteEmail AS InviteEmail,
                CreatedAt AS CreatedAt
            FROM InviteCodes
            WHERE InviteEmail = ? AND UsedAt IS NULL;
            """,
            [NormalizedEmail]
        )
        if ExistingRow is None:
            raise ValueError("Invite already exists for this email.")
        return ExistingRow

    InviteCodeId = str(uuid.uuid4())
    InviteCode = GenerateInviteCode()

    ExecuteQuery(
        """
        INSERT INTO InviteCodes (
            InviteCodeId,
            InviteCode,
            InviteEmail,
            CreatedByUserId,
            RequireGmail
        ) VALUES (?, ?, ?, ?, ?);
        """,
        [
            InviteCodeId,
            InviteCode,
            NormalizedEmail,
            CreatedByUserId,
            1
        ]
    )

    Row = FetchOne(
        """
        SELECT
            InviteCode AS InviteCode,
            InviteEmail AS InviteEmail,
            CreatedAt AS CreatedAt
        FROM InviteCodes
        WHERE InviteCodeId = ?;
        """,
        [InviteCodeId]
    )

    if Row is None:
        raise ValueError("Failed to create invite.")

    return Row


def RegisterLocalUser(
    Email: str,
    Password: str,
    FirstName: str,
    LastName: str | None,
    InviteCode: str | None
) -> tuple[User, bool]:
    NormalizedEmail = NormalizeEmail(Email)
    Existing = FetchOne(
        """
        SELECT UserId AS UserId
        FROM Users
        WHERE Email = ?;
        """,
        [NormalizedEmail]
    )

    if Existing is not None:
        raise ValueError("Email already registered.")

    InviteRow = EnsureInviteForEmail(InviteCode, NormalizedEmail)

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
            0
        ]
    )

    Row = FetchOne(
        """
        SELECT
            UserId AS UserId,
            Email AS Email,
            FirstName AS FirstName,
            LastName AS LastName,
            IsAdmin AS IsAdmin
        FROM Users
        WHERE UserId = ?;
        """,
        [UserId]
    )

    if Row is None:
        raise ValueError("Failed to load user.")

    MarkInviteUsed(InviteRow["InviteCodeId"], UserId)

    return BuildUserFromRow(Row), True


def AuthenticateUser(Email: str, Password: str) -> User:
    NormalizedEmail = NormalizeEmail(Email)
    Row = FetchOne(
        """
        SELECT
            UserId AS UserId,
            Email AS Email,
            FirstName AS FirstName,
            LastName AS LastName,
            PasswordHash AS PasswordHash,
            AuthProvider AS AuthProvider,
            IsAdmin AS IsAdmin
        FROM Users
        WHERE Email = ?;
        """,
        [NormalizedEmail]
    )

    if Row is None:
        raise ValueError("Invalid credentials.")

    if Row["AuthProvider"] != "Local":
        raise ValueError("Use Google sign in for this account.")

    PasswordHash = Row.get("PasswordHash")
    if not PasswordHash or not VerifyPassword(Password, PasswordHash):
        raise ValueError("Invalid credentials.")

    return BuildUserFromRow(Row)


def RegisterGoogleUser(
    Email: str,
    FirstName: str | None,
    LastName: str | None,
    GoogleSubject: str,
    InviteCode: str | None
) -> tuple[User, bool]:
    NormalizedEmail = NormalizeEmail(Email)
    IsSeeded, IsSeededAdmin = GetSeededGoogleRoles(NormalizedEmail)

    Row = FetchOne(
        """
        SELECT
            UserId AS UserId,
            Email AS Email,
            FirstName AS FirstName,
            LastName AS LastName,
            AuthProvider AS AuthProvider,
            GoogleSubject AS GoogleSubject,
            IsAdmin AS IsAdmin
        FROM Users
        WHERE GoogleSubject = ? OR Email = ?;
        """,
        [GoogleSubject, NormalizedEmail]
    )

    if Row is not None:
        if Row["AuthProvider"] != "Google":
            if IsSeeded:
                ExecuteQuery(
                    """
                    UPDATE Users
                    SET
                        AuthProvider = 'Google',
                        PasswordHash = NULL,
                        GoogleSubject = ?,
                        FirstName = COALESCE(?, FirstName),
                        LastName = COALESCE(?, LastName),
                        IsAdmin = CASE WHEN ? THEN 1 ELSE IsAdmin END
                    WHERE UserId = ?;
                    """,
                    [
                        GoogleSubject,
                        FirstName.strip() if FirstName else None,
                        LastName.strip() if LastName else None,
                        1 if IsSeededAdmin else 0,
                        Row["UserId"]
                    ]
                )
                Row = FetchOne(
                    """
                    SELECT
                        UserId AS UserId,
                        Email AS Email,
                        FirstName AS FirstName,
                        LastName AS LastName,
                        IsAdmin AS IsAdmin
                    FROM Users
                    WHERE UserId = ?;
                    """,
                    [Row["UserId"]]
                )
                if Row is None:
                    raise ValueError("Failed to load user.")
                return BuildUserFromRow(Row), False

            raise ValueError("Account already exists for this email.")

        ExistingSubject = Row.get("GoogleSubject")
        if ExistingSubject and ExistingSubject != GoogleSubject:
            raise ValueError("Account already exists for this email.")

        if IsSeededAdmin and not Row["IsAdmin"]:
            ExecuteQuery(
                "UPDATE Users SET IsAdmin = 1 WHERE UserId = ?;",
                [Row["UserId"]]
            )
            Row["IsAdmin"] = 1

        if not ExistingSubject:
            ExecuteQuery(
                """
                UPDATE Users
                SET
                    GoogleSubject = ?,
                    FirstName = COALESCE(?, FirstName),
                    LastName = COALESCE(?, LastName)
                WHERE UserId = ?;
                """,
                [
                    GoogleSubject,
                    FirstName.strip() if FirstName else None,
                    LastName.strip() if LastName else None,
                    Row["UserId"]
                ]
            )
            Row = FetchOne(
                """
                SELECT
                    UserId AS UserId,
                    Email AS Email,
                    FirstName AS FirstName,
                    LastName AS LastName,
                    IsAdmin AS IsAdmin
                FROM Users
                WHERE UserId = ?;
                """,
                [Row["UserId"]]
            )
            if Row is None:
                raise ValueError("Failed to load user.")

        return BuildUserFromRow(Row), False

    if IsSeeded:
        UserId = str(uuid.uuid4())
        ExecuteQuery(
            """
            INSERT INTO Users (
                UserId,
                Email,
                FirstName,
                LastName,
                AuthProvider,
                GoogleSubject,
                IsAdmin
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            [
                UserId,
                NormalizedEmail,
                FirstName.strip() if FirstName else None,
                LastName.strip() if LastName else None,
                "Google",
                GoogleSubject,
                1 if IsSeededAdmin else 0
            ]
        )

        Row = FetchOne(
            """
            SELECT
                UserId AS UserId,
                Email AS Email,
                FirstName AS FirstName,
                LastName AS LastName,
                IsAdmin AS IsAdmin
            FROM Users
            WHERE UserId = ?;
            """,
            [UserId]
        )

        if Row is None:
            raise ValueError("Failed to load user.")

        return BuildUserFromRow(Row), True

    InviteRow = EnsureInviteForEmail(InviteCode, NormalizedEmail)

    UserId = str(uuid.uuid4())

    ExecuteQuery(
        """
        INSERT INTO Users (
            UserId,
            Email,
            FirstName,
            LastName,
            AuthProvider,
            GoogleSubject,
            IsAdmin
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        [
            UserId,
            NormalizedEmail,
            FirstName.strip() if FirstName else None,
            LastName.strip() if LastName else None,
            "Google",
            GoogleSubject,
            0
        ]
    )

    Row = FetchOne(
        """
        SELECT
            UserId AS UserId,
            Email AS Email,
            FirstName AS FirstName,
            LastName AS LastName,
            IsAdmin AS IsAdmin
        FROM Users
        WHERE UserId = ?;
        """,
        [UserId]
    )

    if Row is None:
        raise ValueError("Failed to load user.")

    MarkInviteUsed(InviteRow["InviteCodeId"], UserId)

    return BuildUserFromRow(Row), True
