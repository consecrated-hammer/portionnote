from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MealType(str, Enum):
    Breakfast = "Breakfast"
    Snack1 = "Snack1"
    Lunch = "Lunch"
    Snack2 = "Snack2"
    Dinner = "Dinner"
    Snack3 = "Snack3"


class Food(BaseModel):
    FoodId: str
    OwnerUserId: Optional[str] = None
    FoodName: str
    ServingDescription: str  # Deprecated: use ServingQuantity + ServingUnit
    ServingQuantity: float = 1.0
    ServingUnit: str = "serving"
    CaloriesPerServing: int
    ProteinPerServing: float
    FibrePerServing: Optional[float] = None
    CarbsPerServing: Optional[float] = None
    FatPerServing: Optional[float] = None
    SaturatedFatPerServing: Optional[float] = None
    SugarPerServing: Optional[float] = None
    SodiumPerServing: Optional[float] = None
    DataSource: str = "manual"  # 'manual' or 'ai'
    CountryCode: str = "AU"  # ISO country code
    IsFavourite: bool
    CreatedAt: Optional[str] = None


class FoodInfo(BaseModel):
    """
    Lightweight food information schema for external API responses.
    Used by OpenFoodFacts, AI fallback, and multi-source lookup.
    """
    FoodName: str
    ServingDescription: str
    CaloriesPerServing: Optional[int] = None
    ProteinPerServing: Optional[float] = None
    FatPerServing: Optional[float] = None
    SaturatedFatPerServing: Optional[float] = None
    CarbohydratesPerServing: Optional[float] = None
    SugarPerServing: Optional[float] = None
    FiberPerServing: Optional[float] = None
    SodiumPerServing: Optional[float] = None
    Metadata: Optional[dict] = None  # Source-specific data (barcode, URL, image, etc.)


class DailyLog(BaseModel):
    DailyLogId: str
    LogDate: str
    Steps: int
    StepKcalFactorOverride: Optional[float] = None
    WeightKg: Optional[float] = None
    Notes: Optional[str] = None


class MealEntry(BaseModel):
    MealEntryId: str
    DailyLogId: str
    MealType: MealType
    FoodId: Optional[str] = None
    MealTemplateId: Optional[str] = None
    Quantity: float
    EntryQuantity: Optional[float] = None
    EntryUnit: Optional[str] = None
    ConversionDetail: Optional[str] = None
    EntryNotes: Optional[str] = None
    SortOrder: int
    ScheduleSlotId: Optional[str] = None
    CreatedAt: Optional[str] = None


class MealEntryWithFood(BaseModel):
    MealEntryId: str
    DailyLogId: str
    MealType: MealType
    FoodId: Optional[str] = None
    MealTemplateId: Optional[str] = None
    TemplateName: Optional[str] = None
    FoodName: str
    ServingDescription: str
    CaloriesPerServing: int
    ProteinPerServing: float
    FibrePerServing: Optional[float] = None
    CarbsPerServing: Optional[float] = None
    FatPerServing: Optional[float] = None
    SaturatedFatPerServing: Optional[float] = None
    SugarPerServing: Optional[float] = None
    SodiumPerServing: Optional[float] = None
    Quantity: float
    EntryQuantity: Optional[float] = None
    EntryUnit: Optional[str] = None
    ConversionDetail: Optional[str] = None
    EntryNotes: Optional[str] = None
    SortOrder: int
    ScheduleSlotId: Optional[str] = None
    CreatedAt: Optional[str] = None


class Targets(BaseModel):
    DailyCalorieTarget: int
    ProteinTargetMin: float
    ProteinTargetMax: float
    StepKcalFactor: float
    StepTarget: int
    # New nutrient targets
    FibreTarget: Optional[float] = None
    CarbsTarget: Optional[float] = None
    FatTarget: Optional[float] = None
    SaturatedFatTarget: Optional[float] = None
    SugarTarget: Optional[float] = None
    SodiumTarget: Optional[float] = None
    # Visibility toggles
    ShowProteinOnToday: bool = True
    ShowStepsOnToday: bool = True
    ShowFibreOnToday: bool = False
    ShowCarbsOnToday: bool = False
    ShowFatOnToday: bool = False
    ShowSaturatedFatOnToday: bool = False
    ShowSugarOnToday: bool = False
    ShowSodiumOnToday: bool = False
    # Bar ordering for Today page
    BarOrder: list[str] = Field(default_factory=lambda: ["Calories", "Protein", "Steps", "Fibre", "Carbs", "Fat", "SaturatedFat", "Sugar", "Sodium"])


