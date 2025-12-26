import axios from "axios";
import {
  AiSuggestionResponse,
  DailyLogCreateResponse,
  DailyLogResponse,
  ScheduleSlot,
  ScheduleSlotInput,
  ScheduleSlotsResponse,
  Food,
  InviteResponse,
  LoginInput,
  MealTemplateListResponse,
  MealTemplateWithItems,
  MealEntryWithFood,
  MealType,
  NutritionRecommendation,
  PendingGoogleInvite,
  RegisterInput,
  UpdateProfileInput,
  UserSettings,
  User
} from "../models/Models";
import { AppLogger } from "../utils/Logger";

export const ApiBaseUrl = import.meta.env.VITE_API_BASE_URL || "/";

const ApiClient = axios.create({
  baseURL: ApiBaseUrl,
  withCredentials: true
});

// Global flag to prevent multiple redirects
let IsRedirecting = false;

const ResolveRequestUrl = (Config: any): string => {
  return Config?.url || "";
};

const ResolveRequestMethod = (Config: any): string => {
  return (Config?.method || "get").toUpperCase();
};

// Request logging interceptor
ApiClient.interceptors.request.use(
  (Config) => {
    const UsePerformance = typeof performance !== "undefined";
    const StartTime = UsePerformance ? performance.now() : Date.now();
    (Config as any).Metadata = { StartTime, UsePerformance };
    return Config;
  },
  (ErrorValue) => {
    AppLogger.warn("Api request setup failed", { Message: ErrorValue?.message });
    return Promise.reject(ErrorValue);
  }
);

// Response logging interceptor
ApiClient.interceptors.response.use(
  (Response) => {
    const Metadata = (Response.config as any).Metadata || {};
    const UsePerformance = Boolean(Metadata.UsePerformance);
    const StartTime = Metadata.StartTime || (UsePerformance ? performance.now() : Date.now());
    const EndTime = UsePerformance ? performance.now() : Date.now();
    const DurationMs = Math.round(EndTime - StartTime);
    const Method = ResolveRequestMethod(Response.config);
    const Url = ResolveRequestUrl(Response.config);
    const Status = Response.status;
    const Context = { Method, Url, Status, DurationMs };

    if (Status >= 500) {
      AppLogger.error("Api response error", Context);
    } else if (Status >= 400) {
      AppLogger.warn("Api response warning", Context);
    } else if (Method === "GET") {
      AppLogger.debug("Api response", Context);
    } else {
      AppLogger.info("Api response", Context);
    }

    return Response;
  },
  (ErrorValue) => {
    const Config = ErrorValue?.config;
    const Metadata = Config?.Metadata || {};
    const UsePerformance = Boolean(Metadata.UsePerformance);
    const StartTime = Metadata.StartTime || (UsePerformance ? performance.now() : Date.now());
    const EndTime = UsePerformance ? performance.now() : Date.now();
    const DurationMs = Math.round(EndTime - StartTime);
    const Method = ResolveRequestMethod(Config);
    const Url = ResolveRequestUrl(Config);
    const Status = ErrorValue?.response?.status;

    const Context = {
      Method,
      Url,
      Status,
      DurationMs,
      Message: ErrorValue?.message
    };

    if (Status && Status >= 500) {
      AppLogger.error("Api response failed", Context);
    } else {
      AppLogger.warn("Api response failed", Context);
    }

    return Promise.reject(ErrorValue);
  }
);

// Response interceptor to handle 401 globally
ApiClient.interceptors.response.use(
  (Response) => Response,
  (ErrorValue) => {
    if (axios.isAxiosError(ErrorValue) && ErrorValue.response?.status === 401 && !IsRedirecting) {
      // Session expired or invalid - redirect to auth
      IsRedirecting = true;
      window.dispatchEvent(new CustomEvent("auth:logout"));
      setTimeout(() => {
        IsRedirecting = false;
      }, 1000);
    }
    return Promise.reject(ErrorValue);
  }
);

export const GetCurrentUser = async (): Promise<User> => {
  const Response = await ApiClient.get("/api/auth/me");
  return Response.data.User as User;
};

export const RegisterUser = async (Input: RegisterInput): Promise<User> => {
  const Response = await ApiClient.post("/api/auth/register", Input);
  return Response.data.User as User;
};

export const LoginUser = async (Input: LoginInput): Promise<User> => {
  const Response = await ApiClient.post("/api/auth/login", Input);
  return Response.data.User as User;
};

export const LogoutUser = async (): Promise<void> => {
  await ApiClient.post("/api/auth/logout");
};

