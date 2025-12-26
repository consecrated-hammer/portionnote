import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { LogPage } from "../pages/LogPage";
import { GetDailyLog, GetFoods, GetMealTemplates, GetScheduleSlots } from "../services/ApiClient";

vi.mock("../services/ApiClient", () => ({
  GetDailyLog: vi.fn(),
  GetFoods: vi.fn(),
  CreateDailyLog: vi.fn(),
  UpdateDailySteps: vi.fn(),
  CreateMealEntry: vi.fn(),
  DeleteMealEntry: vi.fn(),
  GetMealTemplates: vi.fn(),
  GetScheduleSlots: vi.fn(),
  CreateMealTemplate: vi.fn(),
  DeleteMealTemplate: vi.fn(),
  ApplyMealTemplate: vi.fn()
}));

it("renders empty log state", async () => {
  vi.mocked(GetDailyLog).mockResolvedValue({
    DailyLog: {
      DailyLogId: "Log-1",
      LogDate: "2024-01-04",
      Steps: 0,
      StepKcalFactorOverride: null,
      Notes: null
    },
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
      RemainingCalories: 0,
      RemainingProteinMin: 0,
      RemainingProteinMax: 0,
      RemainingFibre: 0,
      RemainingCarbs: 0,
      RemainingFat: 0,
      RemainingSaturatedFat: 0,
      RemainingSugar: 0,
      RemainingSodium: 0
    },
    Summary: {
      LogDate: "2024-01-04",
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
  vi.mocked(GetFoods).mockResolvedValue([]);
  vi.mocked(GetMealTemplates).mockResolvedValue([]);
  vi.mocked(GetScheduleSlots).mockResolvedValue([]);

  render(
    <MemoryRouter initialEntries={["/log"]}>
      <LogPage />
    </MemoryRouter>
  );

  expect(screen.getByText("Daily log")).toBeInTheDocument();
  expect(await screen.findByText("Nothing logged")).toBeInTheDocument();
});
