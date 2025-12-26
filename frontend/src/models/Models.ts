export type Food = {
  FoodId: string;
  OwnerUserId?: string | null;
  FoodName: string;
  ServingDescription: string;  // Deprecated
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
  DataSource?: string;
  CountryCode?: string;
  IsFavourite: boolean;
  CreatedAt?: string | null;
  Metadata?: any;
};

export type MealType = "Breakfast" | "Snack1" | "Lunch" | "Snack2" | "Dinner" | "Snack3";

export type DailyLog = {
  DailyLogId: string;
  LogDate: string;
  Steps: number;
  StepKcalFactorOverride?: number | null;
  WeightKg?: number | null;
  Notes?: string | null;
};

export type MealEntryWithFood = {
  MealEntryId: string;
  DailyLogId: string;
  MealType: MealType;
  FoodId?: string | null;
  MealTemplateId?: string | null;
  TemplateName?: string | null;
  FoodName: string;
  ServingDescription: string;
  CaloriesPerServing: number;
  ProteinPerServing: number;
  FibrePerServing?: number | null;
  CarbsPerServing?: number | null;
  FatPerServing?: number | null;
  SaturatedFatPerServing?: number | null;
  SugarPerServing?: number | null;
  SodiumPerServing?: number | null;
  Quantity: number;
  EntryQuantity?: number | null;
  EntryUnit?: string | null;
  ConversionDetail?: string | null;
  EntryNotes?: string | null;
  SortOrder: number;
  ScheduleSlotId?: string | null;
  CreatedAt?: string | null;
};

export type DailyLogResponse = {
  DailyLog: DailyLog | null;
  Entries: MealEntryWithFood[];
  Totals: DailyTotals;
  Summary: DailySummary;
  Targets: Targets;
};

export type DailyLogCreateResponse = {
  DailyLog: DailyLog;
};

export type Targets = {
  DailyCalorieTarget: number;
  ProteinTargetMin: number;
  ProteinTargetMax: number;
  StepKcalFactor: number;
  StepTarget: number;
  // New nutrient targets
  FibreTarget?: number;
  CarbsTarget?: number;
  FatTarget?: number;
  SaturatedFatTarget?: number;
  SugarTarget?: number;
  SodiumTarget?: number;
  // Visibility toggles
  ShowProteinOnToday?: boolean;
  ShowStepsOnToday?: boolean;
  ShowFibreOnToday?: boolean;
  ShowCarbsOnToday?: boolean;
  ShowFatOnToday?: boolean;
  ShowSaturatedFatOnToday?: boolean;
  ShowSugarOnToday?: boolean;
  ShowSodiumOnToday?: boolean;
  // Bar ordering
  BarOrder?: string[];
};

export type DailyTotals = {
  TotalCalories: number;
  TotalProtein: number;
  TotalFibre: number;
  TotalCarbs: number;
  TotalFat: number;
  TotalSaturatedFat: number;
  TotalSugar: number;
  TotalSodium: number;
  CaloriesBurnedFromSteps: number;
  NetCalories: number;
  RemainingCalories: number;
  RemainingProteinMin: number;
  RemainingProteinMax: number;
  RemainingFibre: number;
  RemainingCarbs: number;
  RemainingFat: number;
  RemainingSaturatedFat: number;
  RemainingSugar: number;
  RemainingSodium: number;
};

export type DailySummary = {
  LogDate: string;
  TotalCalories: number;
  TotalProtein: number;
  Steps: number;
  NetCalories: number;
};

export type User = {
  UserId: string;
  Email: string;
  FirstName?: string | null;
  LastName?: string | null;
  BirthDate?: string | null;  // ISO date YYYY-MM-DD
  HeightCm?: number | null;
  WeightKg?: number | null;
  ActivityLevel?: string | null;
  IsAdmin: boolean;
};

export type AdminUser = {
  UserId: string;
  Email: string;
  FirstName?: string | null;
  LastName?: string | null;
  AuthProvider: string;
  IsAdmin: boolean;
  CreatedAt?: string | null;
};

export type AdminUserListResponse = {
  Users: AdminUser[];
};

export type AdminUserCreateInput = {
  Email: string;
  Password: string;
  FirstName: string;
  LastName?: string;
  IsAdmin: boolean;
};

export type UpdateProfileInput = {
  FirstName?: string;
  LastName?: string;
  BirthDate?: string;
  HeightCm?: number;
  WeightKg?: number;
  ActivityLevel?: string;
};

export type RegisterInput = {
  Email: string;
  Password: string;
  FirstName: string;
  LastName?: string;
  InviteCode?: string;
};

export type LoginInput = {
  Email: string;
  Password: string;
};

export type InviteCreateInput = {
  Email: string;
};

export type InviteResponse = {
  InviteCode: string;
  InviteEmail: string;
  InviteUrl: string;
  CreatedAt?: string | null;
};

export type PendingGoogleInvite = {
  HasPending: boolean;
  Email?: string | null;
  Error?: string | null;
};

export type MealTemplate = {
  MealTemplateId: string;
  TemplateName: string;
  CreatedAt: string;
};

export type MealTemplateItem = {
  MealTemplateItemId: string;
  MealTemplateId: string;
  FoodId: string;
  MealType: MealType;
  Quantity: number;
  EntryQuantity?: number;
  EntryUnit?: string;
  EntryNotes?: string | null;
  SortOrder: number;
  FoodName: string;
  ServingDescription: string;
};

export type MealTemplateWithItems = {
  Template: MealTemplate;
  Items: MealTemplateItem[];
};

export type MealTemplateListResponse = {
  Templates: MealTemplateWithItems[];
};

export type MealTextParseResponse = {
  MealName: string;
  ServingQuantity: number;
  ServingUnit: string;
  CaloriesPerServing: number;
  ProteinPerServing: number;
  FibrePerServing?: number;
  CarbsPerServing?: number;
  FatPerServing?: number;
  SaturatedFatPerServing?: number;
  SugarPerServing?: number;
  SodiumPerServing?: number;
  Summary: string;
};

export type AiSuggestion = {
  SuggestionType: string;
  Title: string;
  Detail: string;
};

export type AiSuggestionResponse = {
  Suggestions: AiSuggestion[];
  ModelUsed?: string;
};

export type ScheduleSlot = {
  ScheduleSlotId: string;
  SlotName: string;
  SlotTime: string;
  MealType: MealType;
  SortOrder: number;
};

export type ScheduleSlotInput = {
  ScheduleSlotId?: string | null;
  SlotName: string;
  SlotTime: string;
  MealType: MealType;
  SortOrder: number;
};

export type ScheduleSlotsResponse = {
  Slots: ScheduleSlot[];
};

export type UserSettings = {
  Targets: Targets;
  TodayLayout: string[];
};

export type NutritionRecommendation = {
  DailyCalorieTarget: number;
  ProteinTargetMin: number;
  ProteinTargetMax: number;
  FibreTarget?: number;
  CarbsTarget?: number;
  FatTarget?: number;
  SaturatedFatTarget?: number;
  SugarTarget?: number;
  SodiumTarget?: number;
  Explanation: string;
  ModelUsed?: string;
};
