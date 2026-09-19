import { expect, test } from "@playwright/test";
import path from "node:path";

// Run with the API stopped: OFFLINE=1 npx playwright test
// Every page must say the data service is unreachable and show no figures.
const SHOTS = path.resolve(__dirname, "../../../docs/screenshots");

for (const route of ["/", "/report/DSE:NMB", "/markets", "/fixed-income", "/health"]) {
  test(`@offline ${route} explains the outage and shows no numbers`, async ({ page }, info) => {
    await page.goto(route, { waitUntil: "networkidle" });
    const main = page.locator("main");
    await expect(main).toContainText(/not reachable|offline/i);
    const text = await main.innerText();
    // No money amounts or percentages when the backend is down.
    expect(text).not.toMatch(/\d{1,3}(,\d{3})+|\d+\.\d+%/);
    if (route === "/report/DSE:NMB") {
      await page.screenshot({ path: path.join(SHOTS, `${info.project.name}-offline-report.png`), fullPage: true });
    }
  });
}
