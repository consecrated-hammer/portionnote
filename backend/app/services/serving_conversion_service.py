import json
from typing import Optional, Tuple

import httpx

from app.config import Settings


_MASS_UNITS = {
    "g": 1.0,
    "kg": 1000.0,
    "oz": 28.3495,
    "lb": 453.592
}

_VOLUME_UNITS = {
    "mL": 1.0,
    "L": 1000.0,
    "tsp": 5.0,
    "tbsp": 15.0,
    "cup": 250.0
}

_COUNT_UNITS = {
    "serving",
    "piece",
    "slice",
    "biscuit",
    "egg",
    "can",
    "bar",
    "handful"
}

_UNIT_ALIASES = {
    "gram": "g",
    "grams": "g",
    "gr": "g",
    "kilogram": "kg",
    "kilograms": "kg",
    "ml": "mL",
    "milliliter": "mL",
    "milliliters": "mL",
    "millilitre": "mL",
    "millilitres": "mL",
    "liter": "L",
    "liters": "L",
    "litre": "L",
    "litres": "L",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "cups": "cup",
    "servings": "serving",
    "pieces": "piece",
    "slices": "slice",
    "biscuits": "biscuit",
    "eggs": "egg",
    "cans": "can",
    "bars": "bar",
    "handfuls": "handful"
}


def _FormatNumber(Value: float) -> str:
    if Value.is_integer():
        return str(int(Value))
    return f"{Value:.2f}".rstrip("0").rstrip(".")


def NormalizeUnit(Unit: str) -> str:
    Value = (Unit or "").strip()
    if not Value:
        return "serving"

    ValueLower = Value.lower()
    if ValueLower in _UNIT_ALIASES:
        return _UNIT_ALIASES[ValueLower]

    if ValueLower in _MASS_UNITS:
        return ValueLower

    if ValueLower in ("ml", "l"):
        return "mL" if ValueLower == "ml" else "L"

    if ValueLower in _VOLUME_UNITS:
        return ValueLower

    if ValueLower in _COUNT_UNITS:
        return ValueLower

    # Strip trailing plural 's' for unknown units
    if ValueLower.endswith("s") and len(ValueLower) > 1:
        ValueLower = ValueLower[:-1]
        if ValueLower in _UNIT_ALIASES:
            return _UNIT_ALIASES[ValueLower]
        if ValueLower in _COUNT_UNITS:
            return ValueLower

    return Value


def GetUnitKind(Unit: str) -> str:
    if Unit == "serving":
        return "serving"
    if Unit in _MASS_UNITS:
        return "mass"
    if Unit in _VOLUME_UNITS:
        return "volume"
    if Unit in _COUNT_UNITS:
        return "count"
    return "unknown"


def ConvertToBase(Quantity: float, Unit: str) -> Tuple[float, str]:
    if Unit in _MASS_UNITS:
        return Quantity * _MASS_UNITS[Unit], "g"
    if Unit in _VOLUME_UNITS:
        return Quantity * _VOLUME_UNITS[Unit], "mL"
    return Quantity, Unit


def TryConvertEntryToServings(
    FoodName: str,
    ServingQuantity: float,
    ServingUnit: str,
    EntryQuantity: float,
    EntryUnit: str
) -> Optional[tuple[float, str, str]]:
    NormalizedEntryUnit = NormalizeUnit(EntryUnit)
    NormalizedServingUnit = NormalizeUnit(ServingUnit)

    if NormalizedEntryUnit == "serving":
        return EntryQuantity, "", NormalizedEntryUnit

    EntryKind = GetUnitKind(NormalizedEntryUnit)
    ServingKind = GetUnitKind(NormalizedServingUnit)

    if NormalizedEntryUnit == NormalizedServingUnit:
        Servings = EntryQuantity / ServingQuantity
        Detail = (
            f"Converted {_FormatNumber(EntryQuantity)} {NormalizedEntryUnit} against "
            f"{_FormatNumber(ServingQuantity)} {NormalizedServingUnit} serving. "
            f"Logged {_FormatNumber(Servings)} servings."
        )
        return Servings, Detail, NormalizedEntryUnit

    if EntryKind in ("mass", "volume") and ServingKind == EntryKind:
        EntryBase, BaseUnit = ConvertToBase(EntryQuantity, NormalizedEntryUnit)
        ServingBase, _ = ConvertToBase(ServingQuantity, NormalizedServingUnit)
        Servings = EntryBase / ServingBase
        Detail = (
            f"Converted {_FormatNumber(EntryQuantity)} {NormalizedEntryUnit} to "
            f"{_FormatNumber(EntryBase)} {BaseUnit}. Serving size is "
            f"{_FormatNumber(ServingQuantity)} {NormalizedServingUnit}. "
            f"Logged {_FormatNumber(Servings)} servings."
        )
        return Servings, Detail, NormalizedEntryUnit

    if EntryKind == "count" and ServingKind == "count":
        if NormalizedEntryUnit != NormalizedServingUnit:
            return None
        Servings = EntryQuantity / ServingQuantity
        Detail = (
            f"Converted {_FormatNumber(EntryQuantity)} {NormalizedEntryUnit} against "
            f"{_FormatNumber(ServingQuantity)} {NormalizedServingUnit} serving. "
            f"Logged {_FormatNumber(Servings)} servings."
        )
        return Servings, Detail, NormalizedEntryUnit

    return None


