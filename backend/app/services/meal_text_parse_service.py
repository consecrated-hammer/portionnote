import json
from typing import Any

from app.config import Settings
from app.services.openai_client import GetOpenAiContentWithModel
from app.services.serving_conversion_service import NormalizeUnit


def _TryParseMealTotals(Content: str) -> dict[str, Any] | None:
    if not Content:
        return None
    Cleaned = Content.strip()
    if "```json" in Cleaned:
        Cleaned = Cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in Cleaned:
        Cleaned = Cleaned.split("```")[1].split("```")[0].strip()

    try:
        Parsed = json.loads(Cleaned)
    except json.JSONDecodeError:
        Parsed = None

    if isinstance(Parsed, dict):
        return Parsed

    Start = Cleaned.find("{")
    End = Cleaned.rfind("}")
    if Start != -1 and End != -1 and End > Start:
        Candidate = Cleaned[Start:End + 1]
        try:
            Parsed = json.loads(Candidate)
        except json.JSONDecodeError:
            return None
        if isinstance(Parsed, dict):
            return Parsed

    return None


def _NormalizeUnitValue(Unit: str) -> str:
    Normalized = NormalizeUnit(Unit)
    if Normalized == "ml":
        return "mL"
    if Normalized == "l":
        return "L"
    return Normalized or "serving"


def ParseMealText(Text: str, KnownFoods: list[str] | None = None) -> dict[str, Any]:
    if not Settings.OpenAiApiKey:
        raise ValueError("OpenAI API key not configured.")

    KnownFoodsList = KnownFoods or []
    KnownFoodsList = [Item for Item in KnownFoodsList if isinstance(Item, str) and Item.strip()]
    KnownFoodsList = KnownFoodsList[:200]
    KnownFoodsText = "\n".join(f"- {Item}" for Item in KnownFoodsList)

    SystemPrompt = """
You are a nutrition assistant. Given a free text meal entry, return total nutrition for the whole meal.

Return ONLY a JSON object with:
{
  "MealName": "string",
  "ServingQuantity": 1.0,
  "ServingUnit": "serving",
  "CaloriesPerServing": integer,
  "ProteinPerServing": float,
  "FibrePerServing": float or null,
  "CarbsPerServing": float or null,
  "FatPerServing": float or null,
  "SaturatedFatPerServing": float or null,
  "SugarPerServing": float or null,
  "SodiumPerServing": float or null,
  "Summary": "short explanation, no em dashes"
}

Rules:
- Treat the input as a single meal. Do not list ingredients.
- Prefer metric when estimating.
- If this is an estimate, start Summary with "AI estimate.".
- Use ServingQuantity 1 and ServingUnit "serving".
- Do not include extra text or markdown.
- Keep Summary under 200 characters.
- Populate Fibre, Carbs, Fat, SaturatedFat, Sugar, and Sodium when possible.
""".strip()

    if KnownFoodsText:
        SystemPrompt += "\n\nKnown foods (for name familiarity only):\n" + KnownFoodsText

    UserPrompt = f"Meal entry:\n{Text.strip()}"

    Content, ModelUsed = GetOpenAiContentWithModel(
        [
            {"role": "system", "content": SystemPrompt},
            {"role": "user", "content": UserPrompt}
        ],
        Temperature=0.2,
        MaxTokens=1400,
        ReasoningEffort="medium",
        TextVerbosity="low"
    )

    Data = _TryParseMealTotals(Content)
    if Data is None:
        RetryPrompt = "Return ONLY the JSON object. No extra text."
        RetryContent, _RetryModelUsed = GetOpenAiContentWithModel(
            [
                {"role": "system", "content": RetryPrompt},
                {"role": "user", "content": Content}
            ],
            Temperature=0.1,
            MaxTokens=800,
            ReasoningEffort="medium",
            TextVerbosity="low"
        )
        Data = _TryParseMealTotals(RetryContent)

    if Data is None:
        raise ValueError("Invalid AI response format.")

    MealName = str(Data.get("MealName", "AI meal")).strip() or "AI meal"
    ServingQuantity = Data.get("ServingQuantity", 1.0)
    ServingUnit = _NormalizeUnitValue(str(Data.get("ServingUnit", "serving")))

    try:
        ServingQuantity = float(ServingQuantity)
    except (TypeError, ValueError):
        ServingQuantity = 1.0

    def _to_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    Calories = Data.get("CaloriesPerServing", 0)
    try:
        CaloriesValue = int(float(Calories))
    except (TypeError, ValueError):
        CaloriesValue = 0

    Summary = str(Data.get("Summary", "AI estimate." if CaloriesValue == 0 else "")).strip()
    if not Summary:
        Summary = "AI estimate." if CaloriesValue == 0 else ""

    if CaloriesValue == 0 and (_to_float(Data.get("ProteinPerServing", 0)) or 0) == 0:
        RetryPrompt = (
            "Return ONLY the JSON object with non-zero CaloriesPerServing or ProteinPerServing. "
            "No extra text."
        )
        RetryContent, _RetryModelUsed = GetOpenAiContentWithModel(
            [
                {"role": "system", "content": RetryPrompt},
                {"role": "user", "content": UserPrompt}
            ],
            Temperature=0.1,
            MaxTokens=1600,
            ReasoningEffort="high",
            TextVerbosity="low"
        )
        Data = _TryParseMealTotals(RetryContent)
        if Data is None:
            raise ValueError("Invalid AI response format.")
        Calories = Data.get("CaloriesPerServing", 0)
        try:
            CaloriesValue = int(float(Calories))
        except (TypeError, ValueError):
            CaloriesValue = 0
        Summary = str(Data.get("Summary", "AI estimate." if CaloriesValue == 0 else "")).strip()
        if not Summary:
            Summary = "AI estimate." if CaloriesValue == 0 else ""

    ProteinValue = _to_float(Data.get("ProteinPerServing", 0)) or 0.0

    return {
        "MealName": MealName,
        "ServingQuantity": ServingQuantity,
        "ServingUnit": ServingUnit,
        "CaloriesPerServing": CaloriesValue,
        "ProteinPerServing": ProteinValue,
        "FibrePerServing": _to_float(Data.get("FibrePerServing")),
        "CarbsPerServing": _to_float(Data.get("CarbsPerServing")),
        "FatPerServing": _to_float(Data.get("FatPerServing")),
        "SaturatedFatPerServing": _to_float(Data.get("SaturatedFatPerServing")),
        "SugarPerServing": _to_float(Data.get("SugarPerServing")),
        "SodiumPerServing": _to_float(Data.get("SodiumPerServing")),
        "Summary": Summary
    }