class UserSettings(BaseModel):
    Targets: Targets
    TodayLayout: list[str]


class UpdateSettingsInput(BaseModel):
    DailyCalorieTarget: Optional[int] = Field(default=None, ge=0)
    ProteinTargetMin: Optional[float] = Field(default=None, ge=0)
    ProteinTargetMax: Optional[float] = Field(default=None, ge=0)
    StepKcalFactor: Optional[float] = Field(default=None, ge=0)
    StepTarget: Optional[int] = Field(default=None, ge=0)
    FibreTarget: Optional[float] = Field(default=None, ge=0)
    CarbsTarget: Optional[float] = Field(default=None, ge=0)
    FatTarget: Optional[float] = Field(default=None, ge=0)
    SaturatedFatTarget: Optional[float] = Field(default=None, ge=0)
    SugarTarget: Optional[float] = Field(default=None, ge=0)
    SodiumTarget: Optional[float] = Field(default=None, ge=0)
    ShowProteinOnToday: Optional[bool] = None
    ShowStepsOnToday: Optional[bool] = None
    ShowFibreOnToday: Optional[bool] = None
    ShowCarbsOnToday: Optional[bool] = None
    ShowFatOnToday: Optional[bool] = None
    ShowSaturatedFatOnToday: Optional[bool] = None
    ShowSugarOnToday: Optional[bool] = None
    ShowSodiumOnToday: Optional[bool] = None
    TodayLayout: Optional[list[str]] = None
    BarOrder: Optional[list[str]] = None


class DailyTotals(BaseModel):
    TotalCalories: int
    TotalProtein: float
    TotalFibre: float
    TotalCarbs: float
    TotalFat: float
    TotalSaturatedFat: float
    TotalSugar: float
    TotalSodium: float
    CaloriesBurnedFromSteps: int
    NetCalories: int
    RemainingCalories: int
    RemainingProteinMin: float
    RemainingProteinMax: float
    RemainingFibre: float
    RemainingCarbs: float
    RemainingFat: float
    RemainingSaturatedFat: float
    RemainingSugar: float
    RemainingSodium: float


class DailySummary(BaseModel):
    LogDate: str
    TotalCalories: int
    TotalProtein: float
    Steps: int
    NetCalories: int


class WeeklySummary(BaseModel):
    Days: list[DailySummary]
    Totals: dict
    Averages: dict


class User(BaseModel):
    UserId: str
    Email: str
    FirstName: Optional[str] = None
    LastName: Optional[str] = None
    BirthDate: Optional[str] = None  # ISO date format YYYY-MM-DD
    HeightCm: Optional[int] = None
    WeightKg: Optional[float] = None
    ActivityLevel: Optional[str] = None
    IsAdmin: bool


class AdminUserSummary(BaseModel):
    UserId: str
    Email: str
    FirstName: Optional[str] = None
    LastName: Optional[str] = None
    AuthProvider: str
    IsAdmin: bool
    CreatedAt: Optional[str] = None


class AdminUserListResponse(BaseModel):
    Users: list[AdminUserSummary]


class UpdateProfileInput(BaseModel):
    FirstName: Optional[str] = Field(default=None, max_length=100)
    LastName: Optional[str] = Field(default=None, max_length=100)
    BirthDate: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    HeightCm: Optional[int] = Field(default=None, ge=50, le=300)
    WeightKg: Optional[float] = Field(default=None, ge=20, le=500)
    ActivityLevel: Optional[str] = Field(default=None)


class AdminUserCreateInput(BaseModel):
    Email: str = Field(min_length=1)
    Password: str = Field(min_length=8)
    FirstName: str = Field(min_length=1)
    LastName: Optional[str] = None
    IsAdmin: bool = False


