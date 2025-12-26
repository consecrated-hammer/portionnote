import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { InsightsPage } from "../pages/InsightsPage";
import { GetAiSuggestions } from "../services/ApiClient";

vi.mock("../services/ApiClient", () => ({
  GetAiSuggestions: vi.fn()
}));

it("renders weekly insights", () => {
  vi.mocked(GetAiSuggestions).mockResolvedValue({ Suggestions: [] });

  render(<InsightsPage />);

  expect(screen.getByText("Weekly insights")).toBeInTheDocument();
  expect(screen.getByText("Calories flow")).toBeInTheDocument();
  expect(screen.getByText("AI suggestions")).toBeInTheDocument();
});
