"""
Service for managing AI recommendation logs.
"""
from typing import Optional

from app.models.schemas import RecommendationLog
from app.services.nutrition_recommendations_service import NutritionRecommendation
from app.utils.database import GetConnection


def SaveRecommendationLog(
    UserId: str,
    Age: int,
    HeightCm: float,
    WeightKg: float,
    ActivityLevel: str,
    Recommendation: NutritionRecommendation
) -> int:
    """
    Save an AI recommendation to the logs table.
    
    Args:
        UserId: User ID
        Age: User's age at time of recommendation
        HeightCm: User's height in cm
        WeightKg: User's weight in kg
        ActivityLevel: User's activity level
        Recommendation: The AI recommendation result
    
    Returns:
        RecommendationLogId of the created log entry
    """
    Connection = GetConnection()
    Cursor = Connection.cursor()
    
    Cursor.execute("""
        INSERT INTO RecommendationLogs (
            UserId, Age, HeightCm, WeightKg, ActivityLevel,
            DailyCalorieTarget, ProteinTargetMin, ProteinTargetMax,
            FibreTarget, CarbsTarget, FatTarget, SaturatedFatTarget,
            SugarTarget, SodiumTarget, Explanation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        UserId, Age, HeightCm, WeightKg, ActivityLevel,
        Recommendation.DailyCalorieTarget,
        Recommendation.ProteinTargetMin,
        Recommendation.ProteinTargetMax,
        Recommendation.FibreTarget,
        Recommendation.CarbsTarget,
        Recommendation.FatTarget,
        Recommendation.SaturatedFatTarget,
        Recommendation.SugarTarget,
        Recommendation.SodiumTarget,
        Recommendation.Explanation
    ))
    
    Connection.commit()
    return Cursor.lastrowid


def GetRecommendationLogsByUser(UserId: str, Limit: int = 10) -> list[RecommendationLog]:
    """
    Get recommendation logs for a user, most recent first.
    
    Args:
        UserId: User ID
        Limit: Maximum number of logs to return (default 10)
    
    Returns:
        List of RecommendationLog objects
    """
    Connection = GetConnection()
    Cursor = Connection.cursor()
    
    Cursor.execute("""
        SELECT 
            RecommendationLogId, UserId, CreatedAt, Age, HeightCm, WeightKg, ActivityLevel,
            DailyCalorieTarget, ProteinTargetMin, ProteinTargetMax,
            FibreTarget, CarbsTarget, FatTarget, SaturatedFatTarget,
            SugarTarget, SodiumTarget, Explanation
        FROM RecommendationLogs
        WHERE UserId = ?
        ORDER BY CreatedAt DESC
        LIMIT ?
    """, (UserId, Limit))
    
    Rows = Cursor.fetchall()
    return [BuildRecommendationLogFromRow(Row) for Row in Rows]


def GetRecommendationLogById(RecommendationLogId: int) -> Optional[RecommendationLog]:
    """
    Get a specific recommendation log by ID.
    
    Args:
        RecommendationLogId: Log ID
    
    Returns:
        RecommendationLog or None if not found
    """
    Connection = GetConnection()
    Cursor = Connection.cursor()
    
    Cursor.execute("""
        SELECT 
            RecommendationLogId, UserId, CreatedAt, Age, HeightCm, WeightKg, ActivityLevel,
            DailyCalorieTarget, ProteinTargetMin, ProteinTargetMax,
            FibreTarget, CarbsTarget, FatTarget, SaturatedFatTarget,
            SugarTarget, SodiumTarget, Explanation
        FROM RecommendationLogs
        WHERE RecommendationLogId = ?
    """, (RecommendationLogId,))
    
    Row = Cursor.fetchone()
    return BuildRecommendationLogFromRow(Row) if Row else None


def BuildRecommendationLogFromRow(Row: tuple) -> RecommendationLog:
    """Build RecommendationLog object from database row."""
    return RecommendationLog(
        RecommendationLogId=Row[0],
        UserId=Row[1],
        CreatedAt=Row[2],
        Age=Row[3],
        HeightCm=Row[4],
        WeightKg=Row[5],
        ActivityLevel=Row[6],
        DailyCalorieTarget=Row[7],
        ProteinTargetMin=Row[8],
        ProteinTargetMax=Row[9],
        FibreTarget=Row[10],
        CarbsTarget=Row[11],
        FatTarget=Row[12],
        SaturatedFatTarget=Row[13],
        SugarTarget=Row[14],
        SodiumTarget=Row[15],
        Explanation=Row[16]
    )
