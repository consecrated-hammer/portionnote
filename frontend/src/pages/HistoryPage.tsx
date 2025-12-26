import { useEffect, useState } from "react";
import axios from "axios";
import { CreateDailyLog, CreateMealEntry, DeleteMealEntry, GetDailyLog, GetFoods, GetUserSettings } from "../services/ApiClient";
import { DailyLog, DailyTotals, Food, MealEntryWithFood, Targets } from "../models/Models";
import { QuickMealEntry } from "../components/QuickMealEntry";
import { FormatLocalDate } from "../utils/DateUtils";
import { AppLogger } from "../utils/Logger";

const DefaultTargets: Targets = {
  DailyCalorieTarget: 1498,
  ProteinTargetMin: 70,
  ProteinTargetMax: 188,
  StepKcalFactor: 0.04,
  StepTarget: 8500
};

type DayEntry = {
  LogDate: string;
  DailyLog: DailyLog | null;
  Entries: MealEntryWithFood[];
  Totals: DailyTotals | null;
};

const GetColorClass = (Value: number, Target: number, IsProtein = false) => {
  const Percent = Target > 0 ? (Value / Target) * 100 : 0;
  if (IsProtein) {
    if (Percent >= 100) return "text-green-600";
    if (Percent >= 80) return "text-yellow-600";
    return "text-red-600";
  }
  if (Percent <= 100) return "text-green-600";
  if (Percent <= 110) return "text-yellow-600";
  return "text-red-600";
};

const FormatDate = (DateString: string) => {
  const DateObj = new Date(DateString + "T00:00:00");
  const Today = new Date();
  Today.setHours(0, 0, 0, 0);
  const Yesterday = new Date(Today);
  Yesterday.setDate(Yesterday.getDate() - 1);

  if (DateObj.getTime() === Today.getTime()) return "Today";
  if (DateObj.getTime() === Yesterday.getTime()) return "Yesterday";

  return DateObj.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
};

const GetMealTypeLabel = (MealTypeValue: string) => {
  if (MealTypeValue === "Snack1") return "Morning Snack";
  if (MealTypeValue === "Snack2") return "Afternoon Snack";
  if (MealTypeValue === "Snack3") return "Evening Snack";
  return MealTypeValue;
};

const GetLastNDays = (Count: number): string[] => {
  const Days: string[] = [];
  const Today = new Date();
  for (let i = 0; i < Count; i++) {
    const DateObj = new Date(Today);
    DateObj.setDate(DateObj.getDate() - i);
    Days.push(FormatLocalDate(DateObj));
  }
  return Days;
};

