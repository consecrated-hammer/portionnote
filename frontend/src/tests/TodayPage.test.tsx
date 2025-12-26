import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { TodayPage } from "../pages/TodayPage";
import { AuthProvider } from "../contexts/AuthContext";
import { GetCurrentUser, GetDailyLog, GetScheduleSlots, GetUserSettings } from "../services/ApiClient";

vi.mock("../services/ApiClient", () => ({
  GetCurrentUser: vi.fn(),
  GetDailyLog: vi.fn(),
  GetScheduleSlots: vi.fn(),
  GetUserSettings: vi.fn(),
  UpdateScheduleSlots: vi.fn(),
  UpdateUserSettings: vi.fn(),
  UpdateDailySteps: vi.fn(),
  CreateDailyLog: vi.fn()
}));

it("shows today snapshot and quick add", async () => {
  vi.mocked(GetCurrentUser).mockResolvedValue({
    UserId: "User-1",
    Email: "user@example.com",
    FirstName: "Test",
    LastName: "User",
    IsAdmin: false
  });
  vi.mocked(GetUserSettings).mockResolvedValue({
    Targets: {
      DailyCalorieTarget: 1498,
      ProteinTargetMin: 70,
      ProteinTargetMax: 188,
      StepKcalFactor: 0.04,
      StepTarget: 8500,
      BarOrder: ["Calories", "Protein"]
    },
    TodayLayout: ["snapshot", "quickadd"]
  });
  vi.mocked(GetScheduleSlots).mockResolvedValue([]);
  vi.mocked(GetDailyLog).mockResolvedValue({
    DailyLog: null,
    Entries: [],
    Totals: {
      TotalCalories: 0,
      TotalProtein: 0,
      TotalFibre: 0,
      TotalCarbs: 0,
      TotalFat: 0,
      TotalSaturatedFat: 0,
      TotalSugar: 0,
      TotalSodium: 0,
      CaloriesBurnedFromSteps: 0,
      NetCalories: 0,
      RemainingCalories: 1498,
      RemainingProteinMin: 70,
      RemainingProteinMax: 188,
      RemainingFibre: 0,
      RemainingCarbs: 0,
      RemainingFat: 0,
      RemainingSaturatedFat: 0,
      RemainingSugar: 0,
      RemainingSodium: 0
    },
    Summary: {
      LogDate: "2025-12-24",
      TotalCalories: 0,
      TotalProtein: 0,
      Steps: 0,
      NetCalories: 0
    },
    Targets: {
      DailyCalorieTarget: 1498,
      ProteinTargetMin: 70,
      ProteinTargetMax: 188,
      StepKcalFactor: 0.04,
      StepTarget: 8500
    }
  });

  render(
    <MemoryRouter initialEntries={["/today"]}>
      <AuthProvider>
        <TodayPage />
      </AuthProvider>
    </MemoryRouter>
  );

  expect(await screen.findByText("Daily Progress")).toBeInTheDocument();
  expect(screen.getByLabelText("Quick add")).toBeInTheDocument();
});
