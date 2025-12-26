import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { User } from "../models/Models";
import { GetCurrentUser } from "../services/ApiClient";

interface AuthContextType {
  CurrentUser: User | null;
  IsLoading: boolean;
  SetCurrentUser: (User: User | null) => void;
  Logout: () => void;
  CheckAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const UseAuth = () => {
  const Context = useContext(AuthContext);
  if (!Context) {
    throw new Error("UseAuth must be used within AuthProvider");
  }
  return Context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [CurrentUser, SetCurrentUser] = useState<User | null>(null);
  const [IsLoading, SetIsLoading] = useState(true);

  const CheckAuth = useCallback(async () => {
    try {
      const UserItem = await GetCurrentUser();
      SetCurrentUser(UserItem);
    } catch (ErrorValue) {
      SetCurrentUser(null);
    } finally {
      SetIsLoading(false);
    }
  }, []);

  const Logout = useCallback(() => {
    SetCurrentUser(null);
  }, []);

  useEffect(() => {
    let IsMounted = true;

    const LoadUser = async () => {
      try {
        const UserItem = await GetCurrentUser();
        if (IsMounted) {
          SetCurrentUser(UserItem);
        }
      } catch (ErrorValue) {
        if (IsMounted) {
          SetCurrentUser(null);
        }
      } finally {
        if (IsMounted) {
          SetIsLoading(false);
        }
      }
    };

    void LoadUser();

    return () => {
      IsMounted = false;
    };
  }, []);

  return (
    <AuthContext.Provider value={{ CurrentUser, IsLoading, SetCurrentUser, Logout, CheckAuth }}>
      {children}
    </AuthContext.Provider>
  );
};
