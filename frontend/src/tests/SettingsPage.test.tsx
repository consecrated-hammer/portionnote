import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { SettingsPage } from "../pages/SettingsPage";
import { GetScheduleSlots, GetUserSettings } from "../services/ApiClient";

vi.mock("../services/ApiClient", () => ({
  GetScheduleSlots: vi.fn(),
  GetUserSettings: vi.fn(),
  UpdateUserSettings: vi.fn(),
  UpdateScheduleSlots: vi.fn(),
  LogoutUser: vi.fn(),
  CreateInvite: vi.fn()
}));

it("renders settings controls", async () => {
  vi.mocked(GetUserSettings).mockResolvedValue({
    Targets: {
      DailyCalorieTarget: 1498,
      ProteinTargetMin: 70,
      ProteinTargetMax: 188,
      StepKcalFactor: 0.04,
      StepTarget: 8500
    },
    TodayLayout: ["snapshot", "quickadd"]
  });
  vi.mocked(GetScheduleSlots).mockResolvedValue([]);

  render(
    <SettingsPage
      onLogout={() => {}}
      CurrentUser={{
        UserId: "User-1",
        Email: "admin@gmail.com",
        FirstName: "Admin",
        LastName: "User",
        IsAdmin: true
      }}
    />
  );

  expect(await screen.findByText("Settings")).toBeInTheDocument();
  expect(screen.getByText("AI Nutrition Recommendations")).toBeInTheDocument();
  expect(screen.getByText("Account")).toBeInTheDocument();
});
