import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

const SHOTS = path.resolve(__dirname, "../../../docs/screenshots");

const ROUTES: { path: string; name: string; expectText: RegExp }[] = [
  { path: "/", name: "home", expectText: /Search/i },
  { path: "/report/DSE:NMB", name: "report-nmb", expectText: /NMB Bank Plc/ },
  { path: "/report/DSE:CRDB", name: "report-crdb", expectText: /CRDB Bank Plc/ },
  { path: "/markets", name: "markets", expectText: /Not available/i },
  { path: "/fixed-income", name: "fixed-income", expectText: /Bank of Tanzania/i },
  { path: "/portfolio", name: "portfolio", expectText: /Portfolio/i },
  { path: "/dashboard", name: "dashboard", expectText: /Sign-in is not implemented/i },
  { path: "/health", name: "health", expectText: /dse_prices/i },
  { path: "/research-chat", name: "research-chat", expectText: /not available|switched off|disabled/i },
];

function watchErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(`console: ${m.text()}`);
  });
  return errors;
}

for (const r of ROUTES) {
  test(`${r.name} renders without errors or sideways scrolling`, async ({ page }, info) => {
    const errors = watchErrors(page);
    const res = await page.goto(r.path, { waitUntil: "networkidle" });
    expect(res?.status(), "HTTP status").toBeLessThan(400);
    await expect(page.locator("main")).toContainText(r.expectText);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, "page wider than the screen").toBeLessThanOrEqual(1);
    await page.screenshot({ path: path.join(SHOTS, `${info.project.name}-${r.name}.png`), fullPage: true });
    expect(errors).toEqual([]);
  });
}

test("search finds NMB and opens its report", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("combobox").fill("nmb");
  const option = page.getByRole("option").first();
  await expect(option).toContainText("DSE:NMB");
  await option.click();
  await expect(page).toHaveURL(/\/report\/DSE(%3A|:)NMB/);
  await expect(page.getByTestId("review-banner")).toBeVisible();
});

test("report shows the review state, statuses and a model view, never a trade call", async ({ page }) => {
  await page.goto("/report/DSE:NMB", { waitUntil: "networkidle" });
  await expect(page.getByTestId("review-banner")).toContainText("Draft, not reviewed");
  await expect(page.getByTestId("data-as-of")).toContainText("31 Dec 2025");
  await expect(page.getByTestId("model-view")).toContainText("Model view");
  await expect(page.getByTestId("model-view")).toContainText("BLOCKED");
  await expect(page.getByTestId("status-counts")).toContainText("VERIFIED");
  const body = await page.locator("body").innerText();
  expect(body).not.toMatch(/\b(BUY|SELL|HOLD)\b/);

  await page.getByRole("button", { name: "Ratios" }).click();
  const cor = page.getByTestId("ratios").locator("tr", { hasText: "Cost of risk" });
  await expect(cor).toContainText("CONFLICTING SOURCE");
  await expect(page.getByTestId("ratios")).toContainText("PV");

  await page.getByRole("button", { name: "Sources" }).click();
  await expect(page.getByTestId("source-issues")).toContainText("gross loans");
});

test("CRDB report reads the group columns and shows its own publication date", async ({ page }) => {
  await page.goto("/report/DSE:CRDB", { waitUntil: "networkidle" });
  await expect(page.getByTestId("data-as-of")).toContainText("13 Mar 2026");
  await page.getByRole("button", { name: "Financial statements" }).click();
  const bs = page.getByTestId("statement-BS");
  await expect(bs).toContainText("22,308,936");   // GROUP total assets 2025
  await expect(bs).not.toContainText("20,763,416"); // BANK total assets 2025
});

test("statement values link to their source page", async ({ page }) => {
  await page.goto("/report/DSE:NMB", { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Financial statements" }).click();
  const link = page.getByTestId("statement-BS").locator("a[href*='/api/v1/sources/']").first();
  await expect(link).toHaveAttribute("href", /#page=\d+$/);
});

test("portfolio builder refuses to size positions without prices", async ({ page }) => {
  await page.goto("/portfolio", { waitUntil: "networkidle" });
  await page.getByLabel(/Tanzania \(DSE\)/).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByTestId("capital-currency")).toHaveText("TZS");
  await page.getByLabel(/How much will you invest/).fill("5000000");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: /Moderate/ }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Build proposal" }).click();
  const main = page.locator("main");
  await expect(main).toContainText(/No licensed DSE prices are loaded/);
  expect(await main.innerText()).not.toMatch(/\d+(\.\d+)?%\s+(weight|allocation)/i);
});
