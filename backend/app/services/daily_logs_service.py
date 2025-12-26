import uuid

from app.models.schemas import (
    CreateDailyLogInput,
    CreateMealEntryInput,
    DailyLog,
    MealEntry,
    MealEntryWithFood,
    Targets
)
from app.services.serving_conversion_service import ConvertEntryToServings
from app.utils.database import ExecuteQuery, FetchAll, FetchOne
from app.utils.defaults import DefaultTargets


def GetSettings(UserId: str) -> Targets:
    Row = FetchOne(
        """
        SELECT
            DailyCalorieTarget AS DailyCalorieTarget,
            ProteinTargetMin AS ProteinTargetMin,
            ProteinTargetMax AS ProteinTargetMax,
            StepKcalFactor AS StepKcalFactor,
            StepTarget AS StepTarget,
            FibreTarget AS FibreTarget,
            CarbsTarget AS CarbsTarget,
            FatTarget AS FatTarget,
            SaturatedFatTarget AS SaturatedFatTarget,
            SugarTarget AS SugarTarget,
            SodiumTarget AS SodiumTarget,
            ShowProteinOnToday AS ShowProteinOnToday,
            ShowStepsOnToday AS ShowStepsOnToday,
            ShowFibreOnToday AS ShowFibreOnToday,
            ShowCarbsOnToday AS ShowCarbsOnToday,
            ShowFatOnToday AS ShowFatOnToday,
            ShowSaturatedFatOnToday AS ShowSaturatedFatOnToday,
            ShowSugarOnToday AS ShowSugarOnToday,
            ShowSodiumOnToday AS ShowSodiumOnToday,
            BarOrder AS BarOrder
        FROM Settings
        WHERE UserId = ?
        ORDER BY CreatedAt ASC
        LIMIT 1;
        """,
        [UserId]
    )

    if Row is None:
        return DefaultTargets

    return Targets(
        DailyCalorieTarget=int(Row["DailyCalorieTarget"]),
        ProteinTargetMin=float(Row["ProteinTargetMin"]),
        ProteinTargetMax=float(Row["ProteinTargetMax"]),
        StepKcalFactor=float(Row["StepKcalFactor"]),
        StepTarget=int(Row["StepTarget"]),
        FibreTarget=float(Row["FibreTarget"]) if Row["FibreTarget"] is not None else None,
        CarbsTarget=float(Row["CarbsTarget"]) if Row["CarbsTarget"] is not None else None,
        FatTarget=float(Row["FatTarget"]) if Row["FatTarget"] is not None else None,
        SaturatedFatTarget=float(Row["SaturatedFatTarget"]) if Row["SaturatedFatTarget"] is not None else None,
        SugarTarget=float(Row["SugarTarget"]) if Row["SugarTarget"] is not None else None,
        SodiumTarget=float(Row["SodiumTarget"]) if Row["SodiumTarget"] is not None else None,
        ShowProteinOnToday=bool(Row["ShowProteinOnToday"]),
        ShowStepsOnToday=bool(Row["ShowStepsOnToday"]),
        ShowFibreOnToday=bool(Row["ShowFibreOnToday"]),
        ShowCarbsOnToday=bool(Row["ShowCarbsOnToday"]),
        ShowFatOnToday=bool(Row["ShowFatOnToday"]),
        ShowSaturatedFatOnToday=bool(Row["ShowSaturatedFatOnToday"]),
        ShowSugarOnToday=bool(Row["ShowSugarOnToday"]),
        ShowSodiumOnToday=bool(Row["ShowSodiumOnToday"]),
        BarOrder=Row["BarOrder"].split(",") if Row["BarOrder"] else ["Calories", "Protein", "Steps", "Fibre", "Carbs", "Fat", "SaturatedFat", "Sugar", "Sodium"]
    )


def GetDailyLogByDate(UserId: str, LogDate: str) -> DailyLog | None:
    Row = FetchOne(
        """
        SELECT
            DailyLogId AS DailyLogId,
            LogDate AS LogDate,
            Steps AS Steps,
            StepKcalFactorOverride AS StepKcalFactorOverride,
            WeightKg AS WeightKg,
            Notes AS Notes
        FROM DailyLogs
        WHERE LogDate = ? AND UserId = ?;
        """,
        [LogDate, UserId]
    )

    if Row is None:
        return None

    return DailyLog(
        DailyLogId=Row["DailyLogId"],
        LogDate=Row["LogDate"],
        Steps=int(Row["Steps"]),
        StepKcalFactorOverride=(float(Row["StepKcalFactorOverride"]) if Row["StepKcalFactorOverride"] is not None else None),
        WeightKg=(float(Row["WeightKg"]) if Row["WeightKg"] is not None else None),
        Notes=Row["Notes"]
    )


