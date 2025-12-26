from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import RequireUser
from app.models.schemas import (
    NutritionRecommendationResponse,
    RecommendationLogListResponse,
    UpdateSettingsInput,
    User,
    UserSettings
)
from app.services.nutrition_recommendations_service import (
    CalculateAge,
    GetAiNutritionRecommendations
)
from app.services.recommendation_logs_service import (
    GetRecommendationLogsByUser,
    SaveRecommendationLog
)
from app.services.settings_service import GetUserSettings, UpdateUserSettings

SettingsRouter = APIRouter()


@SettingsRouter.get("/", response_model=UserSettings, tags=["Settings"])
async def GetSettingsRoute(CurrentUser: User = Depends(RequireUser)):
    return GetUserSettings(CurrentUser.UserId)


@SettingsRouter.put("/", response_model=UserSettings, tags=["Settings"])
async def UpdateSettingsRoute(
    Input: UpdateSettingsInput,
    CurrentUser: User = Depends(RequireUser)
):
    try:
        return UpdateUserSettings(CurrentUser.UserId, Input)
    except Exception as ErrorValue:
        raise HTTPException(status_code=400, detail="Failed to update settings.") from ErrorValue


@SettingsRouter.post("/ai-recommendations", response_model=NutritionRecommendationResponse, tags=["Settings"])
async def GetAiRecommendations(CurrentUser: User = Depends(RequireUser)):
    """Get AI-powered nutrition recommendations based on user profile."""
    # Validate required fields
    if not CurrentUser.BirthDate:
        raise HTTPException(status_code=400, detail="Birthdate is required for recommendations.")
    if not CurrentUser.HeightCm:
        raise HTTPException(status_code=400, detail="Height is required for recommendations.")
    if not CurrentUser.WeightKg:
        raise HTTPException(status_code=400, detail="Weight is required for recommendations.")
    if not CurrentUser.ActivityLevel:
        raise HTTPException(status_code=400, detail="Activity level is required for recommendations.")
    
    try:
        Age = CalculateAge(CurrentUser.BirthDate)
        Recommendation, ModelUsed = GetAiNutritionRecommendations(
            Age=Age,
            HeightCm=CurrentUser.HeightCm,
            WeightKg=CurrentUser.WeightKg,
            ActivityLevel=CurrentUser.ActivityLevel
        )
        
        # Save recommendation to logs
        SaveRecommendationLog(
            UserId=CurrentUser.UserId,
            Age=Age,
            HeightCm=CurrentUser.HeightCm,
            WeightKg=CurrentUser.WeightKg,
            ActivityLevel=CurrentUser.ActivityLevel,
            Recommendation=Recommendation
        )
        
        ResponseData = Recommendation.ToDict()
        ResponseData["ModelUsed"] = ModelUsed
        return NutritionRecommendationResponse(**ResponseData)
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail="Failed to generate recommendations.") from ErrorValue


@SettingsRouter.get("/ai-recommendations/history", response_model=RecommendationLogListResponse, tags=["Settings"])
async def GetRecommendationHistory(CurrentUser: User = Depends(RequireUser), Limit: int = 10):
    """Get user's AI recommendation history."""
    try:
        Logs = GetRecommendationLogsByUser(CurrentUser.UserId, Limit)
        return RecommendationLogListResponse(Logs=Logs)
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail="Failed to retrieve recommendation history.") from ErrorValue
