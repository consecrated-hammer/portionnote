import json

import httpx

from app.config import Settings
from app.models.schemas import Suggestion
from app.services.daily_logs_service import GetDailyLogByDate, GetEntriesForLog, GetSettings


def BuildAiPrompt(LogDate: str, Steps: int, Entries: list[dict], Targets: dict) -> str:
    Lines = [
        f"Log date: {LogDate}",
        f"Steps: {Steps}",
        f"Targets: {Targets}",
        "Entries:"
    ]

    if not Entries:
        Lines.append("- None")
    else:
        for Entry in Entries:
            Lines.append(
                f"- {Entry['MealType']}: {Entry['FoodName']} x{Entry['Quantity']} "
                f"({Entry['Calories']} kcal, {Entry['Protein']} g protein)"
            )

    Lines.append("Provide 2-4 concise suggestions focused on protein, calories, or meal balance.")
    return "\n".join(Lines)


def ParseAiSuggestions(Content: str) -> list[Suggestion]:
    Parsed = json.loads(Content)
    if not isinstance(Parsed, list):
        raise ValueError("Invalid AI response.")

    Suggestions: list[Suggestion] = []
    for Item in Parsed:
        if not isinstance(Item, dict):
            continue
        Title = str(Item.get("Title", "")).strip()
        Detail = str(Item.get("Detail", "")).strip()
        if not Title or not Detail:
            continue
        Suggestions.append(
            Suggestion(
                SuggestionType="AiSuggestion",
                Title=Title,
                Detail=Detail
            )
        )

    if not Suggestions:
        raise ValueError("No AI suggestions returned.")

    return Suggestions


def GetAiSuggestions(UserId: str, LogDate: str) -> list[Suggestion]:
    if not Settings.OpenAiApiKey:
        raise ValueError("OpenAI API key not configured.")

    LogItem = GetDailyLogByDate(UserId, LogDate)
    if LogItem is None:
        raise ValueError("Daily log not found.")

    Entries = GetEntriesForLog(UserId, LogItem.DailyLogId)
    Targets = GetSettings(UserId)

    PayloadEntries = [
        {
            "MealType": Entry.MealType.value if hasattr(Entry.MealType, "value") else Entry.MealType,
            "FoodName": Entry.FoodName,
            "Quantity": Entry.Quantity,
            "Calories": round(Entry.CaloriesPerServing * Entry.Quantity, 1),
            "Protein": round(Entry.ProteinPerServing * Entry.Quantity, 1)
        }
        for Entry in Entries
    ]

    TargetsPayload = {
        "DailyCalorieTarget": Targets.DailyCalorieTarget,
        "ProteinTargetMin": Targets.ProteinTargetMin,
        "ProteinTargetMax": Targets.ProteinTargetMax
    }

    Prompt = BuildAiPrompt(LogDate, LogItem.Steps, PayloadEntries, TargetsPayload)

    Payload = {
        "model": Settings.OpenAiModel,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a nutrition assistant for a calorie and protein tracking app. "
                    "Return JSON only as an array of objects with Title and Detail fields."
                )
            },
            {"role": "user", "content": Prompt}
        ],
        "temperature": 0.4
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
    Content = Data.get("choices", [{}])[0].get("message", {}).get("content")
    if not Content:
        raise ValueError("No AI response content.")

    return ParseAiSuggestions(Content)
