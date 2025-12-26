import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  CreateDailyLog,
  GetDailyLog,
  GetUserSettings,
  UpdateDailySteps,
  UpdateUserSettings
} from "../services/ApiClient";
import {
  DailyLog,
  DailyTotals,
  MealEntryWithFood,
  Targets
} from "../models/Models";
import { StepsModal } from "../components/StepsModal";
import { WeightModal } from "../components/WeightModal";
import { GetToday } from "../utils/DateUtils";
import { UseAuth } from "../contexts/AuthContext";

const FormatToday = () => GetToday();

const DefaultTargets: Targets = {
  DailyCalorieTarget: 1498,
  ProteinTargetMin: 70,
  ProteinTargetMax: 188,
  StepKcalFactor: 0.04,
  StepTarget: 8500
};

const DefaultLayout = ["snapshot", "quickadd"] as const;
type SectionKey = (typeof DefaultLayout)[number];

const NormalizeLayout = (Layout: string[]) => {
  const Valid = new Set(DefaultLayout);
  const Ordered = Layout.filter((Key) => Valid.has(Key as SectionKey));
  const Missing = DefaultLayout.filter((Key) => !Ordered.includes(Key));
  return [...Ordered, ...Missing] as SectionKey[];
};

export const TodayPage = () => {
  const { CheckAuth } = UseAuth();
  const Navigate = useNavigate();
  const [SearchParams, SetSearchParams] = useSearchParams();
  const QuickAddWrapRef = useRef<HTMLDivElement>(null);
  const QuickAddButtonRef = useRef<HTMLButtonElement>(null);

  const [IsQuickAddOpen, SetIsQuickAddOpen] = useState(false);
  const [DailyLogItem, SetDailyLogItem] = useState<DailyLog | null>(null);
  const [Entries, SetEntries] = useState<MealEntryWithFood[]>([]);
  const [Totals, SetTotals] = useState<DailyTotals | null>(null);
  const [Targets, SetTargets] = useState<Targets>(DefaultTargets);
  const [IsLoading, SetIsLoading] = useState(true);
  const [ErrorMessage, SetErrorMessage] = useState<string | null>(null);
  const [QuickAddPosition, SetQuickAddPosition] = useState<"above" | "below">("below");
  const [IsStepsModalOpen, SetIsStepsModalOpen] = useState(false);
  const [IsWeightModalOpen, SetIsWeightModalOpen] = useState(false);
  const [BarOrder, SetBarOrder] = useState<string[]>(["Calories", "Protein", "Steps", "Carbs", "Fat", "Fibre", "SaturatedFat", "Sugar", "Sodium"]);
  const [DraggedIndex, SetDraggedIndex] = useState<number | null>(null);
  const [DropTargetIndex, SetDropTargetIndex] = useState<number | null>(null);
  const [WeekOffset, SetWeekOffset] = useState(0);
  const [WeekData, SetWeekData] = useState<Record<string, number>>({});

  const TodayDate = FormatToday();
  const HasEntries = Entries.length > 0;
  const HasSteps = DailyLogItem?.LogDate === TodayDate && (DailyLogItem?.Steps ?? 0) > 0;
  const HasLogData = HasEntries || HasSteps;

  const LoadWeekData = async (Offset: number) => {
    const Today = new Date();
    const TodayDayOfWeek = Today.getDay();
    const MondayOffset = TodayDayOfWeek === 0 ? -6 : 1 - TodayDayOfWeek;
    
    const WeekStart = new Date(Today);
    WeekStart.setDate(Today.getDate() + MondayOffset + (Offset * 7));
    
    const NewWeekData: Record<string, number> = {};
    
    // Load all 7 days
    for (let I = 0; I < 7; I++) {
      const DayDate = new Date(WeekStart);
      DayDate.setDate(WeekStart.getDate() + I);
      const DateStr = DayDate.toISOString().slice(0, 10);
      
      try {
        const Response = await GetDailyLog(DateStr);
        NewWeekData[DateStr] = Response.Totals?.TotalCalories ?? 0;
      } catch {
        NewWeekData[DateStr] = 0;
      }
    }
    
    SetWeekData(NewWeekData);
  };

  const LoadTodayData = async () => {
    SetIsLoading(true);
    SetErrorMessage(null);

    try {
      const Settings = await GetUserSettings();
      SetTargets(Settings.Targets ?? DefaultTargets);
      SetBarOrder(Settings.Targets?.BarOrder ?? ["Calories", "Protein", "Steps", "Carbs", "Fat", "Fibre", "SaturatedFat", "Sugar", "Sodium"]);
    } catch {
      SetErrorMessage("Failed to load settings.");
    }

    try {
      const Response = await GetDailyLog(TodayDate);
      SetDailyLogItem(Response.DailyLog);
      SetEntries(Response.Entries ?? []);
      SetTotals(Response.Totals ?? null);
      
      // Update week data for today
      SetWeekData(Prev => ({
        ...Prev,
        [TodayDate]: Response.Totals?.TotalCalories ?? 0
      }));
    } catch (ErrorValue) {
      SetErrorMessage("Failed to load today.");
    } finally {
      SetIsLoading(false);
    }
    
    // Load week data for graph
    await LoadWeekData(WeekOffset);
  };

  useEffect(() => {
    void LoadTodayData();
  }, []);

  useEffect(() => {
    const Mode = SearchParams.get("mode");
    if (Mode === "steps") {
      SetIsStepsModalOpen(true);
    }
    if (Mode === "weight") {
      SetIsWeightModalOpen(true);
    }
    if (Mode) {
      const NextParams = new URLSearchParams(SearchParams);
      NextParams.delete("mode");
      SetSearchParams(NextParams, { replace: true });
    }
  }, [SearchParams, SetSearchParams]);

  useEffect(() => {
    const HandleRefresh = () => void LoadTodayData();
    window.addEventListener("portionnote:refresh", HandleRefresh);
    return () => window.removeEventListener("portionnote:refresh", HandleRefresh);
  }, []);

  useEffect(() => {
    void LoadWeekData(WeekOffset);
  }, [WeekOffset]);

  useEffect(() => {
    const HandleClickOutside = (Event: MouseEvent) => {
      if (IsQuickAddOpen && QuickAddWrapRef.current && !QuickAddWrapRef.current.contains(Event.target as Node)) {
        SetIsQuickAddOpen(false);
      }
    };
    document.addEventListener("mousedown", HandleClickOutside);
    return () => document.removeEventListener("mousedown", HandleClickOutside);
  }, [IsQuickAddOpen]);

  const HandleQuickAdd = (Mode: string, MealType?: string) => {
    SetIsQuickAddOpen(false);
    if (Mode === "steps") {
      SetIsStepsModalOpen(true);
      return;
    }
    if (Mode === "weight") {
      SetIsWeightModalOpen(true);
      return;
    }
    const Params = new URLSearchParams();
    Params.set("mode", Mode);
    Params.set("date", TodayDate);
    if (MealType) {
      Params.set("mealType", MealType);
    }
    Navigate(`/log?${Params.toString()}`);
  };

  const ToggleQuickAdd = () => {
    if (!IsQuickAddOpen && QuickAddButtonRef.current) {
      const ButtonRect = QuickAddButtonRef.current.getBoundingClientRect();
      const SpaceBelow = window.innerHeight - ButtonRect.bottom;
      SetQuickAddPosition(SpaceBelow > 300 ? "below" : "above");
    }
    SetIsQuickAddOpen((Value) => !Value);
  };

  const GetLogForDate = async (LogDate: string): Promise<DailyLog | null> => {
    if (LogDate === TodayDate) {
      return DailyLogItem;
    }
    const Response = await GetDailyLog(LogDate);
    return Response.DailyLog;
  };

  const HandleSaveSteps = async (Steps: number, LogDate: string) => {
    const ExistingLog = await GetLogForDate(LogDate);
    if (ExistingLog) {
      await UpdateDailySteps(LogDate, Steps);
    } else {
      await CreateDailyLog(LogDate, Steps);
    }
    await LoadTodayData();
  };

  const HandleSaveWeight = async (WeightKg: number, LogDate: string) => {
    const ExistingLog = await GetLogForDate(LogDate);
    if (ExistingLog) {
      await UpdateDailySteps(LogDate, ExistingLog.Steps, WeightKg);
    } else {
      await CreateDailyLog(LogDate, 0, WeightKg);
    }
    await CheckAuth();
    await LoadTodayData();
  };

  const HandleDragStart = (Index: number) => {
    SetDraggedIndex(Index);
  };

  const HandleDragOver = (E: React.DragEvent, Index: number) => {
    E.preventDefault();
    if (DraggedIndex === null || DraggedIndex === Index) return;

    SetDropTargetIndex(Index);

    const NewOrder = [...BarOrder];
    const [Dragged] = NewOrder.splice(DraggedIndex, 1);
    NewOrder.splice(Index, 0, Dragged);
    
    SetBarOrder(NewOrder);
    SetDraggedIndex(Index);
  };

  const HandleDragEnd = async () => {
    SetDraggedIndex(null);
    SetDropTargetIndex(null);
    try {
      await UpdateUserSettings({ BarOrder });
    } catch {
      // Silently fail, order will revert on reload
    }
  };

  const FanItems = [
    { Label: "Log a meal", Emoji: "🍽️", OnClick: () => HandleQuickAdd("meal"), AngleDeg: 180 },
    { Label: "Update steps", Emoji: "👟", OnClick: () => HandleQuickAdd("steps"), AngleDeg: 130 },
    { Label: "Update weight", IconPath: "/images/scale.png", OnClick: () => HandleQuickAdd("weight"), AngleDeg: 230 }
  ];

  const RadiusPx = 60;

  const ProgressBar = ({
    Label,
    Value,
    Target,
    Accent,
    OnClick
  }: {
    Label: string;
    Value: number;
    Target: number;
    Accent: string;
    OnClick?: () => void;
  }) => {
    const PercentOfTarget = Target > 0 ? (Value / Target) * 100 : 0;
    const DisplayPercent = Math.min(100, Math.round(PercentOfTarget));
    const IsOverTarget = PercentOfTarget > 100;
    const BarColor = IsOverTarget ? "#f26b5b" : Accent; // Coral red when over target
    
    return (
      <div 
        className={`py-3 ${OnClick ? "cursor-pointer hover:bg-white/50" : ""} transition-colors`}
        onClick={OnClick}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-semibold text-Ink/80">{Label}</span>
          <span className={`text-sm ${IsOverTarget ? "text-Coral font-semibold" : "text-Ink/60"}`}>
            {Value.toLocaleString()} / {Target.toLocaleString()}
          </span>
        </div>
        <div className="h-2 rounded-full bg-white/70">
          <div
            className="h-2 rounded-full transition-all duration-300"
            style={{ width: `${DisplayPercent}%`, backgroundColor: BarColor }}
          />
        </div>
      </div>
    );
  };

  const WeeklySnapshotBars = () => {
    // Calculate week (Monday - Sunday) with offset
    const Today = new Date();
    const TodayDayOfWeek = Today.getDay(); // 0 = Sunday, 1 = Monday, etc.
    const MondayOffset = TodayDayOfWeek === 0 ? -6 : 1 - TodayDayOfWeek; // Get Monday of current week
    
    const WeekStart = new Date(Today);
    WeekStart.setDate(Today.getDate() + MondayOffset + (WeekOffset * 7));
    
    const WeekEnd = new Date(WeekStart);
    WeekEnd.setDate(WeekStart.getDate() + 6);
    
    const WeekDays = Array.from({ length: 7 }, (_, I) => {
      const DayDate = new Date(WeekStart);
      DayDate.setDate(WeekStart.getDate() + I);
      const DateStr = DayDate.toISOString().slice(0, 10);
      const IsToday = DateStr === TodayDate;
      const IsTodayInCurrentWeek = IsToday && WeekOffset === 0;
      const Value = IsTodayInCurrentWeek ? (Totals?.TotalCalories ?? 0) : (WeekData[DateStr] ?? 0);
      const PercentOfTarget = Targets.DailyCalorieTarget > 0 ? (Value / Targets.DailyCalorieTarget) * 100 : 0;
      
      return {
        Label: ["M", "T", "W", "T", "F", "S", "S"][I],
        Date: DateStr,
        IsToday,
        Value,
        PercentOfTarget
      };
    });
    
    const Values = WeekDays.map(d => d.Value);
    const TargetValue = Targets.DailyCalorieTarget;
    const MaxDataValue = Math.max(...Values, 0);
    const RawMax = Math.max(MaxDataValue, TargetValue);
    const DisplayMax = Math.max(RawMax * 1.15, 100);
    const RoundedMax = Math.ceil(DisplayMax / 100) * 100;
    const AxisLabelColumnWidth = 60;
    const ChartPaddingRight = 12;
    
    const FormatDate = (Date: Date) =>
      Date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
    
    const FormatValueLabel = (Value: number) => Value.toLocaleString();
    
    const AxisMarks = Array.from({ length: 5 }, (_, Index) => ({
      Value: Math.round(RoundedMax * (Index / 4))
    }));
    
    const TargetHeight = RoundedMax > 0 ? Math.min(100, (TargetValue / RoundedMax) * 100) : 0;
    
    const DetermineBarGradient = (PercentOfTarget: number, IsToday: boolean) => {
      const SafePercent = Math.min(PercentOfTarget, 200);
      if (SafePercent >= 115) {
        return "from-[#f99595] via-[#ffc39e] to-[#ffe2a1]";
      }
      if (IsToday) {
        return "from-[#5ac7ff] via-[#7ef0ff] to-[#b7fff7]";
      }
      if (SafePercent >= 90) {
        return "from-[#7bd6a4] via-[#8ddfc1] to-[#b5f0d3]";
      }
      if (SafePercent >= 55) {
        return "from-[#b9e0ff] via-[#d4ebff] to-[#f3fbff]";
      }
      return "from-[#e0e4ff] via-[#f0f3ff] to-[#ffffff]";
    };

    return (
      <div className="space-y-3">
        {/* Header with week navigation */}
        <div className="flex items-center justify-between">
          <h3 className="flex flex-col gap-1">
            <span className="text-sm font-semibold text-Ink/70">Daily Progress</span>
            <span className="text-[11px] text-Ink/50">
              {FormatDate(WeekStart)} to {FormatDate(WeekEnd)}
            </span>
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => SetWeekOffset(WeekOffset - 1)}
              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-Ink/5 transition-colors"
              title="Previous week"
            >
              <span className="material-icons text-lg text-Ink/60">chevron_left</span>
            </button>
            {WeekOffset !== 0 && (
              <button
                onClick={() => SetWeekOffset(0)}
                className="px-3 h-8 flex items-center justify-center rounded-lg bg-Ink/5 hover:bg-Ink/10 transition-colors text-xs font-medium text-Ink/70"
                title="Current week"
              >
                Today
              </button>
            )}
            <button
              onClick={() => SetWeekOffset(WeekOffset + 1)}
              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-Ink/5 transition-colors"
              title="Next week"
            >
              <span className="material-icons text-lg text-Ink/60">chevron_right</span>
            </button>
          </div>
        </div>
        <div className="relative rounded-2xl border border-Ink/5 bg-gradient-to-b from-white to-white/80 p-4 shadow-inner">
          <div
            className="relative h-[220px]"
            role="img"
            aria-label={`Weekly calorie progress ${FormatDate(WeekStart)} - ${FormatDate(WeekEnd)} with target ${FormatValueLabel(TargetValue)} calories.`}
          >
            <div className="absolute inset-0 pointer-events-none z-0">
              <div className="flex h-full">
                <div
                  className="flex flex-col justify-between text-[11px] font-semibold text-Ink/40"
                  style={{ width: AxisLabelColumnWidth }}
                >
                  {[...AxisMarks].reverse().map((Mark, Index) => (
                    <span key={`axis-label-${Index}`}>{FormatValueLabel(Mark.Value)}</span>
                  ))}
                </div>
                <div className="relative flex-1">
                  <div
                    className="absolute inset-0 flex flex-col justify-between"
                    style={{ left: 0, right: ChartPaddingRight }}
                  >
                    {AxisMarks.map((_, Index) => (
                      <div
                        key={`axis-line-${Index}`}
                        className="border-t border-Ink/10"
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div
              className="relative flex items-end h-full gap-3 z-10"
              style={{
                paddingLeft: `${AxisLabelColumnWidth}px`,
                paddingRight: `${ChartPaddingRight}px`
              }}
            >
              {WeekDays.map((Day) => {
                const HeightPercent = RoundedMax > 0 ? (Day.Value / RoundedMax) * 100 : 0;
                const BarHeight = Day.Value > 0 ? HeightPercent : 0;
                const LabelOffset = Math.min(100, BarHeight + 6);
                const HasData = Day.Value > 0;
                return (
                  <div key={Day.Date} className="flex-1 flex items-end h-full">
                    <div className="relative w-full h-full">
                      {HasData ? (
                        <div
                          className={`absolute bottom-0 w-full rounded-[20px] bg-gradient-to-t ${DetermineBarGradient(
                            Day.PercentOfTarget,
                            Day.IsToday
                          )}`}
                          style={{ height: `${BarHeight}%`, minHeight: "14px" }}
                          title={`${FormatValueLabel(Day.Value)} calories`}
                        />
                      ) : (
                        <div className="absolute bottom-0 w-full h-1 rounded-full bg-Ink/10" />
                      )}
                      {HasData && (
                        <div
                          className="absolute left-1/2 flex -translate-x-1/2"
                          style={{ bottom: `${LabelOffset}%` }}
                        >
                          <span className="text-[11px] font-semibold text-Ink/70 bg-white/90 px-2 py-0.5 rounded-full shadow-sm whitespace-nowrap">
                            {FormatValueLabel(Day.Value)} cal
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            <div
              className="absolute border-t border-dashed border-Ink/40 z-20"
              style={{
                left: AxisLabelColumnWidth,
                right: ChartPaddingRight,
                bottom: `${TargetHeight}%`
              }}
            >
              <div className="absolute -top-5 right-2 inline-flex items-center gap-2 rounded-full border border-Ink/10 bg-white/90 px-3 py-1 text-[11px] font-semibold text-Ink/60 shadow-sm">
                <span className="inline-flex h-2 w-2 rounded-full bg-gradient-to-r from-sky-400 to-cyan-400" />
                Target {FormatValueLabel(TargetValue)} cal
              </div>
            </div>
          </div>
          <div className="mt-3 flex gap-3 text-[11px] uppercase tracking-wide text-Ink/50">
            {WeekDays.map((Day) => (
              <span
                key={`label-${Day.Date}`}
                className={`flex-1 text-center ${
                  Day.IsToday ? "text-Ink font-semibold tracking-normal" : ""
                }`}
              >
                {Day.Label}
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  };

  if (IsLoading) {
    return <section className="Card text-sm text-Ink/70">Loading today.</section>;
  }

  const QuickAddButton = (
    <div className="relative inline-block" ref={QuickAddWrapRef}>
      {IsQuickAddOpen && (
        <div className="absolute right-0 top-0 h-12 w-12">
          {FanItems.map((Item, Index) => {
            const AngleDeg = QuickAddPosition === "above" ? 360 - Item.AngleDeg : Item.AngleDeg;
            const Radians = (AngleDeg * Math.PI) / 180;
            const X = Math.cos(Radians) * RadiusPx;
            const Y = Math.sin(Radians) * RadiusPx;
            return (
              <button
                key={Item.Label}
                type="button"
                className="absolute flex h-11 w-11 items-center justify-center rounded-full bg-white text-2xl shadow-Soft transition-transform duration-200 hover:scale-110"
                style={{
                  left: "50%",
                  top: "50%",
                  transform: `translate(-50%, -50%) translate(${X}px, ${Y}px)`,
                  transitionDelay: `${Index * 50}ms`
                }}
                onClick={Item.OnClick}
                aria-label={Item.Label}
                title={Item.Label}
              >
                {Item.IconPath ? (
                  <img src={Item.IconPath} alt="" className="h-6 w-6" />
                ) : (
                  Item.Emoji
                )}
              </button>
            );
          })}
        </div>
      )}

      <button
        ref={QuickAddButtonRef}
        className={`flex h-12 w-12 items-center justify-center rounded-full text-2xl font-semibold text-white shadow-Soft transition-transform duration-300 hover:scale-110 ${
          IsQuickAddOpen ? "rotate-45" : ""
        }`}
        style={{ backgroundColor: "#3CCF91" }}
        type="button"
        onClick={ToggleQuickAdd}
        aria-label="Quick add"
      >
        +
      </button>
    </div>
  );

  return (
    <section className="space-y-6">
      <StepsModal
        IsOpen={IsStepsModalOpen}
        CurrentSteps={DailyLogItem?.Steps ?? 0}
        LogDate={TodayDate}
        MaxDate={TodayDate}
        OnClose={() => SetIsStepsModalOpen(false)}
        OnSave={HandleSaveSteps}
      />
      
      <WeightModal
        IsOpen={IsWeightModalOpen}
        CurrentWeight={DailyLogItem?.WeightKg}
        LogDate={TodayDate}
        MaxDate={TodayDate}
        OnClose={() => SetIsWeightModalOpen(false)}
        OnSave={HandleSaveWeight}
      />
      
      {/* Header with quick add */}
      <div className="max-w-2xl mx-auto flex items-center justify-end -mt-[4.5rem] relative z-10">
        {QuickAddButton}
      </div>

      {ErrorMessage && <div className="Card text-sm text-red-500">{ErrorMessage}</div>}
      
      <div className="space-y-6 max-w-2xl mx-auto">
        {/* Daily Progress - 7 day snapshot */}
        <div className="Card">
          <WeeklySnapshotBars />
        </div>

        {/* Daily Intake - Progress Bars */}
        <div className="Card divide-y divide-white/50">
          <h3 className="text-sm font-semibold text-Ink/70 pb-3">Daily Intake</h3>
          
          {BarOrder.map((BarKey, Index) => {
          let Bar: JSX.Element | null = null;

          if (BarKey === "Calories") {
            Bar = (
              <ProgressBar
                Label="Calories"
                Value={Totals?.TotalCalories ?? 0}
                Target={Targets.DailyCalorieTarget}
                Accent="#20c374"
              />
            );
          } else if (BarKey === "Protein" && Targets.ShowProteinOnToday && Targets.ProteinTargetMin) {
            Bar = (
              <ProgressBar
                Label="Protein"
                Value={Totals?.TotalProtein ?? 0}
                Target={Targets.ProteinTargetMin}
                Accent="#3b9eff"
              />
            );
          } else if (BarKey === "Steps" && Targets.ShowStepsOnToday && Targets.StepTarget) {
            Bar = (
              <ProgressBar
                Label="Steps"
                Value={DailyLogItem?.Steps ?? 0}
                Target={Targets.StepTarget}
                Accent="#5cc0c7"
                OnClick={() => SetIsStepsModalOpen(true)}
              />
            );
          } else if (BarKey === "Carbs" && Targets.ShowCarbsOnToday && Targets.CarbsTarget) {
            Bar = (
              <ProgressBar
                Label="Carbs"
                Value={0}
                Target={Targets.CarbsTarget}
                Accent="#8b7355"
              />
            );
          } else if (BarKey === "Fat" && Targets.ShowFatOnToday && Targets.FatTarget) {
            Bar = (
              <ProgressBar
                Label="Fat"
                Value={0}
                Target={Targets.FatTarget}
                Accent="#f26b5b"
              />
            );
          } else if (BarKey === "Fibre" && Targets.ShowFibreOnToday && Targets.FibreTarget) {
            Bar = (
              <ProgressBar
                Label="Fibre"
                Value={0}
                Target={Targets.FibreTarget}
                Accent="#a0522d"
              />
            );
          } else if (BarKey === "SaturatedFat" && Targets.ShowSaturatedFatOnToday && Targets.SaturatedFatTarget) {
            Bar = (
              <ProgressBar
                Label="Saturated Fat"
                Value={0}
                Target={Targets.SaturatedFatTarget}
                Accent="#cd853f"
              />
            );
          } else if (BarKey === "Sugar" && Targets.ShowSugarOnToday && Targets.SugarTarget) {
            Bar = (
              <ProgressBar
                Label="Sugar"
                Value={0}
                Target={Targets.SugarTarget}
                Accent="#ffb23c"
              />
            );
          } else if (BarKey === "Sodium" && Targets.ShowSodiumOnToday && Targets.SodiumTarget) {
            Bar = (
              <ProgressBar
                Label="Sodium"
                Value={0}
                Target={Targets.SodiumTarget}
                Accent="#778899"
              />
            );
          }

          if (!Bar) return null;

          return (
            <div key={BarKey} className="relative">
              {/* Drop indicator line */}
              {DraggedIndex !== null && DropTargetIndex === Index && DraggedIndex !== Index && (
                <div className="absolute -top-px left-0 right-0 h-0.5 bg-Coral z-10" />
              )}
              <div
                draggable
                onDragStart={() => HandleDragStart(Index)}
                onDragOver={(E) => HandleDragOver(E, Index)}
                onDragEnd={HandleDragEnd}
                className={`transition-all duration-200 cursor-grab active:cursor-grabbing ${
                  DraggedIndex === Index ? "opacity-40 scale-95" : "opacity-100"
                }`}
              >
                {Bar}
              </div>
            </div>
          );
        })}
      </div>

      {/* Meal entries */}
      {Entries.length > 0 && (
        <div className="space-y-3">
          {["Breakfast", "Snack1", "Lunch", "Snack2", "Dinner", "Snack3"].map((MealType) => {
            const MealEntries = Entries.filter((E) => E.MealType === MealType);
            if (MealEntries.length === 0) return null;

            const MealLabel = 
              MealType === "Snack1" ? "Morning Snack" : 
              MealType === "Snack2" ? "Afternoon Snack" : 
              MealType === "Snack3" ? "Evening Snack" :
              MealType;
            const MealEmoji = 
              MealType === "Breakfast" ? "🌅" :
              MealType === "Snack1" ? "🍎" :
              MealType === "Lunch" ? "🍱" :
              MealType === "Snack2" ? "🥨" :
              MealType === "Dinner" ? "🍽️" : "🌙";
            
            const TotalCals = Math.round(
              MealEntries.reduce((Sum, E) => Sum + (E.CaloriesPerServing * E.Quantity), 0)
            );
            const TotalProtein = MealEntries.reduce(
              (Sum, E) => Sum + (E.ProteinPerServing * E.Quantity), 0
            ).toFixed(1);

            return (
              <div key={MealType} className="Card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-Ink flex items-center gap-2">
                      <span>{MealEmoji}</span>
                      <span>{MealLabel}</span>
                    </h4>
                    <div className="mt-2 space-y-1.5">
                      {MealEntries.map((E) => (
                        <div key={E.MealEntryId} className="text-sm text-Ink/70">
                          <span className="font-medium">{E.FoodName}</span>
                          {E.Quantity !== 1 && !E.MealTemplateId && (
                            <span className="text-Ink/50 text-xs ml-1">×{E.Quantity}</span>
                          )}
                        </div>
                      ))}
                    </div>
                    <div className="mt-2 pt-2 border-t border-Ink/10">
                      <p className="text-xs text-Ink/60 font-medium">
                        {TotalCals} cal • {TotalProtein}g protein
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      const Params = new URLSearchParams();
                      Params.set("mode", "meal");
                      Params.set("date", TodayDate);
                      Params.set("mealType", MealType);
                      Navigate(`/log?${Params.toString()}`);
                    }}
                    className="flex-shrink-0 w-12 h-12 flex items-center justify-center rounded-xl hover:bg-Ink/5 transition-all hover:scale-110"
                    title="Edit meal"
                  >
                    <span className="material-icons text-2xl text-Ink/60">edit</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
    </section>
  );
};
