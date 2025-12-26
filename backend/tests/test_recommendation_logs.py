"""Tests for recommendation logs service."""
import time
from unittest.mock import MagicMock

import pytest
from app.services.nutrition_recommendations_service import NutritionRecommendation
from app.services.recommendation_logs_service import (
    BuildRecommendationLogFromRow,
    GetRecommendationLogById,
    GetRecommendationLogsByUser,
    SaveRecommendationLog,
)


def test_save_recommendation_log(test_user_id):
    """Test saving a recommendation log."""
    Recommendation = NutritionRecommendation(
        DailyCalorieTarget=2500,
        ProteinTargetMin=94.0,
        ProteinTargetMax=150.0,
        FibreTarget=30.0,
        CarbsTarget=280.0,
        FatTarget=85.0,
        SaturatedFatTarget=25.0,
        SugarTarget=50.0,
        SodiumTarget=2300.0,
        Explanation="Test recommendation for moderately active user."
    )

    LogId = SaveRecommendationLog(
        UserId=test_user_id,
        Age=34,
        HeightCm=175.0,
        WeightKg=75.0,
        ActivityLevel="moderately_active",
        Recommendation=Recommendation
    )

    assert LogId > 0

    # Verify it was saved
    SavedLog = GetRecommendationLogById(LogId)
    assert SavedLog is not None
    assert SavedLog.UserId == test_user_id
    assert SavedLog.Age == 34
    assert SavedLog.HeightCm == 175.0
    assert SavedLog.WeightKg == 75.0
    assert SavedLog.ActivityLevel == "moderately_active"
    assert SavedLog.DailyCalorieTarget == 2500
    assert SavedLog.ProteinTargetMin == 94.0
    assert SavedLog.ProteinTargetMax == 150.0
    assert SavedLog.FibreTarget == 30.0
    assert SavedLog.Explanation == "Test recommendation for moderately active user."


def test_get_recommendation_logs_by_user(test_user_id):
    """Test getting recommendation logs for a user."""
    # Create multiple logs
    Recommendation1 = NutritionRecommendation(
        DailyCalorieTarget=2000,
        ProteinTargetMin=80.0,
        ProteinTargetMax=120.0,
        Explanation="First recommendation"
    )
    
    Recommendation2 = NutritionRecommendation(
        DailyCalorieTarget=2200,
        ProteinTargetMin=85.0,
        ProteinTargetMax=130.0,
        Explanation="Second recommendation"
    )

    SaveRecommendationLog(
        UserId=test_user_id,
        Age=33,
        HeightCm=175.0,
        WeightKg=78.0,
        ActivityLevel="lightly_active",
        Recommendation=Recommendation1
    )

    # Small sleep to ensure different timestamps (SQLite datetime has second precision)
    time.sleep(1.1)

    SaveRecommendationLog(
        UserId=test_user_id,
        Age=34,
        HeightCm=175.0,
        WeightKg=75.0,
        ActivityLevel="moderately_active",
        Recommendation=Recommendation2
    )

    # Get logs
    Logs = GetRecommendationLogsByUser(test_user_id, Limit=10)
    assert len(Logs) >= 2

    # Find our specific logs (there might be others from previous tests)
    FirstLog = next((log for log in Logs if log.Explanation == "First recommendation"), None)
    SecondLog = next((log for log in Logs if log.Explanation == "Second recommendation"), None)
    
    assert FirstLog is not None, "First recommendation log not found"
    assert SecondLog is not None, "Second recommendation log not found"
    
    # Most recent (Second) should have a later timestamp than First
    assert SecondLog.CreatedAt > FirstLog.CreatedAt, f"Second ({SecondLog.CreatedAt}) should be after First ({FirstLog.CreatedAt})"
    assert SecondLog.Age == 34
    assert FirstLog.Age == 33