class AdminUserUpdateInput(BaseModel):
    IsAdmin: bool


class Suggestion(BaseModel):
    SuggestionType: str
    Title: str
    Detail: str


class SuggestionsResponse(BaseModel):
    Suggestions: list[Suggestion]
    ModelUsed: Optional[str] = None


class DailyLogWithEntries(BaseModel):
    DailyLog: DailyLog
    Entries: list[MealEntryWithFood]


class SuggestionsInput(BaseModel):
    Log: DailyLogWithEntries
    RecentLogs: list[DailyLogWithEntries]


class RegisterUserInput(BaseModel):
    Email: str = Field(min_length=1)
    Password: str = Field(min_length=8)
    FirstName: str = Field(min_length=1)
    LastName: Optional[str] = None
    InviteCode: Optional[str] = None


class InviteCreateInput(BaseModel):
    Email: str = Field(min_length=1)


class InviteResponse(BaseModel):
    InviteCode: str
    InviteEmail: str
    InviteUrl: str
    CreatedAt: Optional[str] = None


class InviteCompleteInput(BaseModel):
    InviteCode: str = Field(min_length=1)


class PendingGoogleInviteResponse(BaseModel):
    HasPending: bool
    Email: Optional[str] = None
    Error: Optional[str] = None


class LoginInput(BaseModel):
    Email: str = Field(min_length=1)
    Password: str = Field(min_length=1)


class CreateFoodInput(BaseModel):
    FoodName: str = Field(min_length=1)
    ServingDescription: str = Field(min_length=1, default="1 serving")  # Deprecated
    ServingQuantity: float = Field(default=1.0, gt=0)
    ServingUnit: str = Field(default="serving", min_length=1)
    CaloriesPerServing: int = Field(ge=0)
    ProteinPerServing: float = Field(ge=0)
    FibrePerServing: Optional[float] = Field(default=None, ge=0)
    CarbsPerServing: Optional[float] = Field(default=None, ge=0)
    FatPerServing: Optional[float] = Field(default=None, ge=0)
    SaturatedFatPerServing: Optional[float] = Field(default=None, ge=0)
    SugarPerServing: Optional[float] = Field(default=None, ge=0)
    SodiumPerServing: Optional[float] = Field(default=None, ge=0)
    DataSource: str = Field(default="manual")
    CountryCode: str = Field(default="AU")
    IsFavourite: bool = False


class UpdateFoodInput(BaseModel):
    FoodName: Optional[str] = Field(default=None, min_length=1)
    ServingQuantity: Optional[float] = Field(default=None, gt=0)
    ServingUnit: Optional[str] = Field(default=None, min_length=1)
    CaloriesPerServing: Optional[int] = Field(default=None, ge=0)
    ProteinPerServing: Optional[float] = Field(default=None, ge=0)
    FibrePerServing: Optional[float] = Field(default=None, ge=0)
    CarbsPerServing: Optional[float] = Field(default=None, ge=0)
    FatPerServing: Optional[float] = Field(default=None, ge=0)
    SaturatedFatPerServing: Optional[float] = Field(default=None, ge=0)
    SugarPerServing: Optional[float] = Field(default=None, ge=0)
    SodiumPerServing: Optional[float] = Field(default=None, ge=0)
    IsFavourite: Optional[bool] = None


class CreateDailyLogInput(BaseModel):
    LogDate: str = Field(min_length=1)
    Steps: int = Field(default=0, ge=0)
    StepKcalFactorOverride: Optional[float] = Field(default=None, ge=0)
    WeightKg: Optional[float] = Field(default=None, ge=20, le=500)
    Notes: Optional[str] = None


class StepUpdateInput(BaseModel):
    Steps: int = Field(ge=0)
    StepKcalFactorOverride: Optional[float] = Field(default=None, ge=0)
    WeightKg: Optional[float] = Field(default=None, ge=20, le=500)


class CreateMealEntryInput(BaseModel):
    DailyLogId: str
    MealType: MealType
    FoodId: Optional[str] = None
    MealTemplateId: Optional[str] = None
    Quantity: float = Field(gt=0)
    EntryQuantity: Optional[float] = Field(default=None, gt=0)
    EntryUnit: Optional[str] = Field(default=None, min_length=1)
    EntryNotes: Optional[str] = None
    SortOrder: int = 0
    ScheduleSlotId: Optional[str] = None


