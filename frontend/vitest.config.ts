import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const ReactPlugin = react();

const Config = defineConfig({
  plugins: [ReactPlugin],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/tests/Setup.ts",
    include: ["src/tests/**/*.test.tsx"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "json-summary"],
      reportsDirectory: "coverage",
      lines: 80,
      functions: 80,
      branches: 80,
      statements: 80,
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/main.tsx",
        "src/vite-env.d.ts",
        "src/models/**/*"
      ]
    }
  }
});

export default Config;