def GetDailyLogById(UserId: str, DailyLogId: str) -> DailyLog | None:
    Row = FetchOne(
        """
        SELECT
            DailyLogId AS DailyLogId,
            LogDate AS LogDate,
            Steps AS Steps,
            StepKcalFactorOverride AS StepKcalFactorOverride,
            WeightKg AS WeightKg,
            Notes AS Notes
        FROM DailyLogs
        WHERE DailyLogId = ? AND UserId = ?;
        """,
        [DailyLogId, UserId]
    )

    if Row is None:
        return None

    return DailyLog(
        DailyLogId=Row["DailyLogId"],
        LogDate=Row["LogDate"],
        Steps=int(Row["Steps"]),
        StepKcalFactorOverride=(float(Row["StepKcalFactorOverride"]) if Row["StepKcalFactorOverride"] is not None else None),
        WeightKg=(float(Row["WeightKg"]) if Row["WeightKg"] is not None else None),
        Notes=Row["Notes"]
    )


def GetEntriesForLog(UserId: str, DailyLogId: str) -> list[MealEntryWithFood]:
    Rows = FetchAll(
        """
        SELECT
            MealEntries.MealEntryId AS MealEntryId,
            MealEntries.DailyLogId AS DailyLogId,
            MealEntries.MealType AS MealType,
            MealEntries.FoodId AS FoodId,
            MealEntries.MealTemplateId AS MealTemplateId,
            MealEntries.Quantity AS Quantity,
            MealEntries.EntryQuantity AS EntryQuantity,
            MealEntries.EntryUnit AS EntryUnit,
            MealEntries.ConversionDetail AS ConversionDetail,
            MealEntries.EntryNotes AS EntryNotes,
            MealEntries.SortOrder AS SortOrder,
            MealEntries.ScheduleSlotId AS ScheduleSlotId,
            MealEntries.CreatedAt AS CreatedAt,
            Foods.FoodName AS FoodName,
            Foods.ServingDescription AS ServingDescription,
            Foods.CaloriesPerServing AS CaloriesPerServing,
            Foods.ProteinPerServing AS ProteinPerServing,
            Foods.FibrePerServing AS FibrePerServing,
            Foods.CarbsPerServing AS CarbsPerServing,
            Foods.FatPerServing AS FatPerServing,
            Foods.SaturatedFatPerServing AS SaturatedFatPerServing,
            Foods.SugarPerServing AS SugarPerServing,
            Foods.SodiumPerServing AS SodiumPerServing,
            MealTemplates.TemplateName AS TemplateName
        FROM MealEntries
        INNER JOIN DailyLogs ON DailyLogs.DailyLogId = MealEntries.DailyLogId
        LEFT JOIN Foods ON Foods.FoodId = MealEntries.FoodId
        LEFT JOIN MealTemplates ON MealTemplates.MealTemplateId = MealEntries.MealTemplateId
        WHERE MealEntries.DailyLogId = ?
            AND DailyLogs.UserId = ?
        ORDER BY MealEntries.MealType, MealEntries.SortOrder, MealEntries.CreatedAt;
        """,
        [DailyLogId, UserId]
    )

    Entries: list[MealEntryWithFood] = []
    for Row in Rows:
        # For template entries, calculate totals from template items
        if Row["MealTemplateId"]:
            TemplateRows = FetchAll(
                """
                SELECT
                    Foods.CaloriesPerServing,
                    Foods.ProteinPerServing,
                    Foods.FibrePerServing,
                    Foods.CarbsPerServing,
                    Foods.FatPerServing,
                    Foods.SaturatedFatPerServing,
                    Foods.SugarPerServing,
                    Foods.SodiumPerServing,
                    MealTemplateItems.Quantity
                FROM MealTemplateItems
                INNER JOIN Foods ON Foods.FoodId = MealTemplateItems.FoodId
                WHERE MealTemplateItems.MealTemplateId = ?
                """,
                [Row["MealTemplateId"]]
            )
            TotalCalories = sum(int(r["CaloriesPerServing"]) * float(r["Quantity"]) for r in TemplateRows)
            TotalProtein = sum(float(r["ProteinPerServing"]) * float(r["Quantity"]) for r in TemplateRows)
            TotalFibre = sum((float(r["FibrePerServing"]) if r["FibrePerServing"] else 0) * float(r["Quantity"]) for r in TemplateRows)
            TotalCarbs = sum((float(r["CarbsPerServing"]) if r["CarbsPerServing"] else 0) * float(r["Quantity"]) for r in TemplateRows)
            TotalFat = sum((float(r["FatPerServing"]) if r["FatPerServing"] else 0) * float(r["Quantity"]) for r in TemplateRows)
            TotalSaturatedFat = sum((float(r["SaturatedFatPerServing"]) if r["SaturatedFatPerServing"] else 0) * float(r["Quantity"]) for r in TemplateRows)
            TotalSugar = sum((float(r["SugarPerServing"]) if r["SugarPerServing"] else 0) * float(r["Quantity"]) for r in TemplateRows)
            TotalSodium = sum((float(r["SodiumPerServing"]) if r["SodiumPerServing"] else 0) * float(r["Quantity"]) for r in TemplateRows)
            
            Entries.append(
                MealEntryWithFood(
                    MealEntryId=Row["MealEntryId"],
                    DailyLogId=Row["DailyLogId"],
                    MealType=Row["MealType"],
                    FoodId=None,
                    MealTemplateId=Row["MealTemplateId"],
                    TemplateName=Row["TemplateName"],
                    FoodName=Row["TemplateName"] or "Template",
                    ServingDescription="meal",
                    CaloriesPerServing=int(TotalCalories),
                    ProteinPerServing=float(TotalProtein),
                    FibrePerServing=float(TotalFibre) if TotalFibre else None,
                    CarbsPerServing=float(TotalCarbs) if TotalCarbs else None,
                    FatPerServing=float(TotalFat) if TotalFat else None,
                    SaturatedFatPerServing=float(TotalSaturatedFat) if TotalSaturatedFat else None,
                    SugarPerServing=float(TotalSugar) if TotalSugar else None,
                    SodiumPerServing=float(TotalSodium) if TotalSodium else None,
                    Quantity=1.0,
                    EntryQuantity=None,
                    EntryUnit=None,
                    ConversionDetail=None,
                    EntryNotes=Row["EntryNotes"],
                    SortOrder=int(Row["SortOrder"]),
                    ScheduleSlotId=Row["ScheduleSlotId"],
                    CreatedAt=Row["CreatedAt"]
                )
            )
        else:
            Entries.append(
                MealEntryWithFood(
                    MealEntryId=Row["MealEntryId"],
                    DailyLogId=Row["DailyLogId"],
                    MealType=Row["MealType"],
                    FoodId=Row["FoodId"],
                    MealTemplateId=None,
                    TemplateName=None,
                    FoodName=Row["FoodName"],
                    ServingDescription=Row["ServingDescription"],
                    CaloriesPerServing=int(Row["CaloriesPerServing"]),
                    ProteinPerServing=float(Row["ProteinPerServing"]),
                    FibrePerServing=float(Row["FibrePerServing"]) if Row["FibrePerServing"] else None,
                    CarbsPerServing=float(Row["CarbsPerServing"]) if Row["CarbsPerServing"] else None,
                    FatPerServing=float(Row["FatPerServing"]) if Row["FatPerServing"] else None,
                    SaturatedFatPerServing=float(Row["SaturatedFatPerServing"]) if Row["SaturatedFatPerServing"] else None,
                    SugarPerServing=float(Row["SugarPerServing"]) if Row["SugarPerServing"] else None,
                    SodiumPerServing=float(Row["SodiumPerServing"]) if Row["SodiumPerServing"] else None,
                    Quantity=float(Row["Quantity"]),
                    EntryQuantity=float(Row["EntryQuantity"]) if Row["EntryQuantity"] is not None else None,
                    EntryUnit=Row["EntryUnit"],
                    ConversionDetail=Row["ConversionDetail"],
                    EntryNotes=Row["EntryNotes"],
                    SortOrder=int(Row["SortOrder"]),
                    ScheduleSlotId=Row["ScheduleSlotId"],
                    CreatedAt=Row["CreatedAt"]
                )
            )
    return Entries


