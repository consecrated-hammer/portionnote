import { FormEvent, useEffect, useRef, useState } from "react";
import axios from "axios";
import { useNavigate, useSearchParams } from "react-router-dom";
import { GetFoods, CreateFood, UpdateFood, DeleteFood, GetMealTemplates, CreateMealTemplate, UpdateMealTemplate, DeleteMealTemplate, GetFoodSuggestions, LookupFoodOptionsByText, SearchFoodDatabases } from "../services/ApiClient";
import { Food, MealTemplateWithItems, MealType } from "../models/Models";
import { UseAuth } from "../contexts/AuthContext";

const CommonServingUnits = [
  "serving", "g", "oz", "cup", "tbsp", "tsp", "mL", "piece", "slice", "small", "medium", "large"
];

const MealEntryUnitOptions = [
  "serving",
  "g",
  "mL",
  "tsp",
  "tbsp",
  "cup",
  "piece",
  "slice",
  "biscuit",
  "handful"
];

type AiFoodOption = {
  FoodName: string;
  ServingQuantity: number;
  ServingUnit: string;
  CaloriesPerServing: number;
  ProteinPerServing: number;
  FibrePerServing?: number | null;
  CarbsPerServing?: number | null;
  FatPerServing?: number | null;
  SaturatedFatPerServing?: number | null;
  SugarPerServing?: number | null;
  SodiumPerServing?: number | null;
  Source: string;
  Confidence: string;
};

