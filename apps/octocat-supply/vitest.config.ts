import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    projects: [
      {
        extends: true,
        test: {
          name: "fixtures",
          environment: "node",
          include: ["test/fixtures/**/*.test.ts"],
        },
      },
      {
        extends: true,
        test: {
          name: "api",
          environment: "node",
          include: ["api/test/**/*.test.ts"],
        },
      },
      {
        extends: true,
        test: {
          name: "web",
          environment: "jsdom",
          environmentOptions: { jsdom: { url: "https://shop.example.test" } },
          include: ["frontend/test/**/*.test.tsx"],
          setupFiles: ["frontend/test/setup.ts"],
        },
      },
    ],
  },
});