def UpsertDailyLog(UserId: str, Input: CreateDailyLogInput) -> DailyLog:
    DailyLogId = str(uuid.uuid4())

    ExecuteQuery(
        """
        INSERT INTO DailyLogs (
            DailyLogId,
            UserId,
            LogDate,
            Steps,
            StepKcalFactorOverride,
            WeightKg,
            Notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (UserId, LogDate)
        DO UPDATE SET
            Steps = excluded.Steps,
            StepKcalFactorOverride = excluded.StepKcalFactorOverride,
            WeightKg = excluded.WeightKg,
            Notes = excluded.Notes;
        """,
        [
            DailyLogId,
            UserId,
            Input.LogDate,
            Input.Steps,
            Input.StepKcalFactorOverride,
            Input.WeightKg,
            Input.Notes
        ]
    )

    if Input.WeightKg is not None:
        UpdateUserWeightFromLatestLog(UserId)

    Result = GetDailyLogByDate(UserId, Input.LogDate)
    if Result is None:
        raise ValueError("Failed to load daily log.")
    return Result


def UpdateSteps(UserId: str, LogDate: str, Steps: int, StepKcalFactorOverride: float | None, WeightKg: float | None = None) -> DailyLog:
    DailyLogId = str(uuid.uuid4())

    ExecuteQuery(
        """
        INSERT INTO DailyLogs (
            DailyLogId,
            UserId,
            LogDate,
            Steps,
            StepKcalFactorOverride,
            WeightKg
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (UserId, LogDate)
        DO UPDATE SET
            Steps = excluded.Steps,
            StepKcalFactorOverride = excluded.StepKcalFactorOverride,
            WeightKg = COALESCE(excluded.WeightKg, WeightKg);
        """,
        [DailyLogId, UserId, LogDate, Steps, StepKcalFactorOverride, WeightKg]
    )

    if WeightKg is not None:
        UpdateUserWeightFromLatestLog(UserId)

    Result = GetDailyLogByDate(UserId, LogDate)
    if Result is None:
        raise ValueError("Failed to load daily log.")
    return Result


