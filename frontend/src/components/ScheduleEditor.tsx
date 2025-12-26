import { useEffect, useState } from "react";
import { MealType, ScheduleSlot, ScheduleSlotInput } from "../models/Models";

const MealTypeOptions: { Label: string; Value: MealType }[] = [
  { Label: "Breakfast", Value: "Breakfast" },
  { Label: "Snack 1", Value: "Snack1" },
  { Label: "Lunch", Value: "Lunch" },
  { Label: "Snack 2", Value: "Snack2" },
  { Label: "Dinner", Value: "Dinner" },
  { Label: "Evening Snack", Value: "Snack3" }
];

const DefaultDraftSlots = (): ScheduleSlotInput[] => [
  { SlotName: "Breakfast", SlotTime: "07:30", MealType: "Breakfast", SortOrder: 0 },
  { SlotName: "Morning snack", SlotTime: "10:30", MealType: "Snack1", SortOrder: 1 },
  { SlotName: "Lunch", SlotTime: "12:30", MealType: "Lunch", SortOrder: 2 },
  { SlotName: "Afternoon snack", SlotTime: "15:30", MealType: "Snack2", SortOrder: 3 },
  { SlotName: "Dinner", SlotTime: "19:00", MealType: "Dinner", SortOrder: 4 },
  { SlotName: "Evening snack", SlotTime: "21:00", MealType: "Snack3", SortOrder: 5 }
];

type ScheduleEditorProps = {
  IsOpen: boolean;
  Slots: ScheduleSlot[];
  Title?: string;
  Prompt?: string;
  AllowClose?: boolean;
  OnClose: () => void;
  OnSave: (Slots: ScheduleSlotInput[]) => Promise<void>;
};

export const ScheduleEditor = ({
  IsOpen,
  Slots,
  Title = "Build your schedule",
  Prompt = "Pick the check-ins you want and the time for each one.",
  AllowClose = true,
  OnClose,
  OnSave
}: ScheduleEditorProps) => {
  const [DraftSlots, SetDraftSlots] = useState<ScheduleSlotInput[]>([]);
  const [IsSaving, SetIsSaving] = useState(false);
  const [ErrorMessage, SetErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!IsOpen) {
      return;
    }
    if (Slots.length > 0) {
      SetDraftSlots(
        Slots.map((Slot, Index) => ({
          ScheduleSlotId: Slot.ScheduleSlotId,
          SlotName: Slot.SlotName,
          SlotTime: Slot.SlotTime,
          MealType: Slot.MealType,
          SortOrder: Index
        }))
      );
    } else {
      SetDraftSlots(DefaultDraftSlots());
    }
  }, [IsOpen, Slots]);

  const UpdateSlot = (Index: number, Updates: Partial<ScheduleSlotInput>) => {
    SetDraftSlots((Current) =>
      Current.map((Slot, SlotIndex) => (SlotIndex === Index ? { ...Slot, ...Updates } : Slot))
    );
  };

  const HandleRemove = (Index: number) => {
    SetDraftSlots((Current) => Current.filter((_, SlotIndex) => SlotIndex !== Index));
  };

  const HandleAddSlot = () => {
    SetDraftSlots((Current) => [
      ...Current,
      {
        SlotName: "New check-in",
        SlotTime: "09:00",
        MealType: "Snack1",
        SortOrder: Current.length
      }
    ]);
  };

  const HandleSave = async () => {
    SetErrorMessage(null);
    SetIsSaving(true);

    const Cleaned = DraftSlots.map((Slot, Index) => ({
      ScheduleSlotId: Slot.ScheduleSlotId ?? undefined,
      SlotName: Slot.SlotName.trim() || `Check-in ${Index + 1}`,
      SlotTime: Slot.SlotTime,
      MealType: Slot.MealType,
      SortOrder: Index
    }));

    try {
      await OnSave(Cleaned);
    } catch (ErrorValue) {
      SetErrorMessage("Failed to save schedule.");
    } finally {
      SetIsSaving(false);
    }
  };

  if (!IsOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-Ink/40 px-4 py-6">
      <div className="w-full max-w-2xl rounded-3xl bg-white p-6 shadow-Soft">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.2em] text-Ink/60">Let us set things up</p>
          <h2 className="Headline text-2xl">{Title}</h2>
          <p className="text-sm text-Ink/70">{Prompt}</p>
        </div>

        <div className="mt-4 space-y-3">
          {DraftSlots.map((Slot, Index) => (
            <div key={Slot.ScheduleSlotId ?? `${Slot.SlotName}-${Index}`} className="grid gap-3 md:grid-cols-12">
              <label className="space-y-1 text-sm md:col-span-5">
                <span className="text-Ink/70">Check-in name</span>
                <input
                  className="InputField"
                  value={Slot.SlotName}
                  onChange={(Event) => UpdateSlot(Index, { SlotName: Event.target.value })}
                />
              </label>
              <label className="space-y-1 text-sm md:col-span-3">
                <span className="text-Ink/70">Time</span>
                <input
                  className="InputField"
                  type="time"
                  value={Slot.SlotTime}
                  onChange={(Event) => UpdateSlot(Index, { SlotTime: Event.target.value })}
                />
              </label>
              <label className="space-y-1 text-sm md:col-span-3">
                <span className="text-Ink/70">Meal type</span>
                <select
                  className="InputField"
                  value={Slot.MealType}
                  onChange={(Event) => UpdateSlot(Index, { MealType: Event.target.value as MealType })}
                >
                  {MealTypeOptions.map((Option) => (
                    <option key={Option.Value} value={Option.Value}>
                      {Option.Label}
                    </option>
                  ))}
                </select>
              </label>
              <div className="flex items-end md:col-span-1">
                <button className="OutlineButton CompactButton" type="button" onClick={() => HandleRemove(Index)}>
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <button className="OutlineButton" type="button" onClick={HandleAddSlot}>
            Add check-in
          </button>
          <div className="flex flex-wrap gap-2">
            {AllowClose && (
              <button className="OutlineButton" type="button" onClick={OnClose}>
                Not now
              </button>
            )}
            <button className="PillButton" type="button" onClick={HandleSave} disabled={IsSaving}>
              {IsSaving ? "Saving" : "Save schedule"}
            </button>
          </div>
        </div>
        {ErrorMessage && <p className="mt-3 text-sm text-red-500">{ErrorMessage}</p>}
      </div>
    </div>
  );
};