class ScheduleSlot(BaseModel):
    ScheduleSlotId: str
    SlotName: str
    SlotTime: str
    MealType: MealType
    SortOrder: int


class ScheduleSlotInput(BaseModel):
    ScheduleSlotId: Optional[str] = None
    SlotName: str = Field(min_length=1)
    SlotTime: str = Field(min_length=1)
    MealType: MealType
    SortOrder: int = 0


class ScheduleSlotsResponse(BaseModel):
    Slots: list[ScheduleSlot]


class ScheduleSlotsUpdateInput(BaseModel):
    Slots: list[ScheduleSlotInput]


class MealTemplate(BaseModel):
    MealTemplateId: str
    TemplateName: str
    CreatedAt: str


class MealTemplateItem(BaseModel):
    MealTemplateItemId: str
    MealTemplateId: str
    FoodId: str
    MealType: MealType
    Quantity: float
    EntryQuantity: Optional[float] = None
    EntryUnit: Optional[str] = None
    EntryNotes: Optional[str] = None
    SortOrder: int
    FoodName: str
    ServingDescription: str


class MealTemplateWithItems(BaseModel):
    Template: MealTemplate
    Items: list[MealTemplateItem]


class MealTemplateListResponse(BaseModel):
    Templates: list[MealTemplateWithItems]


class MealTextParseInput(BaseModel):
    Text: str = Field(min_length=1)
    KnownFoods: Optional[list[str]] = None


class MealTextParseResponse(BaseModel):
    MealName: str
    ServingQuantity: float = 1.0
    ServingUnit: str = "serving"
    CaloriesPerServing: int
    ProteinPerServing: float
    FibrePerServing: Optional[float] = None
    CarbsPerServing: Optional[float] = None
    FatPerServing: Optional[float] = None
    SaturatedFatPerServing: Optional[float] = None
    SugarPerServing: Optional[float] = None
    SodiumPerServing: Optional[float] = None
    Summary: str


class MealTemplateItemInput(BaseModel):
    FoodId: str
    MealType: MealType
    Quantity: float = Field(gt=0)
    EntryQuantity: Optional[float] = Field(default=None, gt=0)
    EntryUnit: Optional[str] = Field(default=None, min_length=1)
    EntryNotes: Optional[str] = None
    SortOrder: int = 0


class CreateMealTemplateInput(BaseModel):
    TemplateName: str = Field(min_length=1)
    Items: list[MealTemplateItemInput]


class UpdateMealTemplateInput(BaseModel):
    TemplateName: Optional[str] = Field(default=None, min_length=1)
    Items: Optional[list[MealTemplateItemInput]] = None


class ApplyMealTemplateInput(BaseModel):
    LogDate: str = Field(min_length=1)


class ApplyMealTemplateResponse(BaseModel):
    CreatedCount: int


class NutritionRecommendationResponse(BaseModel):
    DailyCalorieTarget: int
    ProteinTargetMin: float
    ProteinTargetMax: float
    FibreTarget: Optional[float] = None
    CarbsTarget: Optional[float] = None
    FatTarget: Optional[float] = None
    SaturatedFatTarget: Optional[float] = None
    SugarTarget: Optional[float] = None
    SodiumTarget: Optional[float] = None
    Explanation: str
    ModelUsed: Optional[str] = None


class RecommendationLog(BaseModel):
    RecommendationLogId: int
    UserId: str
    CreatedAt: str
    Age: int
    HeightCm: float
    WeightKg: float
    ActivityLevel: str
    DailyCalorieTarget: int
    ProteinTargetMin: float
    ProteinTargetMax: float
    FibreTarget: Optional[float] = None
    CarbsTarget: Optional[float] = None
    FatTarget: Optional[float] = None
    SaturatedFatTarget: Optional[float] = None
    SugarTarget: Optional[float] = None
    SodiumTarget: Optional[float] = None
    Explanation: str


class RecommendationLogListResponse(BaseModel):
    Logs: list[RecommendationLog]