def UpdateUserWeightFromLatestLog(UserId: str) -> None:
    Row = FetchOne(
        """
        SELECT
            LogDate AS LogDate,
            WeightKg AS WeightKg
        FROM DailyLogs
        WHERE UserId = ? AND WeightKg IS NOT NULL
        ORDER BY LogDate DESC
        LIMIT 1;
        """,
        [UserId]
    )

    if Row is None or Row["WeightKg"] is None:
        return

    ExecuteQuery(
        "UPDATE Users SET WeightKg = ? WHERE UserId = ?;",
        [Row["WeightKg"], UserId]
    )


def EnsureDailyLogForDate(UserId: str, LogDate: str) -> DailyLog:
    Existing = GetDailyLogByDate(UserId, LogDate)
    if Existing is not None:
        return Existing

    DailyLogId = str(uuid.uuid4())
    ExecuteQuery(
        """
        INSERT INTO DailyLogs (
            DailyLogId,
            UserId,
            LogDate,
            Steps,
            StepKcalFactorOverride
        ) VALUES (?, ?, ?, ?, ?);
        """,
        [DailyLogId, UserId, LogDate, 0, None]
    )

    Result = GetDailyLogByDate(UserId, LogDate)
    if Result is None:
        raise ValueError("Failed to load daily log.")
    return Result