export const FoodsPage = () => {
  const Navigate = useNavigate();
  const { CurrentUser } = UseAuth();
  const [SearchParams] = useSearchParams();
  const AddFoodFlag = SearchParams.get("addFood");
  const FoodNameParam = SearchParams.get("foodName");
  const ReturnTo = SearchParams.get("returnTo");
  const ReturnMealType = SearchParams.get("returnMealType");
  const ReturnDate = SearchParams.get("returnDate");
  const [Foods, SetFoods] = useState<Food[]>([]);
  const [Meals, SetMeals] = useState<MealTemplateWithItems[]>([]);
  const [SelectedFoodIds, SetSelectedFoodIds] = useState<Set<string>>(new Set());
  const [SelectedMealItems, SetSelectedMealItems] = useState<Record<string, { EntryQuantity: string; EntryUnit: string }>>({});
  const [IsLoading, SetIsLoading] = useState(true);
  const [IsAddingFood, SetIsAddingFood] = useState(false);
  const [IsAddingMeal, SetIsAddingMeal] = useState(false);
  const [EditingMealId, SetEditingMealId] = useState<string | null>(null);
  const [IsSaving, SetIsSaving] = useState(false);
  const [ErrorMessage, SetErrorMessage] = useState<string | null>(null);
  const [EditingFoodId, SetEditingFoodId] = useState<string | null>(null);
  const [SortBy, SetSortBy] = useState<"name" | "calories" | "protein" | "date">("name");
  const [SortDirection, SetSortDirection] = useState<"asc" | "desc">("asc");
  const [ShowRadialMenu, SetShowRadialMenu] = useState(false);
  const [NewMealName, SetNewMealName] = useState("");
  
  const RadialMenuRef = useRef<HTMLDivElement>(null);
  
  const [NewFoodName, SetNewFoodName] = useState("");
  const [NewFoodCalories, SetNewFoodCalories] = useState("0");
  const [NewFoodProtein, SetNewFoodProtein] = useState("0");
  const [NewFoodFibre, SetNewFoodFibre] = useState("");
  const [NewFoodCarbs, SetNewFoodCarbs] = useState("");
  const [NewFoodFat, SetNewFoodFat] = useState("");
  const [NewFoodSaturatedFat, SetNewFoodSaturatedFat] = useState("");
  const [NewFoodSugar, SetNewFoodSugar] = useState("");
  const [NewFoodSodium, SetNewFoodSodium] = useState("");
  const [NewFoodQuantity, SetNewFoodQuantity] = useState("1");
  const [NewFoodUnit, SetNewFoodUnit] = useState("serving");
  const [FoodSuggestions, SetFoodSuggestions] = useState<string[]>([]);
  const [ShowSuggestions, SetShowSuggestions] = useState(false);
  const [IsLoadingSuggestion, SetIsLoadingSuggestion] = useState(false);
  const [IsPopulatingFromAI, SetIsPopulatingFromAI] = useState(false);
  const [DisableAutocomplete, SetDisableAutocomplete] = useState(false);
  const SuggestionsRef = useRef<HTMLDivElement>(null);

  // Multi-source search states
  const [IsSearchingDatabases, SetIsSearchingDatabases] = useState(false);
  const [DatabaseSearchResults, SetDatabaseSearchResults] = useState<any>(null);
  const [SelectedSearchResult, SetSelectedSearchResult] = useState<any>(null);
  const [SearchOpenFoodFacts, SetSearchOpenFoodFacts] = useState(true);
  const [SearchAI, SetSearchAI] = useState(true);
  const [DataSourceUsed, SetDataSourceUsed] = useState<string | null>(null);

  // Modal editing states
  const [EditingFood, SetEditingFood] = useState<Food | null>(null);
  const [EditFoodName, SetEditFoodName] = useState("");
  const [EditFoodCalories, SetEditFoodCalories] = useState("");
  const [EditFoodProtein, SetEditFoodProtein] = useState("");
  const [EditFoodFibre, SetEditFoodFibre] = useState("");
  const [EditFoodCarbs, SetEditFoodCarbs] = useState("");
  const [EditFoodFat, SetEditFoodFat] = useState("");
  const [EditFoodSaturatedFat, SetEditFoodSaturatedFat] = useState("");
  const [EditFoodSugar, SetEditFoodSugar] = useState("");
  const [EditFoodSodium, SetEditFoodSodium] = useState("");
  const [EditFoodQuantity, SetEditFoodQuantity] = useState("");
  const [EditFoodUnit, SetEditFoodUnit] = useState("");

  const RadialItems = [
    { Label: "Add Food", Emoji: "🥕", OnClick: () => { SetIsAddingFood(true); SetShowRadialMenu(false); }, AngleDeg: 210 },
    { Label: "Add Meal", Emoji: "🍲", OnClick: () => { SetIsAddingMeal(true); SetShowRadialMenu(false); }, AngleDeg: 150 }
  ];

  const RadiusPx = 60;

  const GetMealEntryDefaults = () => ({ EntryQuantity: "1", EntryUnit: "serving" });

  const NormalizeMealUnit = (Unit: string) => {
    const Value = Unit.trim().toLowerCase();
    if (Value === "ml") return "ml";
    if (Value === "grams" || Value === "gram" || Value === "gr") return "g";
    if (Value === "servings") return "serving";
    if (Value.endsWith("s") && Value.length > 1) return Value.slice(0, -1);
    return Value;
  };

  const GetPreviewServings = (FoodItem: Food, EntryQty: number, EntryUnit: string) => {
    const NormalizedEntryUnit = NormalizeMealUnit(EntryUnit);
    const NormalizedServingUnit = NormalizeMealUnit(FoodItem.ServingUnit);

    if (NormalizedEntryUnit === "serving") {
      return EntryQty;
    }

    if (NormalizedEntryUnit === NormalizedServingUnit && FoodItem.ServingQuantity > 0) {
      return EntryQty / FoodItem.ServingQuantity;
    }

    return null;
  };

  const LoadFoods = async () => {
    SetIsLoading(true);
    SetErrorMessage(null);
    try {
      const [FoodList, MealList] = await Promise.all([GetFoods(), GetMealTemplates()]);
      SetFoods(FoodList);
      SetMeals(MealList);
    } catch (ErrorValue) {
      SetErrorMessage("Failed to load data");
    } finally {
      SetIsLoading(false);
    }
  };

  const GetSortedFoods = () => {
    const Sorted = [...Foods];
    const Multiplier = SortDirection === "asc" ? 1 : -1;
    
    switch (SortBy) {
      case "name":
        return Sorted.sort((A, B) => Multiplier * A.FoodName.localeCompare(B.FoodName));
      case "calories":
        return Sorted.sort((A, B) => Multiplier * (A.CaloriesPerServing - B.CaloriesPerServing));
      case "protein":
        return Sorted.sort((A, B) => Multiplier * (A.ProteinPerServing - B.ProteinPerServing));
      case "date":
        return Sorted.sort((A, B) => Multiplier * (new Date(A.CreatedAt || 0).getTime() - new Date(B.CreatedAt || 0).getTime()));
      default:
        return Sorted;
    }
  };

  useEffect(() => {
    void LoadFoods();
  }, []);

  useEffect(() => {
    if (AddFoodFlag || FoodNameParam) {
      SetIsAddingFood(true);
      SetIsAddingMeal(false);
      SetEditingMealId(null);
      SetShowRadialMenu(false);
      SetErrorMessage(null);
      if (FoodNameParam) {
        SetNewFoodName(FoodNameParam);
        SetDisableAutocomplete(false);
      }
    }
  }, [AddFoodFlag, FoodNameParam]);

  useEffect(() => {
    const HandleClickOutside = (Event: MouseEvent) => {
      if (ShowRadialMenu && RadialMenuRef.current && !RadialMenuRef.current.contains(Event.target as Node)) {
        SetShowRadialMenu(false);
      }
    };
    document.addEventListener("mousedown", HandleClickOutside);
    return () => document.removeEventListener("mousedown", HandleClickOutside);
  }, [ShowRadialMenu]);

  // Autocomplete handler - debounced
  useEffect(() => {
    if (NewFoodName.length >= 2 && IsAddingFood && !DisableAutocomplete) {
      const Timer = setTimeout(async () => {
        SetIsLoadingSuggestion(true);
        try {
          const Suggestions = await GetFoodSuggestions(NewFoodName, 8);
          SetFoodSuggestions(Suggestions);
          SetShowSuggestions(Suggestions.length > 0);
        } catch (Error) {
          console.error("Failed to load suggestions:", Error);
          SetFoodSuggestions([]);
          SetShowSuggestions(false);
        } finally {
          SetIsLoadingSuggestion(false);
        }
      }, 300);
      return () => clearTimeout(Timer);
    } else {
      SetFoodSuggestions([]);
      SetShowSuggestions(false);
    }
  }, [NewFoodName, IsAddingFood, DisableAutocomplete]);

  // Click outside handler for suggestions
  useEffect(() => {
    const HandleClickOutside = (Event: MouseEvent) => {
      if (ShowSuggestions && SuggestionsRef.current && !SuggestionsRef.current.contains(Event.target as Node)) {
        SetShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", HandleClickOutside);
    return () => document.removeEventListener("mousedown", HandleClickOutside);
  }, [ShowSuggestions]);

  const HandleSelectSuggestion = (Suggestion: string) => {
    SetShowSuggestions(false);
    SetDisableAutocomplete(true);
    SetNewFoodName(Suggestion);
    SetErrorMessage(null);
    
    // Suggestions just fill the name field
    // User then clicks "Search Selected Sources" to get nutrition from their chosen sources
  };

  const BuildAiResults = (AiOptions: AiFoodOption[]) =>
    AiOptions.map((Option) => ({
      FoodName: Option.FoodName,
      ServingDescription: `${Option.ServingQuantity} ${Option.ServingUnit}`,
      CaloriesPerServing: Option.CaloriesPerServing,
      ProteinPerServing: Option.ProteinPerServing,
      FibrePerServing: Option.FibrePerServing,
      CarbsPerServing: Option.CarbsPerServing,
      FatPerServing: Option.FatPerServing,
      SaturatedFatPerServing: Option.SaturatedFatPerServing,
      SugarPerServing: Option.SugarPerServing,
      SodiumPerServing: Option.SodiumPerServing,
      Metadata: { source: "ai-generated", confidence: Option.Confidence }
    }));

  const HandleSearchDatabases = async () => {
    if (!NewFoodName || NewFoodName.length < 3) {
      SetErrorMessage("Enter at least 3 characters to search");
      return;
    }

    if (!SearchOpenFoodFacts && !SearchAI) {
      SetErrorMessage("Select at least one source to search");
      return;
    }

    SetDisableAutocomplete(true);
    SetShowSuggestions(false);
    SetIsSearchingDatabases(true);
    SetErrorMessage(null);
    SetDatabaseSearchResults(null);
    SetDataSourceUsed(null);
    
    try {
      const [SearchResults, AiOptions] = await Promise.all([
        SearchOpenFoodFacts ? SearchFoodDatabases(NewFoodName) : Promise.resolve({ Openfoodfacts: [], AiFallbackAvailable: false }),
        SearchAI ? LookupFoodOptionsByText(NewFoodName) : Promise.resolve([])
      ]);

      const FilteredResults = {
        Openfoodfacts: SearchOpenFoodFacts ? SearchResults.Openfoodfacts : [],
        AiResults: SearchAI ? BuildAiResults(AiOptions as AiFoodOption[]) : [],
        AiFallbackAvailable: SearchAI && SearchResults.AiFallbackAvailable
      };

      SetDatabaseSearchResults(FilteredResults);
    } catch (Error) {
      console.error("Database search failed:", Error);
      SetErrorMessage("Failed to search food databases");
    } finally {
      SetIsSearchingDatabases(false);
    }
  };

  const HandleUseAIFallback = async () => {
    if (!NewFoodName) return;
    
    SetIsPopulatingFromAI(true);
    SetDisableAutocomplete(true);
    SetShowSuggestions(false);
    SetErrorMessage(null);
    
    try {
      const AiOptions = await LookupFoodOptionsByText(NewFoodName);
      const LookupResult = AiOptions[0];
      if (!LookupResult) {
        SetErrorMessage("No AI options available");
        return;
      }
      
      // Populate all fields from AI
      SetNewFoodName(LookupResult.FoodName);
      SetNewFoodCalories(String(LookupResult.CaloriesPerServing || 0));
      SetNewFoodProtein(String(LookupResult.ProteinPerServing || 0));
      SetNewFoodFibre(LookupResult.FibrePerServing ? String(LookupResult.FibrePerServing) : "");
      SetNewFoodCarbs(LookupResult.CarbsPerServing ? String(LookupResult.CarbsPerServing) : "");
      SetNewFoodFat(LookupResult.FatPerServing ? String(LookupResult.FatPerServing) : "");
      SetNewFoodSaturatedFat(LookupResult.SaturatedFatPerServing ? String(LookupResult.SaturatedFatPerServing) : "");
      SetNewFoodSugar(LookupResult.SugarPerServing ? String(LookupResult.SugarPerServing) : "");
      SetNewFoodSodium(LookupResult.SodiumPerServing ? String(LookupResult.SodiumPerServing) : "");
      SetNewFoodQuantity(String(LookupResult.ServingQuantity || 1));
      SetNewFoodUnit(LookupResult.ServingUnit || "serving");
      
      SetDataSourceUsed('ai-generated');
      
      // Clear search results after populating
      SetDatabaseSearchResults(null);
    } catch (Error) {
      console.error("AI fallback failed:", Error);
      SetErrorMessage("Failed to generate nutrition info with AI");
    } finally {
      SetIsPopulatingFromAI(false);
    }
  };

  const HandleSelectDatabaseResult = (Result: any, Source: string) => {
    SetSelectedSearchResult({ ...Result, Source });
    SetDatabaseSearchResults(null);
    SetDataSourceUsed(Source);
    SetDisableAutocomplete(true);
    SetShowSuggestions(false);
    
    PopulateBasicInfo(Result);
  };
  
  const PopulateBasicInfo = (Result: any) => {
    SetNewFoodName(Result.FoodName);
    SetNewFoodCalories(Result.CaloriesPerServing ? String(Result.CaloriesPerServing) : "0");
    SetNewFoodProtein(Result.ProteinPerServing ? String(Result.ProteinPerServing) : "0");
    SetNewFoodFibre(Result.FiberPerServing ? String(Result.FiberPerServing) : "");
    SetNewFoodCarbs(Result.CarbohydratesPerServing ? String(Result.CarbohydratesPerServing) : "");
    SetNewFoodFat(Result.FatPerServing ? String(Result.FatPerServing) : "");
    SetNewFoodSaturatedFat(Result.SaturatedFatPerServing ? String(Result.SaturatedFatPerServing) : "");
    SetNewFoodSugar(Result.SugarPerServing ? String(Result.SugarPerServing) : "");
    SetNewFoodSodium(Result.SodiumPerServing ? String(Result.SodiumPerServing) : "");
    
    // Parse serving description to quantity and unit
    const ServingMatch = Result.ServingDescription?.match(/^(\d+(?:\.\d+)?)\s*(.+)$/);
    if (ServingMatch) {
      SetNewFoodQuantity(ServingMatch[1]);
      SetNewFoodUnit(ServingMatch[2]);
    } else {
      SetNewFoodQuantity("1");
      SetNewFoodUnit(Result.ServingDescription || "serving");
    }
  };

  const HandleSort = (Column: "name" | "calories" | "protein" | "date") => {
    if (SortBy === Column) {
      SetSortDirection(SortDirection === "asc" ? "desc" : "asc");
    } else {
      SetSortBy(Column);
      SetSortDirection("asc");
    }
  };

  const HandleAddFood = async (Event: FormEvent) => {
    Event.preventDefault();
    SetErrorMessage(null);
    SetIsSaving(true);

    try {
      const NewFood = await CreateFood({
        FoodName: NewFoodName,
        ServingQuantity: Number(NewFoodQuantity),
        ServingUnit: NewFoodUnit,
        CaloriesPerServing: Number(NewFoodCalories),
        ProteinPerServing: Number(NewFoodProtein),
        FibrePerServing: NewFoodFibre ? Number(NewFoodFibre) : null,
        CarbsPerServing: NewFoodCarbs ? Number(NewFoodCarbs) : null,
        FatPerServing: NewFoodFat ? Number(NewFoodFat) : null,
        SaturatedFatPerServing: NewFoodSaturatedFat ? Number(NewFoodSaturatedFat) : null,
        SugarPerServing: NewFoodSugar ? Number(NewFoodSugar) : null,
        SodiumPerServing: NewFoodSodium ? Number(NewFoodSodium) : null,
        DataSource: DataSourceUsed || "manual",
        CountryCode: "AU",
        IsFavourite: false
      });

      if (ReturnTo === "log") {
        const Params = new URLSearchParams();
        Params.set("mode", "meal");
        Params.set("selectedFoodId", NewFood.FoodId);
        if (ReturnMealType) {
          Params.set("mealType", ReturnMealType);
        }
        if (ReturnDate) {
          Params.set("date", ReturnDate);
        }
        Navigate(`/log?${Params.toString()}`);
        return;
      }
      
      SetNewFoodName("");
      SetNewFoodCalories("0");
      SetNewFoodProtein("0");
      SetNewFoodFibre("");
      SetNewFoodCarbs("");
      SetNewFoodFat("");
      SetNewFoodSaturatedFat("");
      SetNewFoodSugar("");
      SetNewFoodSodium("");
      SetNewFoodQuantity("1");
      SetNewFoodUnit("serving");
      SetIsAddingFood(false);
      SetIsPopulatingFromAI(false);
      SetDataSourceUsed(null);
      
      await LoadFoods();
      
      // Auto-select the newly created food if in meal creation mode
      if (IsAddingMeal) {
        SetSelectedFoodIds(prev => new Set([...prev, NewFood.FoodId]));
        SetSelectedMealItems(prev => ({
          ...prev,
          [NewFood.FoodId]: GetMealEntryDefaults()
        }));
      }
    } catch (ErrorValue) {
      SetErrorMessage("Failed to create food");
    } finally {
      SetIsSaving(false);
    }
  };

  const HandleEditFood = (FoodItem: Food) => {
    SetEditingFood(FoodItem);
    SetEditFoodName(FoodItem.FoodName);
    SetEditFoodCalories(String(FoodItem.CaloriesPerServing));
    SetEditFoodProtein(String(FoodItem.ProteinPerServing));
    SetEditFoodFibre(FoodItem.FibrePerServing ? String(FoodItem.FibrePerServing) : "");
    SetEditFoodCarbs(FoodItem.CarbsPerServing ? String(FoodItem.CarbsPerServing) : "");
    SetEditFoodFat(FoodItem.FatPerServing ? String(FoodItem.FatPerServing) : "");
    SetEditFoodSaturatedFat(FoodItem.SaturatedFatPerServing ? String(FoodItem.SaturatedFatPerServing) : "");
    SetEditFoodSugar(FoodItem.SugarPerServing ? String(FoodItem.SugarPerServing) : "");
    SetEditFoodSodium(FoodItem.SodiumPerServing ? String(FoodItem.SodiumPerServing) : "");
    SetEditFoodQuantity(String(FoodItem.ServingQuantity));
    SetEditFoodUnit(FoodItem.ServingUnit);
  };

  const HandleSaveEditFood = async (Event: FormEvent) => {
    Event.preventDefault();
    if (!EditingFood) return;
    
    SetErrorMessage(null);
    SetIsSaving(true);

    try {
      await UpdateFood(EditingFood.FoodId, {
        FoodName: EditFoodName,
        ServingQuantity: Number(EditFoodQuantity),
        ServingUnit: EditFoodUnit,
        CaloriesPerServing: Number(EditFoodCalories),
        ProteinPerServing: Number(EditFoodProtein),
        FibrePerServing: EditFoodFibre ? Number(EditFoodFibre) : null,
        CarbsPerServing: EditFoodCarbs ? Number(EditFoodCarbs) : null,
        FatPerServing: EditFoodFat ? Number(EditFoodFat) : null,
        SaturatedFatPerServing: EditFoodSaturatedFat ? Number(EditFoodSaturatedFat) : null,
        SugarPerServing: EditFoodSugar ? Number(EditFoodSugar) : null,
        SodiumPerServing: EditFoodSodium ? Number(EditFoodSodium) : null
      });
      
      SetEditingFood(null);
      await LoadFoods();
    } catch (ErrorValue) {
      SetErrorMessage("Failed to update food");
    } finally {
      SetIsSaving(false);
    }
  };

  const HandleCancelEditFood = () => {
    SetEditingFood(null);
  };

  const HandleDeleteFood = async (FoodId: string) => {
    if (!confirm("Delete this food? This cannot be undone.")) return;
    
    SetErrorMessage(null);
    try {
      await DeleteFood(FoodId);
      await LoadFoods();
    } catch (ErrorValue) {
      if (axios.isAxiosError(ErrorValue)) {
        SetErrorMessage(ErrorValue.response?.data?.detail || "Failed to delete food");
      } else {
        SetErrorMessage("Failed to delete food");
      }
    }
  };

  const HandleCreateOrUpdateMeal = async (Event: FormEvent) => {
    Event.preventDefault();
    SetErrorMessage(null);
    SetIsSaving(true);

    try {
      const Items = Array.from(SelectedFoodIds).map((FoodId, Index) => {
        const Entry = SelectedMealItems[FoodId] ?? GetMealEntryDefaults();
        const EntryQuantityValue = Number(Entry.EntryQuantity);
        if (!Number.isFinite(EntryQuantityValue) || EntryQuantityValue <= 0) {
          throw new Error("Entry quantity must be greater than zero.");
        }
        return {
          FoodId,
          MealType: "Breakfast" as MealType,
          Quantity: EntryQuantityValue,
          EntryQuantity: EntryQuantityValue,
          EntryUnit: Entry.EntryUnit.trim() || "serving",
          EntryNotes: null,
          SortOrder: Index
        };
      });

      if (EditingMealId) {
        await UpdateMealTemplate(EditingMealId, {
          TemplateName: NewMealName,
          Items
        });
      } else {
        await CreateMealTemplate({
          TemplateName: NewMealName,
          Items
        });
      }

      SetNewMealName("");
      SetSelectedFoodIds(new Set());
      SetSelectedMealItems({});
      SetIsAddingMeal(false);
      SetEditingMealId(null);
      await LoadFoods();
    } catch (ErrorValue) {
      SetErrorMessage(EditingMealId ? "Failed to update meal" : "Failed to create meal");
    } finally {
      SetIsSaving(false);
    }
  };

  const HandleEditMeal = (Meal: MealTemplateWithItems) => {
    SetEditingMealId(Meal.Template.MealTemplateId);
    SetNewMealName(Meal.Template.TemplateName);
    const NextSelected = new Set(Meal.Items.map(Item => Item.FoodId));
    const NextItems: Record<string, { EntryQuantity: string; EntryUnit: string }> = {};
    Meal.Items.forEach((Item) => {
      NextItems[Item.FoodId] = {
        EntryQuantity: String(Item.EntryQuantity ?? Item.Quantity ?? 1),
        EntryUnit: Item.EntryUnit ?? "serving"
      };
    });
    SetSelectedFoodIds(NextSelected);
    SetSelectedMealItems(NextItems);
    SetIsAddingMeal(true);
  };

  const HandleDeleteMeal = async (MealTemplateId: string) => {
    if (!confirm("Delete this meal? This cannot be undone.")) return;

    SetErrorMessage(null);
    try {
      await DeleteMealTemplate(MealTemplateId);
      await LoadFoods();
    } catch (ErrorValue) {
      SetErrorMessage("Failed to delete meal");
    }
  };

  const HandleToggleFoodSelection = (FoodId: string) => {
    const NewSelection = new Set(SelectedFoodIds);
    if (NewSelection.has(FoodId)) {
      NewSelection.delete(FoodId);
      SetSelectedMealItems((Prev) => {
        const Next = { ...Prev };
        delete Next[FoodId];
        return Next;
      });
    } else {
      NewSelection.add(FoodId);
      SetSelectedMealItems((Prev) => ({
        ...Prev,
        [FoodId]: Prev[FoodId] ?? GetMealEntryDefaults()
      }));
    }
    SetSelectedFoodIds(NewSelection);
  };

  if (IsLoading) {
    return <section className="Card text-sm text-Ink/70">Loading foods...</section>;
  }

  const OpenFoodFactsResults = DatabaseSearchResults?.Openfoodfacts ?? [];
  const AiResults = DatabaseSearchResults?.AiResults ?? [];
  const ShowAiFirst = OpenFoodFactsResults.length === 0 && AiResults.length > 0;

  return (
    <section className="space-y-4">
      <div className="Card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="Headline text-2xl">Foods & Meals</h2>
            <p className="mt-1 text-sm text-Ink/70">
              {Foods.length} {Foods.length === 1 ? "food" : "foods"}, {Meals.length} {Meals.length === 1 ? "meal" : "meals"}
            </p>
          </div>
          <div className="relative" ref={RadialMenuRef}>
            {ShowRadialMenu && (
              <div className="absolute right-0 top-0 h-12 w-12">
                {RadialItems.map((Item, Index) => {
                  const Radians = (Item.AngleDeg * Math.PI) / 180;
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
                      {Item.Emoji}
                    </button>
                  );
                })}
              </div>
            )}
            
            <button
              className={`flex h-12 w-12 items-center justify-center rounded-full bg-Ink text-2xl text-white shadow-Soft transition-transform duration-300 hover:scale-110 ${
                ShowRadialMenu ? "rotate-45" : ""
              }`}
              type="button"
              onClick={() => SetShowRadialMenu(!ShowRadialMenu)}
              aria-label="Add menu"
            >
              +
            </button>
          </div>
        </div>
      </div>

      {ErrorMessage && (
        <div className="Card text-sm text-red-500">{ErrorMessage}</div>
      )}

      {IsAddingFood && (
        <div className="Card bg-blue-50 border-2 border-blue-200">
          <h3 className="Headline text-lg mb-4">Add new food</h3>
          <form className="space-y-3" onSubmit={HandleAddFood}>
            <label className="space-y-2 text-sm relative">
              <span className="text-Ink/70">Food name</span>
              <input
                className="InputField"
                type="text"
                value={NewFoodName}
                onChange={(Event) => {
                  SetNewFoodName(Event.target.value);
                  SetDisableAutocomplete(false);
                }}
                onFocus={() => {
                  if (FoodSuggestions.length > 0 && !DisableAutocomplete) SetShowSuggestions(true);
                }}
                placeholder="e.g. Tim Tam Original, Vegemite, Banana"
                autoFocus
                required
              />
              {IsLoadingSuggestion && (
                <div className="absolute right-3 top-9 text-Ink/40 text-xs">
                  Loading...
                </div>
              )}
              {ShowSuggestions && FoodSuggestions.length > 0 && (
                <div ref={SuggestionsRef} className="absolute z-10 w-full mt-1 bg-white border border-Ink/20 rounded-lg shadow-Soft max-h-60 overflow-y-auto">
                  {FoodSuggestions.map((Suggestion, Index) => (
                    <button
                      key={Index}
                      type="button"
                      className="w-full text-left px-4 py-2.5 hover:bg-blue-50 transition-colors text-sm border-b border-Ink/10 last:border-0"
                      onClick={() => HandleSelectSuggestion(Suggestion)}
                    >
                      {Suggestion}
                    </button>
                  ))}
                </div>
              )}
              <p className="text-xs text-Ink/60">
                Start typing to see AI-powered food suggestions
              </p>
              {DataSourceUsed && (
                <div className="mt-1 text-xs font-medium">
                  {DataSourceUsed === 'openfoodfacts' && (
                    <p className="text-green-600 flex items-center gap-1">
                      <img src="/source-icons/openfoodfacts.png" alt="" className="w-3 h-3" />
                      Nutrition from OpenFoodFacts
                      {SelectedSearchResult?.Metadata?.url && (
                        <a 
                          href={SelectedSearchResult.Metadata.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="underline hover:text-green-700"
                        >
                          (view)
                        </a>
                      )}
                    </p>
                  )}
                  {DataSourceUsed === 'ai-generated' && (
                    <p className="text-purple-600 flex items-center gap-1">
                      <img src="/source-icons/openai.png" alt="" className="w-3 h-3" />
                      Nutrition generated by AI
                    </p>
                  )}
                  {DataSourceUsed === 'ai-suggestion' && (
                    <p className="text-purple-600 flex items-center gap-1">
                      <img src="/source-icons/openai.png" alt="" className="w-3 h-3" />
                      Auto-populated by AI (from suggestion)
                    </p>
                  )}
                </div>
              )}
              <div className="mt-2 space-y-3">
                <div className="text-xs font-medium text-Ink/70">Search sources:</div>
                <div className="flex flex-wrap gap-3">
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={SearchOpenFoodFacts}
                      onChange={(E) => SetSearchOpenFoodFacts(E.target.checked)}
                      className="w-4 h-4"
                    />
                    <img src="/source-icons/openfoodfacts.png" alt="" className="w-4 h-4" />
                    <span>OpenFoodFacts</span>
                  </label>
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={SearchAI}
                      onChange={(e) => SetSearchAI(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <img src="/source-icons/openai.png" alt="" className="w-4 h-4" />
                    <span>AI</span>
                  </label>
                </div>
                <button
                  type="button"
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  onClick={HandleSearchDatabases}
                  disabled={IsSearchingDatabases || !NewFoodName || NewFoodName.length < 3 || (!SearchOpenFoodFacts && !SearchAI)}
                >
                  <span className="material-icons text-lg">search</span>
                  {IsSearchingDatabases ? "Searching..." : "Search Selected"}
                </button>
                
                <div className="border-t border-Ink/10 pt-3">
                  <p className="text-xs text-Ink/60 mb-2">Or search directly:</p>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      className="flex items-center justify-center gap-2 px-3 py-2 bg-white border border-Ink/20 text-Ink rounded-lg hover:bg-Ink/5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                      onClick={() => {
                        if (NewFoodName) {
                          window.open(`https://www.calorieking.com/au/en/foods/search?keywords=${encodeURIComponent(NewFoodName)}`, '_blank');
                        }
                      }}
                      disabled={!NewFoodName || NewFoodName.length < 3}
                      title="Search CalorieKing"
                    >
                      <img src="/source-icons/calorieking.png" alt="" className="w-4 h-4" />
                      CalorieKing
                    </button>
                    <button
                      type="button"
                      className="flex items-center justify-center gap-2 px-3 py-2 bg-white border border-Ink/20 text-Ink rounded-lg hover:bg-Ink/5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                      onClick={() => {
                        if (NewFoodName) {
                          window.open(`https://www.google.com/search?q=${encodeURIComponent(NewFoodName + ' nutrition')}`, '_blank');
                        }
                      }}
                      disabled={!NewFoodName || NewFoodName.length < 3}
                      title="Search Google"
                    >
                      <img src="/source-icons/google.png" alt="" className="w-4 h-4" />
                      Google
                    </button>
                  </div>
                </div>
              </div>
            </label>

            {DatabaseSearchResults && (
              <div className="border border-Ink/20 rounded-lg p-4 bg-white shadow-md">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-Ink">Search Results</h4>
                  <button
                    type="button"
                    onClick={() => SetDatabaseSearchResults(null)}
                    className="text-Ink/60 hover:text-Ink"
                  >
                    <span className="material-icons text-sm">close</span>
                  </button>
                </div>
                
                {/* AI Results */}
                {SearchAI && ShowAiFirst && AiResults.length > 0 && (
                  <div className="mb-4">
                    <h5 className="text-sm font-medium text-Ink/70 mb-2 flex items-center gap-2">
                      <img src="/source-icons/openai.png" alt="" className="w-4 h-4" />
                      AI Generated {AiResults.length > 1 && `(${AiResults.length})`}
                    </h5>
                    <div className="space-y-2">
                      {AiResults.map((Result: any, Index: number) => (
                        <button
                          key={`ai-${Index}`}
                          type="button"
                          className="w-full text-left p-3 border border-Ink/10 rounded hover:bg-purple-50 hover:border-purple-300 transition-colors"
                          onClick={() => HandleSelectDatabaseResult(Result, "ai-generated")}
                        >
                          <div className="font-medium text-sm">{Result.FoodName}</div>
                          <div className="text-xs text-Ink/60 mt-1">
                            {Result.ServingDescription} • {Result.CaloriesPerServing || "?"} cal • {Result.ProteinPerServing || "?"}g protein
                          </div>
                          <div className="text-xs text-purple-600 mt-1">Generated by AI</div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* OpenFoodFacts Results */}
                {SearchOpenFoodFacts && (
                  <div className="mb-4">
                    <h5 className="text-sm font-medium text-Ink/70 mb-2 flex items-center gap-2">
                      <img src="/source-icons/openfoodfacts.png" alt="" className="w-4 h-4" />
                      OpenFoodFacts {OpenFoodFactsResults.length > 0 && `(${OpenFoodFactsResults.length})`}
                    </h5>
                    {OpenFoodFactsResults.length > 0 ? (
                      <div className="space-y-2">
                        {OpenFoodFactsResults.slice(0, 5).map((Result: any, Index: number) => (
                          <button
                            key={Index}
                            type="button"
                            className="w-full text-left p-3 border border-Ink/10 rounded hover:bg-green-50 hover:border-green-300 transition-colors"
                            onClick={() => HandleSelectDatabaseResult(Result, "openfoodfacts")}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <div className="font-medium text-sm">{Result.FoodName}</div>
                                <div className="text-xs text-Ink/60 mt-1">
                                  {Result.ServingDescription} • {Result.CaloriesPerServing || "?"} cal • {Result.ProteinPerServing || "?"}g protein
                                </div>
                                {Result.Metadata?.brands && (
                                  <div className="text-xs text-Ink/40 mt-0.5">{Result.Metadata.brands}</div>
                                )}
                              </div>
                              {Result.Metadata?.image_url && (
                                <img
                                  src={Result.Metadata.image_url}
                                  alt={Result.FoodName}
                                  className="w-12 h-12 object-cover rounded ml-2"
                                />
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-Ink/40 py-2">No products found in OpenFoodFacts</p>
                    )}
                  </div>
                )}

                {/* AI Results */}
                {SearchAI && !ShowAiFirst && AiResults.length > 0 && (
                  <div className="mb-4">
                    <h5 className="text-sm font-medium text-Ink/70 mb-2 flex items-center gap-2">
                      <img src="/source-icons/openai.png" alt="" className="w-4 h-4" />
                      AI Generated {AiResults.length > 1 && `(${AiResults.length})`}
                    </h5>
                    <div className="space-y-2">
                      {AiResults.map((Result: any, Index: number) => (
                        <button
                          key={`ai-${Index}`}
                          type="button"
                          className="w-full text-left p-3 border border-Ink/10 rounded hover:bg-purple-50 hover:border-purple-300 transition-colors"
                          onClick={() => HandleSelectDatabaseResult(Result, "ai-generated")}
                        >
                          <div className="font-medium text-sm">{Result.FoodName}</div>
                          <div className="text-xs text-Ink/60 mt-1">
                            {Result.ServingDescription} • {Result.CaloriesPerServing || "?"} cal • {Result.ProteinPerServing || "?"}g protein
                          </div>
                          <div className="text-xs text-purple-600 mt-1">Generated by AI</div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI Fallback Section */}
                {SearchAI && AiResults.length === 0 && OpenFoodFactsResults.length === 0 && (
                  <div className="text-center py-4 border-t border-Ink/10">
                    <p className="text-sm text-Ink/60 mb-3">No results found in databases</p>
                    <button
                      type="button"
                      onClick={HandleUseAIFallback}
                      disabled={IsPopulatingFromAI}
                      className="text-sm px-4 py-2 bg-purple-100 text-purple-700 rounded hover:bg-purple-200 transition-colors disabled:opacity-50 inline-flex items-center gap-2"
                    >
                      <img src="/source-icons/openai.png" alt="" className="w-4 h-4" />
                      {IsPopulatingFromAI ? "Generating..." : "Generate with AI"}
                    </button>
                  </div>
                )}
              </div>
            )}

            {IsPopulatingFromAI && (
              <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 px-3 py-2 rounded border border-blue-200">
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Loading nutrition info...</span>
              </div>
            )}

            <div className="space-y-2 text-sm">
              <span className="text-Ink/70">Serving size</span>
              <div className="grid grid-cols-2 gap-3">
                <input
                  className="InputField"
                  type="number"
                  min="0.01"
                  step="any"
                  value={NewFoodQuantity}
                  onChange={(Event) => SetNewFoodQuantity(Event.target.value)}
                  placeholder="1"
                  required
                />
                <select
                  className="InputField"
                  value={NewFoodUnit}
                  onChange={(Event) => SetNewFoodUnit(Event.target.value)}
                  required
                >
                  {CommonServingUnits.map((Unit) => (
                    <option key={Unit} value={Unit}>
                      {Unit}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <label className="space-y-2 text-sm">
                <span className="text-Ink/70">Calories *</span>
                <input
                  className="InputField"
                  type="number"
                  min="0"
                  value={NewFoodCalories}
                  onChange={(Event) => SetNewFoodCalories(Event.target.value)}
                  required
                />
              </label>

              <label className="space-y-2 text-sm">
                <span className="text-Ink/70">Protein (g) *</span>
                <input
                  className="InputField"
                  type="number"
                  min="0"
                  step="0.1"
                  value={NewFoodProtein}
                  onChange={(Event) => SetNewFoodProtein(Event.target.value)}
                  required
                />
              </label>
            </div>

            <details className="space-y-3">
              <summary className="text-sm text-Ink/70 cursor-pointer hover:text-Ink">
                More nutrition info (optional)
              </summary>
              <div className="grid grid-cols-2 gap-3 pt-2">
                <label className="space-y-2 text-sm">
                  <span className="text-Ink/70">Fibre (g)</span>
                  <input
                    className="InputField"
                    type="number"
                    min="0"
                    step="0.1"
                    value={NewFoodFibre}
                    onChange={(Event) => SetNewFoodFibre(Event.target.value)}
                    placeholder="Optional"
                  />
                </label>

                <label className="space-y-2 text-sm">
                  <span className="text-Ink/70">Carbs (g)</span>
                  <input
                    className="InputField"
                    type="number"
                    min="0"
                    step="0.1"
                    value={NewFoodCarbs}
                    onChange={(Event) => SetNewFoodCarbs(Event.target.value)}
                    placeholder="Optional"
                  />
                </label>

                <label className="space-y-2 text-sm">
                  <span className="text-Ink/70">Fat (g)</span>
                  <input
                    className="InputField"
                    type="number"
                    min="0"
                    step="0.1"
                    value={NewFoodFat}
                    onChange={(Event) => SetNewFoodFat(Event.target.value)}
                    placeholder="Optional"
                  />
                </label>

                <label className="space-y-2 text-sm">
                  <span className="text-Ink/70">Sat. Fat (g)</span>
                  <input
                    className="InputField"
                    type="number"
                    min="0"
                    step="0.1"
                    value={NewFoodSaturatedFat}
                    onChange={(Event) => SetNewFoodSaturatedFat(Event.target.value)}
                    placeholder="Optional"
                  />
                </label>

                <label className="space-y-2 text-sm">
                  <span className="text-Ink/70">Sugar (g)</span>
                  <input
                    className="InputField"
                    type="number"
                    min="0"
                    step="0.1"
                    value={NewFoodSugar}
                    onChange={(Event) => SetNewFoodSugar(Event.target.value)}
                    placeholder="Optional"
                  />
                </label>

                <label className="space-y-2 text-sm">
                  <span className="text-Ink/70">Sodium (mg)</span>
                  <input
                    className="InputField"
                    type="number"
                    min="0"
                    step="1"
                    value={NewFoodSodium}
                    onChange={(Event) => SetNewFoodSodium(Event.target.value)}
                    placeholder="Optional"
                  />
                </label>
              </div>
            </details>

            <div className="flex gap-3 pt-2">
              <button
                className="OutlineButton flex-1"
                type="button"
                onClick={() => {
                  SetIsAddingFood(false);
                  SetNewFoodName("");
                  SetNewFoodCalories("0");
                  SetNewFoodProtein("0");
                  SetNewFoodFibre("");
                  SetNewFoodCarbs("");
                  SetNewFoodFat("");
                  SetNewFoodSaturatedFat("");
                  SetNewFoodSugar("");
                  SetNewFoodSodium("");
                  SetNewFoodQuantity("1");
                  SetNewFoodUnit("serving");
                  SetIsPopulatingFromAI(false);
                  SetShowSuggestions(false);
                  SetDisableAutocomplete(false);
                  SetDatabaseSearchResults(null);
                  SetSelectedSearchResult(null);
                  SetDataSourceUsed(null);
                }}
                disabled={IsSaving}
              >
                Cancel
              </button>
              <button
                className="PillButton flex-1"
                type="submit"
                disabled={IsSaving}
              >
                {IsSaving ? "Adding..." : "Add food"}
              </button>
            </div>
          </form>
        </div>
      )}

      {IsAddingMeal && (
        <div className="Card bg-purple-50 border-2 border-purple-200">
          <h3 className="Headline text-lg mb-4">
            {EditingMealId ? "Edit meal" : "Create new meal"}
          </h3>
          <form className="space-y-3" onSubmit={HandleCreateOrUpdateMeal}>
            <label className="space-y-2 text-sm">
              <span className="text-Ink/70">Meal name</span>
              <input
                className="InputField"
                type="text"
                value={NewMealName}
                onChange={(Event) => SetNewMealName(Event.target.value)}
                placeholder="e.g. Breakfast combo"
                autoFocus
                required
              />
            </label>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-Ink/70">
                  Selected foods: {SelectedFoodIds.size}
                </span>
                <button
                  type="button"
                  className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                  onClick={() => SetIsAddingFood(true)}
                >
                  + Quick add food
                </button>
              </div>
              {SelectedFoodIds.size > 0 && (() => {
                const Totals = Array.from(SelectedFoodIds).reduce((Acc, FoodId) => {
                  const FoodItem = Foods.find(F => F.FoodId === FoodId);
                  if (!FoodItem) {
                    return Acc;
                  }
                  const Entry = SelectedMealItems[FoodId] ?? GetMealEntryDefaults();
                  const EntryQuantityValue = Number(Entry.EntryQuantity);
                  const PreviewServings = Number.isFinite(EntryQuantityValue)
                    ? GetPreviewServings(FoodItem, EntryQuantityValue, Entry.EntryUnit)
                    : null;
                  if (PreviewServings === null) {
                    Acc.NeedsConversion += 1;
                    Acc.Calories += FoodItem.CaloriesPerServing;
                    Acc.Protein += FoodItem.ProteinPerServing;
                    return Acc;
                  }
                  Acc.Calories += FoodItem.CaloriesPerServing * PreviewServings;
                  Acc.Protein += FoodItem.ProteinPerServing * PreviewServings;
                  return Acc;
                }, { Calories: 0, Protein: 0, NeedsConversion: 0 });
                return (
                  <div className="space-y-1">
                    <div className="text-xs text-Ink/70 bg-white rounded px-2 py-1.5 border border-purple-200">
                      {Math.round(Totals.Calories)} cal • {Totals.Protein.toFixed(1)}g protein
                    </div>
                    {Totals.NeedsConversion > 0 && (
                      <p className="text-[11px] text-Ink/50">
                        Some items will be converted when logging.
                      </p>
                    )}
                  </div>
                );
              })()}
              <p className="text-xs text-Ink/60">
                Select food items from the table below to add them to this meal
              </p>
            </div>

            {SelectedFoodIds.size > 0 && (
              <div className="space-y-3">
                <p className="text-xs font-medium text-Ink/70">Amounts per selected food</p>
                <div className="space-y-2">
                  {Array.from(SelectedFoodIds).map((FoodId) => {
                    const FoodItem = Foods.find((F) => F.FoodId === FoodId);
                    if (!FoodItem) return null;
                    const Entry = SelectedMealItems[FoodId] ?? GetMealEntryDefaults();
                    return (
                      <div key={FoodId} className="grid gap-2 rounded-lg bg-white border border-purple-100 p-2 sm:grid-cols-[1fr,140px,160px]">
                        <div>
                          <div className="text-sm font-medium text-Ink">{FoodItem.FoodName}</div>
                          <div className="text-xs text-Ink/60">
                            Serving: {FoodItem.ServingQuantity} {FoodItem.ServingUnit}
                          </div>
                        </div>
                        <input
                          className="InputField"
                          type="number"
                          min="0.01"
                          step="any"
                          value={Entry.EntryQuantity}
                          onChange={(Event) => {
                            const Value = Event.target.value;
                            SetSelectedMealItems((Prev) => ({
                              ...Prev,
                              [FoodId]: { ...Entry, EntryQuantity: Value }
                            }));
                          }}
                        />
                        <input
                          className="InputField"
                          list="meal-entry-unit-options"
                          value={Entry.EntryUnit}
                          onChange={(Event) => {
                            const Value = Event.target.value;
                            SetSelectedMealItems((Prev) => ({
                              ...Prev,
                              [FoodId]: { ...Entry, EntryUnit: Value }
                            }));
                          }}
                          placeholder="Unit"
                        />
                      </div>
                    );
                  })}
                </div>
                <datalist id="meal-entry-unit-options">
                  {MealEntryUnitOptions.map((Unit) => (
                    <option key={Unit} value={Unit} />
                  ))}
                </datalist>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button
                className="OutlineButton flex-1"
                type="button"
                onClick={() => {
                  SetIsAddingMeal(false);
                  SetEditingMealId(null);
                  SetNewMealName("");
                  SetSelectedFoodIds(new Set());
                  SetSelectedMealItems({});
                }}
                disabled={IsSaving}
              >
                Cancel
              </button>
              <button
                className="PillButton flex-1"
                type="submit"
                disabled={IsSaving || SelectedFoodIds.size === 0}
              >
                {IsSaving ? (EditingMealId ? "Updating..." : "Creating...") : (EditingMealId ? "Update meal" : "Create meal")}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Meals Section */}
      {Meals.length > 0 && !IsAddingMeal && (
        <div className="Card">
          <h3 className="Headline text-lg mb-3 flex items-center gap-2">
            <span>🍲</span>
            <span>Meals ({Meals.length})</span>
          </h3>
          <div className="space-y-2">
            {Meals.map((Meal) => {
              const TotalCalories = Meal.Items.reduce((Sum, Item) => {
                const FoodItem = Foods.find(F => F.FoodId === Item.FoodId);
                return Sum + (FoodItem ? FoodItem.CaloriesPerServing * Item.Quantity : 0);
              }, 0);
              const TotalProtein = Meal.Items.reduce((Sum, Item) => {
                const FoodItem = Foods.find(F => F.FoodId === Item.FoodId);
                return Sum + (FoodItem ? FoodItem.ProteinPerServing * Item.Quantity : 0);
              }, 0);

              return (
                <div
                  key={Meal.Template.MealTemplateId}
                  className="bg-purple-50/50 border border-purple-100 rounded-lg p-3 hover:bg-purple-50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-Ink truncate">{Meal.Template.TemplateName}</h4>
                      <p className="text-xs text-Ink/60 mt-0.5">
                        {Meal.Items.length} {Meal.Items.length === 1 ? "item" : "items"} • {Math.round(TotalCalories)} cal • {TotalProtein.toFixed(1)}g protein
                      </p>
                      <p className="text-xs text-Ink/50 mt-1">
                        {Meal.Items.map(Item => Item.FoodName).join(", ")}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <button
                        className="text-Ink/60 hover:text-Ink transition-colors p-1"
                        type="button"
                        onClick={() => HandleEditMeal(Meal)}
                        aria-label="Edit meal"
                      >
                        <span className="material-icons text-lg">edit</span>
                      </button>
                      <button
                        className="text-red-500/60 hover:text-red-500 transition-colors p-1"
                        type="button"
                        onClick={() => HandleDeleteMeal(Meal.Template.MealTemplateId)}
                        aria-label="Delete meal"
                      >
                        <span className="material-icons text-lg">delete</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Foods Section */}
      {Foods.length === 0 ? (
        <div className="Card text-center text-sm text-Ink/50">
          No foods yet. Add your first food to get started!
        </div>
      ) : (
        <div className="Card">
          <h3 className="Headline text-lg mb-3 flex items-center gap-2">
            <span>🥕</span>
            <span>Foods ({Foods.length})</span>
          </h3>
          <div className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-Ink/5 border-b border-Ink/10">
                  <tr>
                    {IsAddingMeal && (
                      <th className="w-12 px-4 py-3">
                        <input
                          type="checkbox"
                          className="w-4 h-4"
                          checked={SelectedFoodIds.size === Foods.length && Foods.length > 0}
                          onChange={(Event) => {
                            if (Event.target.checked) {
                              SetSelectedFoodIds(new Set(Foods.map(F => F.FoodId)));
                              const NextItems: Record<string, { EntryQuantity: string; EntryUnit: string }> = {};
                              Foods.forEach((FoodItem) => {
                                NextItems[FoodItem.FoodId] = SelectedMealItems[FoodItem.FoodId] ?? GetMealEntryDefaults();
                              });
                              SetSelectedMealItems(NextItems);
                            } else {
                              SetSelectedFoodIds(new Set());
                              SetSelectedMealItems({});
                            }
                          }}
                          aria-label="Select all"
                        />
                      </th>
                    )}
                    <th
                      className="text-left px-4 py-3 text-sm font-medium text-Ink/70 cursor-pointer hover:bg-Ink/10 transition-colors"
                      onClick={() => HandleSort("name")}
                    >
                      <div className="flex items-center gap-2">
                        Name
                        <span className={`material-icons text-sm ${SortBy === "name" ? "opacity-100" : "opacity-0"}`}>
                          {SortDirection === "asc" ? "arrow_upward" : "arrow_downward"}
                        </span>
                      </div>
                    </th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-Ink/70">
                      Serving
                    </th>
                    <th
                      className="text-center px-4 py-3 text-sm font-medium text-Ink/70 cursor-pointer hover:bg-Ink/10 transition-colors"
                      onClick={() => HandleSort("calories")}
                    >
                      <div className="flex items-center justify-center gap-2">
                        Calories
                        <span className={`material-icons text-sm ${SortBy === "calories" ? "opacity-100" : "opacity-0"}`}>
                          {SortDirection === "asc" ? "arrow_upward" : "arrow_downward"}
                        </span>
                      </div>
                    </th>
                    <th
                      className="text-center px-4 py-3 text-sm font-medium text-Ink/70 cursor-pointer hover:bg-Ink/10 transition-colors"
                      onClick={() => HandleSort("protein")}
                    >
                      <div className="flex items-center justify-center gap-2">
                        Protein
                        <span className={`material-icons text-sm ${SortBy === "protein" ? "opacity-100" : "opacity-0"}`}>
                          {SortDirection === "asc" ? "arrow_upward" : "arrow_downward"}
                        </span>
                      </div>
                    </th>
                    <th
                      className="text-center px-4 py-3 text-sm font-medium text-Ink/70 cursor-pointer hover:bg-Ink/10 transition-colors"
                      onClick={() => HandleSort("date")}
                    >
                      <div className="flex items-center justify-center gap-2">
                        Date added
                        <span className={`material-icons text-sm ${SortBy === "date" ? "opacity-100" : "opacity-0"}`}>
                          {SortDirection === "asc" ? "arrow_upward" : "arrow_downward"}
                        </span>
                      </div>
                    </th>
                    <th className="text-right px-4 py-3 text-sm font-medium text-Ink/70">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {GetSortedFoods().map((Food) => (
                    <tr
                      key={Food.FoodId}
                      className="border-b border-Ink/5 hover:bg-Ink/5 transition-colors"
                    >
                      {IsAddingMeal && (
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            className="w-4 h-4"
                            checked={SelectedFoodIds.has(Food.FoodId)}
                            onChange={() => HandleToggleFoodSelection(Food.FoodId)}
                            aria-label={`Select ${Food.FoodName}`}
                          />
                        </td>
                      )}
                      
                      <td className="px-4 py-3 font-medium text-Ink">
                        <div className="flex items-center gap-2">
                          {Food.FoodName}
                          {Food.DataSource && Food.DataSource !== "manual" && (
                            <span className="inline-flex items-center">
                                  {Food.DataSource === "openfoodfacts" && Food.Metadata?.url && (
                                    <a 
                                      href={Food.Metadata.url} 
                                      target="_blank" 
                                      rel="noopener noreferrer"
                                      title="View on OpenFoodFacts"
                                      className="hover:opacity-70 transition-opacity"
                                    >
                                      <img src="/source-icons/openfoodfacts.png" alt="OpenFoodFacts" className="w-4 h-4" />
                                    </a>
                                  )}
                                  {Food.DataSource === "openfoodfacts" && !Food.Metadata?.url && (
                                    <img src="/source-icons/openfoodfacts.png" alt="OpenFoodFacts" className="w-4 h-4" title="From OpenFoodFacts" />
                                  )}
                                  {(Food.DataSource === "ai" || Food.DataSource === "ai-generated" || Food.DataSource === "ai-suggestion") && (
                                    <img src="/source-icons/openai.png" alt="AI Generated" className="w-4 h-4" title="AI Generated" />
                                  )}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-Ink/70">
                            {Food.ServingQuantity} {Food.ServingUnit}
                          </td>
                          <td className="px-4 py-3 text-center text-sm text-Ink">
                            {Food.CaloriesPerServing}
                          </td>
                          <td className="px-4 py-3 text-center text-sm text-Ink">
                            {Food.ProteinPerServing}g
                          </td>
                          <td className="px-4 py-3 text-center text-xs text-Ink/60">
                            {Food.CreatedAt ? new Date(Food.CreatedAt).toLocaleDateString() : "-"}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              {(!Food.OwnerUserId || Food.OwnerUserId === CurrentUser?.UserId) && (
                                <>
                                  <button
                                    className="text-Ink/60 hover:text-Ink transition-colors"
                                    type="button"
                                    onClick={() => HandleEditFood(Food)}
                                    aria-label="Edit food"
                                  >
                                    <span className="material-icons text-lg">edit</span>
                                  </button>
                                  <button
                                    className="text-red-500/60 hover:text-red-500 transition-colors"
                                    type="button"
                                    onClick={() => HandleDeleteFood(Food.FoodId)}
                                    aria-label="Delete food"
                                  >
                                    <span className="material-icons text-lg">delete</span>
                                  </button>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Edit Food Modal */}
      {EditingFood && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="Card bg-white max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h3 className="Headline text-lg mb-4">Edit Food</h3>
            <form className="space-y-3" onSubmit={HandleSaveEditFood}>
              <label className="space-y-2 text-sm">
                <span className="text-Ink/70">Food name *</span>
                <input
                  className="InputField"
                  type="text"
                  value={EditFoodName}
                  onChange={(E) => SetEditFoodName(E.target.value)}
                  required
                  autoFocus
                />
              </label>

              <label className="space-y-2 text-sm">
                <span className="text-Ink/70">Serving size</span>
                <div className="flex gap-2">
                  <input
                    className="InputField w-24"
                    type="number"
                    min="0.01"
                    step="any"
                    value={EditFoodQuantity}
                    onChange={(E) => SetEditFoodQuantity(E.target.value)}
                    required
                  />
                  <select
                    className="InputField flex-1"
                    value={EditFoodUnit}
                    onChange={(E) => SetEditFoodUnit(E.target.value)}
                    required
                  >
                    {CommonServingUnits.map((Unit) => (
                      <option key={Unit} value={Unit}>
                        {Unit}
                      </option>
                    ))}
                  </select>
                </div>
              </label>

              <div className="grid grid-cols-2 gap-3">
                <label className="space-y-2 text-sm">
                  <span className="text-Ink/70">Calories *</span>
                  <input
                    className="InputField"
                    type="number"
                    min="0"
                    value={EditFoodCalories}
                    onChange={(E) => SetEditFoodCalories(E.target.value)}
                    required
                  />
                </label>

                <label className="space-y-2 text-sm">
                  <span className="text-Ink/70">Protein (g) *</span>
                  <input
                    className="InputField"
                    type="number"
                    min="0"
                    step="0.1"
                    value={EditFoodProtein}
                    onChange={(E) => SetEditFoodProtein(E.target.value)}
                    required
                  />
                </label>
              </div>

              <details className="text-sm">
                <summary className="cursor-pointer text-Ink/70 hover:text-Ink list-none">
                  <span className="inline-flex items-center gap-1">
                    <span className="material-icons text-base transition-transform duration-200 [details[open]_&]:rotate-180">expand_more</span>
                    More nutrition info (optional)
                  </span>
                </summary>
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <label className="space-y-2">
                    <span className="text-Ink/70">Fibre (g)</span>
                    <input
                      className="InputField"
                      type="number"
                      min="0"
                      step="0.1"
                      value={EditFoodFibre}
                      onChange={(E) => SetEditFoodFibre(E.target.value)}
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-Ink/70">Carbs (g)</span>
                    <input
                      className="InputField"
                      type="number"
                      min="0"
                      step="0.1"
                      value={EditFoodCarbs}
                      onChange={(E) => SetEditFoodCarbs(E.target.value)}
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-Ink/70">Fat (g)</span>
                    <input
                      className="InputField"
                      type="number"
                      min="0"
                      step="0.1"
                      value={EditFoodFat}
                      onChange={(E) => SetEditFoodFat(E.target.value)}
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-Ink/70">Saturated Fat (g)</span>
                    <input
                      className="InputField"
                      type="number"
                      min="0"
                      step="0.1"
                      value={EditFoodSaturatedFat}
                      onChange={(E) => SetEditFoodSaturatedFat(E.target.value)}
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-Ink/70">Sugar (g)</span>
                    <input
                      className="InputField"
                      type="number"
                      min="0"
                      step="0.1"
                      value={EditFoodSugar}
                      onChange={(E) => SetEditFoodSugar(E.target.value)}
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-Ink/70">Sodium (mg)</span>
                    <input
                      className="InputField"
                      type="number"
                      min="0"
                      step="1"
                      value={EditFoodSodium}
                      onChange={(E) => SetEditFoodSodium(E.target.value)}
                    />
                  </label>
                </div>
              </details>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={IsSaving}
                >
                  {IsSaving ? "Saving..." : "Save Changes"}
                </button>
                <button
                  type="button"
                  className="flex-1 px-4 py-2.5 bg-white text-Ink border border-Ink/20 rounded-lg hover:bg-Ink/5 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  onClick={HandleCancelEditFood}
                  disabled={IsSaving}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
};