def _ParseJsonContent(Content: str) -> dict:
    if not Content:
        raise ValueError("No AI response content.")

    if "```json" in Content:
        Content = Content.split("```json")[1].split("```")[0].strip()
    elif "```" in Content:
        Content = Content.split("```")[1].split("```")[0].strip()

    try:
        Parsed = json.loads(Content)
    except json.JSONDecodeError as ErrorValue:
        raise ValueError(f"Invalid AI response format: {ErrorValue}") from ErrorValue

    if not isinstance(Parsed, dict):
        raise ValueError("Invalid AI response format.")

    return Parsed


def ConvertEntryToServings(
    FoodName: str,
    ServingQuantity: float,
    ServingUnit: str,
    EntryQuantity: float,
    EntryUnit: str
) -> tuple[float, Optional[str], str]:
    Attempt = TryConvertEntryToServings(
        FoodName,
        ServingQuantity,
        ServingUnit,
        EntryQuantity,
        EntryUnit
    )
    if Attempt is not None:
        Servings, Detail, NormalizedEntryUnit = Attempt
        DetailValue = Detail if Detail else None
        return Servings, DetailValue, NormalizedEntryUnit

    if not Settings.OpenAiApiKey:
        raise ValueError("Unable to convert units without AI enabled. Use the serving unit instead.")

    SystemPrompt = """
You are a nutrition assistant. Convert a meal entry amount into number of servings.

Return ONLY a JSON object with:
{
  \"Servings\": float,
  \"ConversionDetail\": \"concise explanation with assumptions, no em dashes\"
}

Rules:
- Use metric where possible.
- If this is an estimate, start ConversionDetail with \"AI estimate.\".
- Include the serving size and the final servings in the detail.
- When converting between named units, include the assumed unit conversion.
""".strip()

    UserPrompt = (
        f"Food: {FoodName}. Serving size: {ServingQuantity} {ServingUnit}. "
        f"Entry: {EntryQuantity} {EntryUnit}. Convert to servings."
    )

    Payload = {
        "model": Settings.OpenAiModel,
        "messages": [
            {"role": "system", "content": SystemPrompt},
            {"role": "user", "content": UserPrompt}
        ],
        "temperature": 0.2,
        "max_tokens": 200
    }

    Headers = {
        "Authorization": f"Bearer {Settings.OpenAiApiKey}",
        "Content-Type": "application/json"
    }

    Response = httpx.post(
        Settings.OpenAiBaseUrl,
        headers=Headers,
        json=Payload,
        timeout=20.0
    )
    Response.raise_for_status()

    Data = Response.json()
    Content = Data.get("choices", [{}])[0].get("message", {}).get("content", "")
    Parsed = _ParseJsonContent(Content)

    ServingsValue = Parsed.get("Servings")
    DetailValue = Parsed.get("ConversionDetail")

    if ServingsValue is None or DetailValue is None:
        raise ValueError("Invalid AI conversion response.")

    try:
        ServingsFloat = float(ServingsValue)
    except (TypeError, ValueError) as ErrorValue:
        raise ValueError("Invalid AI conversion servings value.") from ErrorValue

    return ServingsFloat, str(DetailValue).strip(), NormalizeUnit(EntryUnit)
