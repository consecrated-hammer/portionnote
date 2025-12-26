import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import App from "../App";
import { GetCurrentUser, GetDailyLog, GetScheduleSlots, GetUserSettings } from "../services/ApiClient";

vi.mock("../services/ApiClient", () => ({
  GetCurrentUser: vi.fn(),
  GetDailyLog: vi.fn(),
  GetScheduleSlots: vi.fn(),
  GetUserSettings: vi.fn(),
  UpdateScheduleSlots: vi.fn(),
  UpdateUserSettings: vi.fn()
}));

it("renders today route", async () => {
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
      StepTarget: 8500
    },
    TodayLayout: ["snapshot", "checkins", "quickadd"]
  });
  vi.mocked(GetScheduleSlots).mockResolvedValue([]);
  vi.mocked(GetDailyLog).mockRejectedValue({ isAxiosError: true, response: { status: 404 } });

  render(
    <MemoryRouter initialEntries={["/today"]}>
      <App />
    </MemoryRouter>
  );

  expect(await screen.findByText("Daily snapshot")).toBeInTheDocument();
});
