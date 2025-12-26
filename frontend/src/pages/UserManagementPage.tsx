import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { CreateAdminUser, GetAdminUsers, UpdateAdminUser } from "../services/ApiClient";
import { AdminUser } from "../models/Models";
import { UseAuth } from "../contexts/AuthContext";

type CreateUserForm = {
  Email: string;
  Password: string;
  FirstName: string;
  LastName: string;
  IsAdmin: boolean;
};

const EmptyForm: CreateUserForm = {
  Email: "",
  Password: "",
  FirstName: "",
  LastName: "",
  IsAdmin: false
};

export const UserManagementPage = () => {
  const { CurrentUser } = UseAuth();
  const [Users, SetUsers] = useState<AdminUser[]>([]);
  const [IsLoading, SetIsLoading] = useState(false);
  const [ErrorMessage, SetErrorMessage] = useState<string | null>(null);
  const [StatusMessage, SetStatusMessage] = useState<string | null>(null);
  const [CreateForm, SetCreateForm] = useState<CreateUserForm>(EmptyForm);
  const [IsCreating, SetIsCreating] = useState(false);

  const SortedUsers = useMemo(() => {
    return [...Users].sort((A, B) => {
      const DateA = A.CreatedAt ? new Date(A.CreatedAt).getTime() : 0;
      const DateB = B.CreatedAt ? new Date(B.CreatedAt).getTime() : 0;
      return DateB - DateA;
    });
  }, [Users]);

  const LoadUsers = async () => {
    SetIsLoading(true);
    SetErrorMessage(null);
    try {
      const Data = await GetAdminUsers();
      SetUsers(Data);
    } catch (ErrorValue) {
      SetErrorMessage("Failed to load users.");
    } finally {
      SetIsLoading(false);
    }
  };

  useEffect(() => {
    if (!CurrentUser?.IsAdmin) {
      return;
    }
    void LoadUsers();
  }, [CurrentUser?.IsAdmin]);

  const HandleCreateUser = async (Event: FormEvent) => {
    Event.preventDefault();
    SetErrorMessage(null);
    SetStatusMessage(null);
    SetIsCreating(true);

    try {
      const Created = await CreateAdminUser({
        Email: CreateForm.Email,
        Password: CreateForm.Password,
        FirstName: CreateForm.FirstName,
        LastName: CreateForm.LastName || undefined,
        IsAdmin: CreateForm.IsAdmin
      });
      SetUsers((Previous) => [Created, ...Previous]);
      SetCreateForm(EmptyForm);
      SetStatusMessage("User created.");
    } catch (ErrorValue: any) {
      const Message = ErrorValue?.response?.data?.detail || "Failed to create user.";
      SetErrorMessage(Message);
    } finally {
      SetIsCreating(false);
    }
  };

  const HandleToggleAdmin = async (UserItem: AdminUser) => {
    SetErrorMessage(null);
    SetStatusMessage(null);

    try {
      const Updated = await UpdateAdminUser(UserItem.UserId, !UserItem.IsAdmin);
      SetUsers((Previous) => Previous.map((Existing) => (Existing.UserId === Updated.UserId ? Updated : Existing)));
      SetStatusMessage("User updated.");
    } catch (ErrorValue: any) {
      const Message = ErrorValue?.response?.data?.detail || "Failed to update user.";
      SetErrorMessage(Message);
    }
  };

  if (!CurrentUser?.IsAdmin) {
    return (
      <section className="space-y-4">
        <div className="Card">
          <h2 className="Headline text-2xl">User Management</h2>
          <p className="text-sm text-Ink/70 mt-1">Admin access required.</p>
          <Link className="OutlineButton mt-3 inline-flex" to="/settings">
            Back to settings
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <div className="Card flex items-start justify-between gap-3">
        <div>
          <h2 className="Headline text-2xl">User Management</h2>
          <p className="text-sm text-Ink/70 mt-1">Create local users and manage admin access.</p>
        </div>
        <Link className="OutlineButton" to="/settings">
          Back to settings
        </Link>
      </div>

      <div className="Card">
        <h3 className="font-medium text-Ink mb-3">Create local user</h3>
        <form className="space-y-3" onSubmit={HandleCreateUser}>
          <div className="grid gap-3 md:grid-cols-2">
            <input
              className="InputField"
              type="text"
              placeholder="First name"
              value={CreateForm.FirstName}
              onChange={(Event) => SetCreateForm({ ...CreateForm, FirstName: Event.target.value })}
              required
            />
            <input
              className="InputField"
              type="text"
              placeholder="Last name"
              value={CreateForm.LastName}
              onChange={(Event) => SetCreateForm({ ...CreateForm, LastName: Event.target.value })}
            />
          </div>
          <input
            className="InputField"
            type="email"
            placeholder="Email"
            value={CreateForm.Email}
            onChange={(Event) => SetCreateForm({ ...CreateForm, Email: Event.target.value })}
            required
          />
          <input
            className="InputField"
            type="password"
            placeholder="Password (min 8 characters)"
            value={CreateForm.Password}
            onChange={(Event) => SetCreateForm({ ...CreateForm, Password: Event.target.value })}
            required
            minLength={8}
          />
          <label className="flex items-center gap-2 text-sm text-Ink/70">
            <input
              type="checkbox"
              className="w-4 h-4"
              checked={CreateForm.IsAdmin}
              onChange={(Event) => SetCreateForm({ ...CreateForm, IsAdmin: Event.target.checked })}
            />
            Grant admin access
          </label>
          <button className="PillButton w-full" type="submit" disabled={IsCreating}>
            {IsCreating ? "Creating user..." : "Create user"}
          </button>
        </form>
        {StatusMessage && <p className="text-sm text-green-600 mt-2">{StatusMessage}</p>}
        {ErrorMessage && <p className="text-sm text-red-500 mt-2">{ErrorMessage}</p>}
      </div>

      <div className="Card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-medium text-Ink">Users</h3>
          <button className="OutlineButton" type="button" onClick={LoadUsers} disabled={IsLoading}>
            {IsLoading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
        {IsLoading && Users.length === 0 ? (
          <p className="text-sm text-Ink/60">Loading users...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-Ink/10 text-left text-Ink/60">
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Email</th>
                  <th className="py-2 pr-4">Auth</th>
                  <th className="py-2 pr-4">Admin</th>
                  <th className="py-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {SortedUsers.map((UserItem) => (
                  <tr key={UserItem.UserId} className="border-b border-Ink/5">
                    <td className="py-2 pr-4 text-Ink">
                      {[UserItem.FirstName, UserItem.LastName].filter(Boolean).join(" ") || "Unnamed"}
                    </td>
                    <td className="py-2 pr-4 text-Ink/80">{UserItem.Email}</td>
                    <td className="py-2 pr-4 text-Ink/70">{UserItem.AuthProvider}</td>
                    <td className="py-2 pr-4">
                      <button
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          UserItem.IsAdmin ? "bg-green-100 text-green-700" : "bg-Ink/5 text-Ink/70"
                        }`}
                        type="button"
                        onClick={() => HandleToggleAdmin(UserItem)}
                      >
                        {UserItem.IsAdmin ? "Admin" : "Standard"}
                      </button>
                    </td>
                    <td className="py-2 text-Ink/60">
                      {UserItem.CreatedAt ? new Date(UserItem.CreatedAt).toLocaleDateString() : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {SortedUsers.length === 0 && (
              <p className="text-sm text-Ink/60 py-3">No users found.</p>
            )}
          </div>
        )}
      </div>
    </section>
  );
};
