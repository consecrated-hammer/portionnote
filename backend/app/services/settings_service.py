import json

from app.models.schemas import UpdateSettingsInput, UserSettings
from app.services.daily_logs_service import GetSettings
from app.utils.database import ExecuteQuery, FetchOne
from app.utils.defaults import DefaultTodayLayout
from app.utils.seed import EnsureSettingsForUser


def ParseTodayLayout(RawLayout: str | None) -> list[str]:
    if not RawLayout:
        return list(DefaultTodayLayout)
    try:
        Parsed = json.loads(RawLayout)
    except json.JSONDecodeError:
        return list(DefaultTodayLayout)
    if not isinstance(Parsed, list):
        return list(DefaultTodayLayout)
    return [str(Item) for Item in Parsed if isinstance(Item, str)]


def GetUserSettings(UserId: str) -> UserSettings:
    Targets = GetSettings(UserId)
    Row = FetchOne(
        """
        SELECT
            TodayLayout AS TodayLayout
        FROM Settings
        WHERE UserId = ?
        LIMIT 1;
        """,
        [UserId]
    )
    Layout = ParseTodayLayout(Row["TodayLayout"] if Row else None)
    return UserSettings(Targets=Targets, TodayLayout=Layout)


def UpdateUserSettings(UserId: str, Input: UpdateSettingsInput) -> UserSettings:
    Existing = FetchOne(
        "SELECT SettingsId AS SettingsId FROM Settings WHERE UserId = ?;",
        [UserId]
    )
    if Existing is None:
        EnsureSettingsForUser(UserId)

    Updates: list[str] = []
    Params: list[object] = []

    if Input.DailyCalorieTarget is not None:
        Updates.append("DailyCalorieTarget = ?")
        Params.append(Input.DailyCalorieTarget)
    if Input.ProteinTargetMin is not None:
        Updates.append("ProteinTargetMin = ?")
        Params.append(Input.ProteinTargetMin)
    if Input.ProteinTargetMax is not None:
        Updates.append("ProteinTargetMax = ?")
        Params.append(Input.ProteinTargetMax)
    if Input.StepKcalFactor is not None:
        Updates.append("StepKcalFactor = ?")
        Params.append(Input.StepKcalFactor)
    if Input.StepTarget is not None:
        Updates.append("StepTarget = ?")
        Params.append(Input.StepTarget)
    if Input.FibreTarget is not None:
        Updates.append("FibreTarget = ?")
        Params.append(Input.FibreTarget)
    if Input.CarbsTarget is not None:
        Updates.append("CarbsTarget = ?")
        Params.append(Input.CarbsTarget)
    if Input.FatTarget is not None:
        Updates.append("FatTarget = ?")
        Params.append(Input.FatTarget)
    if Input.SaturatedFatTarget is not None:
        Updates.append("SaturatedFatTarget = ?")
        Params.append(Input.SaturatedFatTarget)
    if Input.SugarTarget is not None:
        Updates.append("SugarTarget = ?")
        Params.append(Input.SugarTarget)
    if Input.SodiumTarget is not None:
        Updates.append("SodiumTarget = ?")
        Params.append(Input.SodiumTarget)
    if Input.ShowProteinOnToday is not None:
        Updates.append("ShowProteinOnToday = ?")
        Params.append(1 if Input.ShowProteinOnToday else 0)
    if Input.ShowStepsOnToday is not None:
        Updates.append("ShowStepsOnToday = ?")
        Params.append(1 if Input.ShowStepsOnToday else 0)
    if Input.ShowFibreOnToday is not None:
        Updates.append("ShowFibreOnToday = ?")
        Params.append(1 if Input.ShowFibreOnToday else 0)
    if Input.ShowCarbsOnToday is not None:
        Updates.append("ShowCarbsOnToday = ?")
        Params.append(1 if Input.ShowCarbsOnToday else 0)
    if Input.ShowFatOnToday is not None:
        Updates.append("ShowFatOnToday = ?")
        Params.append(1 if Input.ShowFatOnToday else 0)
    if Input.ShowSaturatedFatOnToday is not None:
        Updates.append("ShowSaturatedFatOnToday = ?")
        Params.append(1 if Input.ShowSaturatedFatOnToday else 0)
    if Input.ShowSugarOnToday is not None:
        Updates.append("ShowSugarOnToday = ?")
        Params.append(1 if Input.ShowSugarOnToday else 0)
    if Input.ShowSodiumOnToday is not None:
        Updates.append("ShowSodiumOnToday = ?")
        Params.append(1 if Input.ShowSodiumOnToday else 0)
    if Input.TodayLayout is not None:
        Updates.append("TodayLayout = ?")
        Params.append(json.dumps(Input.TodayLayout))
    if Input.BarOrder is not None:
        Updates.append("BarOrder = ?")
        Params.append(",".join(Input.BarOrder))

    if Updates:
        ExecuteQuery(
            f"UPDATE Settings SET {', '.join(Updates)} WHERE UserId = ?;",
            [*Params, UserId]
        )

    return GetUserSettings(UserId)
