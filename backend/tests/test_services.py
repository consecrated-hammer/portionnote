import pytest

from app.models.schemas import (
    CreateDailyLogInput,
    CreateFoodInput,
    CreateMealEntryInput,
    MealType
)
from app.services.daily_logs_service import (
    CreateMealEntry,
    DeleteMealEntry,
    GetDailyLogByDate,
    GetEntriesForLog,
    GetSettings,
    UpdateSteps,
    UpsertDailyLog
)
from app.services.foods_service import GetFoods, UpsertFood
from app.services.summary_service import GetWeeklySummary
from app.utils.database import FetchOne


def test_get_settings_defaults_when_empty(test_user_id):
    Settings = GetSettings(test_user_id)

    assert Settings.DailyCalorieTarget == 1498
    assert Settings.ProteinTargetMin == 70
    assert Settings.ProteinTargetMax == 188
    assert Settings.StepKcalFactor == 0.04
    assert Settings.StepTarget == 8500


def test_foods_upsert_and_list(test_user_id):
    FoodInput = CreateFoodInput(
        FoodName="Overnight Oats",
        ServingDescription="1 bowl",
        CaloriesPerServing=280,
        ProteinPerServing=18,
        IsFavourite=True
    )

    Created = UpsertFood(test_user_id, FoodInput)
    Foods = GetFoods(test_user_id)

    assert Created.FoodName == "Overnight Oats"
    assert Created.IsFavourite is True
    assert len(Foods) == 1
    assert Foods[0].FoodName == "Overnight Oats"


def test_daily_log_flow_with_entries(test_user_id):
    Food = UpsertFood(
        test_user_id,
        CreateFoodInput(
            FoodName="Protein Bowl",
            ServingDescription="1 bowl",
            CaloriesPerServing=420,
            ProteinPerServing=36,
            IsFavourite=False
        )
    )

    DailyLog = UpsertDailyLog(
        test_user_id,
        CreateDailyLogInput(
            LogDate="2024-01-04",
            Steps=2000,
            StepKcalFactorOverride=0.05,
            Notes="Morning lift"
        )
    )

    Fetched = GetDailyLogByDate(test_user_id, "2024-01-04")

    assert Fetched is not None
    assert Fetched.DailyLogId == DailyLog.DailyLogId
    assert Fetched.StepKcalFactorOverride == 0.05

    Updated = UpdateSteps(test_user_id, "2024-01-04", 3200, 0.06)
    assert Updated.Steps == 3200
    assert Updated.StepKcalFactorOverride == 0.06

    MealEntry = CreateMealEntry(
        test_user_id,
        CreateMealEntryInput(
            DailyLogId=DailyLog.DailyLogId,
            MealType=MealType.Breakfast,
            FoodId=Food.FoodId,
            Quantity=1.5,
            EntryNotes="Post workout",
            SortOrder=1
        )
    )

    Entries = GetEntriesForLog(test_user_id, DailyLog.DailyLogId)

    assert MealEntry.MealEntryId == Entries[0].MealEntryId
    assert Entries[0].FoodName == "Protein Bowl"
    assert Entries[0].Quantity == 1.5

    DeleteMealEntry(test_user_id, MealEntry.MealEntryId)
    EntriesAfterDelete = GetEntriesForLog(test_user_id, DailyLog.DailyLogId)
    assert EntriesAfterDelete == []


def test_weekly_summary_calculation(seeded_db):
    AdminUserId = seeded_db
    Food = UpsertFood(
        AdminUserId,
        CreateFoodInput(
            FoodName="Grain Bowl",
            ServingDescription="1 bowl",
            CaloriesPerServing=200,
            ProteinPerServing=25,
            IsFavourite=False
        )
    )

    LogOne = UpsertDailyLog(
        AdminUserId,
        CreateDailyLogInput(
            LogDate="2024-01-01",
            Steps=1000,
            StepKcalFactorOverride=None
        )
    )
    LogTwo = UpsertDailyLog(
        AdminUserId,
        CreateDailyLogInput(
            LogDate="2024-01-02",
            Steps=2000,
            StepKcalFactorOverride=0.05
        )
    )

    CreateMealEntry(
        AdminUserId,
        CreateMealEntryInput(
            DailyLogId=LogOne.DailyLogId,
            MealType=MealType.Lunch,
            FoodId=Food.FoodId,
            Quantity=1,
            EntryNotes=None,
            SortOrder=0
        )
    )
    CreateMealEntry(
        AdminUserId,
        CreateMealEntryInput(
            DailyLogId=LogTwo.DailyLogId,
            MealType=MealType.Dinner,
            FoodId=Food.FoodId,
            Quantity=2,
            EntryNotes=None,
            SortOrder=0
        )
    )

    Summary = GetWeeklySummary(AdminUserId, "2024-01-01")

    assert Summary.Totals["TotalCalories"] == 600
    assert Summary.Totals["TotalProtein"] == 75
    assert Summary.Totals["TotalSteps"] == 3000
    assert Summary.Totals["TotalNetCalories"] == 460
    assert Summary.Averages["AverageCalories"] == 300
    assert Summary.Averages["AverageProtein"] == 37.5
    assert Summary.Averages["AverageSteps"] == 1500


def test_weight_log_updates_user_weight_latest_date(test_user_id):
    UpsertDailyLog(
        test_user_id,
        CreateDailyLogInput(
            LogDate="2025-12-24",
            Steps=0,
            WeightKg=100.0
        )
    )

    UpsertDailyLog(
        test_user_id,
        CreateDailyLogInput(
            LogDate="2025-12-23",
            Steps=0,
            WeightKg=99.9
        )
    )

    UpsertDailyLog(
        test_user_id,
        CreateDailyLogInput(
            LogDate="2025-12-22",
            Steps=0,
            WeightKg=101.5
        )
    )

    Row = FetchOne(
        "SELECT WeightKg AS WeightKg FROM Users WHERE UserId = ?;",
        [test_user_id]
    )
    assert Row is not None
    assert Row["WeightKg"] == pytest.approx(100.0)
