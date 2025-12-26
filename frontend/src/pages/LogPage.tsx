import { FormEvent, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useSearchParams } from "react-router-dom";
import {
  ApplyMealTemplate,
  CreateDailyLog,
  CreateMealEntry,
  CreateMealTemplate,
  DeleteMealTemplate,
  DeleteMealEntry,
  GetDailyLog,
  GetFoods,
  GetMealTemplates
} from "../services/ApiClient";
import {
  DailyLog,
  Food,
  MealEntryWithFood,
  MealTemplateWithItems,
  MealType
} from "../models/Models";
import { QuickMealEntry } from "../components/QuickMealEntry";

const MealTypeOptions: { Label: string; Value: MealType }[] = [
  { Label: "Breakfast", Value: "Breakfast" },
  { Label: "Snack 1", Value: "Snack1" },
  { Label: "Lunch", Value: "Lunch" },
  { Label: "Snack 2", Value: "Snack2" },
  { Label: "Dinner", Value: "Dinner" },
  { Label: "Evening Snack", Value: "Snack3" }
];

const MealOrder: Record<MealType, number> = {
  Breakfast: 0,
  Snack1: 1,
  Lunch: 2,
  Snack2: 3,
  Dinner: 4,
  Snack3: 5
};

const ResolveMealType = (Value: string): MealType | undefined => {
  const Match = MealTypeOptions.find((Option) => Option.Value === Value);
  return Match ? Match.Value : undefined;
};

const GetMealLabel = (Value: MealType) => {
  const Match = MealTypeOptions.find((Option) => Option.Value === Value);
  return Match ? Match.Label : Value;
};

const FormatAmount = (Value: number) => {
  if (Number.isInteger(Value)) return Value.toString();
  return Value.toFixed(2).replace(/\.?0+$/, "");
};

const FormatToday = () => new Date().toISOString().slice(0, 10);
const IsValidDate = (Value: string | null) => !!Value && /^\d{4}-\d{2}-\d{2}$/.test(Value);

type TemplateItemDraft = {
  FoodId: string;
  MealType: MealType;
  Quantity: string;
  EntryNotes: string;
};

