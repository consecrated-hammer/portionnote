import json

import pytest

from app.config import Settings
from app.models.schemas import CreateDailyLogInput, CreateFoodInput, CreateMealEntryInput, MealType
from app.services.ai_suggestions_service import BuildAiPrompt, GetAiSuggestions, ParseAiSuggestions
from app.services.daily_logs_service import CreateMealEntry, UpsertDailyLog
from app.services.foods_service import UpsertFood


def test_ai_suggestions_requires_api_key(test_user_id):
    OriginalKey = Settings.OpenAiApiKey
    Settings.OpenAiApiKey = None

    try:
        with pytest.raises(ValueError):
            GetAiSuggestions(test_user_id, "2024-01-01")
    finally:
        Settings.OpenAiApiKey = OriginalKey


def test_ai_prompt_and_parse():
    Prompt = BuildAiPrompt("2024-01-01", 1000, [], {"DailyCalorieTarget": 1500})
    assert "Log date" in Prompt

    Suggestions = ParseAiSuggestions(json.dumps([
        {"Title": "Hydrate", "Detail": "Drink water early."}
    ]))
    assert Suggestions[0].Title == "Hydrate"

    with pytest.raises(ValueError):
        ParseAiSuggestions("{bad json")


def test_get_ai_suggestions_success(monkeypatch, test_user_id):
    OriginalKey = Settings.OpenAiApiKey
    OriginalModel = Settings.OpenAiModel
    OriginalUrl = Settings.OpenAiBaseUrl
    Settings.OpenAiApiKey = "test-key"
    Settings.OpenAiModel = "test-model"
    Settings.OpenAiBaseUrl = "http://test"

    Food = UpsertFood(
        test_user_id,
        CreateFoodInput(
            FoodName="Yogurt",
            ServingDescription="1 cup",
            CaloriesPerServing=120,
            ProteinPerServing=10,
            IsFavourite=False
        )
    )
    DailyLog = UpsertDailyLog(
        test_user_id,
        CreateDailyLogInput(
            LogDate="2024-01-02",
            Steps=1500,
            StepKcalFactorOverride=None
        )
    )
    CreateMealEntry(
        test_user_id,
        CreateMealEntryInput(
            DailyLogId=DailyLog.DailyLogId,
            MealType=MealType.Breakfast,
            FoodId=Food.FoodId,
            Quantity=1,
            EntryNotes=None,
            SortOrder=0
        )
    )

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps([
                                {"Title": "Add protein", "Detail": "Aim for 20g at breakfast."}
                            ])
                        }
                    }
                ]
            }

    def DummyPost(*_args, **_kwargs):
        return DummyResponse()

    monkeypatch.setattr("app.services.ai_suggestions_service.httpx.post", DummyPost)

    try:
        Suggestions = GetAiSuggestions(test_user_id, "2024-01-02")
        assert Suggestions[0].SuggestionType == "AiSuggestion"
    finally:
        Settings.OpenAiApiKey = OriginalKey
        Settings.OpenAiModel = OriginalModel
        Settings.OpenAiBaseUrl = OriginalUrl
