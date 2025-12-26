import { FormEvent, useEffect, useState } from "react";
import { CompleteGoogleInvite, GetGooglePendingInvite, LoginUser, RegisterUser, StartGoogleLogin } from "../services/ApiClient";
import { User } from "../models/Models";

type AuthPageProps = {
  onAuthSuccess: (UserItem: User) => void;
};

export const AuthPage = ({ onAuthSuccess }: AuthPageProps) => {
  const [Mode, SetMode] = useState<"login" | "register">("login");
  const [Email, SetEmail] = useState("");
  const [Password, SetPassword] = useState("");
  const [FirstName, SetFirstName] = useState("");
  const [LastName, SetLastName] = useState("");
  const [InviteCode, SetInviteCode] = useState("");
  const [PendingInvite, SetPendingInvite] = useState(false);
  const [PendingEmail, SetPendingEmail] = useState<string | null>(null);
  const [ErrorMessage, SetErrorMessage] = useState<string | null>(null);
  const [PendingError, SetPendingError] = useState<string | null>(null);
  const [IsChecking, SetIsChecking] = useState(true);
  const [IsCompleting, SetIsCompleting] = useState(false);
  const [IsSubmitting, SetIsSubmitting] = useState(false);

  useEffect(() => {
    let IsMounted = true;
    const Params = new URLSearchParams(window.location.search);
    if (Params.get("error")) {
      SetErrorMessage("Sign in failed. Contact your admin for access.");
    }

    const LoadPending = async () => {
      try {
        const Result = await GetGooglePendingInvite();
        if (!IsMounted) {
          return;
        }
        SetPendingInvite(Result.HasPending);
        SetPendingEmail(Result.Email ?? null);
        SetPendingError(Result.Error ?? null);
      } catch (ErrorValue) {
        if (IsMounted) {
          SetPendingInvite(false);
        }
      } finally {
        if (IsMounted) {
          SetIsChecking(false);
        }
      }
    };

    void LoadPending();
    return () => {
      IsMounted = false;
    };
  }, []);

  const HandleCompleteInvite = async (Event: FormEvent) => {
    Event.preventDefault();
    SetErrorMessage(null);
    SetPendingError(null);
    SetIsCompleting(true);

    try {
      const UserItem = await CompleteGoogleInvite(InviteCode.trim());
      onAuthSuccess(UserItem);
    } catch (ErrorValue) {
      SetErrorMessage("Invite code rejected. Ask your admin for a new link.");
    } finally {
      SetIsCompleting(false);
    }
  };

  const HandleLocalAuth = async (Event: FormEvent) => {
    Event.preventDefault();
    SetErrorMessage(null);
    SetIsSubmitting(true);

    try {
      if (Mode === "login") {
        const UserItem = await LoginUser({ Email, Password });
        onAuthSuccess(UserItem);
      } else {
        const UserItem = await RegisterUser({
          Email,
          Password,
          FirstName,
          LastName: LastName || null,
          InviteCode: InviteCode || null
        });
        onAuthSuccess(UserItem);
      }
    } catch (ErrorValue) {
      SetErrorMessage(Mode === "login" ? "Login failed. Check your credentials." : "Registration failed. Check your details.");
    } finally {
      SetIsSubmitting(false);
    }
  };

  return (
    <div className="AppFrame">
      <section className="Card space-y-3">
        <h1 className="Headline text-3xl">Portion Note</h1>
        <p className="text-sm text-Ink/70">
          Track your daily nutrition progress against your targets.
        </p>
      </section>

      <section className="Card mt-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="Headline text-xl">{Mode === "login" ? "Sign in" : "Create account"}</h2>
          <button
            className="text-sm text-Ink/70 hover:text-Ink"
            type="button"
            onClick={() => {
              SetMode(Mode === "login" ? "register" : "login");
              SetErrorMessage(null);
            }}
          >
            {Mode === "login" ? "Need an account?" : "Have an account?"}
          </button>
        </div>

        <form className="space-y-3" onSubmit={HandleLocalAuth} method="post" autoComplete="on">
          {Mode === "register" && (
            <label htmlFor="first-name" className="space-y-2 text-sm">
              <span className="text-Ink/70">First name</span>
              <input
                id="first-name"
                name="given-name"
                className="InputField"
                type="text"
                autoComplete="given-name"
                value={FirstName}
                onChange={(Event) => SetFirstName(Event.target.value)}
                required
              />
            </label>
          )}
          {Mode === "register" && (
            <label htmlFor="last-name" className="space-y-2 text-sm">
              <span className="text-Ink/70">Last name (optional)</span>
              <input
                id="last-name"
                name="family-name"
                className="InputField"
                type="text"
                autoComplete="family-name"
                value={LastName}
                onChange={(Event) => SetLastName(Event.target.value)}
              />
            </label>
          )}
          <label htmlFor="email" className="space-y-2 text-sm">
            <span className="text-Ink/70">Email</span>
            <input
              id="email"
              name="email"
              className="InputField"
              type="email"
              autoComplete={Mode === "login" ? "username" : "email"}
              inputMode="email"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              value={Email}
              onChange={(Event) => SetEmail(Event.target.value)}
              required
            />
          </label>
          <label htmlFor="password" className="space-y-2 text-sm">
            <span className="text-Ink/70">Password</span>
            <input
              id="password"
              name="password"
              className="InputField"
              type="password"
              autoComplete={Mode === "login" ? "current-password" : "new-password"}
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              value={Password}
              onChange={(Event) => SetPassword(Event.target.value)}
              required
              minLength={8}
            />
          </label>
          {Mode === "register" && (
            <label htmlFor="invite-code" className="space-y-2 text-sm">
              <span className="text-Ink/70">Invite code (optional)</span>
              <input
                id="invite-code"
                name="invite-code"
                className="InputField"
                type="text"
                autoComplete="off"
                value={InviteCode}
                onChange={(Event) => SetInviteCode(Event.target.value)}
                data-1p-ignore
              />
            </label>
          )}
          <button className="PillButton" type="submit" disabled={IsSubmitting}>
            {IsSubmitting ? (Mode === "login" ? "Signing in..." : "Creating account...") : (Mode === "login" ? "Sign in" : "Create account")}
          </button>
        </form>
      </section>

      <section className="Card mt-6 space-y-4">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-Ink/20"></div>
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white px-2 text-Ink/60">Or</span>
          </div>
        </div>
        <button
          className="OutlineButton w-full"
          type="button"
          onClick={() => StartGoogleLogin()}
          disabled={IsChecking}
        >
          {IsChecking ? "Checking session..." : "Continue with Google"}
        </button>
        <p className="text-xs text-Ink/60 text-center">
          Google sign-in may require an invite from an admin.
        </p>
      </section>

      {PendingInvite && (
        <section className="Card mt-6 space-y-4">
          <div>
            <h2 className="Headline text-xl">Enter invite code</h2>
            {PendingEmail && (
              <p className="text-sm text-Ink/70">
                Invite needed for {PendingEmail}.
              </p>
            )}
          </div>
          <form className="space-y-3" onSubmit={HandleCompleteInvite} method="post">
            <label htmlFor="google-invite-code" className="space-y-2 text-sm">
              <span className="text-Ink/70">Invite code</span>
              <input
                id="google-invite-code"
                name="invite-code"
                className="InputField"
                type="text"
                autoComplete="off"
                value={InviteCode}
                onChange={(Event) => SetInviteCode(Event.target.value)}
                required
                data-1p-ignore
              />
            </label>
            <button className="PillButton" type="submit" disabled={IsCompleting}>
              {IsCompleting ? "Finishing signup..." : "Finish signup"}
            </button>
          </form>
          {PendingError && (
            <p className="text-sm text-red-500">{PendingError}</p>
          )}
        </section>
      )}

      {ErrorMessage && (
        <div className="Card mt-6 text-sm text-red-500">
          {ErrorMessage}
        </div>
      )}
    </div>
  );
};