export const LogPage = () => {
  const [SearchParams] = useSearchParams();
  const Mode = SearchParams.get("mode");
  const DateParam = SearchParams.get("date");
  const SlotParam = SearchParams.get("slotId");
  const SelectedFoodId = SearchParams.get("selectedFoodId");
  const DefaultMealType = useMemo(() => {
    const MealTypeParam = SearchParams.get("mealType");
    if (MealTypeParam) {
      return ResolveMealType(MealTypeParam);
    }
    if (Mode === "snack") {
      return "Snack1";
    }
    return undefined;
  }, [Mode, SearchParams]);
  const StepsAutoFocus = Mode === "steps";

  const [LogDate, SetLogDate] = useState(() => (IsValidDate(DateParam) ? DateParam! : FormatToday()));
  const [DailyLogItem, SetDailyLogItem] = useState<DailyLog | null>(null);
  const [Entries, SetEntries] = useState<MealEntryWithFood[]>([]);
  const [Foods, SetFoods] = useState<Food[]>([]);
  const [StatusMessage, SetStatusMessage] = useState<string | null>(null);
  const [ErrorMessage, SetErrorMessage] = useState<string | null>(null);
  const [IsLoading, SetIsLoading] = useState(true);

  const [Templates, SetTemplates] = useState<MealTemplateWithItems[]>([]);
  const [TemplateName, SetTemplateName] = useState("");
  const [TemplateItems, SetTemplateItems] = useState<TemplateItemDraft[]>([]);
  const [TemplateItemFoodId, SetTemplateItemFoodId] = useState("");
  const [TemplateItemMealType, SetTemplateItemMealType] = useState<MealType>("Breakfast");
  const [TemplateItemQuantity, SetTemplateItemQuantity] = useState("1");
  const [TemplateItemNotes, SetTemplateItemNotes] = useState("");
  const [IsSavingTemplate, SetIsSavingTemplate] = useState(false);
  const [ShowTemplateForm, SetShowTemplateForm] = useState(false);

  const SortedEntries = useMemo(
    () =>
      [...Entries].sort((Left, Right) => {
        const OrderDiff = MealOrder[Left.MealType] - MealOrder[Right.MealType];
        if (OrderDiff !== 0) {
          return OrderDiff;
        }
        return Left.SortOrder - Right.SortOrder;
      }),
    [Entries]
  );

  const LoadFoods = async () => {
    try {
      const FoodItems = await GetFoods();
      SetFoods(FoodItems);
      if (FoodItems.length > 0 && !TemplateItemFoodId) {
        SetTemplateItemFoodId(FoodItems[0].FoodId);
      }
    } catch (ErrorValue) {
      if (axios.isAxiosError(ErrorValue)) {
        if (ErrorValue.response?.status === 401) {
          // Handled by global interceptor
          return;
        } else if (!ErrorValue.response) {
          SetErrorMessage("Cannot connect to server. Please check your connection.");
        } else {
          SetErrorMessage("Failed to load foods.");
        }
      } else {
        SetErrorMessage("Failed to load foods.");
      }
    }
  };

  const LoadTemplates = async () => {
    try {
      const TemplateItems = await GetMealTemplates();
      SetTemplates(TemplateItems);
    } catch (ErrorValue) {
      if (axios.isAxiosError(ErrorValue)) {
        if (ErrorValue.response?.status === 401) {
          // Handled by global interceptor
          return;
        } else if (!ErrorValue.response) {
          SetErrorMessage("Cannot connect to server. Please check your connection.");
        } else {
          SetErrorMessage("Failed to load templates.");
        }
      }
    }
  };

  const LoadLog = async () => {
    SetIsLoading(true);
    SetErrorMessage(null);
    SetStatusMessage(null);

    try {
      const Response = await GetDailyLog(LogDate);
      SetDailyLogItem(Response.DailyLog);
      SetEntries(Response.Entries);
    } catch (ErrorValue) {
      if (axios.isAxiosError(ErrorValue)) {
        if (ErrorValue.response?.status === 401) {
          // Handled by global interceptor
          return;
        } else if (ErrorValue.response?.status === 404) {
          SetDailyLogItem(null);
          SetEntries([]);
        } else if (!ErrorValue.response) {
          SetErrorMessage("Cannot connect to server. Please check your connection.");
        } else {
          SetErrorMessage("Failed to load log.");
        }
      } else {
        SetErrorMessage("Failed to load log.");
      }
    } finally {
      SetIsLoading(false);
    }
  };

  const TriggerRefresh = () => {
    window.dispatchEvent(new Event("portionnote:refresh"));
  };

  useEffect(() => {
    void LoadFoods();
  }, []);

  useEffect(() => {
    void LoadTemplates();
  }, []);

  useEffect(() => {
    if (IsValidDate(DateParam)) {
      SetLogDate(DateParam!);
    }
  }, [DateParam]);

  useEffect(() => {
    void LoadLog();
  }, [LogDate]);

  const EnsureLog = async (): Promise<DailyLog> => {
    if (DailyLogItem) {
      return DailyLogItem;
    }

    const StepsValue = Number(StepsInput || 0);
    await CreateDailyLog(LogDate, Number.isFinite(StepsValue) ? StepsValue : 0);
    const Response = await GetDailyLog(LogDate);
    SetDailyLogItem(Response.DailyLog);
    SetEntries(Response.Entries);
    SetStepsInput(Response.DailyLog.Steps.toString());
    return Response.DailyLog;
  };

  const HandleDeleteEntry = async (MealEntryId: string) => {
    SetErrorMessage(null);
    SetStatusMessage(null);
    try {
      await DeleteMealEntry(MealEntryId);
      await LoadLog();
      TriggerRefresh();
    } catch (ErrorValue) {
      SetErrorMessage("Failed to delete entry.");
    }
  };

  const HandleAddTemplateItem = () => {
    SetErrorMessage(null);
    const QuantityValue = Number(TemplateItemQuantity);
    if (!TemplateItemFoodId) {
      SetErrorMessage("Select a food for the template item.");
      return;
    }
    if (!Number.isFinite(QuantityValue) || QuantityValue <= 0) {
      SetErrorMessage("Enter a valid template quantity.");
      return;
    }

    SetTemplateItems((Items) => [
      ...Items,
      {
        FoodId: TemplateItemFoodId,
        MealType: TemplateItemMealType,
        Quantity: TemplateItemQuantity,
        EntryNotes: TemplateItemNotes
      }
    ]);
    SetTemplateItemNotes("");
  };

  const HandleRemoveTemplateItem = (Index: number) => {
    SetTemplateItems((Items) => Items.filter((_, ItemIndex) => ItemIndex !== Index));
  };

  const HandleCreateTemplate = async (Event: FormEvent) => {
    Event.preventDefault();
    SetErrorMessage(null);
    SetStatusMessage(null);

    if (!TemplateName.trim()) {
      SetErrorMessage("Template name is required.");
      return;
    }
    if (TemplateItems.length === 0) {
      SetErrorMessage("Add at least one template item.");
      return;
    }

    SetIsSavingTemplate(true);
    try {
      const Template = await CreateMealTemplate({
        TemplateName: TemplateName.trim(),
        Items: TemplateItems.map((Item, Index) => ({
          FoodId: Item.FoodId,
          MealType: Item.MealType,
          Quantity: Number(Item.Quantity),
          EntryNotes: Item.EntryNotes.trim() ? Item.EntryNotes.trim() : null,
          SortOrder: Index
        }))
      });
      SetTemplates((Items) => [Template, ...Items]);
      SetTemplateName("");
      SetTemplateItems([]);
      SetStatusMessage("Template saved.");
    } catch (ErrorValue) {
      SetErrorMessage("Failed to save template.");
    } finally {
      SetIsSavingTemplate(false);
    }
  };

  const HandleApplyTemplate = async (MealTemplateId: string) => {
    SetErrorMessage(null);
    SetStatusMessage(null);
    try {
      await ApplyMealTemplate(MealTemplateId, LogDate);
      await LoadLog();
      TriggerRefresh();
      SetStatusMessage("Template logged.");
      setTimeout(() => SetStatusMessage(null), 3000);
    } catch (ErrorValue) {
      SetErrorMessage("Failed to apply template.");
    }
  };

  const HandleDeleteTemplate = async (MealTemplateId: string) => {
    SetErrorMessage(null);
    SetStatusMessage(null);
    try {
      await DeleteMealTemplate(MealTemplateId);
      SetTemplates((Items) => Items.filter((Item) => Item.Template.MealTemplateId !== MealTemplateId));
    } catch (ErrorValue) {
      SetErrorMessage("Failed to delete template.");
    }
  };

  const HandleStartLog = async () => {
    await EnsureLog();
    SetShowEntryForm(true);
  };

  return (
    <section className="space-y-5">
      {/* Add Entry - Move to Top */}
      <div className="Card space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="Headline text-2xl">Log a meal</h2>
            <p className="text-sm text-Ink/60 mt-1">
              {LogDate === FormatToday() ? "Today" : LogDate}
            </p>
          </div>
          <label className="space-y-1 text-sm">
            <input
              className="InputField"
              type="date"
              value={LogDate}
              onChange={(Event) => SetLogDate(Event.target.value)}
            />
          </label>
        </div>
        {Foods.length === 0 ? (
          <p className="text-sm text-Ink/70">
            Add foods first before logging a meal.
          </p>
        ) : (
          <QuickMealEntry
            Foods={Foods}
            Templates={Templates}
            RecentEntries={Entries.map((E) => ({
              FoodId: E.FoodId,
              MealTemplateId: E.MealTemplateId,
              MealType: E.MealType,
              LastUsed: E.CreatedAt || new Date().toISOString()
            }))}
            DefaultMealType={DefaultMealType}
            ReturnToLog
            ReturnDate={LogDate}
            PreselectedFoodId={SelectedFoodId ?? undefined}
            OnSubmit={async (FoodId, MealType, EntryQuantity, EntryUnit) => {
              const Log = await EnsureLog();
              await CreateMealEntry({
                DailyLogId: Log.DailyLogId,
                MealType,
                FoodId,
                Quantity: EntryQuantity,
                EntryQuantity,
                EntryUnit,
                EntryNotes: null,
                SortOrder: Entries.length,
                ScheduleSlotId: null
              });
              await LoadLog();
              TriggerRefresh();
              SetStatusMessage("Entry logged.");
              setTimeout(() => SetStatusMessage(null), 3000);
            }}
            OnSubmitTemplate={async (TemplateId, MealType) => {
              await HandleApplyTemplate(TemplateId);
            }}
            AutoFocus={Mode === "meal" || Mode === "snack"}
          />
        )}
      </div>

      {Entries.length > 0 && (
        <div className="Card space-y-4">
          <h3 className="Headline text-xl">Logged items</h3>
          <div className="space-y-3">
            {["Breakfast", "Snack1", "Lunch", "Snack2", "Dinner", "Snack3"].map((MealTypeKey) => {
              const MealEntries = SortedEntries.filter((E) => E.MealType === MealTypeKey);
              if (MealEntries.length === 0) return null;

              const MealLabel = GetMealLabel(MealTypeKey as MealType);
              const MealEmoji = 
                MealTypeKey === "Breakfast" ? "🌅" :
                MealTypeKey === "Snack1" ? "🍎" :
                MealTypeKey === "Lunch" ? "🍱" :
                MealTypeKey === "Snack2" ? "🥨" :
                MealTypeKey === "Dinner" ? "🍽️" : "🌙";
              
              const TotalCalories = Math.round(
                MealEntries.reduce((Sum, E) => Sum + (E.CaloriesPerServing * E.Quantity), 0)
              );
              const TotalProtein = MealEntries.reduce(
                (Sum, E) => Sum + (E.ProteinPerServing * E.Quantity), 0
              ).toFixed(1);

              return (
                <div key={MealTypeKey} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-Ink/70 uppercase tracking-wider flex items-center gap-2">
                      <span>{MealEmoji}</span>
                      <span>{MealLabel}</span>
                    </h4>
                    <div className="text-xs text-Ink/60 font-medium">
                      {TotalCalories} cal • {TotalProtein}g protein
                    </div>
                  </div>
                  <div className="space-y-2">
                    {MealEntries.map((Entry) => {
                      const EntryCalories = Math.round(Entry.CaloriesPerServing * Entry.Quantity);
                      const EntryProtein = (Entry.ProteinPerServing * Entry.Quantity).toFixed(1);
                      const EntryAmount = Entry.EntryQuantity ?? Entry.Quantity;
                      const EntryUnit = Entry.EntryUnit ?? "serving";
                      const EntryLine = EntryUnit === "serving"
                        ? `${FormatAmount(EntryAmount)} × ${Entry.ServingDescription}`
                        : `${FormatAmount(EntryAmount)} ${EntryUnit}`;
                      
                      return (
                        <div
                          key={Entry.MealEntryId}
                          className="flex items-center justify-between gap-3 rounded-xl bg-white border border-Ink/10 px-4 py-3 hover:border-Ink/20 transition-colors"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold text-sm truncate">{Entry.FoodName}</p>
                            {!Entry.MealTemplateId && (
                              <p className="text-xs text-Ink/60 mt-0.5">
                                {EntryLine}
                              </p>
                            )}
                            {!Entry.MealTemplateId && Entry.ConversionDetail && EntryUnit !== "serving" && (
                              <p className="text-xs text-Ink/50 mt-0.5">
                                {Entry.ConversionDetail}
                              </p>
                            )}
                            <p className="text-xs text-Ink/60 mt-0.5">
                              {EntryCalories} cal • {EntryProtein}g protein
                            </p>
                          </div>
                          <button
                            className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg hover:bg-red-50 text-Ink/40 hover:text-red-600 transition-colors"
                            type="button"
                            onClick={() => HandleDeleteEntry(Entry.MealEntryId)}
                            title="Delete"
                          >
                            <span className="material-icons text-xl">delete</span>
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {StatusMessage && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 Card text-sm text-Ink/70 shadow-lg animate-fade-in">
          {StatusMessage}
        </div>
      )}
      {ErrorMessage && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 Card text-sm text-red-500 shadow-lg animate-fade-in">
          {ErrorMessage}
        </div>
      )}
    </section>
  );
};
