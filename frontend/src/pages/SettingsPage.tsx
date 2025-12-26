import { FormEvent, useEffect, useState } from "react";
import {
  CreateInvite,
  GetAiNutritionRecommendations,
  GetUserSettings,
  LogoutUser,
  UpdateProfile,
  UpdateUserSettings
} from "../services/ApiClient";
import { NutritionRecommendation, Targets, User } from "../models/Models";
import { AppLogger } from "../utils/Logger";

const DefaultTargets: Targets = {
  DailyCalorieTarget: 1498,
  ProteinTargetMin: 70,
  ProteinTargetMax: 188,
  StepKcalFactor: 0.04,
  StepTarget: 8500,
  ShowProteinOnToday: true,
  ShowStepsOnToday: true,
  ShowFibreOnToday: false,
  ShowCarbsOnToday: false,
  ShowFatOnToday: false,
  ShowSaturatedFatOnToday: false,
  ShowSugarOnToday: false,
  ShowSodiumOnToday: false
};

type SettingsPageProps = {
  onLogout: () => void;
  CurrentUser: User;
};

type NutrientConfig = {
  key: keyof Targets;
  label: string;
  unit: string;
  min?: keyof Targets;
  max?: keyof Targets;
  showKey?: keyof Targets;
  step: string;
};

const Nutrients: NutrientConfig[] = [
  { key: "ProteinTargetMin", label: "Protein", unit: "g", min: "ProteinTargetMin", max: "ProteinTargetMax", showKey: "ShowProteinOnToday", step: "0.1" },
  { key: "FibreTarget", label: "Fibre", unit: "g", showKey: "ShowFibreOnToday", step: "0.1" },
  { key: "CarbsTarget", label: "Carbs", unit: "g", showKey: "ShowCarbsOnToday", step: "0.1" },
  { key: "FatTarget", label: "Fat", unit: "g", showKey: "ShowFatOnToday", step: "0.1" },
  { key: "SaturatedFatTarget", label: "Saturated Fat", unit: "g", showKey: "ShowSaturatedFatOnToday", step: "0.1" },
  { key: "SugarTarget", label: "Sugar", unit: "g", showKey: "ShowSugarOnToday", step: "0.1" },
  { key: "SodiumTarget", label: "Sodium", unit: "mg", showKey: "ShowSodiumOnToday", step: "1" }
];