export const HistoryPage = () => {
  const [Days, SetDays] = useState<DayEntry[]>([]);
  const [Foods, SetFoods] = useState<Food[]>([]);
  const [Targets, SetTargets] = useState<Targets>(DefaultTargets);
  const [ExpandedDay, SetExpandedDay] = useState<string | null>(null);
  const [IsLoading, SetIsLoading] = useState(true);
  const [DaysToShow, SetDaysToShow] = useState(7);
  const [IsEntryModalOpen, SetIsEntryModalOpen] = useState(false);
  const [EntryModalDate, SetEntryModalDate] = useState<string | null>(null);
  const [EntryToEdit, SetEntryToEdit] = useState<MealEntryWithFood | null>(null);
  const [ErrorMessage, SetErrorMessage] = useState<string | null>(null);

  const LoadFoods = async () => {
    try {
      const FoodItems = await GetFoods();
      SetFoods(FoodItems);
    } catch (ErrorValue) {
      console.error("Failed to load foods", ErrorValue);
      SetErrorMessage("Failed to load foods.");
    }
  };

  const LoadData = async () => {
    AppLogger.debug("Loading history data");
    SetIsLoading(true);
    SetErrorMessage(null);

    try {
      AppLogger.debug("Fetching settings");
      const Settings = await GetUserSettings();
      SetTargets(Settings.Targets ?? DefaultTargets);
      AppLogger.debug("Settings loaded", { HasSettings: Boolean(Settings) });
    } catch (ErrorValue) {
      console.error("Failed to load settings", ErrorValue);
      SetErrorMessage("Failed to load settings");
    }

    const DateList = GetLastNDays(DaysToShow);
    AppLogger.debug("Loading days", { DayCount: DateList.length });
    const DayData: DayEntry[] = [];

    for (const DateString of DateList) {
      try {
        AppLogger.debug("Fetching day", { Date: DateString });
        const Response = await GetDailyLog(DateString);
        DayData.push({
          LogDate: DateString,
          DailyLog: Response.DailyLog,
          Entries: Response.Entries ?? [],
          Totals: Response.Totals ?? null
        });
      } catch (ErrorValue) {
        if (axios.isAxiosError(ErrorValue) && ErrorValue.response?.status === 404) {
          AppLogger.debug("No data for day", { Date: DateString });
          DayData.push({
            LogDate: DateString,
            DailyLog: null,
            Entries: [],
            Totals: null
          });
        } else {
          console.error("Error loading day", DateString, ErrorValue);
          DayData.push({
            LogDate: DateString,
            DailyLog: null,
            Entries: [],
            Totals: null
          });
        }
      }
    }

    AppLogger.debug("Days loaded", { Count: DayData.length });
    const DaysWithData = DayData.filter((Day) => {
      const WeightValue = Day.DailyLog?.WeightKg ?? 0;
      const HasLog = Day.DailyLog !== null && (Day.DailyLog.Steps > 0 || Day.Entries.length > 0 || WeightValue > 0);
      return HasLog;
    });
    AppLogger.debug("Days with data", { Count: DaysWithData.length });
    SetDays(DaysWithData);
    SetIsLoading(false);
  };

  useEffect(() => {
    void LoadData();
  }, [DaysToShow]);

  useEffect(() => {
    void LoadFoods();
  }, []);

  const HandleToggleExpand = (LogDate: string) => {
    SetExpandedDay(ExpandedDay === LogDate ? null : LogDate);
  };

  const HandleCopyToToday = (Entries: MealEntryWithFood[]) => {
    // TODO: Implement copy meals to today functionality
    AppLogger.debug("Copy to today", { EntryCount: Entries.length });
  };

  const HandleOpenEntryModal = (Day: DayEntry, Entry?: MealEntryWithFood) => {
    SetEntryModalDate(Day.LogDate);
    SetEntryToEdit(Entry ?? null);
    SetIsEntryModalOpen(true);
  };

  const HandleCloseEntryModal = () => {
    SetIsEntryModalOpen(false);
    SetEntryToEdit(null);
    SetEntryModalDate(null);
  };

  const EnsureLogForDate = async (LogDate: string): Promise<DailyLog> => {
    const ExistingLog = Days.find((Day) => Day.LogDate === LogDate)?.DailyLog;
    if (ExistingLog) return ExistingLog;
    const Created = await CreateDailyLog(LogDate, 0);
    return Created.DailyLog;
  };

  const HandleSaveEntry = async (FoodId: string, MealType: MealEntryWithFood["MealType"], Quantity: number) => {
    if (!EntryModalDate) return;
    try {
      const LogItem = await EnsureLogForDate(EntryModalDate);
      const DayEntry = Days.find((Day) => Day.LogDate === EntryModalDate);
      const SortOrder = EntryToEdit?.SortOrder ?? DayEntry?.Entries.length ?? 0;

      if (EntryToEdit) {
        await DeleteMealEntry(EntryToEdit.MealEntryId);
      }

      await CreateMealEntry({
        DailyLogId: LogItem.DailyLogId,
        MealType,
        FoodId,
        Quantity,
        EntryNotes: EntryToEdit?.EntryNotes ?? null,
        SortOrder,
        ScheduleSlotId: null
      });

      await LoadData();
      HandleCloseEntryModal();
    } catch (ErrorValue) {
      console.error("Failed to save entry", ErrorValue);
      SetErrorMessage("Failed to save entry.");
    }
  };

  const HandleDeleteEntry = async (MealEntryId: string) => {
    try {
      await DeleteMealEntry(MealEntryId);
      await LoadData();
    } catch (ErrorValue) {
      console.error("Failed to delete entry", ErrorValue);
      SetErrorMessage("Failed to delete entry.");
    }
  };

  const HandleLoadMore = () => {
    SetDaysToShow(DaysToShow + 7);
  };

  if (IsLoading) {
    return (
      <section className="Card text-sm text-Ink/70">
        Loading history...
        <div className="mt-2 text-xs text-Ink/50">Check console for details</div>
      </section>
    );
  }

  return (
    <>
      {IsEntryModalOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-Ink/40 px-4 py-6">
          <div className="w-full max-w-2xl rounded-3xl bg-white p-6 shadow-Soft">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="Headline text-xl">{EntryToEdit ? "Edit entry" : "Add entry"}</h3>
                {EntryModalDate && (
                  <p className="text-sm text-Ink/60">Log date: {EntryModalDate}</p>
                )}
              </div>
              <button
                type="button"
                onClick={HandleCloseEntryModal}
                className="rounded-full p-2 text-Ink/50 hover:bg-Ink/10"
                aria-label="Close"
              >
                <span className="material-icons text-lg">close</span>
              </button>
            </div>
            <div className="mt-4">
              {Foods.length === 0 ? (
                <div className="text-sm text-Ink/60">
                  Add foods first to log meals.
                </div>
              ) : (
                <QuickMealEntry
                  Foods={Foods}
                  Templates={[]}
                  RecentEntries={[]}
                  DefaultMealType={EntryToEdit?.MealType}
                  PreselectedFoodId={EntryToEdit?.FoodId ?? undefined}
                  InitialQuantity={EntryToEdit?.Quantity}
                  OnSubmit={HandleSaveEntry}
                  OnCancel={HandleCloseEntryModal}
                  AutoFocus
                />
              )}
            </div>
          </div>
        </div>
      )}

      <section className="space-y-4">
        {ErrorMessage && (
          <div className="Card text-sm text-red-500">
            {ErrorMessage}
          </div>
        )}

        <div className="Card">
          <h2 className="Headline text-2xl">History</h2>
          <p className="mt-1 text-sm text-Ink/70">
            View and edit past entries
          </p>
        </div>

        {Days.map((Day) => {
          const IsExpanded = ExpandedDay === Day.LogDate;
          const HasData = Day.Totals !== null;

          return (
            <div key={Day.LogDate} className="Card space-y-3">
              <button
                className="w-full text-left"
                type="button"
                onClick={() => HandleToggleExpand(Day.LogDate)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="Headline text-lg">{FormatDate(Day.LogDate)}</h3>
                    <p className="text-xs text-Ink/60">{Day.LogDate}</p>
                  </div>
                  <div className="text-2xl text-Ink/40">
                    {IsExpanded ? "−" : "+"}
                  </div>
                </div>

                {HasData && Day.Totals && (
                  <div className="mt-3 grid grid-cols-3 gap-3 text-center text-sm">
                    <div>
                      <div className="text-xs text-Ink/60">Calories</div>
                      <div className={`text-lg font-semibold ${GetColorClass(Day.Totals.TotalCalories, Targets.DailyCalorieTarget)}`}>
                        {Day.Totals.TotalCalories.toLocaleString()}
                      </div>
                      <div className="text-xs text-Ink/50">/ {Targets.DailyCalorieTarget.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-xs text-Ink/60">Protein</div>
                      <div className={`text-lg font-semibold ${GetColorClass(Day.Totals.TotalProtein, Targets.ProteinTargetMin, true)}`}>
                        {Day.Totals.TotalProtein.toLocaleString()}g
                      </div>
                      <div className="text-xs text-Ink/50">/ {Targets.ProteinTargetMin.toLocaleString()}g</div>
                    </div>
                    <div>
                      <div className="text-xs text-Ink/60">Steps</div>
                      <div className={`text-lg font-semibold ${GetColorClass(Day.DailyLog?.Steps ?? 0, Targets.StepTarget)}`}>
                        {(Day.DailyLog?.Steps ?? 0).toLocaleString()}
                      </div>
                      <div className="text-xs text-Ink/50">/ {Targets.StepTarget.toLocaleString()}</div>
                    </div>
                  </div>
                )}

                {(Day.DailyLog?.WeightKg ?? 0) > 0 && (
                  <div className="mt-3 text-center text-xs text-Ink/60">
                    Weight{" "}
                    <span className="font-semibold text-Ink">
                      {Day.DailyLog?.WeightKg?.toFixed(1)} kg
                    </span>
                  </div>
                )}

                {!HasData && (
                  <div className="mt-3 text-center text-sm text-Ink/50">
                    No data logged
                  </div>
                )}
              </button>

              {IsExpanded && (
                <div className="space-y-3 border-t border-Ink/10 pt-3">
                  {Day.Entries.length > 0 ? (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-semibold text-Ink/70">Meals</h4>
                        <button
                          type="button"
                          className="text-xs font-semibold text-blue-600 hover:text-blue-700"
                          onClick={(Event) => {
                            Event.stopPropagation();
                            HandleOpenEntryModal(Day);
                          }}
                        >
                          + Add entry
                        </button>
                      </div>
                      {Day.Entries.map((Entry) => {
                        const CanEdit = !!Entry.FoodId;
                        return (
                          <div
                            key={Entry.MealEntryId}
                            className="flex items-center justify-between rounded-xl bg-white/80 p-3 text-sm"
                          >
                            <div>
                              <div className="font-medium text-Ink">{Entry.FoodName}</div>
                              <div className="text-xs text-Ink/60">
                                {GetMealTypeLabel(Entry.MealType)} • Qty: {Entry.Quantity}
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="text-right text-xs">
                                <div className="font-semibold text-Ink">
                                  {Math.round(Entry.CaloriesPerServing * Entry.Quantity)} cal
                                </div>
                                <div className="text-Ink/60">
                                  {(Entry.ProteinPerServing * Entry.Quantity).toFixed(1)}g protein
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                <button
                                  type="button"
                                  onClick={() => CanEdit && HandleOpenEntryModal(Day, Entry)}
                                  disabled={!CanEdit}
                                  className="flex h-9 w-9 items-center justify-center rounded-lg text-Ink/50 hover:bg-Ink/10 hover:text-Ink disabled:opacity-40"
                                  aria-label="Edit entry"
                                >
                                  <span className="material-icons text-base">edit</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => HandleDeleteEntry(Entry.MealEntryId)}
                                  className="flex h-9 w-9 items-center justify-center rounded-lg text-red-500/70 hover:bg-red-50 hover:text-red-600"
                                  aria-label="Delete entry"
                                >
                                  <span className="material-icons text-base">delete</span>
                                </button>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="space-y-2 text-center text-sm text-Ink/50">
                      <p>No meals logged</p>
                      <button
                        type="button"
                        className="text-xs font-semibold text-blue-600 hover:text-blue-700"
                        onClick={(Event) => {
                          Event.stopPropagation();
                          HandleOpenEntryModal(Day);
                        }}
                      >
                        + Add entry
                      </button>
                    </div>
                  )}

                  <div className="flex gap-2">
                    {Day.Entries.length > 0 && (
                      <button
                        className="OutlineButton flex-1 text-sm"
                        type="button"
                        onClick={(Event) => {
                          Event.stopPropagation();
                          HandleCopyToToday(Day.Entries);
                        }}
                      >
                        Copy to today
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {Days.length === 0 && (
          <div className="Card text-center text-sm text-Ink/50">
            No history yet. Start logging on the Today page!
          </div>
        )}

        {Days.length > 0 && (
          <button
            className="OutlineButton w-full"
            type="button"
            onClick={HandleLoadMore}
          >
            Load more
          </button>
        )}
      </section>
    </>
  );
};
