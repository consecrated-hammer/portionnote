import uuid

from app.models.schemas import (
    ApplyMealTemplateResponse,
    CreateMealTemplateInput,
    UpdateMealTemplateInput,
    CreateMealEntryInput,
    MealTemplate,
    MealTemplateItem,
    MealTemplateWithItems
)
from app.services.daily_logs_service import CreateMealEntry, EnsureDailyLogForDate, GetEntriesForLog
from app.utils.database import ExecuteQuery, FetchAll, FetchOne


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
            SELECT FoodId AS FoodId
            FROM Foods
            WHERE FoodId = ?;
            """,
            [Item.FoodId]
        )
        if FoodRow is None:
            raise ValueError("Food not found.")

        ExecuteQuery(
            """
            INSERT INTO MealTemplateItems (
                MealTemplateItemId,
                MealTemplateId,
                FoodId,
                MealType,
                Quantity,
                EntryNotes,
                SortOrder
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            [
                str(uuid.uuid4()),
                MealTemplateId,
                Item.FoodId,
                Item.MealType,
                Item.Quantity,
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


def DeleteMealTemplate(UserId: str, MealTemplateId: str) -> None:
    Row = FetchOne(
        """
        SELECT MealTemplateId AS MealTemplateId
        FROM MealTemplates
        WHERE MealTemplateId = ? AND UserId = ?;
        """,
        [MealTemplateId, UserId]
    )
    if Row is None:
        raise ValueError("Template not found.")

    ExecuteQuery(
        "DELETE FROM MealTemplates WHERE MealTemplateId = ?;",
        [MealTemplateId]
    )


def UpdateMealTemplate(UserId: str, MealTemplateId: str, Input: UpdateMealTemplateInput) -> MealTemplateWithItems:
    # Verify template exists and user owns it
    Row = FetchOne(
        """
        SELECT MealTemplateId AS MealTemplateId
        FROM MealTemplates
        WHERE MealTemplateId = ? AND UserId = ?;
        """,
        [MealTemplateId, UserId]
    )
    if Row is None:
        raise ValueError("Template not found.")

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
            [UserId, TemplateName, MealTemplateId]
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
                SELECT FoodId AS FoodId
                FROM Foods
                WHERE FoodId = ?;
                """,
                [Item.FoodId]
            )
            if FoodRow is None:
                raise ValueError("Food not found.")

            ExecuteQuery(
                """
                INSERT INTO MealTemplateItems (
                    MealTemplateItemId,
                    MealTemplateId,
                    FoodId,
                    MealType,
                    Quantity,
                    EntryNotes,
                    SortOrder
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                [
                    str(uuid.uuid4()),
                    MealTemplateId,
                    Item.FoodId,
                    Item.MealType,
                    Item.Quantity,
                    Item.EntryNotes,
                    Item.SortOrder
                ]
            )

    return GetMealTemplate(UserId, MealTemplateId)


def ApplyMealTemplate(UserId: str, MealTemplateId: str, LogDate: str) -> ApplyMealTemplateResponse:
    from app.utils.database import ExecuteQuery
    import uuid
    
    Template = GetMealTemplate(UserId, MealTemplateId)
    DailyLogItem = EnsureDailyLogForDate(UserId, LogDate)
    ExistingEntries = GetEntriesForLog(UserId, DailyLogItem.DailyLogId)
    NextSortOrder = max((Entry.SortOrder for Entry in ExistingEntries), default=-1) + 1

    if not Template.Items:
        return ApplyMealTemplateResponse(CreatedCount=0)

    CreatedCount = 0
    for Index, Item in enumerate(Template.Items):
        MealEntryId = str(uuid.uuid4())
        ExecuteQuery(
            """
            INSERT INTO MealEntries (
                MealEntryId,
                DailyLogId,
                MealType,
                FoodId,
                Quantity,
                EntryNotes,
                SortOrder
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            [
                MealEntryId,
                DailyLogItem.DailyLogId,
                Item.MealType,
                Item.FoodId,
                Item.Quantity,
                Item.EntryNotes,
                NextSortOrder + Index
            ]
        )
        CreatedCount += 1

    return ApplyMealTemplateResponse(CreatedCount=CreatedCount)