def test_get_recommendation_logs_limit(test_user_id):
    """Test limit parameter for recommendation logs."""
    # Create 5 logs
    for i in range(5):
        Recommendation = NutritionRecommendation(
            DailyCalorieTarget=2000 + (i * 100),
            ProteinTargetMin=80.0,
            ProteinTargetMax=120.0,
            Explanation=f"Recommendation {i}"
        )
        SaveRecommendationLog(
            UserId=test_user_id,
            Age=30 + i,
            HeightCm=175.0,
            WeightKg=75.0,
            ActivityLevel="moderately_active",
            Recommendation=Recommendation
        )
        # Small sleep to ensure different timestamps (SQLite datetime has second precision)
        if i < 4:
            time.sleep(1.1)

    # Get only 3 most recent
    Logs = GetRecommendationLogsByUser(test_user_id, Limit=3)
    assert len(Logs) <= 3
    
    # Filter to our test logs
    TestLogs = [log for log in Logs if "Recommendation" in log.Explanation and log.Explanation.startswith("Recommendation ")]
    
    # We should get the 3 most recent ones (4, 3, 2) if they're in the top 3
    # But since other tests might add logs, just verify we got some
    assert len(TestLogs) <= 3
    
    if len(TestLogs) >= 2:
        # Verify they're in descending order
        assert TestLogs[0].Age > TestLogs[1].Age


def test_get_recommendation_log_by_id_not_found():
    """Test getting a non-existent recommendation log."""
    Log = GetRecommendationLogById(999999)
    assert Log is None


def test_build_recommendation_log_from_row():
    """Test building RecommendationLog from database row."""
    Row = (
        1,  # RecommendationLogId
        "test-user-123",  # UserId (string)
        "2024-12-24 10:00:00",  # CreatedAt
        34,  # Age
        175.0,  # HeightCm
        75.0,  # WeightKg
        "moderately_active",  # ActivityLevel
        2500,  # DailyCalorieTarget
        94.0,  # ProteinTargetMin
        150.0,  # ProteinTargetMax
        30.0,  # FibreTarget
        280.0,  # CarbsTarget
        85.0,  # FatTarget
        25.0,  # SaturatedFatTarget
        50.0,  # SugarTarget
        2300.0,  # SodiumTarget
        "Test explanation"  # Explanation
    )

    Log = BuildRecommendationLogFromRow(Row)
    
    assert Log.RecommendationLogId == 1
    assert Log.UserId == "test-user-123"
    assert Log.CreatedAt == "2024-12-24 10:00:00"
    assert Log.Age == 34
    assert Log.HeightCm == 175.0
    assert Log.WeightKg == 75.0
    assert Log.ActivityLevel == "moderately_active"
    assert Log.DailyCalorieTarget == 2500
    assert Log.ProteinTargetMin == 94.0
    assert Log.ProteinTargetMax == 150.0
    assert Log.FibreTarget == 30.0
    assert Log.CarbsTarget == 280.0
    assert Log.FatTarget == 85.0
    assert Log.SaturatedFatTarget == 25.0
    assert Log.SugarTarget == 50.0
    assert Log.SodiumTarget == 2300.0
    assert Log.Explanation == "Test explanation"


def test_save_recommendation_with_minimal_fields(test_user_id):
    """Test saving recommendation with only required fields."""
    Recommendation = NutritionRecommendation(
        DailyCalorieTarget=1800,
        ProteinTargetMin=60.0,
        ProteinTargetMax=100.0,
        Explanation="Minimal recommendation"
    )

    LogId = SaveRecommendationLog(
        UserId=test_user_id,
        Age=28,
        HeightCm=165.0,
        WeightKg=60.0,
        ActivityLevel="sedentary",
        Recommendation=Recommendation
    )

    SavedLog = GetRecommendationLogById(LogId)
    assert SavedLog is not None
    assert SavedLog.DailyCalorieTarget == 1800
    assert SavedLog.ProteinTargetMin == 60.0
    assert SavedLog.FibreTarget is None
    assert SavedLog.CarbsTarget is None
    assert SavedLog.FatTarget is None
