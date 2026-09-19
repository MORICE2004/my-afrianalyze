import { defineConfig } from "@playwright/test";

// Browser checks for every page at desktop (1440px) and phone (375px) width.
// Start the API (port 8000) and this app (port 3000) first; see CLAUDE.md "Project map and commands".
// OFFLINE=1 runs only the backend-stopped checks (stop the API before running them).
export default defineConfig({
  testDir: "./e2e",
  outputDir: "./test-results",
  timeout: 60_000,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:3000",
    trace: "off",
    // Uses the installed Google Chrome (fresh temporary profile). Set PW_CHANNEL= to use Playwright's own Chromium.
    channel: process.env.PW_CHANNEL ?? "chrome",
  },
  grep: process.env.OFFLINE ? /@offline/ : undefined,
  grepInvert: process.env.OFFLINE ? undefined : /@offline/,
  projects: [
    { name: "desktop-1440", use: { viewport: { width: 1440, height: 900 } } },
    { name: "mobile-375", use: { viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true } },
  ],
});
