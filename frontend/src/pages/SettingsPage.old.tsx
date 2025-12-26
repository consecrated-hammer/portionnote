import { FormEvent, useEffect, useState } from "react";
import {
  CreateInvite,
  GetUserSettings,
  LogoutUser,
  UpdateUserSettings
} from "../services/ApiClient";
import { Targets, User } from "../models/Models";

const DefaultTargets: Targets = {
  DailyCalorieTarget: 1498,
  ProteinTargetMin: 70,
  ProteinTargetMax: 188,
  StepKcalFactor: 0.04,
  StepTarget: 8500
};

type SettingsPageProps = {
  onLogout: () => void;
  CurrentUser: User;
};

export const SettingsPage = ({ onLogout, CurrentUser }: SettingsPageProps) => {
  const [Targets, SetTargets] = useState<Targets>(DefaultTargets);
  const [IsSavingSettings, SetIsSavingSettings] = useState(false);
  const [SettingsStatus, SetSettingsStatus] = useState<string | null>(null);
  const [SettingsError, SetSettingsError] = useState<string | null>(null);
  const [InviteEmail, SetInviteEmail] = useState("");
  const [InviteUrl, SetInviteUrl] = useState<string | null>(null);
  const [InviteStatus, SetInviteStatus] = useState<string | null>(null);
  const [InviteError, SetInviteError] = useState<string | null>(null);
  const [IsInviteLoading, SetIsInviteLoading] = useState(false);

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
      SetTargets(Settings.Targets ?? DefaultTargets);
    } catch (ErrorValue) {
      SetSettingsError("Failed to load settings.");
    }
  };

  useEffect(() => {
    void LoadSettings();
  }, []);

  const HandleSaveSettings = async (Event: FormEvent) => {
    Event.preventDefault();
    SetSettingsError(null);
    SetSettingsStatus(null);
    SetIsSavingSettings(true);

    try {
      const Updated = await UpdateUserSettings(Targets);
      SetTargets(Updated.Targets ?? Targets);
      SetSettingsStatus("Settings saved.");
    } catch (ErrorValue) {
      SetSettingsError("Failed to save settings.");
    } finally {
      SetIsSavingSettings(false);
    }
  };

  return (
    <section className="space-y-6">
      <div className="Card space-y-3">
        <h2 className="Headline text-2xl">Settings</h2>
        <p className="text-sm text-Ink/70">
          Set your daily nutrition targets.
        </p>
      </div>

      <div className="Card space-y-4">
        <form className="space-y-3" onSubmit={HandleSaveSettings}>
          <label className="space-y-2 text-sm">
            <span className="text-Ink/70">Daily calorie target</span>
            <input
              className="InputField"
              type="number"
              step="1"
              value={Targets.DailyCalorieTarget}
              onChange={(Event) =>
                SetTargets({ ...Targets, DailyCalorieTarget: Number(Event.target.value) })
              }
            />
          </label>
          <label className="space-y-2 text-sm">
            <span className="text-Ink/70">Protein target min</span>
            <input
              className="InputField"
              type="number"
              step="0.1"
              value={Targets.ProteinTargetMin}
              onChange={(Event) =>
                SetTargets({ ...Targets, ProteinTargetMin: Number(Event.target.value) })
              }
            />
          </label>
          <label className="space-y-2 text-sm">
            <span className="text-Ink/70">Protein target max</span>
            <input
              className="InputField"
              type="number"
              step="0.1"
              value={Targets.ProteinTargetMax}
              onChange={(Event) =>
                SetTargets({ ...Targets, ProteinTargetMax: Number(Event.target.value) })
              }
            />
          </label>
          <label className="space-y-2 text-sm">
            <span className="text-Ink/70">Step target</span>
            <input
              className="InputField"
              type="number"
              step="1"
              value={Targets.StepTarget}
              onChange={(Event) =>
                SetTargets({ ...Targets, StepTarget: Number(Event.target.value) })
              }
            />
          </label>
          <label className="space-y-2 text-sm">
            <span className="text-Ink/70">Step kcal factor</span>
            <input
              className="InputField"
              type="number"
              step="0.01"
              value={Targets.StepKcalFactor}
              onChange={(Event) =>
                SetTargets({ ...Targets, StepKcalFactor: Number(Event.target.value) })
              }
            />
          </label>
          <button className="PillButton" type="submit" disabled={IsSavingSettings}>
            {IsSavingSettings ? "Saving" : "Save changes"}
          </button>
        </form>
        {SettingsStatus && <p className="text-sm text-Ink/70">{SettingsStatus}</p>}
        {SettingsError && <p className="text-sm text-red-500">{SettingsError}</p>}
      </div>

      {CurrentUser.IsAdmin && (
        <div className="Card space-y-4">
          <div>
            <h3 className="Headline text-xl">Invite user</h3>
            <p className="text-sm text-Ink/70">
              Invite links require a Gmail address and Google sign in.
            </p>
          </div>
          <form className="space-y-3" onSubmit={HandleCreateInvite}>
            <label className="space-y-2 text-sm">
              <span className="text-Ink/70">Gmail address</span>
              <input
                className="InputField"
                type="email"
                value={InviteEmail}
                onChange={(Event) => SetInviteEmail(Event.target.value)}
                placeholder="name@gmail.com"
                required
              />
            </label>
            <button className="PillButton" type="submit" disabled={IsInviteLoading}>
              {IsInviteLoading ? "Creating invite" : "Create invite link"}
            </button>
          </form>
          {InviteUrl && (
            <div className="space-y-2">
              <label className="space-y-2 text-sm">
                <span className="text-Ink/70">Invite link</span>
                <input className="InputField" value={InviteUrl} readOnly />
              </label>
              <button className="OutlineButton" type="button" onClick={HandleCopyInvite}>
                Copy invite link
              </button>
            </div>
          )}
          {InviteStatus && (
            <p className="text-sm text-Ink/70">{InviteStatus}</p>
          )}
          {InviteError && (
            <p className="text-sm text-red-500">{InviteError}</p>
          )}
        </div>
      )}

      <div className="Card space-y-3">
        <h3 className="Headline text-xl">Account</h3>
        <button className="OutlineButton" onClick={HandleLogout}>
          Sign out
        </button>
      </div>
    </section>
  );
};
