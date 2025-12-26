import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { TopNav } from "../components/TopNav";

it("renders top navigation labels", () => {
  render(
    <MemoryRouter initialEntries={['/today']}>
      <TopNav />
    </MemoryRouter>
  );

  expect(screen.getByText("Today")).toBeInTheDocument();
  expect(screen.getByText("Foods")).toBeInTheDocument();
  expect(screen.getByText("History")).toBeInTheDocument();
  expect(screen.getByText("Settings")).toBeInTheDocument();
});
