import json
import uuid

from app.config import Settings
from app.services.auth_service import CreateInviteForEmail
from app.utils.auth import HashPassword
from app.utils.database import ExecuteQuery, FetchOne
from app.utils.defaults import DefaultFoods, DefaultTargets, DefaultTodayLayout


def EnsureAdminUser() -> str:
    NormalizedEmail = Settings.AdminEmail.strip().lower()
    Row = FetchOne(
        """
        SELECT
            UserId AS UserId
        FROM Users
        WHERE Email = ?;
        """,
        [NormalizedEmail]
    )

    if Row is not None:
        ExecuteQuery(
            """
            UPDATE Users
            SET
                PasswordHash = ?,
                AuthProvider = ?,
                IsAdmin = 1
            WHERE UserId = ?;
            """,
            [HashPassword(Settings.AdminPassword), "Local", Row["UserId"]]
        )
        return Row["UserId"]

    AdminUserId = str(uuid.uuid4())

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
            AdminUserId,
            NormalizedEmail,
            "Admin",
            "User",
            HashPassword(Settings.AdminPassword),
            "Local",
            1
        ]
    )

    return AdminUserId


def BackfillUserIds(AdminUserId: str) -> None:
    ExecuteQuery("UPDATE Settings SET UserId = ? WHERE UserId IS NULL;", [AdminUserId])
    ExecuteQuery("UPDATE Foods SET UserId = ? WHERE UserId IS NULL;", [AdminUserId])
    ExecuteQuery("UPDATE DailyLogs SET UserId = ? WHERE UserId IS NULL;", [AdminUserId])
    ExecuteQuery("UPDATE Suggestions SET UserId = ? WHERE UserId IS NULL;", [AdminUserId])


def EnsureSettingsForUser(UserId: str) -> None:
    ExecuteQuery(
        """
        INSERT INTO Settings (
            SettingsId,
            UserId,
            DailyCalorieTarget,
            ProteinTargetMin,
            ProteinTargetMax,
            StepKcalFactor,
            StepTarget,
            TodayLayout
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (UserId)
        DO UPDATE SET
            DailyCalorieTarget = excluded.DailyCalorieTarget,
            ProteinTargetMin = excluded.ProteinTargetMin,
            ProteinTargetMax = excluded.ProteinTargetMax,
            StepKcalFactor = excluded.StepKcalFactor,
            StepTarget = excluded.StepTarget,
            TodayLayout = excluded.TodayLayout;
        """,
        [
            str(uuid.uuid4()),
            UserId,
            DefaultTargets.DailyCalorieTarget,
            DefaultTargets.ProteinTargetMin,
            DefaultTargets.ProteinTargetMax,
            DefaultTargets.StepKcalFactor,
            DefaultTargets.StepTarget,
            json.dumps(DefaultTodayLayout)
        ]
    )


def SeedFoodsForUser(UserId: str) -> None:
    for FoodName, ServingDescription, CaloriesPerServing, ProteinPerServing in DefaultFoods:
        ExecuteQuery(
            """
            INSERT INTO Foods (
                FoodId,
                UserId,
                FoodName,
                ServingDescription,
                CaloriesPerServing,
                ProteinPerServing,
                IsFavourite
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (UserId, FoodName)
            DO UPDATE SET
                ServingDescription = excluded.ServingDescription,
                CaloriesPerServing = excluded.CaloriesPerServing,
                ProteinPerServing = excluded.ProteinPerServing,
                IsFavourite = excluded.IsFavourite;
            """,
            [
                str(uuid.uuid4()),
                UserId,
                FoodName,
                ServingDescription,
                CaloriesPerServing,
                ProteinPerServing,
                0
            ]
        )


def SeedDatabase() -> str:
    AdminUserId = EnsureAdminUser()
    BackfillUserIds(AdminUserId)
    EnsureSettingsForUser(AdminUserId)
    SeedFoodsForUser(AdminUserId)
    SeedInviteEmails(AdminUserId)
    SeedGoogleUsers()
    return AdminUserId


def ParseSeedEmails(RawEmails: str) -> list[str]:
    return [Email.strip() for Email in RawEmails.split(",") if Email.strip()]


def SeedInviteEmails(AdminUserId: str) -> None:
    RawEmails = Settings.SeedInviteEmails.strip()
    if not RawEmails:
        return

    Emails = ParseSeedEmails(RawEmails)
    for Email in Emails:
        try:
            CreateInviteForEmail(Email, AdminUserId)
        except ValueError:
            continue


def SeedGoogleUsers() -> None:
    SeedUsers = set(ParseSeedEmails(Settings.SeedGoogleUsers))
    SeedAdmins = set(ParseSeedEmails(Settings.SeedGoogleAdmins))
    AllEmails = sorted(SeedUsers | SeedAdmins)
    if not AllEmails:
        return

    for Email in AllEmails:
        NormalizedEmail = Email.strip().lower()
        Existing = FetchOne(
            """
            SELECT
                UserId AS UserId,
                AuthProvider AS AuthProvider,
                IsAdmin AS IsAdmin
            FROM Users
            WHERE Email = ?;
            """,
            [NormalizedEmail]
        )

        if Existing is not None:
            if NormalizedEmail in SeedAdmins and not Existing["IsAdmin"]:
                ExecuteQuery(
                    "UPDATE Users SET IsAdmin = 1 WHERE UserId = ?;",
                    [Existing["UserId"]]
                )
            continue

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
                str(uuid.uuid4()),
                NormalizedEmail,
                None,
                None,
                None,
                "Google",
                None,
                1 if NormalizedEmail in SeedAdmins else 0
            ]
        )
