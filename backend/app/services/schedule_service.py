import re
import uuid

from app.models.schemas import ScheduleSlot, ScheduleSlotInput
from app.utils.database import ExecuteQuery, FetchAll

TimePattern = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def NormalizeSlotTime(SlotTime: str) -> str:
    Match = TimePattern.match(SlotTime.strip())
    if not Match:
        raise ValueError("Invalid slot time.")
    return f"{Match.group(1)}:{Match.group(2)}"


def GetScheduleSlots(UserId: str) -> list[ScheduleSlot]:
    Rows = FetchAll(
        """
        SELECT
            ScheduleSlotId AS ScheduleSlotId,
            SlotName AS SlotName,
            SlotTime AS SlotTime,
            MealType AS MealType,
            SortOrder AS SortOrder
        FROM ScheduleSlots
        WHERE UserId = ?
        ORDER BY SortOrder, SlotTime, CreatedAt;
        """,
        [UserId]
    )

    Slots: list[ScheduleSlot] = []
    for Row in Rows:
        Slots.append(
            ScheduleSlot(
                ScheduleSlotId=Row["ScheduleSlotId"],
                SlotName=Row["SlotName"],
                SlotTime=Row["SlotTime"],
                MealType=Row["MealType"],
                SortOrder=int(Row["SortOrder"])
            )
        )
    return Slots


def UpdateScheduleSlots(UserId: str, Slots: list[ScheduleSlotInput]) -> list[ScheduleSlot]:
    ExistingRows = FetchAll(
        "SELECT ScheduleSlotId AS ScheduleSlotId FROM ScheduleSlots WHERE UserId = ?;",
        [UserId]
    )
    ExistingIds = {Row["ScheduleSlotId"] for Row in ExistingRows}
    KeepIds: list[str] = []

    for Slot in Slots:
        SlotTime = NormalizeSlotTime(Slot.SlotTime)
        SlotName = Slot.SlotName.strip()
        if not SlotName:
            raise ValueError("Slot name required.")
        SortOrder = max(0, int(Slot.SortOrder))
        if Slot.ScheduleSlotId and Slot.ScheduleSlotId in ExistingIds:
            ExecuteQuery(
                """
                UPDATE ScheduleSlots
                SET
                    SlotName = ?,
                    SlotTime = ?,
                    MealType = ?,
                    SortOrder = ?
                WHERE ScheduleSlotId = ? AND UserId = ?;
                """,
                [
                    SlotName,
                    SlotTime,
                    Slot.MealType,
                    SortOrder,
                    Slot.ScheduleSlotId,
                    UserId
                ]
            )
            KeepIds.append(Slot.ScheduleSlotId)
        else:
            ScheduleSlotId = str(uuid.uuid4())
            ExecuteQuery(
                """
                INSERT INTO ScheduleSlots (
                    ScheduleSlotId,
                    UserId,
                    SlotName,
                    SlotTime,
                    MealType,
                    SortOrder
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                [
                    ScheduleSlotId,
                    UserId,
                    SlotName,
                    SlotTime,
                    Slot.MealType,
                    SortOrder
                ]
            )
            KeepIds.append(ScheduleSlotId)

    RemovedIds = [SlotId for SlotId in ExistingIds if SlotId not in KeepIds]
    if RemovedIds:
        Placeholder = ",".join(["?"] * len(RemovedIds))
        ExecuteQuery(
            f"""
            UPDATE MealEntries
            SET ScheduleSlotId = NULL
            WHERE ScheduleSlotId IN ({Placeholder})
                AND DailyLogId IN (
                    SELECT DailyLogId FROM DailyLogs WHERE UserId = ?
                );
            """,
            [*RemovedIds, UserId]
        )
        ExecuteQuery(
            f"""
            DELETE FROM ScheduleSlots
            WHERE UserId = ? AND ScheduleSlotId IN ({Placeholder});
            """,
            [UserId, *RemovedIds]
        )

    return GetScheduleSlots(UserId)
