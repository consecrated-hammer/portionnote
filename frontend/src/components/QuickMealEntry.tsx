import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Food, MealType, MealTemplateWithItems } from "../models/Models";

interface QuickMealEntryProps {
  Foods: Food[];
  Templates?: MealTemplateWithItems[];
  RecentEntries?: Array<{ 
    FoodId?: string | null; 
    MealTemplateId?: string | null;
    MealType: MealType; 
    LastUsed: string;
  }>;
  DefaultMealType?: MealType;
  OnSubmit: (FoodId: string, MealType: MealType, Quantity: number) => Promise<void>;
  OnSubmitTemplate?: (TemplateId: string, MealType: MealType) => Promise<void>;
  OnCancel?: () => void;
  AutoFocus?: boolean;
  ReturnToLog?: boolean;
  ReturnDate?: string;
  PreselectedFoodId?: string;
  InitialQuantity?: number;
}

const MealTypeOptions: { Label: string; Value: MealType; Emoji: string }[] = [
  { Label: "Breakfast", Value: "Breakfast", Emoji: "🌅" },
  { Label: "Morning Snack", Value: "Snack1", Emoji: "🍎" },
  { Label: "Lunch", Value: "Lunch", Emoji: "🍱" },
  { Label: "Afternoon Snack", Value: "Snack2", Emoji: "🥨" },
  { Label: "Dinner", Value: "Dinner", Emoji: "🍽️" },
  { Label: "Evening Snack", Value: "Snack3", Emoji: "🌙" }
];

// Smart default based on time of day
const GetSmartMealType = (): MealType => {
  const Hour = new Date().getHours();
  if (Hour < 10) return "Breakfast";
  if (Hour < 12) return "Snack1";
  if (Hour < 14) return "Lunch";
  if (Hour < 17) return "Snack2";
  if (Hour < 20) return "Dinner";
  return "Snack3";
};

type FoodOrTemplate = 
  | { Type: "food"; Food: Food }
  | { Type: "template"; Template: MealTemplateWithItems };

