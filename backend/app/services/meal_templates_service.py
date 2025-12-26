import uuid

from app.models.schemas import (
    ApplyMealTemplateResponse,
    CreateMealTemplateInput,
    UpdateMealTemplateInput,
    CreateMealEntryInput,
    MealTemplate,
    MealTemplateItem,
    MealTemplateItemInput,
    MealTemplateWithItems
)
from app.services.daily_logs_service import CreateMealEntry, EnsureDailyLogForDate, GetEntriesForLog
from app.services.serving_conversion_service import ConvertEntryToServings
from app.utils.database import ExecuteQuery, FetchAll, FetchOne


def _ResolveTemplateItemAmount(FoodRow: dict, Item: MealTemplateItemInput) -> tuple[float, float, str]:
    if (Item.EntryQuantity is None) != (Item.EntryUnit is None):
        raise ValueError("EntryQuantity and EntryUnit must be provided together.")

    EntryQuantity = Item.EntryQuantity if Item.EntryQuantity is not None else Item.Quantity
    EntryUnit = Item.EntryUnit or "serving"

    if EntryUnit == "serving":
        return EntryQuantity, EntryQuantity, EntryUnit

    Quantity, _Detail, NormalizedUnit = ConvertEntryToServings(
        FoodRow["FoodName"],
        float(FoodRow["ServingQuantity"]) if FoodRow["ServingQuantity"] else 1.0,
        FoodRow["ServingUnit"] or "serving",
        EntryQuantity,
        EntryUnit
    )
    return Quantity, EntryQuantity, NormalizedUnit


