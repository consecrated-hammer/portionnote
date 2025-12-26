from app.models.schemas import DailySummary, MealEntryWithFood, WeeklySummary
from app.services.calculations_service import BuildDailySummary, CalculateDailyTotals, CalculateWeeklySummary
from app.services.daily_logs_service import GetSettings
from app.utils.database import FetchAll


def GetWeeklySummary(UserId: str, StartDate: str) -> WeeklySummary:
    Logs = FetchAll(
        """
        SELECT
            DailyLogId AS DailyLogId,
            LogDate AS LogDate,
            Steps AS Steps,
            StepKcalFactorOverride AS StepKcalFactorOverride,
            Notes AS Notes
        FROM DailyLogs
        WHERE LogDate BETWEEN ? AND date(?, '+6 days')
            AND UserId = ?
        ORDER BY LogDate ASC;
        """,
        [StartDate, StartDate, UserId]
    )

    Entries = FetchAll(
        """
        SELECT
            MealEntries.MealEntryId AS MealEntryId,
            MealEntries.DailyLogId AS DailyLogId,
            MealEntries.MealType AS MealType,
            MealEntries.FoodId AS FoodId,
            MealEntries.Quantity AS Quantity,
            MealEntries.EntryNotes AS EntryNotes,
            MealEntries.SortOrder AS SortOrder,
            Foods.FoodName AS FoodName,
            Foods.ServingDescription AS ServingDescription,
            Foods.CaloriesPerServing AS CaloriesPerServing,
            Foods.ProteinPerServing AS ProteinPerServing
        FROM MealEntries
        INNER JOIN Foods ON Foods.FoodId = MealEntries.FoodId
        INNER JOIN DailyLogs ON DailyLogs.DailyLogId = MealEntries.DailyLogId
        WHERE DailyLogs.LogDate BETWEEN ? AND date(?, '+6 days')
            AND DailyLogs.UserId = ?
            AND Foods.UserId = DailyLogs.UserId
        ORDER BY DailyLogs.LogDate ASC, MealEntries.MealType, MealEntries.SortOrder;
        """,
        [StartDate, StartDate, UserId]
    )

    EntriesByLogId: dict[str, list[MealEntryWithFood]] = {}
    for Row in Entries:
        Entry = MealEntryWithFood(
            MealEntryId=Row["MealEntryId"],
            DailyLogId=Row["DailyLogId"],
            MealType=Row["MealType"],
            FoodId=Row["FoodId"],
            FoodName=Row["FoodName"],
            ServingDescription=Row["ServingDescription"],
            CaloriesPerServing=int(Row["CaloriesPerServing"]),
            ProteinPerServing=float(Row["ProteinPerServing"]),
            Quantity=float(Row["Quantity"]),
            EntryNotes=Row["EntryNotes"],
            SortOrder=int(Row["SortOrder"])
        )
        EntriesByLogId.setdefault(Entry.DailyLogId, []).append(Entry)

    Settings = GetSettings(UserId)
    Summaries: list[DailySummary] = []

    for Log in Logs:
        EntriesForLog = EntriesByLogId.get(Log["DailyLogId"], [])
        StepFactor = Log["StepKcalFactorOverride"]
        StepFactor = float(StepFactor) if StepFactor is not None else Settings.StepKcalFactor
        Totals = CalculateDailyTotals(
            EntriesForLog,
            int(Log["Steps"]),
            StepFactor,
            Settings
        )
        Summaries.append(BuildDailySummary(Log["LogDate"], int(Log["Steps"]), Totals))

    return CalculateWeeklySummary(Summaries)
