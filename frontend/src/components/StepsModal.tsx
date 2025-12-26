import { FormEvent, useEffect, useState } from "react";

type StepsModalProps = {
  IsOpen: boolean;
  CurrentSteps: number;
  LogDate: string;
  MaxDate?: string;
  OnClose: () => void;
  OnSave: (Steps: number, LogDate: string) => Promise<void>;
};

export const StepsModal = ({ IsOpen, CurrentSteps, LogDate, MaxDate, OnClose, OnSave }: StepsModalProps) => {
  const [Steps, SetSteps] = useState("");
  const [SelectedDate, SetSelectedDate] = useState(LogDate);
  const [IsSaving, SetIsSaving] = useState(false);
  const [ErrorMessage, SetErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (IsOpen) {
      SetSteps("");
      SetSelectedDate(LogDate);
      SetErrorMessage(null);
    }
  }, [IsOpen, LogDate]);

  const HandleSubmit = async (Event: FormEvent) => {
    Event.preventDefault();
    SetErrorMessage(null);
    SetIsSaving(true);

    try {
      await OnSave(Number(Steps), SelectedDate);
      OnClose();
    } catch (ErrorValue) {
      SetErrorMessage("Failed to save steps. Please try again.");
    } finally {
      SetIsSaving(false);
    }
  };

  if (!IsOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={OnClose}
    >
      <div
        className="w-full max-w-md rounded-3xl bg-white p-6 shadow-Soft"
        onClick={(Event) => Event.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="Headline text-2xl">Update steps</h2>
          <button
            className="text-2xl text-Ink/60 hover:text-Ink"
            type="button"
            onClick={OnClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {CurrentSteps > 0 && SelectedDate === LogDate && (
          <div className="mb-4 rounded-2xl bg-Ink/5 p-3 text-sm">
            <div className="text-Ink/70">Current steps:</div>
            <div className="font-semibold text-Ink">{CurrentSteps.toLocaleString()} steps</div>
          </div>
        )}

        <form className="space-y-4" onSubmit={HandleSubmit}>
          <label className="space-y-2 text-sm">
            <span className="text-Ink/70">Log date</span>
            <input
              className="InputField"
              type="date"
              value={SelectedDate}
              max={MaxDate}
              onChange={(Event) => SetSelectedDate(Event.target.value)}
              required
            />
          </label>
          <label className="space-y-2 text-sm">
            <span className="text-Ink/70">Step count</span>
            <input
              className="InputField text-2xl font-semibold"
              type="number"
              min="0"
              step="1"
              value={Steps}
              onChange={(Event) => SetSteps(Event.target.value)}
              placeholder="0"
              autoFocus
              required
            />
          </label>

          {ErrorMessage && (
            <p className="text-sm text-red-500">{ErrorMessage}</p>
          )}

          <div className="flex gap-3">
            <button
              className="OutlineButton flex-1"
              type="button"
              onClick={OnClose}
              disabled={IsSaving}
            >
              Cancel
            </button>
            <button
              className="PillButton flex-1"
              type="submit"
              disabled={IsSaving}
            >
              {IsSaving ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
