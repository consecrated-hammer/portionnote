"""
Service for generating AI-powered nutrition recommendations based on user profile.
"""
import json
from datetime import datetime
from typing import Optional

from app.config import Settings
from app.services.openai_client import GetOpenAiContent


class NutritionRecommendation:
    """Recommended nutrition targets from AI."""
    
    def __init__(
        self,
        DailyCalorieTarget: int,
        ProteinTargetMin: float,
        ProteinTargetMax: float,
        FibreTarget: Optional[float] = None,
        CarbsTarget: Optional[float] = None,
        FatTarget: Optional[float] = None,
        SaturatedFatTarget: Optional[float] = None,
        SugarTarget: Optional[float] = None,
        SodiumTarget: Optional[float] = None,
        Explanation: str = ""
    ):
        self.DailyCalorieTarget = DailyCalorieTarget
        self.ProteinTargetMin = ProteinTargetMin
        self.ProteinTargetMax = ProteinTargetMax
        self.FibreTarget = FibreTarget
        self.CarbsTarget = CarbsTarget
        self.FatTarget = FatTarget
        self.SaturatedFatTarget = SaturatedFatTarget
        self.SugarTarget = SugarTarget
        self.SodiumTarget = SodiumTarget
        self.Explanation = Explanation

    def ToDict(self) -> dict:
        return {
            "DailyCalorieTarget": self.DailyCalorieTarget,
            "ProteinTargetMin": self.ProteinTargetMin,
            "ProteinTargetMax": self.ProteinTargetMax,
            "FibreTarget": self.FibreTarget,
            "CarbsTarget": self.CarbsTarget,
            "FatTarget": self.FatTarget,
            "SaturatedFatTarget": self.SaturatedFatTarget,
            "SugarTarget": self.SugarTarget,
            "SodiumTarget": self.SodiumTarget,
            "Explanation": self.Explanation
        }


def CalculateAge(BirthDate: str) -> int:
    """Calculate age from birthdate string (YYYY-MM-DD)."""
    Birth = datetime.strptime(BirthDate, "%Y-%m-%d")
    Today = datetime.now()
    Age = Today.year - Birth.year - ((Today.month, Today.day) < (Birth.month, Birth.day))
    return Age


def GetAiNutritionRecommendations(
    Age: int,
    HeightCm: int,
    WeightKg: float,
    ActivityLevel: str
) -> NutritionRecommendation:
    """
    Get personalized nutrition recommendations from AI based on user profile.
    
    Args:
        Age: User's age in years
        HeightCm: User's height in centimeters
        WeightKg: User's current weight in kilograms
        ActivityLevel: Activity level (sedentary, lightly_active, moderately_active, very_active, extra_active)
    
    Returns:
        NutritionRecommendation with personalized targets
    
    Raises:
        ValueError: If OpenAI API key not configured or invalid response
    """
    if not Settings.OpenAiApiKey:
        raise ValueError("OpenAI API key not configured.")

    SystemPrompt = """You are a nutrition and fitness expert. Given a person's age, height, weight, and activity level, provide personalized daily nutrition targets.

Return ONLY a JSON object with these exact fields:
{
  "DailyCalorieTarget": integer (daily calories),
  "ProteinTargetMin": float (grams),
  "ProteinTargetMax": float (grams),
  "FibreTarget": float (grams),
  "CarbsTarget": float (grams),
  "FatTarget": float (grams),
  "SaturatedFatTarget": float (grams, max),
  "SugarTarget": float (grams, max),
  "SodiumTarget": float (mg, max),
  "Explanation": "Brief explanation of recommendations (2-3 sentences)"
}

Base your recommendations on:
- Basal Metabolic Rate (BMR) + activity level
- Standard macronutrient ratios for balanced diet
- General health guidelines (WHO, dietary guidelines)
- Protein: 0.8-2.0g per kg body weight depending on activity
- Fibre: 25-35g per day
- Saturated fat: <10% of calories
- Sugar: <50g per day
- Sodium: <2300mg per day"""

    UserPrompt = f"""User profile:
- Age: {Age} years
- Height: {HeightCm} cm
- Weight: {WeightKg} kg
- Activity Level: {ActivityLevel}

Provide personalized daily nutrition targets."""

    Content = GetOpenAiContent(
        [
            {"role": "system", "content": SystemPrompt},
            {"role": "user", "content": UserPrompt}
        ],
        Temperature=0.3,
        MaxTokens=600
    )
    
    if not Content:
        raise ValueError("No response from AI.")

    # Parse JSON response
    try:
        # Handle markdown code blocks if present
        if "```json" in Content:
            Content = Content.split("```json")[1].split("```")[0].strip()
        elif "```" in Content:
            Content = Content.split("```")[1].split("```")[0].strip()
        
        RecommendationData = json.loads(Content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid AI response format: {e}")

    return NutritionRecommendation(
        DailyCalorieTarget=int(RecommendationData.get("DailyCalorieTarget", 2000)),
        ProteinTargetMin=float(RecommendationData.get("ProteinTargetMin", 60)),
        ProteinTargetMax=float(RecommendationData.get("ProteinTargetMax", 120)),
        FibreTarget=float(RecommendationData.get("FibreTarget", 30)) if RecommendationData.get("FibreTarget") else None,
        CarbsTarget=float(RecommendationData.get("CarbsTarget", 250)) if RecommendationData.get("CarbsTarget") else None,
        FatTarget=float(RecommendationData.get("FatTarget", 70)) if RecommendationData.get("FatTarget") else None,
        SaturatedFatTarget=float(RecommendationData.get("SaturatedFatTarget", 20)) if RecommendationData.get("SaturatedFatTarget") else None,
        SugarTarget=float(RecommendationData.get("SugarTarget", 50)) if RecommendationData.get("SugarTarget") else None,
        SodiumTarget=float(RecommendationData.get("SodiumTarget", 2300)) if RecommendationData.get("SodiumTarget") else None,
        Explanation=RecommendationData.get("Explanation", "Personalized recommendations based on your profile.")
    )
