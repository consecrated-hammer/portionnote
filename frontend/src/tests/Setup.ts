import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

if (!("PointerEvent" in window)) {
  class PointerEvent extends MouseEvent {}
  window.PointerEvent = PointerEvent as typeof window.PointerEvent;
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});
