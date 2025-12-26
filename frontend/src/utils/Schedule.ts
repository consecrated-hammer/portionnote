import { MealEntryWithFood, ScheduleSlot } from "../models/Models";

export type NextCheckIn = {
  SlotName: string;
  SlotTime: string;
  IsTomorrow: boolean;
};

export const ParseMinutes = (SlotTime: string) => {
  const [Hours, Minutes] = SlotTime.split(":").map((Value) => Number(Value));
  if (!Number.isFinite(Hours) || !Number.isFinite(Minutes)) {
    return 0;
  }
  return Hours * 60 + Minutes;
};

export const FormatSlotTimeLabel = (SlotTime: string, ReferenceDate: Date) => {
  const [Hours, Minutes] = SlotTime.split(":").map((Value) => Number(Value));
  const LocalDate = new Date(ReferenceDate);
  if (Number.isFinite(Hours) && Number.isFinite(Minutes)) {
    LocalDate.setHours(Hours, Minutes, 0, 0);
  }
  return LocalDate.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
};

export const BuildNextCheckIn = (
  Slots: ScheduleSlot[],
  Entries: MealEntryWithFood[],
  Now: Date
): NextCheckIn | null => {
  if (Slots.length === 0) {
    return null;
  }

  const SortedSlots = [...Slots].sort((Left, Right) => {
    const OrderDiff = Left.SortOrder - Right.SortOrder;
    if (OrderDiff !== 0) {
      return OrderDiff;
    }
    return ParseMinutes(Left.SlotTime) - ParseMinutes(Right.SlotTime);
  });

  const SlotMap = new Map(SortedSlots.map((Slot) => [Slot.ScheduleSlotId, Slot]));
  const CompletedSlotIds = new Set(
    Entries.filter((Entry) => Entry.ScheduleSlotId).map((Entry) => Entry.ScheduleSlotId as string)
  );

  const LastEntry = [...Entries]
    .filter((Entry) => Entry.CreatedAt)
    .sort((Left, Right) => {
      const LeftTime = new Date(Left.CreatedAt as string).getTime();
      const RightTime = new Date(Right.CreatedAt as string).getTime();
      return LeftTime - RightTime;
    })
    .pop();

  const NowMinutes = Now.getHours() * 60 + Now.getMinutes();
  const LastSlotMinutes = LastEntry?.ScheduleSlotId
    ? ParseMinutes(SlotMap.get(LastEntry.ScheduleSlotId)?.SlotTime ?? "00:00")
    : null;
  const ReferenceMinutes = LastSlotMinutes !== null ? Math.max(NowMinutes, LastSlotMinutes) : NowMinutes;

  const NextSlot =
    SortedSlots.find(
      (Slot) => !CompletedSlotIds.has(Slot.ScheduleSlotId) && ParseMinutes(Slot.SlotTime) > ReferenceMinutes
    ) ?? SortedSlots.find((Slot) => !CompletedSlotIds.has(Slot.ScheduleSlotId)) ?? SortedSlots[0];

  if (!NextSlot) {
    return null;
  }

  const IsTomorrow = ParseMinutes(NextSlot.SlotTime) <= ReferenceMinutes;

  return {
    SlotName: NextSlot.SlotName,
    SlotTime: NextSlot.SlotTime,
    IsTomorrow
  };
};
