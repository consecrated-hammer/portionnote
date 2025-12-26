"""Tests for nutrition recommendations service."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.nutrition_recommendations_service import (
    CalculateAge,
    GetAiNutritionRecommendations,
    NutritionRecommendation,
)


def test_calculate_age():
    """Test age calculation from birthdate."""
    # Test with specific dates - just test the actual function
    # Person born in 1990, checked in 2024 (after birthday)
    BirthDate = "1990-01-01"
    Age = CalculateAge(BirthDate)
    # Age should be based on current year minus 1990
    CurrentYear = datetime.now().year
    ExpectedAge = CurrentYear - 1990
    assert Age >= ExpectedAge - 1 and Age <= ExpectedAge  # Allow for before/after birthday

    # Test younger person
    BirthDate2 = "2000-06-15"
    Age2 = CalculateAge(BirthDate2)
    ExpectedAge2 = CurrentYear - 2000
    assert Age2 >= ExpectedAge2 - 1 and Age2 <= ExpectedAge2


def test_get_ai_nutrition_recommendations_success(monkeypatch):
    """Test successful AI nutrition recommendations."""
    Age = 34
    HeightCm = 175
    WeightKg = 75.0
    ActivityLevel = "moderately_active"

    MockResponse = MagicMock()
    MockResponse.status_code = 200
    MockResponse.raise_for_status = MagicMock()
    MockResponse.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": """```json
{
  "DailyCalorieTarget": 2500,
  "ProteinTargetMin": 94,
  "ProteinTargetMax": 150,
  "FibreTarget": 30,
  "CarbsTarget": 280,
  "FatTarget": 85,
  "SaturatedFatTarget": 25,
  "SugarTarget": 50,
  "SodiumTarget": 2300,
  "Explanation": "Your moderately active lifestyle with regular exercise requires adequate calories to support your training and recovery."
}
```"""
                }
            }
        ]
    }

    with patch("app.services.nutrition_recommendations_service.httpx.post", return_value=MockResponse):
        Result = GetAiNutritionRecommendations(Age, HeightCm, WeightKg, ActivityLevel)

        assert isinstance(Result, NutritionRecommendation)
        assert Result.DailyCalorieTarget == 2500
        assert Result.ProteinTargetMin == 94
        assert Result.ProteinTargetMax == 150
        assert Result.FibreTarget == 30
        assert Result.CarbsTarget == 280
        assert Result.FatTarget == 85
        assert Result.SaturatedFatTarget == 25
        assert Result.SugarTarget == 50
        assert Result.SodiumTarget == 2300
        assert "moderately active lifestyle" in Result.Explanation


def test_get_ai_nutrition_recommendations_minimal(monkeypatch):
    """Test AI recommendations with only required fields."""
    Age = 29
    HeightCm = 160
    WeightKg = 55.0
    ActivityLevel = "sedentary"

    MockResponse = MagicMock()
    MockResponse.status_code = 200
    MockResponse.raise_for_status = MagicMock()
    MockResponse.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": """{
  "DailyCalorieTarget": 1600,
  "ProteinTargetMin": 55,
  "ProteinTargetMax": 88,
  "Explanation": "These targets support your maintenance needs with adequate protein."
}"""
                }
            }
        ]
    }

    with patch("app.services.nutrition_recommendations_service.httpx.post", return_value=MockResponse):
        Result = GetAiNutritionRecommendations(Age, HeightCm, WeightKg, ActivityLevel)

        assert isinstance(Result, NutritionRecommendation)
        assert Result.DailyCalorieTarget == 1600
        assert Result.ProteinTargetMin == 55
        assert Result.ProteinTargetMax == 88
        assert Result.FibreTarget is None
        assert Result.CarbsTarget is None
        assert Result.FatTarget is None


def test_get_ai_nutrition_recommendations_api_error(monkeypatch):
    """Test handling of OpenAI API errors."""
    Age = 34
    HeightCm = 175
    WeightKg = 75.0
    ActivityLevel = "moderately_active"

    MockResponse = MagicMock()
    MockResponse.status_code = 500
    MockResponse.raise_for_status.side_effect = Exception("OpenAI API error: 500")

    with patch("app.services.nutrition_recommendations_service.httpx.post", return_value=MockResponse):
        with pytest.raises(Exception) as ExcInfo:
            GetAiNutritionRecommendations(Age, HeightCm, WeightKg, ActivityLevel)

        assert "OpenAI API error" in str(ExcInfo.value)


def test_get_ai_nutrition_recommendations_invalid_response(monkeypatch):
    """Test handling of invalid AI response format."""
    Age = 34
    HeightCm = 175
    WeightKg = 75.0
    ActivityLevel = "moderately_active"

    MockResponse = MagicMock()
    MockResponse.status_code = 200
    MockResponse.raise_for_status = MagicMock()
    MockResponse.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "This is an invalid response without proper JSON."
                }
            }
        ]
    }

    with patch("app.services.nutrition_recommendations_service.httpx.post", return_value=MockResponse):
        with pytest.raises(ValueError) as ExcInfo:
            GetAiNutritionRecommendations(Age, HeightCm, WeightKg, ActivityLevel)

        assert "Invalid AI response format" in str(ExcInfo.value)


def test_get_ai_nutrition_recommendations_extra_active(monkeypatch):
    """Test recommendations for extra active user."""
    Age = 39
    HeightCm = 180
    WeightKg = 85.0
    ActivityLevel = "extra_active"

    MockResponse = MagicMock()
    MockResponse.status_code = 200
    MockResponse.raise_for_status = MagicMock()
    MockResponse.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": """```
{
  "DailyCalorieTarget": 3200,
  "ProteinTargetMin": 140,
  "ProteinTargetMax": 200,
  "FibreTarget": 35,
  "CarbsTarget": 400,
  "FatTarget": 100,
  "Explanation": "Your high activity level requires significant energy and recovery support."
}
```"""
                }
            }
        ]
    }

    with patch("app.services.nutrition_recommendations_service.httpx.post", return_value=MockResponse):
        Result = GetAiNutritionRecommendations(Age, HeightCm, WeightKg, ActivityLevel)

        assert Result.DailyCalorieTarget >= 3000
        assert Result.ProteinTargetMin >= 130
        assert "activity level" in Result.Explanation.lower()

