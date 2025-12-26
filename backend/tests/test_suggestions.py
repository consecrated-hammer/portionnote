from app.models.schemas import DailyLog, DailyLogWithEntries, MealEntryWithFood, MealType, SuggestionsInput
from app.services.suggestions_service import BuildMealBuckets, BuildSuggestions


def BuildEntry(
    MealTypeValue: MealType,
    FoodName: str,
    CaloriesPerServing: int,
    ProteinPerServing: float,
    MealEntryId: str
) -> MealEntryWithFood:
    return MealEntryWithFood(
        MealEntryId=MealEntryId,
        DailyLogId="1",
        MealType=MealTypeValue,
        FoodId="Food-1",
        FoodName=FoodName,
        ServingDescription="1",
        CaloriesPerServing=CaloriesPerServing,
        ProteinPerServing=ProteinPerServing,
        Quantity=1,
        EntryNotes=None,
        SortOrder=0
    )


def BuildLog(LogDate: str, Entries: list[MealEntryWithFood], DailyLogId: str) -> DailyLogWithEntries:
    return DailyLogWithEntries(
        DailyLog=DailyLog(
            DailyLogId=DailyLogId,
            LogDate=LogDate,
            Steps=0,
            StepKcalFactorOverride=None,
            Notes=None
        ),
        Entries=Entries
    )


def test_build_suggestions_rule_set():
    Entries = [
        BuildEntry(MealType.Breakfast, "Toast", 200, 8, "Entry-1"),
        BuildEntry(MealType.Snack1, "Cookies", 520, 4, "Entry-2")
    ]

    RecentLogs = [
        BuildLog("2024-01-01", [BuildEntry(MealType.Snack1, "Chips", 300, 3, "Entry-3")], "Log-1"),
        BuildLog("2024-01-02", [BuildEntry(MealType.Snack1, "Chips", 300, 3, "Entry-4")], "Log-2"),
        BuildLog("2024-01-03", [BuildEntry(MealType.Snack2, "Chips", 300, 3, "Entry-5")], "Log-3")
    ]

    Suggestions = BuildSuggestions(
        SuggestionsInput(Log=BuildLog("2024-01-04", Entries, "Log-4"), RecentLogs=RecentLogs)
    )

    SuggestionTypes = {Suggestion.SuggestionType for Suggestion in Suggestions}

    assert "LowProteinMorning" in SuggestionTypes
    assert "HighCalorieSnacks" in SuggestionTypes
    assert "MissedMeals" in SuggestionTypes
    assert "RepeatedPattern" in SuggestionTypes


def test_skips_suggestions_when_thresholds_met():
    Entries = [
        BuildEntry(MealType.Breakfast, "Egg Bowl", 400, 32, "Entry-6"),
        BuildEntry(MealType.Lunch, "Salad", 350, 28, "Entry-7"),
        BuildEntry(MealType.Dinner, "Salmon", 500, 40, "Entry-8")
    ]

    RecentLogs = [
        BuildLog("2024-01-01", [BuildEntry(MealType.Snack1, "Crackers", 200, 3, "Entry-9")], "Log-5"),
        BuildLog("2024-01-02", [BuildEntry(MealType.Snack2, "Crackers", 200, 3, "Entry-10")], "Log-6")
    ]

    Suggestions = BuildSuggestions(
        SuggestionsInput(Log=BuildLog("2024-01-05", Entries, "Log-7"), RecentLogs=RecentLogs)
    )

    assert Suggestions == []


def test_skips_low_protein_when_no_breakfast():
    Entries = [
        BuildEntry(MealType.Lunch, "Soup", 220, 12, "Entry-11")
    ]

    Suggestions = BuildSuggestions(
        SuggestionsInput(Log=BuildLog("2024-01-06", Entries, "Log-8"), RecentLogs=[])
    )

    SuggestionTypes = {Suggestion.SuggestionType for Suggestion in Suggestions}

    assert "LowProteinMorning" not in SuggestionTypes


def test_skips_high_calorie_snack_when_under_threshold():
    Entries = [
        BuildEntry(MealType.Snack1, "Apple", 120, 0.5, "Entry-12")
    ]

    Suggestions = BuildSuggestions(
        SuggestionsInput(Log=BuildLog("2024-01-07", Entries, "Log-9"), RecentLogs=[])
    )

    SuggestionTypes = {Suggestion.SuggestionType for Suggestion in Suggestions}

    assert "HighCalorieSnacks" not in SuggestionTypes


def test_high_calorie_snack_includes_evening_snack():
    Entries = [
        BuildEntry(MealType.Snack3, "Ice Cream", 520, 6, "Entry-18")
    ]

    Suggestions = BuildSuggestions(
        SuggestionsInput(Log=BuildLog("2024-01-09", Entries, "Log-12"), RecentLogs=[])
    )

    SuggestionTypes = {Suggestion.SuggestionType for Suggestion in Suggestions}

    assert "HighCalorieSnacks" in SuggestionTypes


def test_ignores_blank_snack_names_in_repeats():
    Entries = [
        BuildEntry(MealType.Snack1, "   ", 200, 4, "Entry-13")
    ]

    Suggestions = BuildSuggestions(
        SuggestionsInput(
            Log=BuildLog("2024-01-08", Entries, "Log-10"),
            RecentLogs=[BuildLog("2024-01-07", Entries, "Log-11")]
        )
    )

    SuggestionTypes = {Suggestion.SuggestionType for Suggestion in Suggestions}

    assert "RepeatedPattern" not in SuggestionTypes


def test_builds_meal_buckets_sorted_by_order():
    Entries = [
        BuildEntry(MealType.Lunch, "Salad", 250, 12, "Entry-14"),
        BuildEntry(MealType.Breakfast, "Oats", 180, 6, "Entry-15"),
        BuildEntry(MealType.Breakfast, "Eggs", 160, 12, "Entry-16")
    ]

    Entries[0].SortOrder = 2
    Entries[1].SortOrder = 1
    Entries[2].SortOrder = 0

    Buckets = BuildMealBuckets(Entries)

    assert [Entry.MealEntryId for Entry in Buckets[MealType.Breakfast]] == [
        "Entry-16",
        "Entry-15"
    ]
    assert [Entry.MealEntryId for Entry in Buckets[MealType.Lunch]] == ["Entry-14"]