def CreateMealTemplate(UserId: str, Input: CreateMealTemplateInput) -> MealTemplateWithItems:
    TemplateName = Input.TemplateName.strip()
    if not TemplateName:
        raise ValueError("Template name is required.")

    if not Input.Items:
        raise ValueError("Template items are required.")

    Existing = FetchOne(
        """
        SELECT MealTemplateId AS MealTemplateId
        FROM MealTemplates
        WHERE UserId = ? AND TemplateName = ?;
        """,
        [UserId, TemplateName]
    )
    if Existing is not None:
        raise ValueError("Template name already exists.")

    MealTemplateId = str(uuid.uuid4())

    ExecuteQuery(
        """
        INSERT INTO MealTemplates (
            MealTemplateId,
            UserId,
            TemplateName
        ) VALUES (?, ?, ?);
        """,
        [MealTemplateId, UserId, TemplateName]
    )

    for Item in Input.Items:
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
            [Item.FoodId]
        )
        if FoodRow is None:
            raise ValueError("Food not found.")

        Quantity, EntryQuantity, EntryUnit = _ResolveTemplateItemAmount(FoodRow, Item)

        ExecuteQuery(
            """
            INSERT INTO MealTemplateItems (
                MealTemplateItemId,
                MealTemplateId,
                FoodId,
                MealType,
                Quantity,
                EntryQuantity,
                EntryUnit,
                EntryNotes,
                SortOrder
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            [
                str(uuid.uuid4()),
                MealTemplateId,
                Item.FoodId,
                Item.MealType,
                Quantity,
                EntryQuantity,
                EntryUnit,
                Item.EntryNotes,
                Item.SortOrder
            ]
        )

    return GetMealTemplate(UserId, MealTemplateId)


def GetMealTemplate(UserId: str, MealTemplateId: str) -> MealTemplateWithItems:
    TemplateRow = FetchOne(
        """
        SELECT
            MealTemplateId AS MealTemplateId,
            TemplateName AS TemplateName,
            CreatedAt AS CreatedAt
        FROM MealTemplates
        WHERE MealTemplateId = ? AND UserId = ?;
        """,
        [MealTemplateId, UserId]
    )
    if TemplateRow is None:
        raise ValueError("Template not found.")

    ItemRows = FetchAll(
        """
        SELECT
            MealTemplateItems.MealTemplateItemId AS MealTemplateItemId,
            MealTemplateItems.MealTemplateId AS MealTemplateId,
            MealTemplateItems.FoodId AS FoodId,
            MealTemplateItems.MealType AS MealType,
            MealTemplateItems.Quantity AS Quantity,
            MealTemplateItems.EntryQuantity AS EntryQuantity,
            MealTemplateItems.EntryUnit AS EntryUnit,
            MealTemplateItems.EntryNotes AS EntryNotes,
            MealTemplateItems.SortOrder AS SortOrder,
            Foods.FoodName AS FoodName,
            Foods.ServingDescription AS ServingDescription
        FROM MealTemplateItems
        INNER JOIN Foods
            ON MealTemplateItems.FoodId = Foods.FoodId
        WHERE MealTemplateItems.MealTemplateId = ?
        ORDER BY MealTemplateItems.SortOrder ASC;
        """,
        [MealTemplateId]
    )

    Template = MealTemplate(
        MealTemplateId=TemplateRow["MealTemplateId"],
        TemplateName=TemplateRow["TemplateName"],
        CreatedAt=TemplateRow["CreatedAt"]
    )

    Items = [
        MealTemplateItem(
            MealTemplateItemId=Row["MealTemplateItemId"],
            MealTemplateId=Row["MealTemplateId"],
            FoodId=Row["FoodId"],
            MealType=Row["MealType"],
            Quantity=float(Row["Quantity"]),
            EntryQuantity=float(Row["EntryQuantity"]) if Row.get("EntryQuantity") is not None else None,
            EntryUnit=Row.get("EntryUnit"),
            EntryNotes=Row["EntryNotes"],
            SortOrder=int(Row["SortOrder"]),
            FoodName=Row["FoodName"],
            ServingDescription=Row["ServingDescription"]
        )
        for Row in ItemRows
    ]

    return MealTemplateWithItems(Template=Template, Items=Items)


def GetMealTemplates(UserId: str) -> list[MealTemplateWithItems]:
    TemplateRows = FetchAll(
        """
        SELECT
            MealTemplateId AS MealTemplateId,
            TemplateName AS TemplateName,
            CreatedAt AS CreatedAt
        FROM MealTemplates
        WHERE UserId = ?
        ORDER BY CreatedAt DESC;
        """,
        [UserId]
    )

    if not TemplateRows:
        return []

    TemplateIds = [Row["MealTemplateId"] for Row in TemplateRows]
    Placeholders = ",".join("?" for _ in TemplateIds)
    ItemRows = FetchAll(
        f"""
        SELECT
            MealTemplateItems.MealTemplateItemId AS MealTemplateItemId,
            MealTemplateItems.MealTemplateId AS MealTemplateId,
            MealTemplateItems.FoodId AS FoodId,
            MealTemplateItems.MealType AS MealType,
            MealTemplateItems.Quantity AS Quantity,
            MealTemplateItems.EntryQuantity AS EntryQuantity,
            MealTemplateItems.EntryUnit AS EntryUnit,
            MealTemplateItems.EntryNotes AS EntryNotes,
            MealTemplateItems.SortOrder AS SortOrder,
            Foods.FoodName AS FoodName,
            Foods.ServingDescription AS ServingDescription
        FROM MealTemplateItems
        INNER JOIN Foods
            ON MealTemplateItems.FoodId = Foods.FoodId
        WHERE MealTemplateItems.MealTemplateId IN ({Placeholders})
        ORDER BY MealTemplateItems.SortOrder ASC;
        """,
        TemplateIds
    )

    ItemsByTemplate: dict[str, list[MealTemplateItem]] = {}
    for Row in ItemRows:
        Item = MealTemplateItem(
            MealTemplateItemId=Row["MealTemplateItemId"],
            MealTemplateId=Row["MealTemplateId"],
            FoodId=Row["FoodId"],
            MealType=Row["MealType"],
            Quantity=float(Row["Quantity"]),
            EntryQuantity=float(Row["EntryQuantity"]) if Row.get("EntryQuantity") is not None else None,
            EntryUnit=Row.get("EntryUnit"),
            EntryNotes=Row["EntryNotes"],
            SortOrder=int(Row["SortOrder"]),
            FoodName=Row["FoodName"],
            ServingDescription=Row["ServingDescription"]
        )
        ItemsByTemplate.setdefault(Row["MealTemplateId"], []).append(Item)

    Templates: list[MealTemplateWithItems] = []
    for Row in TemplateRows:
        Template = MealTemplate(
            MealTemplateId=Row["MealTemplateId"],
            TemplateName=Row["TemplateName"],
            CreatedAt=Row["CreatedAt"]
        )
        Items = ItemsByTemplate.get(Row["MealTemplateId"], [])
        Templates.append(MealTemplateWithItems(Template=Template, Items=Items))

    return Templates


def _FetchMealTemplateRow(UserId: str, MealTemplateId: str, IsAdmin: bool) -> dict:
    if IsAdmin:
        Row = FetchOne(
            """
            SELECT MealTemplateId AS MealTemplateId, UserId AS UserId
            FROM MealTemplates
            WHERE MealTemplateId = ?;
            """,
            [MealTemplateId]
        )
    else:
        Row = FetchOne(
            """
            SELECT MealTemplateId AS MealTemplateId, UserId AS UserId
            FROM MealTemplates
            WHERE MealTemplateId = ? AND UserId = ?;
            """,
            [MealTemplateId, UserId]
        )

    if Row is None:
        raise ValueError("Template not found.")

    return Row


def DeleteMealTemplate(UserId: str, MealTemplateId: str, IsAdmin: bool = False) -> None:
    _FetchMealTemplateRow(UserId, MealTemplateId, IsAdmin)

    ExecuteQuery(
        "DELETE FROM MealTemplates WHERE MealTemplateId = ?;",
        [MealTemplateId]
    )


def UpdateMealTemplate(
    UserId: str,
    MealTemplateId: str,
    Input: UpdateMealTemplateInput,
    IsAdmin: bool = False
) -> MealTemplateWithItems:
    # Verify template exists and user owns it
    Row = _FetchMealTemplateRow(UserId, MealTemplateId, IsAdmin)
    OwnerUserId = Row["UserId"]

    # Update template name if provided
    if Input.TemplateName is not None:
        TemplateName = Input.TemplateName.strip()
        if not TemplateName:
            raise ValueError("Template name cannot be empty.")
        
        # Check for duplicate name
        Existing = FetchOne(
            """
            SELECT MealTemplateId AS MealTemplateId
            FROM MealTemplates
            WHERE UserId = ? AND TemplateName = ? AND MealTemplateId != ?;
            """,
            [OwnerUserId, TemplateName, MealTemplateId]
        )
        if Existing is not None:
            raise ValueError("Template name already exists.")
        
        ExecuteQuery(
            "UPDATE MealTemplates SET TemplateName = ? WHERE MealTemplateId = ?;",
            [TemplateName, MealTemplateId]
        )

    # Update items if provided
    if Input.Items is not None:
        if not Input.Items:
            raise ValueError("Template items cannot be empty.")
        
        # Delete existing items
        ExecuteQuery(
            "DELETE FROM MealTemplateItems WHERE MealTemplateId = ?;",
            [MealTemplateId]
        )
        
        # Insert new items
        for Item in Input.Items:
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
                [Item.FoodId]
            )
            if FoodRow is None:
                raise ValueError("Food not found.")

            Quantity, EntryQuantity, EntryUnit = _ResolveTemplateItemAmount(FoodRow, Item)

            ExecuteQuery(
                """
                INSERT INTO MealTemplateItems (
                    MealTemplateItemId,
                    MealTemplateId,
                    FoodId,
                    MealType,
                    Quantity,
                    EntryQuantity,
                    EntryUnit,
                    EntryNotes,
                    SortOrder
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                [
                    str(uuid.uuid4()),
                    MealTemplateId,
                    Item.FoodId,
                    Item.MealType,
                    Quantity,
                    EntryQuantity,
                    EntryUnit,
                    Item.EntryNotes,
                    Item.SortOrder
                ]
            )

    return GetMealTemplate(OwnerUserId, MealTemplateId)


def ApplyMealTemplate(UserId: str, MealTemplateId: str, LogDate: str) -> ApplyMealTemplateResponse:
    Template = GetMealTemplate(UserId, MealTemplateId)
    DailyLogItem = EnsureDailyLogForDate(UserId, LogDate)
    ExistingEntries = GetEntriesForLog(UserId, DailyLogItem.DailyLogId)
    NextSortOrder = max((Entry.SortOrder for Entry in ExistingEntries), default=-1) + 1

    if not Template.Items:
        return ApplyMealTemplateResponse(CreatedCount=0)

    CreatedCount = 0
    for Index, Item in enumerate(Template.Items):
        CreateMealEntry(
            UserId,
            CreateMealEntryInput(
                DailyLogId=DailyLogItem.DailyLogId,
                MealType=Item.MealType,
                FoodId=Item.FoodId,
                Quantity=Item.Quantity,
                EntryQuantity=Item.EntryQuantity,
                EntryUnit=Item.EntryUnit,
                EntryNotes=Item.EntryNotes,
                SortOrder=NextSortOrder + Index,
                ScheduleSlotId=None
            )
        )
        CreatedCount += 1

    return ApplyMealTemplateResponse(CreatedCount=CreatedCount)
