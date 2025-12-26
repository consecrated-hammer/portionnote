import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { FoodsPage } from "../pages/FoodsPage";
import { GetFoods, GetMealTemplates } from "../services/ApiClient";

vi.mock("../services/ApiClient", () => ({
  GetFoods: vi.fn(),
  GetMealTemplates: vi.fn(),
  DeleteFood: vi.fn(),
  DeleteMealTemplate: vi.fn()
}));

it("loads foods from the api", async () => {
  vi.mocked(GetFoods).mockResolvedValue([
    {
      FoodId: "Food-1",
      FoodName: "Coffee With Sugar And Light Milk",
      ServingDescription: "1 cup",
      ServingQuantity: 1.0,
      ServingUnit: "cup",
      CaloriesPerServing: 70,
      ProteinPerServing: 2,
      IsFavourite: true,
      CreatedAt: "2024-01-01T00:00:00Z"
    }
  ]);
  vi.mocked(GetMealTemplates).mockResolvedValue([]);

  render(
    <MemoryRouter initialEntries={["/foods"]}>
      <FoodsPage />
    </MemoryRouter>
  );

  expect(await screen.findByText("Foods & Meals")).toBeInTheDocument();
  expect(await screen.findByText("Coffee With Sugar And Light Milk")).toBeInTheDocument();
});

it("shows error message when api fails", async () => {
  vi.mocked(GetFoods).mockRejectedValue(new Error("Failure"));
  vi.mocked(GetMealTemplates).mockRejectedValue(new Error("Failure"));

  render(
    <MemoryRouter initialEntries={["/foods"]}>
      <FoodsPage />
    </MemoryRouter>
  );

  expect(await screen.findByText("Failed to load data")).toBeInTheDocument();
});

it("prepopulates add food form from query params", async () => {
  vi.mocked(GetFoods).mockResolvedValue([]);
  vi.mocked(GetMealTemplates).mockResolvedValue([]);

  render(
    <MemoryRouter initialEntries={["/foods?addFood=1&foodName=Test%20Food"]}>
      <FoodsPage />
    </MemoryRouter>
  );

  expect(await screen.findByText("Add new food")).toBeInTheDocument();
  expect(await screen.findByDisplayValue("Test Food")).toBeInTheDocument();
});
