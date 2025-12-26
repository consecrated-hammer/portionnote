import pytest

from app.models.schemas import CreateDailyLogInput, CreateFoodInput, CreateMealEntryInput, MealType, ScheduleSlotInput
from app.services.daily_logs_service import CreateMealEntry, GetEntriesForLog, UpsertDailyLog
from app.services.foods_service import UpsertFood
from app.services.schedule_service import GetScheduleSlots, UpdateScheduleSlots


def test_schedule_slots_update_and_remove(test_user_id):
    Slots = UpdateScheduleSlots(
        test_user_id,
        [
            ScheduleSlotInput(
                SlotName="Morning snack",
                SlotTime="10:00",
                MealType=MealType.Snack1,
                SortOrder=0
            ),
            ScheduleSlotInput(
                SlotName="Lunch break",
                SlotTime="12:30",
                MealType=MealType.Lunch,
                SortOrder=1
            )
        ]
    )

    assert len(Slots) == 2
    FirstSlotId = Slots[0].ScheduleSlotId
    SecondSlotId = Slots[1].ScheduleSlotId

    Food = UpsertFood(
        test_user_id,
        CreateFoodInput(
            FoodName="Fruit cup",
            ServingDescription="1 cup",
            CaloriesPerServing=120,
            ProteinPerServing=2,
            IsFavourite=False
        )
    )

    DailyLog = UpsertDailyLog(
        test_user_id,
        CreateDailyLogInput(
            LogDate="2024-02-01",
            Steps=1000,
            StepKcalFactorOverride=None
        )
    )

    CreateMealEntry(
        test_user_id,
        CreateMealEntryInput(
            DailyLogId=DailyLog.DailyLogId,
            MealType=MealType.Snack1,
            FoodId=Food.FoodId,
            Quantity=1,
            EntryNotes=None,
            SortOrder=0,
            ScheduleSlotId=FirstSlotId
        )
    )

    Entries = GetEntriesForLog(test_user_id, DailyLog.DailyLogId)
    assert Entries[0].ScheduleSlotId == FirstSlotId

    UpdateScheduleSlots(
        test_user_id,
        [
            ScheduleSlotInput(
                ScheduleSlotId=SecondSlotId,
                SlotName="Lunch break",
                SlotTime="12:30",
                MealType=MealType.Lunch,
                SortOrder=0
            )
        ]
    )

    EntriesAfterRemove = GetEntriesForLog(test_user_id, DailyLog.DailyLogId)
    assert EntriesAfterRemove[0].ScheduleSlotId is None
    assert len(GetScheduleSlots(test_user_id)) == 1


def test_schedule_rejects_invalid_time(test_user_id):
    with pytest.raises(ValueError):
        UpdateScheduleSlots(
            test_user_id,
            [
                ScheduleSlotInput(
                    SlotName="Bad time",
                    SlotTime="25:70",
                    MealType=MealType.Breakfast,
                    SortOrder=0
                )
            ]
        )