export const UpdateProfile = async (Input: UpdateProfileInput): Promise<User> => {
  const Response = await ApiClient.patch("/api/auth/profile", Input);
  return Response.data.User as User;
};

export const StartGoogleLogin = (InviteCode?: string) => {
  const BaseUrl = ApiBaseUrl.startsWith("http") ? ApiBaseUrl : window.location.origin;
  const Url = new URL("/api/auth/google/login", BaseUrl);
  if (InviteCode && InviteCode.trim().length > 0) {
    Url.searchParams.set("InviteCode", InviteCode.trim());
  }
  window.location.assign(Url.toString());
};

export const CreateInvite = async (Email: string): Promise<InviteResponse> => {
  const Response = await ApiClient.post("/api/auth/invites", { Email });
  return Response.data as InviteResponse;
};

export const GetGooglePendingInvite = async (): Promise<PendingGoogleInvite> => {
  const Response = await ApiClient.get("/api/auth/google/pending");
  return Response.data as PendingGoogleInvite;
};

export const CompleteGoogleInvite = async (InviteCode: string): Promise<User> => {
  const Response = await ApiClient.post("/api/auth/google/complete", { InviteCode });
  return Response.data.User as User;
};

export const GetFoods = async (): Promise<Food[]> => {
  const Response = await ApiClient.get("/api/foods/");
  const Foods = Response.data?.Foods;
  return Array.isArray(Foods) ? (Foods as Food[]) : [];
};

export const CreateFood = async (Input: {
  FoodName: string;
  ServingDescription?: string;
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
}): Promise<Food> => {
  const Response = await ApiClient.post("/api/foods/", Input);
  return Response.data.Food as Food;
};

export const UpdateFood = async (FoodId: string, Input: {
  FoodName?: string;
  ServingQuantity?: number;
  ServingUnit?: string;
  CaloriesPerServing?: number;
  ProteinPerServing?: number;
  FibrePerServing?: number | null;
  CarbsPerServing?: number | null;
  FatPerServing?: number | null;
  SaturatedFatPerServing?: number | null;
  SugarPerServing?: number | null;
  SodiumPerServing?: number | null;
  IsFavourite?: boolean;
}): Promise<Food> => {
  const Response = await ApiClient.patch(`/api/foods/${FoodId}`, Input);
  return Response.data.Food as Food;
};

export const GetFoodSuggestions = async (Query: string, Limit: number = 10): Promise<string[]> => {
  const Response = await ApiClient.get("/api/food-lookup/suggestions", {
    params: { Q: Query, Limit }
  });
  return Response.data.Suggestions as string[];
};

export const LookupFoodByText = async (Query: string): Promise<{
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
}> => {
  const Response = await ApiClient.post("/api/food-lookup/text", { Query });
  return Response.data.Result;
};

export const LookupFoodOptionsByText = async (Query: string): Promise<Array<{
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
}>> => {
  const Response = await ApiClient.post("/api/food-lookup/text-options", { Query });
  return Response.data.Results;
};

export const SearchFoodDatabases = async (Query: string): Promise<{
  Openfoodfacts: any[];
  AiFallbackAvailable: boolean;
}> => {
  const Response = await ApiClient.post("/api/food-lookup/multi-source/search", { Query });
  return Response.data;
};

export const DeleteFood = async (FoodId: string): Promise<void> => {
  await ApiClient.delete(`/api/foods/${FoodId}`);
};

export const GetMealTemplates = async (): Promise<MealTemplateWithItems[]> => {
  const Response = await ApiClient.get("/api/meal-templates");
  const Templates = Response.data?.Templates;
  return Array.isArray(Templates) ? (Templates as MealTemplateWithItems[]) : [];
};

export const CreateMealTemplate = async (Input: {
  TemplateName: string;
  Items: Array<{
    FoodId: string;
    MealType: MealType;
    Quantity: number;
    EntryQuantity?: number;
    EntryUnit?: string;
    EntryNotes?: string | null;
    SortOrder: number;
  }>;
}): Promise<MealTemplateWithItems> => {
  const Response = await ApiClient.post("/api/meal-templates", Input);
  return Response.data.Template as MealTemplateWithItems;
};

