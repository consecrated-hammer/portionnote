import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { vi } from "vitest";
import { QuickMealEntry } from "../components/QuickMealEntry";

const LocationDisplay = () => {
  const Location = useLocation();
  return <div data-testid="location">{Location.pathname}{Location.search}</div>;
};

it("navigates to add food with prefilled name when no food matches", async () => {
  render(
    <MemoryRouter initialEntries={["/log"]}>
      <Routes>
        <Route
          path="/log"
          element={
            <QuickMealEntry
              Foods={[
                {
                  FoodId: "Food-1",
                  FoodName: "Apple",
                  ServingDescription: "1 fruit",
                  ServingQuantity: 1,
                  ServingUnit: "piece",
                  CaloriesPerServing: 95,
                  ProteinPerServing: 0.5,
                  IsFavourite: false
                }
              ]}
              Templates={[]}
              RecentEntries={[]}
              OnSubmit={vi.fn(async () => {})}
              AutoFocus={false}
            />
          }
        />
        <Route path="/foods" element={<LocationDisplay />} />
      </Routes>
    </MemoryRouter>
  );

  fireEvent.change(screen.getByPlaceholderText("Type to search..."), {
    target: { value: "Dragonfruit" }
  });

  fireEvent.click(await screen.findByRole("button", { name: /add food/i }));

  expect(await screen.findByTestId("location")).toHaveTextContent(
    "/foods?addFood=1&foodName=Dragonfruit"
  );
});
