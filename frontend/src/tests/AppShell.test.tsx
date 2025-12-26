import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { AppShell } from "../components/AppShell";
import { GetDailyLog, GetScheduleSlots } from "../services/ApiClient";

vi.mock("../services/ApiClient", () => ({
  GetDailyLog: vi.fn(),
  GetScheduleSlots: vi.fn()
}));

it("renders app shell content", async () => {
  vi.mocked(GetScheduleSlots).mockResolvedValue([]);
  vi.mocked(GetDailyLog).mockRejectedValue({ isAxiosError: true, response: { status: 404 } });

  render(
    <MemoryRouter initialEntries={["/today"]}>
      <AppShell>
        <div>Shell content</div>
      </AppShell>
    </MemoryRouter>
  );

  expect(await screen.findByText("Portion Note")).toBeInTheDocument();
  expect(screen.getByText("Shell content")).toBeInTheDocument();
});