export const DeleteMealTemplate = async (MealTemplateId: string): Promise<void> => {
  await ApiClient.delete(`/api/meal-templates/${MealTemplateId}`);
};
export const UpdateMealTemplate = async (MealTemplateId: string, Input: {
  TemplateName?: string;
  Items?: Array<{
    FoodId: string;
    MealType: MealType;
    Quantity: number;
    EntryQuantity?: number;
    EntryUnit?: string;
    EntryNotes?: string | null;
    SortOrder: number;
  }>;
}): Promise<MealTemplateWithItems> => {
  const Response = await ApiClient.patch(`/api/meal-templates/${MealTemplateId}`, Input);
  return Response.data.Template as MealTemplateWithItems;
};
export const GetDailyLog = async (LogDate: string): Promise<DailyLogResponse> => {
  const Response = await ApiClient.get(`/api/daily-logs/${LogDate}`);
  const Data = Response.data as DailyLogResponse;
  return {
    DailyLog: Data.DailyLog,
    Entries: Array.isArray(Data.Entries) ? Data.Entries : [],
    Totals: Data.Totals,
    Summary: Data.Summary,
    Targets: Data.Targets
  };
};

export const CreateDailyLog = async (LogDate: string, Steps: number, WeightKg?: number): Promise<DailyLogResponse> => {
  const Response = await ApiClient.post("/api/daily-logs/", {
    LogDate,
    Steps,
    WeightKg
  });
  return Response.data as DailyLogCreateResponse;
};

export const UpdateDailySteps = async (LogDate: string, Steps: number, WeightKg?: number): Promise<void> => {
  await ApiClient.patch(`/api/daily-logs/${LogDate}/steps`, { Steps, WeightKg });
};

export const CreateMealEntry = async (Input: {
  DailyLogId: string;
  MealType: MealType;
  FoodId?: string | null;
  MealTemplateId?: string | null;
  Quantity: number;
  EntryQuantity?: number | null;
  EntryUnit?: string | null;
  EntryNotes?: string | null;
  SortOrder?: number;
  ScheduleSlotId?: string | null;
}): Promise<MealEntryWithFood> => {
  const Response = await ApiClient.post("/api/daily-logs/meal-entries", {
    DailyLogId: Input.DailyLogId,
    MealType: Input.MealType,
    FoodId: Input.FoodId ?? null,
    MealTemplateId: Input.MealTemplateId ?? null,
    Quantity: Input.Quantity,
    EntryQuantity: Input.EntryQuantity ?? null,
    EntryUnit: Input.EntryUnit ?? null,
    EntryNotes: Input.EntryNotes ?? null,
    SortOrder: Input.SortOrder ?? 0,
    ScheduleSlotId: Input.ScheduleSlotId ?? null
  });
  return Response.data.MealEntry as MealEntryWithFood;
};

export const DeleteMealEntry = async (MealEntryId: string): Promise<void> => {
  await ApiClient.delete(`/api/daily-logs/meal-entries/${MealEntryId}`);
};

export const ApplyMealTemplate = async (MealTemplateId: string, LogDate: string): Promise<void> => {
  await ApiClient.post(`/api/meal-templates/${MealTemplateId}/apply`, { LogDate });
};

export const GetAiSuggestions = async (LogDate: string): Promise<AiSuggestionResponse> => {
  const EncodedDate = encodeURIComponent(LogDate);
  const Response = await ApiClient.get(`/api/suggestions/ai?LogDate=${EncodedDate}`);
  return Response.data as AiSuggestionResponse;
};

export const GetScheduleSlots = async (): Promise<ScheduleSlot[]> => {
  const Response = await ApiClient.get("/api/schedule/");
  const Data = Response.data as ScheduleSlotsResponse;
  return Array.isArray(Data?.Slots) ? Data.Slots : [];
};

export const UpdateScheduleSlots = async (Slots: ScheduleSlotInput[]): Promise<ScheduleSlot[]> => {
  const Response = await ApiClient.put("/api/schedule/", { Slots });
  const Data = Response.data as ScheduleSlotsResponse;
  return Array.isArray(Data?.Slots) ? Data.Slots : [];
};

export const GetUserSettings = async (): Promise<UserSettings> => {
  const Response = await ApiClient.get("/api/settings/");
  return Response.data as UserSettings;
};

export const UpdateUserSettings = async (Input: Partial<UserSettings["Targets"]> & {
  TodayLayout?: string[];
}): Promise<UserSettings> => {
  const Response = await ApiClient.put("/api/settings/", Input);
  return Response.data as UserSettings;
};

export const GetAiNutritionRecommendations = async (): Promise<NutritionRecommendation> => {
  const Response = await ApiClient.post("/api/settings/ai-recommendations");
  return Response.data as NutritionRecommendation;
};
