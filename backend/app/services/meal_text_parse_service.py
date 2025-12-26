import json
from typing import Any

from app.config import Settings
from app.services.openai_client import GetOpenAiContentWithModel
from app.services.serving_conversion_service import NormalizeUnit


_ALLOWED_UNITS = {
    "serving",
    "g",
    "kg",
    "oz",
    "lb",
    "mL",
    "L",
    "tsp",
    "tbsp",
    "cup",
    "piece",
    "slice",
    "biscuit",
    "handful"
}


def _TryParseMealItems(Content: str) -> list[dict[str, Any]] | None:
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

    if isinstance(Parsed, list):
        return Parsed

    Start = Cleaned.find("[")
    End = Cleaned.rfind("]")
    if Start != -1 and End != -1 and End > Start:
        Candidate = Cleaned[Start:End + 1]
        try:
            Parsed = json.loads(Candidate)
        except json.JSONDecodeError:
            return None
        if isinstance(Parsed, list):
            return Parsed

    return None


def _NormalizeUnitValue(Unit: str) -> str:
    Normalized = NormalizeUnit(Unit)
    if Normalized == "ml":
        return "mL"
    if Normalized == "l":
        return "L"
    return Normalized or "serving"


def ParseMealText(Text: str, KnownFoods: list[str] | None = None) -> list[dict[str, Any]]:
    if not Settings.OpenAiApiKey:
        raise ValueError("OpenAI API key not configured.")

    KnownFoodsList = KnownFoods or []
    KnownFoodsList = [Item for Item in KnownFoodsList if isinstance(Item, str) and Item.strip()]
    KnownFoodsList = KnownFoodsList[:200]
    KnownFoodsText = "\n".join(f"- {Item}" for Item in KnownFoodsList)

    SystemPrompt = """
You are a nutrition assistant. Parse a free text meal entry into structured items.

Return ONLY a JSON array of objects with:
[
  {
    "FoodName": "string",
    "Quantity": float,
    "Unit": "serving|g|kg|oz|lb|mL|L|tsp|tbsp|cup|piece|slice|biscuit|handful"
  }
]

Rules:
- Convert fractions to decimals (half to 0.5).
- If quantity is missing, use 1.
- Prefer metric units (g or mL) when possible.
- Use "serving" ONLY for named menu items or combo meals and include size in FoodName.
- Do not include extra text. Do not include markdown.
""".strip()

    if KnownFoodsText:
        SystemPrompt += "\n\nKnown foods to prefer when matching names:\n" + KnownFoodsText

    UserPrompt = f"Parse this meal entry:\n{Text.strip()}"

    Content, ModelUsed = GetOpenAiContentWithModel(
        [
            {"role": "system", "content": SystemPrompt},
            {"role": "user", "content": UserPrompt}
        ],
        Temperature=0.2,
        MaxTokens=500
    )

    Items = _TryParseMealItems(Content)
    if Items is None:
        RetryPrompt = "Return ONLY the JSON array of items. No extra text."
        RetryContent, _RetryModelUsed = GetOpenAiContentWithModel(
            [
                {"role": "system", "content": RetryPrompt},
                {"role": "user", "content": Content}
            ],
            Temperature=0.1,
            MaxTokens=300
        )
        Items = _TryParseMealItems(RetryContent)

    if Items is None:
        raise ValueError("Invalid AI response format.")

    CleanItems: list[dict[str, Any]] = []
    for Item in Items:
        if not isinstance(Item, dict):
            continue
        Name = str(Item.get("FoodName", "")).strip()
        if not Name:
            continue
        QuantityValue = Item.get("Quantity", 1)
        try:
            QuantityFloat = float(QuantityValue)
        except (TypeError, ValueError):
            QuantityFloat = 1.0
        if QuantityFloat <= 0:
            continue
        UnitValue = _NormalizeUnitValue(str(Item.get("Unit", "serving")))
        if UnitValue not in _ALLOWED_UNITS:
            UnitValue = "serving"
        CleanItems.append({
            "FoodName": Name,
            "Quantity": QuantityFloat,
            "Unit": UnitValue
        })

    if not CleanItems:
        raise ValueError("No items parsed from AI response.")

    return CleanItems