def CreateMealEntry(UserId: str, Input: CreateMealEntryInput) -> MealEntry:
    LogRow = FetchOne(
        """
        SELECT
            DailyLogId AS DailyLogId
        FROM DailyLogs
        WHERE DailyLogId = ? AND UserId = ?;
        """,
        [Input.DailyLogId, UserId]
    )

    if LogRow is None:
        raise ValueError("Daily log not found.")

    # Validate that either FoodId or MealTemplateId is provided (not both, not neither)
    if (Input.FoodId and Input.MealTemplateId) or (not Input.FoodId and not Input.MealTemplateId):
        raise ValueError("Either FoodId or MealTemplateId must be provided (but not both).")

    FoodRow = None
    if Input.FoodId:
        FoodRow = FetchOne(
            """
            SELECT
                FoodId AS FoodId,
                FoodName AS FoodName,
                ServingQuantity AS ServingQuantity,
                ServingUnit AS ServingUnit
            FROM Foods
            WHERE FoodId = ?;
            """,
            [Input.FoodId]
        )

        if FoodRow is None:
            raise ValueError("Food not found.")

    if Input.MealTemplateId:
        TemplateRow = FetchOne(
            """
            SELECT
                MealTemplateId AS MealTemplateId
            FROM MealTemplates
            WHERE MealTemplateId = ? AND UserId = ?;
            """,
            [Input.MealTemplateId, UserId]
        )

        if TemplateRow is None:
            raise ValueError("Meal template not found.")

    if Input.ScheduleSlotId:
        SlotRow = FetchOne(
            """
            SELECT
                ScheduleSlotId AS ScheduleSlotId
            FROM ScheduleSlots
            WHERE ScheduleSlotId = ? AND UserId = ?;
            """,
            [Input.ScheduleSlotId, UserId]
        )
        if SlotRow is None:
            raise ValueError("Schedule slot not found.")

    Quantity = Input.Quantity
    EntryQuantity = Input.EntryQuantity
    EntryUnit = Input.EntryUnit
    ConversionDetail = None

    if Input.FoodId:
        if (EntryQuantity is None) != (EntryUnit is None):
            raise ValueError("EntryQuantity and EntryUnit must be provided together.")
        if EntryQuantity is not None and EntryUnit is not None and FoodRow is not None:
            Quantity, ConversionDetail, EntryUnit = ConvertEntryToServings(
                FoodRow["FoodName"],
                float(FoodRow["ServingQuantity"]) if FoodRow["ServingQuantity"] else 1.0,
                FoodRow["ServingUnit"] or "serving",
                EntryQuantity,
                EntryUnit
            )
        else:
            EntryQuantity = Input.Quantity
            EntryUnit = "serving"

    if Quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    MealEntryId = str(uuid.uuid4())

    ExecuteQuery(
        """
        INSERT INTO MealEntries (
            MealEntryId,
            DailyLogId,
            MealType,
            FoodId,
            MealTemplateId,
            Quantity,
            EntryQuantity,
            EntryUnit,
            ConversionDetail,
            EntryNotes,
            SortOrder,
            ScheduleSlotId
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        [
            MealEntryId,
            Input.DailyLogId,
            Input.MealType,
            Input.FoodId,
            Input.MealTemplateId,
            Quantity,
            EntryQuantity,
            EntryUnit,
            ConversionDetail,
            Input.EntryNotes,
            Input.SortOrder,
            Input.ScheduleSlotId
        ]
    )

    Row = FetchOne(
        """
        SELECT
            MealEntryId AS MealEntryId,
            DailyLogId AS DailyLogId,
            MealType AS MealType,
            FoodId AS FoodId,
            MealTemplateId AS MealTemplateId,
            Quantity AS Quantity,
            EntryQuantity AS EntryQuantity,
            EntryUnit AS EntryUnit,
            ConversionDetail AS ConversionDetail,
            EntryNotes AS EntryNotes,
            SortOrder AS SortOrder,
            ScheduleSlotId AS ScheduleSlotId,
            CreatedAt AS CreatedAt
        FROM MealEntries
        WHERE MealEntryId = ?;
        """,
        [MealEntryId]
    )

    if Row is None:
        raise ValueError("Failed to load meal entry.")

    return MealEntry(
        MealEntryId=Row["MealEntryId"],
        DailyLogId=Row["DailyLogId"],
        MealType=Row["MealType"],
        FoodId=Row["FoodId"],
        MealTemplateId=Row["MealTemplateId"],
        Quantity=float(Row["Quantity"]),
        EntryQuantity=float(Row["EntryQuantity"]) if Row["EntryQuantity"] is not None else None,
        EntryUnit=Row["EntryUnit"],
        ConversionDetail=Row["ConversionDetail"],
        EntryNotes=Row["EntryNotes"],
        SortOrder=int(Row["SortOrder"]),
        ScheduleSlotId=Row["ScheduleSlotId"],
        CreatedAt=Row["CreatedAt"]
    )


def DeleteMealEntry(UserId: str, MealEntryId: str, IsAdmin: bool = False) -> None:
    if IsAdmin:
        Existing = FetchOne(
            """
            SELECT MealEntryId AS MealEntryId
            FROM MealEntries
            WHERE MealEntryId = ?;
            """,
            [MealEntryId]
        )
    else:
        Existing = FetchOne(
            """
            SELECT
                MealEntries.MealEntryId AS MealEntryId
            FROM MealEntries
            INNER JOIN DailyLogs
                ON MealEntries.DailyLogId = DailyLogs.DailyLogId
            WHERE MealEntries.MealEntryId = ? AND DailyLogs.UserId = ?;
            """,
            [MealEntryId, UserId]
        )

    if Existing is None:
        raise ValueError("Meal entry not found.")

    ExecuteQuery(
        "DELETE FROM MealEntries WHERE MealEntryId = ?;",
        [MealEntryId]
    )