export const QuickMealEntry = ({
  Foods,
  Templates = [],
  RecentEntries = [],
  DefaultMealType,
  OnSubmit,
  OnSubmitTemplate,
  OnCancel,
  AutoFocus = false,
  ReturnToLog = false,
  ReturnDate,
  PreselectedFoodId,
  InitialQuantity
}: QuickMealEntryProps) => {
  const Navigate = useNavigate();
  const [MealType, SetMealType] = useState<MealType>(DefaultMealType ?? GetSmartMealType());
  const [SelectedItem, SetSelectedItem] = useState<FoodOrTemplate | null>(null);
  const [Quantity, SetQuantity] = useState(1);
  const [IsSubmitting, SetIsSubmitting] = useState(false);
  const [SearchTerm, SetSearchTerm] = useState("");
  const AppliedPreselectRef = useRef<string | null>(null);
  const SearchTermValue = SearchTerm.trim();
  const SearchTermLower = SearchTermValue.toLowerCase();

  // Get foods and templates recently used for this specific meal type
  const GetRecentItemsForMealType = () => {
    // Separate recent food IDs and template IDs
    const RecentFoodIds = RecentEntries
      .filter((E) => E.MealType === MealType && E.FoodId)
      .sort((A, B) => new Date(B.LastUsed).getTime() - new Date(A.LastUsed).getTime())
      .slice(0, 10)
      .map((E) => E.FoodId!);
    
    const RecentTemplateIds = RecentEntries
      .filter((E) => E.MealType === MealType && E.MealTemplateId)
      .sort((A, B) => new Date(B.LastUsed).getTime() - new Date(A.LastUsed).getTime())
      .slice(0, 10)
      .map((E) => E.MealTemplateId!);
    
    const RecentFoodSet = new Set(RecentFoodIds);
    const RecentTemplateSet = new Set(RecentTemplateIds);
    
    const RecentFoodsList = Foods.filter((F) => RecentFoodSet.has(F.FoodId));
    const RecentTemplatesList = Templates.filter((T) => RecentTemplateSet.has(T.Template.MealTemplateId));
    const OtherFoods = Foods.filter((F) => !RecentFoodSet.has(F.FoodId));
    const OtherTemplates = Templates.filter((T) => !RecentTemplateSet.has(T.Template.MealTemplateId));
    
    // Sort recent foods by their position in RecentFoodIds
    RecentFoodsList.sort((A, B) => RecentFoodIds.indexOf(A.FoodId) - RecentFoodIds.indexOf(B.FoodId));
    RecentTemplatesList.sort((A, B) => RecentTemplateIds.indexOf(A.Template.MealTemplateId) - RecentTemplateIds.indexOf(B.Template.MealTemplateId));
    
    return {
      RecentFoods: RecentFoodsList,
      RecentTemplates: RecentTemplatesList,
      OtherFoods: OtherFoods.sort((A, B) => A.FoodName.localeCompare(B.FoodName)),
      OtherTemplates: OtherTemplates.sort((A, B) => A.Template.TemplateName.localeCompare(B.Template.TemplateName))
    };
  };

  // Combine foods and templates for display
  const GetFilteredItems = (): FoodOrTemplate[] => {
    const { RecentFoods, RecentTemplates, OtherFoods, OtherTemplates } = GetRecentItemsForMealType();
    const Items: FoodOrTemplate[] = [
      ...RecentTemplates.map((T) => ({ Type: "template" as const, Template: T })),
      ...RecentFoods.map((F) => ({ Type: "food" as const, Food: F })),
      ...OtherTemplates.map((T) => ({ Type: "template" as const, Template: T })),
      ...OtherFoods.map((F) => ({ Type: "food" as const, Food: F }))
    ];
    
    // Apply search filter
    if (SearchTermValue) {
      return Items.filter((Item) => {
        if (Item.Type === "food") {
          return Item.Food.FoodName.toLowerCase().includes(SearchTermLower);
        } else {
          return Item.Template.Template.TemplateName.toLowerCase().includes(SearchTermLower);
        }
      });
    }
    
    return Items.slice(0, 10);
  };

  const FilteredItems = GetFilteredItems();
  const HasFoodMatch = SearchTermValue.length > 0 && Foods.some((FoodItem) =>
    FoodItem.FoodName.toLowerCase().includes(SearchTermLower)
  );
  const ShowAddFoodOption = SearchTermValue.length > 0 && !HasFoodMatch;

  // Reset selection when meal type changes
  useEffect(() => {
    SetSelectedItem(null);
  }, [MealType]);

  useEffect(() => {
    if (AutoFocus && FilteredItems.length > 0 && !SelectedItem) {
      SetSelectedItem(FilteredItems[0]);
    }
  }, [AutoFocus, FilteredItems]);

  useEffect(() => {
    if (!PreselectedFoodId) {
      AppliedPreselectRef.current = null;
      return;
    }
    if (AppliedPreselectRef.current === PreselectedFoodId) {
      return;
    }
    const Match = Foods.find((FoodItem) => FoodItem.FoodId === PreselectedFoodId);
    if (Match) {
      SetSearchTerm(Match.FoodName);
      SetSelectedItem({ Type: "food", Food: Match });
      SetQuantity(InitialQuantity && InitialQuantity > 0 ? InitialQuantity : 1);
      AppliedPreselectRef.current = PreselectedFoodId;
    }
  }, [Foods, PreselectedFoodId, InitialQuantity]);

  useEffect(() => {
    if (InitialQuantity && InitialQuantity > 0) {
      SetQuantity(InitialQuantity);
    }
  }, [InitialQuantity]);

  const HandleSubmit = async () => {
    if (!SelectedItem) return;
    
    SetIsSubmitting(true);
    try {
      if (SelectedItem.Type === "food") {
        if (Quantity <= 0) return;
        await OnSubmit(SelectedItem.Food.FoodId, MealType, Quantity);
      } else {
        if (OnSubmitTemplate) {
          await OnSubmitTemplate(SelectedItem.Template.Template.MealTemplateId, MealType);
        }
      }
      // Reset form
      SetQuantity(1);
      SetSelectedItem(null);
      SetSearchTerm("");
    } catch (Error) {
      console.error("Failed to submit meal entry:", Error);
    } finally {
      SetIsSubmitting(false);
    }
  };

  const AdjustQuantity = (Delta: number) => {
    SetQuantity((Prev) => Math.max(0.5, Prev + Delta));
  };

  const HandleAddFood = () => {
    if (!SearchTermValue) return;
    const Params = new URLSearchParams();
    Params.set("addFood", "1");
    Params.set("foodName", SearchTermValue);
    if (ReturnToLog) {
      Params.set("returnTo", "log");
      Params.set("returnMealType", MealType);
      if (ReturnDate) {
        Params.set("returnDate", ReturnDate);
      }
    }
    Navigate(`/foods?${Params.toString()}`);
  };

  return (
    <div className="space-y-4">
      {/* Meal Type Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {MealTypeOptions.map((Option) => (
          <button
            key={Option.Value}
            type="button"
            onClick={() => SetMealType(Option.Value)}
            className={`flex-shrink-0 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
              MealType === Option.Value
                ? "bg-blue-600 text-white"
                : "bg-white border border-Ink/20 text-Ink hover:bg-Ink/5"
            }`}
            style={{ minHeight: "44px" }}
          >
            <span className="mr-1">{Option.Emoji}</span>
            {Option.Label}
          </button>
        ))}
      </div>

      {/* Food Search */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-Ink/70">Search food:</label>
        <input
          type="text"
          value={SearchTerm}
          onChange={(E) => SetSearchTerm(E.target.value)}
          placeholder="Type to search..."
          className="w-full px-4 py-3 rounded-lg border border-Ink/20 focus:outline-none focus:ring-2 focus:ring-blue-500"
          style={{ minHeight: "48px" }}
        />
      </div>

      {/* Recent/Filtered Foods */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-Ink/60 uppercase tracking-wider">
          {SearchTerm ? "Search Results" : `Recent ${MealTypeOptions.find((O) => O.Value === MealType)?.Label || "Foods"}`}
        </p>
        <div className="grid gap-2 max-h-64 overflow-y-auto">
          {FilteredItems.length === 0 ? (
            <>
              <p className="text-sm text-Ink/40 py-4 text-center">No items found</p>
              {ShowAddFoodOption && (
                <button
                  type="button"
                  onClick={HandleAddFood}
                  className="w-full text-left p-4 rounded-lg border-2 border-dashed border-blue-200 bg-blue-50/60 text-blue-700 hover:bg-blue-50 transition-colors"
                  style={{ minHeight: "72px" }}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">Add food</p>
                      <p className="text-xs text-blue-700/80 mt-1">
                        Use "{SearchTermValue}" as the name
                      </p>
                    </div>
                    <span className="material-icons text-blue-600">add_circle</span>
                  </div>
                </button>
              )}
            </>
          ) : (
            <>
              {ShowAddFoodOption && (
                <button
                  type="button"
                  onClick={HandleAddFood}
                  className="w-full text-left p-4 rounded-lg border-2 border-dashed border-blue-200 bg-blue-50/60 text-blue-700 hover:bg-blue-50 transition-colors"
                  style={{ minHeight: "72px" }}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">Add food</p>
                      <p className="text-xs text-blue-700/80 mt-1">
                        Use "{SearchTermValue}" as the name
                      </p>
                    </div>
                    <span className="material-icons text-blue-600">add_circle</span>
                  </div>
                </button>
              )}
              {FilteredItems.map((Item) => {
                const IsSelected = 
                  (SelectedItem?.Type === "food" && Item.Type === "food" && SelectedItem.Food.FoodId === Item.Food.FoodId) ||
                  (SelectedItem?.Type === "template" && Item.Type === "template" && SelectedItem.Template.Template.MealTemplateId === Item.Template.Template.MealTemplateId);
                
                if (Item.Type === "food") {
                  const FoodItem = Item.Food;
                  const TotalCalories = Math.round(FoodItem.CaloriesPerServing * Quantity);
                  const TotalProtein = (FoodItem.ProteinPerServing * Quantity).toFixed(1);

                  return (
                    <button
                      key={`food-${FoodItem.FoodId}`}
                      type="button"
                      onClick={() => SetSelectedItem(Item)}
                      className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                        IsSelected
                          ? "border-blue-600 bg-blue-50"
                          : "border-Ink/10 bg-white hover:border-blue-300"
                      }`}
                      style={{ minHeight: "72px" }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-semibold text-sm">{FoodItem.FoodName}</p>
                          <p className="text-xs text-Ink/60 mt-1">
                            {FoodItem.ServingQuantity} {FoodItem.ServingUnit} • {FoodItem.CaloriesPerServing} cal • {FoodItem.ProteinPerServing}g protein
                          </p>
                          {IsSelected && Quantity !== 1 && (
                            <p className="text-xs text-blue-600 mt-1 font-medium">
                              Total: {TotalCalories} cal • {TotalProtein}g protein
                            </p>
                          )}
                        </div>
                        {IsSelected && (
                          <span className="material-icons text-blue-600 ml-2">check_circle</span>
                        )}
                      </div>
                    </button>
                  );
                } else {
                  const TemplateItem = Item.Template;
                  const TotalCalories = Math.round(
                    TemplateItem.Items.reduce((Sum, I) => {
                      const Food = Foods.find((F) => F.FoodId === I.FoodId);
                      return Sum + (Food ? Food.CaloriesPerServing * I.Quantity : 0);
                    }, 0)
                  );
                  const TotalProtein = TemplateItem.Items.reduce((Sum, I) => {
                    const Food = Foods.find((F) => F.FoodId === I.FoodId);
                    return Sum + (Food ? Food.ProteinPerServing * I.Quantity : 0);
                  }, 0).toFixed(1);

                  return (
                    <button
                      key={`template-${TemplateItem.Template.MealTemplateId}`}
                      type="button"
                      onClick={() => SetSelectedItem(Item)}
                      className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                        IsSelected
                          ? "border-purple-600 bg-purple-50"
                          : "border-Ink/10 bg-white hover:border-purple-300"
                      }`}
                      style={{ minHeight: "72px" }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="material-icons text-purple-600 text-sm">restaurant_menu</span>
                            <p className="font-semibold text-sm">{TemplateItem.Template.TemplateName}</p>
                          </div>
                          <p className="text-xs text-Ink/60 mt-1">
                            {TemplateItem.Items.length} items • {TotalCalories} cal • {TotalProtein}g protein
                          </p>
                          <p className="text-xs text-Ink/40 mt-0.5">
                            {TemplateItem.Items.map((I) => I.FoodName).join(", ")}
                          </p>
                        </div>
                        {IsSelected && (
                          <span className="material-icons text-purple-600 ml-2">check_circle</span>
                        )}
                      </div>
                    </button>
                  );
                }
              })}
            </>
          )}
        </div>
      </div>

      {/* Quantity Stepper */}
      {SelectedItem && SelectedItem.Type === "food" && (
        <div className="space-y-2">
          <label className="text-sm font-medium text-Ink/70">Servings:</label>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => AdjustQuantity(-0.5)}
              disabled={Quantity <= 0.5}
              className="w-12 h-12 flex items-center justify-center rounded-lg bg-white border-2 border-Ink/20 hover:bg-Ink/5 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              style={{ minHeight: "48px", minWidth: "48px" }}
            >
              <span className="material-icons">remove</span>
            </button>
            <div className="flex-1 text-center">
              <p className="text-3xl font-bold text-Ink">{Quantity.toFixed(1)}</p>
              <p className="text-xs text-Ink/60">servings</p>
            </div>
            <button
              type="button"
              onClick={() => AdjustQuantity(0.5)}
              className="w-12 h-12 flex items-center justify-center rounded-lg bg-white border-2 border-Ink/20 hover:bg-Ink/5 transition-colors"
              style={{ minHeight: "48px", minWidth: "48px" }}
            >
              <span className="material-icons">add</span>
            </button>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => AdjustQuantity(-1)}
              className="flex-1 px-3 py-2 rounded-lg bg-white border border-Ink/20 hover:bg-Ink/5 text-sm font-medium"
              style={{ minHeight: "44px" }}
            >
              -1
            </button>
            <button
              type="button"
              onClick={() => AdjustQuantity(1)}
              className="flex-1 px-3 py-2 rounded-lg bg-white border border-Ink/20 hover:bg-Ink/5 text-sm font-medium"
              style={{ minHeight: "44px" }}
            >
              +1
            </button>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-2">
        {OnCancel && (
          <button
            type="button"
            onClick={OnCancel}
            disabled={IsSubmitting}
            className="flex-1 px-4 py-3 rounded-lg bg-white border border-Ink/20 text-Ink hover:bg-Ink/5 font-medium transition-colors disabled:opacity-50"
            style={{ minHeight: "48px" }}
          >
            Cancel
          </button>
        )}
        <button
          type="button"
          onClick={HandleSubmit}
          disabled={!SelectedItem || IsSubmitting || (SelectedItem.Type === "food" && Quantity <= 0)}
          className="flex-1 px-4 py-3 rounded-lg bg-blue-600 text-white hover:bg-blue-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ minHeight: "48px" }}
        >
          {IsSubmitting ? "Adding..." : 
           SelectedItem?.Type === "template" ? `Add ${SelectedItem.Template.Template.TemplateName}` :
           `Add to ${MealTypeOptions.find((O) => O.Value === MealType)?.Label}`}
        </button>
      </div>
    </div>
  );
};
