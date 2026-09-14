import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "../venv/bin/python -m uvicorn src.api.app:app --app-dir .. --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: !process.env.CI,
      env: {
        APP_ENVIRONMENT: "test",
        MCP_TRANSPORT: "memory",
        RESULT_OUTPUT_DIR: ".e2e-results",
        CORS_ALLOWED_ORIGINS: '["http://127.0.0.1:3000", "http://localhost:3000"]',
      },
    },
    {
      command: "node node_modules/next/dist/bin/next dev --hostname 127.0.0.1",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
