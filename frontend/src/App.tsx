import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { AboutPage } from "./pages/AboutPage";
import { AuthPage } from "./pages/AuthPage";
import { FoodsPage } from "./pages/FoodsPage";
import { HistoryPage } from "./pages/HistoryPage";
import { LogPage } from "./pages/LogPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TodayPage } from "./pages/TodayPage";
import { UserManagementPage } from "./pages/UserManagementPage";
import { AuthProvider, UseAuth } from "./contexts/AuthContext";
import { AppLogger, InitializeFrontendLogging } from "./utils/Logger";

const AppRoutes = () => {
  const { CurrentUser, IsLoading, SetCurrentUser, Logout } = UseAuth();
  const CurrentLocation = useLocation();

  useEffect(() => {
    AppLogger.info("Route change", {
      Path: CurrentLocation.pathname,
      Search: CurrentLocation.search
    });
  }, [CurrentLocation.pathname, CurrentLocation.search]);

  useEffect(() => {
    // Listen for global logout events (from 401 interceptor)
    const HandleLogout = () => {
      Logout();
    };

    window.addEventListener("auth:logout", HandleLogout);

    return () => {
      window.removeEventListener("auth:logout", HandleLogout);
    };
  }, [Logout]);

  if (IsLoading) {
    return (
      <div className="AppFrame">
        <div className="Card">Checking your session...</div>
      </div>
    );
  }

  if (!CurrentUser) {
    return <AuthPage onAuthSuccess={SetCurrentUser} />;
  }

  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/today" replace />} />
        <Route path="/today" element={<TodayPage />} />
        <Route path="/log" element={<LogPage />} />
        <Route path="/foods" element={<FoodsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route
          path="/settings"
          element={<SettingsPage onLogout={Logout} CurrentUser={CurrentUser} />}
        />
        <Route path="/settings/users" element={<UserManagementPage />} />
        <Route path="/auth" element={<Navigate to="/today" replace />} />
      </Routes>
    </AppShell>
  );
};

const App = () => {
  useEffect(() => {
    InitializeFrontendLogging();
    return () => {
      AppLogger.destroy();
    };
  }, []);

  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
};

export default App;
