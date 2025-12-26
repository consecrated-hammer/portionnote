import json

from app.models.schemas import UpdateSettingsInput
from app.services.settings_service import GetUserSettings, UpdateUserSettings
from app.utils.database import ExecuteQuery
from app.utils.defaults import DefaultTodayLayout


def test_settings_defaults_when_missing(test_user_id):
    Settings = GetUserSettings(test_user_id)
    assert Settings.Targets.DailyCalorieTarget == 1498
    assert Settings.TodayLayout == DefaultTodayLayout


def test_update_settings_creates_row_and_updates_layout(test_user_id):
    Updated = UpdateUserSettings(
        test_user_id,
        UpdateSettingsInput(
            DailyCalorieTarget=1600,
            ProteinTargetMin=80,
            ProteinTargetMax=170,
            StepKcalFactor=0.05,
            StepTarget=9000,
            TodayLayout=["quickadd", "snapshot", "checkins"]
        )
    )

    assert Updated.Targets.DailyCalorieTarget == 1600
    assert Updated.Targets.StepTarget == 9000
    assert Updated.TodayLayout == ["quickadd", "snapshot", "checkins"]


def test_settings_fallback_on_invalid_layout_json(test_user_id):
    UpdateUserSettings(test_user_id, UpdateSettingsInput())
    ExecuteQuery(
        "UPDATE Settings SET TodayLayout = ? WHERE UserId = ?;",
        [json.dumps({"bad": "layout"}), test_user_id]
    )

    Settings = GetUserSettings(test_user_id)
    assert Settings.TodayLayout == DefaultTodayLayout
