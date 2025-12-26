from app.models.schemas import MealEntryWithFood, MealType, Targets
from app.services.calculations_service import BuildDailySummary, CalculateDailyTotals, CalculateWeeklySummary

TargetsFixture = Targets(
    DailyCalorieTarget=1498,
    ProteinTargetMin=70,
    ProteinTargetMax=188,
    StepKcalFactor=0.04,
    StepTarget=8500
)

EntriesFixture = [
    MealEntryWithFood(
        MealEntryId="1",
        DailyLogId="1",
        MealType=MealType.Breakfast,
        FoodId="1",
        FoodName="Greek Yogurt",
        ServingDescription="1 cup",
        CaloriesPerServing=120,
        ProteinPerServing=15.5,
        Quantity=1,
        EntryNotes=None,
        SortOrder=0
    ),
    MealEntryWithFood(
        MealEntryId="2",
        DailyLogId="1",
        MealType=MealType.Lunch,
        FoodId="2",
        FoodName="Chicken Bowl",
        ServingDescription="1 bowl",
        CaloriesPerServing=430,
        ProteinPerServing=32.2,
        Quantity=1,
        EntryNotes=None,
        SortOrder=1
    )
]


def test_calculate_daily_totals():
    Totals = CalculateDailyTotals(EntriesFixture, 2000, 0.04, TargetsFixture)

    assert Totals.TotalCalories == 550
    assert Totals.TotalProtein == 47.7
    assert Totals.CaloriesBurnedFromSteps == 80
    assert Totals.NetCalories == 470
    assert Totals.RemainingCalories == 1028
    assert Totals.RemainingProteinMin == 22.3
    assert Totals.RemainingProteinMax == 140.3


def test_calculate_weekly_summary():
    DayOneTotals = CalculateDailyTotals(EntriesFixture, 2000, 0.04, TargetsFixture)
    DayTwoTotals = CalculateDailyTotals(EntriesFixture, 5000, 0.04, TargetsFixture)

    DaySummaries = [
        BuildDailySummary("2024-01-01", 2000, DayOneTotals),
        BuildDailySummary("2024-01-02", 5000, DayTwoTotals)
    ]

    Weekly = CalculateWeeklySummary(DaySummaries)

    assert Weekly.Totals["TotalCalories"] == 1100
    assert Weekly.Totals["TotalProtein"] == 95.4
    assert Weekly.Totals["TotalSteps"] == 7000
    assert Weekly.Averages["AverageCalories"] == 550
    assert Weekly.Averages["AverageProtein"] == 47.7
    assert Weekly.Averages["AverageSteps"] == 3500