export const SettingsPage = ({ onLogout, CurrentUser }: SettingsPageProps) => {
  const [Targets, SetTargets] = useState<Targets>(DefaultTargets);
  const [OriginalTargets, SetOriginalTargets] = useState<Targets>(DefaultTargets);
  const [Profile, SetProfile] = useState<{ FirstName: string; LastName: string; BirthDate: string; HeightCm: string; WeightKg: string; ActivityLevel: string }>({
    FirstName: CurrentUser.FirstName || "",
    LastName: CurrentUser.LastName || "",
    BirthDate: CurrentUser.BirthDate || "",
    HeightCm: CurrentUser.HeightCm?.toString() || "",
    WeightKg: CurrentUser.WeightKg?.toString() || "",
    ActivityLevel: CurrentUser.ActivityLevel || ""
  });
  const [OriginalProfile, SetOriginalProfile] = useState(Profile);
  const [ExpandedSections, SetExpandedSections] = useState<Set<string>>(new Set());
  const [IsSavingSettings, SetIsSavingSettings] = useState(false);
  const [IsSavingProfile, SetIsSavingProfile] = useState(false);
  const [SettingsStatus, SetSettingsStatus] = useState<string | null>(null);
  const [SettingsError, SetSettingsError] = useState<string | null>(null);
  const [ProfileStatus, SetProfileStatus] = useState<string | null>(null);
  const [ProfileError, SetProfileError] = useState<string | null>(null);
  const [InviteEmail, SetInviteEmail] = useState("");
  const [InviteUrl, SetInviteUrl] = useState<string | null>(null);
  const [InviteStatus, SetInviteStatus] = useState<string | null>(null);
  const [InviteError, SetInviteError] = useState<string | null>(null);
  const [IsInviteLoading, SetIsInviteLoading] = useState(false);
  const [IsLoadingRecommendations, SetIsLoadingRecommendations] = useState(false);
  const [Recommendations, SetRecommendations] = useState<NutritionRecommendation | null>(null);
  const [ShowRecommendationsModal, SetShowRecommendationsModal] = useState(false);
  const [SelectedRecommendations, SetSelectedRecommendations] = useState<Set<string>>(new Set());

  const HasProfileMissing = !CurrentUser.FirstName || !CurrentUser.BirthDate || !CurrentUser.HeightCm || !CurrentUser.WeightKg || !CurrentUser.ActivityLevel;

  useEffect(() => {
    const CurrentProfile = {
      FirstName: CurrentUser.FirstName || "",
      LastName: CurrentUser.LastName || "",
      BirthDate: CurrentUser.BirthDate || "",
      HeightCm: CurrentUser.HeightCm?.toString() || "",
      WeightKg: CurrentUser.WeightKg?.toString() || "",
      ActivityLevel: CurrentUser.ActivityLevel || ""
    };
    SetProfile(CurrentProfile);
    SetOriginalProfile(CurrentProfile);
  }, [CurrentUser]);

  const ToggleSection = (Section: string) => {
    const NewExpanded = new Set(ExpandedSections);
    if (NewExpanded.has(Section)) {
      NewExpanded.delete(Section);
    } else {
      NewExpanded.add(Section);
    }
    SetExpandedSections(NewExpanded);
  };

  const HandleLogout = async () => {
    try {
      await LogoutUser();
    } finally {
      onLogout();
    }
  };

  const HandleCreateInvite = async (Event: FormEvent) => {
    Event.preventDefault();
    SetInviteError(null);
    SetInviteStatus(null);
    SetIsInviteLoading(true);

    try {
      const Invite = await CreateInvite(InviteEmail);
      SetInviteUrl(Invite.InviteUrl);
      SetInviteStatus("Invite link ready.");
    } catch (ErrorValue) {
      SetInviteError("Invite failed. Use a Gmail address that has not been invited.");
    } finally {
      SetIsInviteLoading(false);
    }
  };

  const HandleCopyInvite = async () => {
    if (!InviteUrl) {
      return;
    }

    try {
      await navigator.clipboard.writeText(InviteUrl);
      SetInviteStatus("Invite link copied.");
    } catch (ErrorValue) {
      SetInviteStatus("Copy failed. Select the link and copy it.");
    }
  };

  const LoadSettings = async () => {
    try {
      const Settings = await GetUserSettings();
      AppLogger.debug("Loaded settings from API", {
        HasSettings: Boolean(Settings)
      });
      const LoadedTargets = { ...DefaultTargets, ...Settings.Targets };
      AppLogger.debug("Merged targets", {
        DailyCalorieTarget: LoadedTargets.DailyCalorieTarget,
        ProteinTargetMin: LoadedTargets.ProteinTargetMin,
        ProteinTargetMax: LoadedTargets.ProteinTargetMax,
        StepKcalFactor: LoadedTargets.StepKcalFactor
      });
      SetTargets(LoadedTargets);
      SetOriginalTargets(LoadedTargets);
    } catch (ErrorValue) {
      SetSettingsError("Failed to load settings.");
    }
  };

  useEffect(() => {
    void LoadSettings();
  }, []);

  const HandleSaveSettings = async () => {
    SetSettingsError(null);
    SetSettingsStatus(null);
    SetIsSavingSettings(true);

    try {
      const Updated = await UpdateUserSettings(Targets);
      const UpdatedTargets = { ...DefaultTargets, ...Updated.Targets };
      SetTargets(UpdatedTargets);
      SetOriginalTargets(UpdatedTargets);
      SetSettingsStatus("Settings saved.");
      setTimeout(() => SetSettingsStatus(null), 3000);
    } catch (ErrorValue) {
      SetSettingsError("Failed to save settings.");
    } finally {
      SetIsSavingSettings(false);
    }
  };

  const UpdateTarget = (key: keyof Targets, value: number | boolean) => {
    SetTargets({ ...Targets, [key]: value });
  };

  const HandleSaveProfile = async () => {
    SetProfileError(null);
    SetProfileStatus(null);
    SetIsSavingProfile(true);

    try {
      const Input = {
        FirstName: Profile.FirstName || undefined,
        LastName: Profile.LastName || undefined,
        BirthDate: Profile.BirthDate || undefined,
        HeightCm: Profile.HeightCm ? Number(Profile.HeightCm) : undefined,
        WeightKg: Profile.WeightKg ? Number(Profile.WeightKg) : undefined,
        ActivityLevel: Profile.ActivityLevel || undefined
      };

      await UpdateProfile(Input);
      SetOriginalProfile(Profile);
      SetProfileStatus("Profile saved.");
      setTimeout(() => SetProfileStatus(null), 3000);
      // Refresh the page to update CurrentUser
      window.location.reload();
    } catch (ErrorValue) {
      SetProfileError("Failed to save profile.");
    } finally {
      SetIsSavingProfile(false);
    }
  };

  const HandleGetRecommendations = async () => {
    SetIsLoadingRecommendations(true);
    try {
      const Result = await GetAiNutritionRecommendations();
      SetRecommendations(Result);
      // Pre-select all recommendations by default
      const AllKeys = new Set<string>(["DailyCalorieTarget", "ProteinTargetMin", "ProteinTargetMax"]);
      if (Result.FibreTarget) AllKeys.add("FibreTarget");
      if (Result.CarbsTarget) AllKeys.add("CarbsTarget");
      if (Result.FatTarget) AllKeys.add("FatTarget");
      if (Result.SaturatedFatTarget) AllKeys.add("SaturatedFatTarget");
      if (Result.SugarTarget) AllKeys.add("SugarTarget");
      if (Result.SodiumTarget) AllKeys.add("SodiumTarget");
      SetSelectedRecommendations(AllKeys);
      SetShowRecommendationsModal(true);
    } catch (ErrorValue: any) {
      const Message = ErrorValue?.response?.data?.detail || "Failed to get recommendations. Please ensure your profile is complete.";
      alert(Message);
    } finally {
      SetIsLoadingRecommendations(false);
    }
  };

  const HandleApplyRecommendations = async () => {
    if (!Recommendations) return;
    
    const Updates: Partial<Targets> = {};
    if (SelectedRecommendations.has("DailyCalorieTarget")) Updates.DailyCalorieTarget = Recommendations.DailyCalorieTarget;
    if (SelectedRecommendations.has("ProteinTargetMin")) Updates.ProteinTargetMin = Recommendations.ProteinTargetMin;
    if (SelectedRecommendations.has("ProteinTargetMax")) Updates.ProteinTargetMax = Recommendations.ProteinTargetMax;
    if (SelectedRecommendations.has("FibreTarget") && Recommendations.FibreTarget) Updates.FibreTarget = Recommendations.FibreTarget;
    if (SelectedRecommendations.has("CarbsTarget") && Recommendations.CarbsTarget) Updates.CarbsTarget = Recommendations.CarbsTarget;
    if (SelectedRecommendations.has("FatTarget") && Recommendations.FatTarget) Updates.FatTarget = Recommendations.FatTarget;
    if (SelectedRecommendations.has("SaturatedFatTarget") && Recommendations.SaturatedFatTarget) Updates.SaturatedFatTarget = Recommendations.SaturatedFatTarget;
    if (SelectedRecommendations.has("SugarTarget") && Recommendations.SugarTarget) Updates.SugarTarget = Recommendations.SugarTarget;
    if (SelectedRecommendations.has("SodiumTarget") && Recommendations.SodiumTarget) Updates.SodiumTarget = Recommendations.SodiumTarget;

    SetTargets({ ...Targets, ...Updates });
    SetShowRecommendationsModal(false);
  };

  const ToggleRecommendation = (Key: string) => {
    const NewSelected = new Set(SelectedRecommendations);
    if (NewSelected.has(Key)) {
      NewSelected.delete(Key);
    } else {
      NewSelected.add(Key);
    }
    SetSelectedRecommendations(NewSelected);
  };

  const HasChanges = JSON.stringify(Targets) !== JSON.stringify(OriginalTargets);
  const HasProfileChanges = JSON.stringify(Profile) !== JSON.stringify(OriginalProfile);

  return (
    <section className="space-y-4">
      {HasProfileMissing && (
        <div className="Card bg-yellow-50 border-2 border-yellow-400">
          <div className="flex items-start gap-3">
            <span className="material-icons text-yellow-600">info</span>
            <div>
              <h3 className="font-medium text-Ink">Complete your profile</h3>
              <p className="text-sm text-Ink/70 mt-1">
                Please add your name, birthdate, and height for personalized tracking.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="Card">
        <h2 className="Headline text-2xl">Settings</h2>
        <p className="mt-1 text-sm text-Ink/70">
          Customize your daily nutrition targets and preferences
        </p>
      </div>

      {/* AI Recommendations - Always Visible */}
      <div className="Card">
        <div className="flex items-center gap-3 mb-3">
          <span className="material-icons text-purple-500">psychology</span>
          <div>
            <h3 className="font-medium text-Ink">AI Nutrition Recommendations</h3>
            <p className="text-xs text-Ink/60">Get personalized targets based on your profile</p>
          </div>
        </div>
        <button
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white rounded-lg font-medium transition-all shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={HandleGetRecommendations}
          disabled={IsLoadingRecommendations || !CurrentUser.BirthDate || !CurrentUser.HeightCm || !CurrentUser.WeightKg || !CurrentUser.ActivityLevel}
          type="button"
        >
          <span className="material-icons text-lg">psychology</span>
          {IsLoadingRecommendations ? "Getting recommendations..." : "Get AI Recommendations"}
        </button>
        {(!CurrentUser.BirthDate || !CurrentUser.HeightCm || !CurrentUser.WeightKg || !CurrentUser.ActivityLevel) && (
          <p className="text-xs text-center text-Ink/60 mt-2">Complete your profile to get personalized recommendations</p>
        )}
      </div>

      {/* Profile Section */}
      <div className="Card p-0 overflow-hidden">
        <button
          className="w-full flex items-center justify-between p-4 hover:bg-Ink/5 transition-colors"
          onClick={() => ToggleSection("profile")}
          type="button"
        >
          <div className="flex items-center gap-3">
            <span className="material-icons text-Ink/70">person</span>
            <div className="text-left">
              <h3 className="font-medium text-Ink">Personal Information</h3>
              <p className="text-xs text-Ink/60">Name, birthdate, and height</p>
            </div>
          </div>
          <span className={`material-icons text-Ink/70 transition-transform ${ExpandedSections.has("profile") ? "rotate-180" : ""}`}>
            expand_more
          </span>
        </button>

        {ExpandedSections.has("profile") && (
          <div className="border-t border-Ink/10 p-4 space-y-4 bg-Ink/[0.02]">
            <div className="bg-white rounded-lg p-3 border border-Ink/10">
              <label className="block">
                <span className="text-sm font-medium text-Ink mb-2 block">First Name</span>
                <input
                  className="w-full px-3 py-2 text-sm border border-Ink/20 rounded"
                  type="text"
                  placeholder="Your first name"
                  value={Profile.FirstName}
                  onChange={(E) => SetProfile({ ...Profile, FirstName: E.target.value })}
                />
              </label>
            </div>

            <div className="bg-white rounded-lg p-3 border border-Ink/10">
              <label className="block">
                <span className="text-sm font-medium text-Ink mb-2 block">Last Name</span>
                <input
                  className="w-full px-3 py-2 text-sm border border-Ink/20 rounded"
                  type="text"
                  placeholder="Your last name"
                  value={Profile.LastName}
                  onChange={(E) => SetProfile({ ...Profile, LastName: E.target.value })}
                />
              </label>
            </div>

            <div className="bg-white rounded-lg p-3 border border-Ink/10">
              <label className="block">
                <span className="text-sm font-medium text-Ink mb-2 block">Birthdate</span>
                <input
                  className="w-full px-3 py-2 text-sm border border-Ink/20 rounded"
                  type="date"
                  value={Profile.BirthDate}
                  onChange={(E) => SetProfile({ ...Profile, BirthDate: E.target.value })}
                />
              </label>
            </div>

            <div className="bg-white rounded-lg p-3 border border-Ink/10">
              <label className="block">
                <span className="text-sm font-medium text-Ink mb-2 block">Height</span>
                <div className="flex items-center gap-2">
                  <input
                    className="flex-1 px-3 py-2 text-sm text-right border border-Ink/20 rounded"
                    type="number"
                    step="1"
                    min="50"
                    max="300"
                    placeholder="170"
                    value={Profile.HeightCm}
                    onChange={(E) => SetProfile({ ...Profile, HeightCm: E.target.value })}
                  />
                  <span className="text-sm text-Ink/60">cm</span>
                </div>
              </label>
            </div>

            <div className="bg-white rounded-lg p-3 border border-Ink/10">
              <label className="block">
                <span className="text-sm font-medium text-Ink mb-2 block">Weight</span>
                <div className="flex items-center gap-2">
                  <input
                    className="flex-1 px-3 py-2 text-sm text-right border border-Ink/20 rounded"
                    type="number"
                    step="0.1"
                    min="20"
                    max="500"
                    placeholder="70"
                    value={Profile.WeightKg}
                    onChange={(E) => SetProfile({ ...Profile, WeightKg: E.target.value })}
                  />
                  <span className="text-sm text-Ink/60">kg</span>
                </div>
              </label>
            </div>

            <div className="bg-white rounded-lg p-3 border border-Ink/10">
              <label className="block">
                <span className="text-sm font-medium text-Ink mb-2 block">Activity Level</span>
                <select
                  className="w-full px-3 py-2 text-sm border border-Ink/20 rounded"
                  value={Profile.ActivityLevel}
                  onChange={(E) => SetProfile({ ...Profile, ActivityLevel: E.target.value })}
                >
                  <option value="">Select activity level</option>
                  <option value="sedentary">Sedentary (office work, little exercise)</option>
                  <option value="lightly_active">Lightly Active (light exercise 1-3 days/week)</option>
                  <option value="moderately_active">Moderately Active (moderate exercise 3-5 days/week)</option>
                  <option value="very_active">Very Active (hard exercise 6-7 days/week)</option>
                  <option value="extra_active">Extra Active (physical job + training)</option>
                </select>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Nutrition Targets Section */}
      <div className="Card p-0 overflow-hidden">
        <button
          className="w-full flex items-center justify-between p-4 hover:bg-Ink/5 transition-colors"
          onClick={() => ToggleSection("nutrition")}
          type="button"
        >
          <div className="flex items-center gap-3">
            <span className="material-icons text-Ink/70">restaurant</span>
            <div className="text-left">
              <h3 className="font-medium text-Ink">Nutrition Targets</h3>
              <p className="text-xs text-Ink/60">Daily calorie and nutrient goals</p>
            </div>
          </div>
          <span className={`material-icons text-Ink/70 transition-transform ${ExpandedSections.has("nutrition") ? "rotate-180" : ""}`}>
            expand_more
          </span>
        </button>

        {ExpandedSections.has("nutrition") && (
          <div className="border-t border-Ink/10 p-4 space-y-4 bg-Ink/[0.02]">
            {/* Calories */}
            <div className="bg-white rounded-lg p-3 border border-Ink/10">
              <label className="flex items-center justify-between gap-4">
                <span className="text-sm font-medium text-Ink">Daily Calories</span>
                <div className="flex items-center gap-2 shrink-0">
                  <input
                    className="w-20 px-2 py-1 text-sm text-right border border-Ink/20 rounded"
                    type="number"
                    step="1"
                    value={Targets.DailyCalorieTarget}
                    onChange={(E) => UpdateTarget("DailyCalorieTarget", Number(E.target.value))}
                  />
                  <span className="text-xs text-Ink/60 w-10">kcal</span>
                </div>
              </label>
            </div>

            {/* Nutrients */}
            {Nutrients.map((Nutrient) => {
              const HasTarget = Nutrient.min 
                ? (Targets[Nutrient.min] !== undefined || Targets[Nutrient.max!] !== undefined)
                : Targets[Nutrient.key] !== undefined && Targets[Nutrient.key] !== null;
              
              return (
                <div key={Nutrient.label} className="bg-white rounded-lg p-3 border border-Ink/10">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-Ink">{Nutrient.label}</span>
                    {Nutrient.showKey && (
                      <label className="flex items-center gap-2 cursor-pointer">
                        <span className="text-xs text-Ink/60">Show on Today</span>
                        <input
                          type="checkbox"
                          className="w-4 h-4"
                          checked={Targets[Nutrient.showKey] as boolean ?? false}
                          onChange={(E) => UpdateTarget(Nutrient.showKey!, E.target.checked)}
                        />
                      </label>
                    )}
                  </div>

                  {Nutrient.min && Nutrient.max ? (
                    <div className="flex items-center gap-2 justify-end">
                      <input
                        className="w-16 px-2 py-1 text-sm text-right border border-Ink/20 rounded"
                        type="number"
                        step={Nutrient.step}
                        placeholder="Min"
                        value={Targets[Nutrient.min] ?? ""}
                        onChange={(E) => UpdateTarget(Nutrient.min!, E.target.value ? Number(E.target.value) : undefined as any)}
                      />
                      <span className="text-xs text-Ink/60 font-medium">to</span>
                      <input
                        className="w-16 px-2 py-1 text-sm text-right border border-Ink/20 rounded"
                        type="number"
                        step={Nutrient.step}
                        placeholder="Max"
                        value={Targets[Nutrient.max] ?? ""}
                        onChange={(E) => UpdateTarget(Nutrient.max!, E.target.value ? Number(E.target.value) : undefined as any)}
                      />
                      <span className="text-xs text-Ink/60 w-6">{Nutrient.unit}</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 justify-end">
                      <input
                        className="w-20 px-2 py-1 text-sm text-right border border-Ink/20 rounded"
                        type="number"
                        step={Nutrient.step}
                        placeholder="Target"
                        value={Targets[Nutrient.key] ?? ""}
                        onChange={(E) => UpdateTarget(Nutrient.key, E.target.value ? Number(E.target.value) : undefined as any)}
                      />
                      <span className="text-xs text-Ink/60 w-10">{Nutrient.unit}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Activity Section */}
      <div className="Card p-0 overflow-hidden">
        <button
          className="w-full flex items-center justify-between p-4 hover:bg-Ink/5 transition-colors"
          onClick={() => ToggleSection("activity")}
          type="button"
        >
          <div className="flex items-center gap-3">
            <span className="material-icons text-Ink/70">directions_walk</span>
            <div className="text-left">
              <h3 className="font-medium text-Ink">Activity</h3>
              <p className="text-xs text-Ink/60">Steps and calorie burn rate</p>
            </div>
          </div>
          <span className={`material-icons text-Ink/70 transition-transform ${ExpandedSections.has("activity") ? "rotate-180" : ""}`}>
            expand_more
          </span>
        </button>

        {ExpandedSections.has("activity") && (
          <div className="border-t border-Ink/10 p-4 space-y-4 bg-Ink/[0.02]">
            <div className="bg-white rounded-lg p-3 border border-Ink/10">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-Ink">Step Target</span>
                <label className="flex items-center gap-2 cursor-pointer">
                  <span className="text-xs text-Ink/60">Show on Today</span>
                  <input
                    type="checkbox"
                    className="w-4 h-4"
                    checked={Targets.ShowStepsOnToday ?? true}
                    onChange={(E) => UpdateTarget("ShowStepsOnToday", E.target.checked)}
                  />
                </label>
              </div>
              <div className="flex items-center gap-2 justify-end">
                <input
                  className="w-20 px-2 py-1 text-sm text-right border border-Ink/20 rounded"
                  type="number"
                  step="1"
                  value={Targets.StepTarget}
                  onChange={(E) => UpdateTarget("StepTarget", Number(E.target.value))}
                />
                <span className="text-xs text-Ink/60 w-12">steps</span>
              </div>
            </div>

            <div className="bg-white rounded-lg p-3 border border-Ink/10">
              <label className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-sm font-medium text-Ink">Calorie Burn Factor</div>
                  <div className="text-xs text-Ink/50 mt-0.5">Calories burned per step</div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <input
                    className="w-20 px-2 py-1 text-sm text-right border border-Ink/20 rounded"
                    type="number"
                    step="0.001"
                    value={Targets.StepKcalFactor}
                    onChange={(E) => UpdateTarget("StepKcalFactor", Number(E.target.value))}
                  />
                  <span className="text-xs text-Ink/60 w-12">kcal</span>
                </div>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Admin Invite Section */}
      {CurrentUser.IsAdmin && (
        <div className="Card p-0 overflow-hidden">
          <button
            className="w-full flex items-center justify-between p-4 hover:bg-Ink/5 transition-colors"
            onClick={() => ToggleSection("invite")}
            type="button"
          >
            <div className="flex items-center gap-3">
              <span className="material-icons text-Ink/70">person_add</span>
              <div className="text-left">
                <h3 className="font-medium text-Ink">Invite User</h3>
                <p className="text-xs text-Ink/60">Gmail addresses only</p>
              </div>
            </div>
            <span className={`material-icons text-Ink/70 transition-transform ${ExpandedSections.has("invite") ? "rotate-180" : ""}`}>
              expand_more
            </span>
          </button>

          {ExpandedSections.has("invite") && (
            <div className="border-t border-Ink/10 p-4 space-y-3 bg-Ink/[0.02]">
              <form className="space-y-3" onSubmit={HandleCreateInvite}>
                <input
                  className="InputField"
                  type="email"
                  value={InviteEmail}
                  onChange={(Event) => SetInviteEmail(Event.target.value)}
                  placeholder="name@gmail.com"
                  required
                />
                <button className="PillButton w-full" type="submit" disabled={IsInviteLoading}>
                  {IsInviteLoading ? "Creating invite..." : "Create invite link"}
                </button>
              </form>
              {InviteUrl && (
                <div className="space-y-2">
                  <input className="InputField" value={InviteUrl} readOnly />
                  <button className="OutlineButton w-full" type="button" onClick={HandleCopyInvite}>
                    Copy invite link
                  </button>
                </div>
              )}
              {InviteStatus && <p className="text-sm text-Ink/70">{InviteStatus}</p>}
              {InviteError && <p className="text-sm text-red-500">{InviteError}</p>}
            </div>
          )}
        </div>
      )}

      {/* Account Section */}
      <div className="Card p-0 overflow-hidden">
        <button
          className="w-full flex items-center justify-between p-4 hover:bg-Ink/5 transition-colors"
          onClick={() => ToggleSection("account")}
          type="button"
        >
          <div className="flex items-center gap-3">
            <span className="material-icons text-Ink/70">account_circle</span>
            <div className="text-left">
              <h3 className="font-medium text-Ink">Account</h3>
              <p className="text-xs text-Ink/60">{CurrentUser.Email}</p>
            </div>
          </div>
          <span className={`material-icons text-Ink/70 transition-transform ${ExpandedSections.has("account") ? "rotate-180" : ""}`}>
            expand_more
          </span>
        </button>

        {ExpandedSections.has("account") && (
          <div className="border-t border-Ink/10 p-4 bg-Ink/[0.02]">
            <button className="OutlineButton w-full" onClick={HandleLogout}>
              Sign out
            </button>
          </div>
        )}
      </div>

      {/* Save Button - Sticky bar that works on mobile and desktop */}
      {(HasChanges || HasProfileChanges) && (
        <div className="sticky bottom-0 left-0 right-0 mt-4 pb-4">
          <div className="Card bg-white/95 backdrop-blur-sm border-2 border-blue-600">
            {HasProfileChanges && (
              <button 
                className="PillButton w-full bg-blue-600 hover:bg-blue-700 mb-2" 
                type="button" 
                onClick={HandleSaveProfile}
                disabled={IsSavingProfile}
              >
                {IsSavingProfile ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="material-icons animate-spin">refresh</span>
                    Saving profile...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <span className="material-icons">save</span>
                    Save profile
                  </span>
                )}
              </button>
            )}
            {HasChanges && (
              <button 
                className="PillButton w-full bg-blue-600 hover:bg-blue-700" 
                type="button" 
                onClick={HandleSaveSettings}
                disabled={IsSavingSettings}
              >
                {IsSavingSettings ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="material-icons animate-spin">refresh</span>
                    Saving settings...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <span className="material-icons">save</span>
                    Save settings
                  </span>
                )}
              </button>
            )}
            {ProfileStatus && <p className="text-sm text-green-600 mt-2 text-center">{ProfileStatus}</p>}
            {ProfileError && <p className="text-sm text-red-500 mt-2 text-center">{ProfileError}</p>}
            {SettingsStatus && <p className="text-sm text-green-600 mt-2 text-center">{SettingsStatus}</p>}
            {SettingsError && <p className="text-sm text-red-500 mt-2 text-center">{SettingsError}</p>}
          </div>
        </div>
      )}

      {/* AI Recommendations Modal */}
      {ShowRecommendationsModal && Recommendations && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => SetShowRecommendationsModal(false)}>
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl" onClick={(E) => E.stopPropagation()}>
            <div className="sticky top-0 bg-white border-b border-Ink/10 p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold text-Ink flex items-center gap-2">
                  <span className="material-icons text-purple-500">psychology</span>
                  AI Nutrition Recommendations
                </h3>
                <button
                  className="material-icons text-Ink/70 hover:text-Ink"
                  onClick={() => SetShowRecommendationsModal(false)}
                  type="button"
                >
                  close
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Explanation */}
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-100">
                <p className="text-sm text-Ink/80 leading-relaxed">{Recommendations.Explanation}</p>
                {Recommendations.ModelUsed && (
                  <p className="mt-2 text-xs text-Ink/60">Model used: {Recommendations.ModelUsed}</p>
                )}
              </div>

              {/* Recommendations Grid */}
              <div className="space-y-3">
                <p className="text-sm font-medium text-Ink/70">Select targets to apply:</p>

                {/* Daily Calories */}
                <label className="flex items-center justify-between p-4 bg-white rounded-lg border-2 border-Ink/10 hover:border-purple-200 cursor-pointer transition-colors">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={SelectedRecommendations.has("DailyCalorieTarget")}
                      onChange={() => ToggleRecommendation("DailyCalorieTarget")}
                      className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                    />
                    <div>
                      <div className="font-medium text-Ink">Daily Calories</div>
                      <div className="text-xs text-Ink/60">Current: {Targets.DailyCalorieTarget} kcal</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-purple-600">{Recommendations.DailyCalorieTarget} kcal</div>
                  </div>
                </label>

                {/* Protein Min */}
                <label className="flex items-center justify-between p-4 bg-white rounded-lg border-2 border-Ink/10 hover:border-purple-200 cursor-pointer transition-colors">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={SelectedRecommendations.has("ProteinTargetMin")}
                      onChange={() => ToggleRecommendation("ProteinTargetMin")}
                      className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                    />
                    <div>
                      <div className="font-medium text-Ink">Protein Min</div>
                      <div className="text-xs text-Ink/60">Current: {Targets.ProteinTargetMin}g</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-purple-600">{Recommendations.ProteinTargetMin}g</div>
                  </div>
                </label>

                {/* Protein Max */}
                <label className="flex items-center justify-between p-4 bg-white rounded-lg border-2 border-Ink/10 hover:border-purple-200 cursor-pointer transition-colors">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={SelectedRecommendations.has("ProteinTargetMax")}
                      onChange={() => ToggleRecommendation("ProteinTargetMax")}
                      className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                    />
                    <div>
                      <div className="font-medium text-Ink">Protein Max</div>
                      <div className="text-xs text-Ink/60">Current: {Targets.ProteinTargetMax}g</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-purple-600">{Recommendations.ProteinTargetMax}g</div>
                  </div>
                </label>

                {/* Fibre */}
                {Recommendations.FibreTarget && (
                  <label className="flex items-center justify-between p-4 bg-white rounded-lg border-2 border-Ink/10 hover:border-purple-200 cursor-pointer transition-colors">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={SelectedRecommendations.has("FibreTarget")}
                        onChange={() => ToggleRecommendation("FibreTarget")}
                        className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                      />
                      <div>
                        <div className="font-medium text-Ink">Fibre</div>
                        <div className="text-xs text-Ink/60">Current: {Targets.FibreTarget || "Not set"}g</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-purple-600">{Recommendations.FibreTarget}g</div>
                    </div>
                  </label>
                )}

                {/* Carbs */}
                {Recommendations.CarbsTarget && (
                  <label className="flex items-center justify-between p-4 bg-white rounded-lg border-2 border-Ink/10 hover:border-purple-200 cursor-pointer transition-colors">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={SelectedRecommendations.has("CarbsTarget")}
                        onChange={() => ToggleRecommendation("CarbsTarget")}
                        className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                      />
                      <div>
                        <div className="font-medium text-Ink">Carbs</div>
                        <div className="text-xs text-Ink/60">Current: {Targets.CarbsTarget || "Not set"}g</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-purple-600">{Recommendations.CarbsTarget}g</div>
                    </div>
                  </label>
                )}

                {/* Fat */}
                {Recommendations.FatTarget && (
                  <label className="flex items-center justify-between p-4 bg-white rounded-lg border-2 border-Ink/10 hover:border-purple-200 cursor-pointer transition-colors">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={SelectedRecommendations.has("FatTarget")}
                        onChange={() => ToggleRecommendation("FatTarget")}
                        className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                      />
                      <div>
                        <div className="font-medium text-Ink">Fat</div>
                        <div className="text-xs text-Ink/60">Current: {Targets.FatTarget || "Not set"}g</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-purple-600">{Recommendations.FatTarget}g</div>
                    </div>
                  </label>
                )}

                {/* Saturated Fat */}
                {Recommendations.SaturatedFatTarget && (
                  <label className="flex items-center justify-between p-4 bg-white rounded-lg border-2 border-Ink/10 hover:border-purple-200 cursor-pointer transition-colors">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={SelectedRecommendations.has("SaturatedFatTarget")}
                        onChange={() => ToggleRecommendation("SaturatedFatTarget")}
                        className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                      />
                      <div>
                        <div className="font-medium text-Ink">Saturated Fat</div>
                        <div className="text-xs text-Ink/60">Current: {Targets.SaturatedFatTarget || "Not set"}g</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-purple-600">{Recommendations.SaturatedFatTarget}g</div>
                    </div>
                  </label>
                )}

                {/* Sugar */}
                {Recommendations.SugarTarget && (
                  <label className="flex items-center justify-between p-4 bg-white rounded-lg border-2 border-Ink/10 hover:border-purple-200 cursor-pointer transition-colors">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={SelectedRecommendations.has("SugarTarget")}
                        onChange={() => ToggleRecommendation("SugarTarget")}
                        className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                      />
                      <div>
                        <div className="font-medium text-Ink">Sugar</div>
                        <div className="text-xs text-Ink/60">Current: {Targets.SugarTarget || "Not set"}g</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-purple-600">{Recommendations.SugarTarget}g</div>
                    </div>
                  </label>
                )}

                {/* Sodium */}
                {Recommendations.SodiumTarget && (
                  <label className="flex items-center justify-between p-4 bg-white rounded-lg border-2 border-Ink/10 hover:border-purple-200 cursor-pointer transition-colors">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={SelectedRecommendations.has("SodiumTarget")}
                        onChange={() => ToggleRecommendation("SodiumTarget")}
                        className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                      />
                      <div>
                        <div className="font-medium text-Ink">Sodium</div>
                        <div className="text-xs text-Ink/60">Current: {Targets.SodiumTarget || "Not set"}mg</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-purple-600">{Recommendations.SodiumTarget}mg</div>
                    </div>
                  </label>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4 border-t border-Ink/10">
                <button
                  className="flex-1 px-4 py-3 border-2 border-Ink/10 text-Ink rounded-lg font-medium hover:bg-Ink/5 transition-colors"
                  onClick={() => SetShowRecommendationsModal(false)}
                  type="button"
                >
                  Cancel
                </button>
                <button
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white rounded-lg font-medium transition-all shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                  onClick={HandleApplyRecommendations}
                  disabled={SelectedRecommendations.size === 0}
                  type="button"
                >
                  Apply Selected ({SelectedRecommendations.size})
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
