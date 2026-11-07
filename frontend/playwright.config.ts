import { defineConfig, devices } from "@playwright/test";
import { env } from "node:process";

const browserChannel = env.PLAYWRIGHT_USE_CHROME === "1" ? "chrome" : undefined;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:4173",
    ...devices["Desktop Chrome"],
    ...(browserChannel ? { channel: browserChannel } : {}),
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 4173 --strictPort",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
    env: {
      VITE_API_BASE_URL: "",
      VITE_API_PROXY_TARGET: "http://127.0.0.1:8000",
    },
  },
});
