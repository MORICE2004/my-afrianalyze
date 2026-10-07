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
  { path: "/dashboard", name: "dashboard", expectText: /Sign in to see your portfolios/i },
  { path: "/login", name: "login", expectText: /Sign in to AfriEdge/i },
  { path: "/health", name: "health", expectText: /dse_prices/i },
  { path: "/research-chat", name: "research-chat", expectText: /Every number in an answer is checked/i },
];

const API = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

async function nmbClose(): Promise<number> {
  const r = await fetch(`${API}/api/v1/reports/DSE:NMB`);
  return Number((await r.json()).header.price.value);
}

function money(n: number): string {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

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

test("report shows the review state, statuses, a model view and the disclaimer", async ({ page }) => {
  await page.goto("/report/DSE:NMB", { waitUntil: "networkidle" });
  await expect(page.getByTestId("review-banner")).toContainText("Draft, not reviewed");
  await expect(page.getByTestId("data-as-of")).toContainText("31 Dec 2025");
  await expect(page.getByTestId("model-view")).toContainText("Model view");
  // The DSE's last stored close, read from the API (it changes with every data refresh).
  const close = await nmbClose();
  await expect(page.getByTestId("price")).toContainText(`TZS ${money(close)}`);
  await expect(page.getByTestId("price-attribution")).toContainText("Not live");
  await expect(page.getByTestId("status-counts")).toContainText("VERIFIED");
  // A trade label is allowed (owner's decision 2026-09-19) but only beside the model view, and the
  // disclaimer must always be on the page.
  const body = await page.locator("body").innerText();
  expect(body).toMatch(/not investment advice/i);
  if (/\b(BUY|SELL|HOLD)\b/.test(body)) {
    await expect(page.getByTestId("model-view")).toContainText(/Undervalued|Fairly valued|Overvalued/);
  }

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

test("portfolio builder refuses to size positions it cannot size", async ({ page }) => {
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
  // Prices exist now, but the weighting rules and board lots do not, so it must still show no numbers.
  await expect(main).toContainText(/not implemented yet/);
  expect(await main.innerText()).not.toMatch(/\d+(\.\d+)?%\s+(weight|allocation)/i);
});

// Sign-up, a saved portfolio valued from the stored close, and isolation through the real UI. Each run makes
// two throwaway accounts with unique emails in the local database (synthetic test users, not real people).
test("a portfolio is private to the account that saved it", async ({ browser }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  const run = `${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
  const password = `e2e-only-${run}`;

  async function signUp(email: string) {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    const errors = watchErrors(page);
    await page.goto("/login", { waitUntil: "networkidle" });
    await page.getByRole("tab", { name: "Create account" }).click();
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Create account" }).last().click();
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.locator("main")).toContainText(`Signed in as ${email}`);
    return { ctx, page, errors };
  }

  const a = await signUp(`e2e-a-${run}@afriedge.test`);
  await a.page.getByLabel("Portfolio name").fill("E2E holdings");
  await a.page.getByLabel("Security 1").selectOption("DSE:NMB");
  await a.page.getByLabel("Quantity 1").fill("10");
  await a.page.getByRole("button", { name: "Save portfolio" }).click();
  const card = a.page.getByTestId("portfolio-card");
  await expect(card).toContainText("E2E holdings");
  // 10 shares x the stored close, whatever the latest refresh stored
  await expect(card).toContainText(money((await nmbClose()) * 10));
  const ids: number[] = await a.page.evaluate(async () =>
    (await (await fetch("/api/portfolios")).json()).portfolios.map((p: { id: number }) => p.id));
  expect(a.errors).toEqual([]);

  const b = await signUp(`e2e-b-${run}@afriedge.test`);
  await expect(b.page.locator("main")).toContainText("No saved portfolios");
  const attempt = await b.page.evaluate(async (id) => {
    const get = await fetch(`/api/portfolios/${id}`);
    const del = await fetch(`/api/portfolios/${id}`, { method: "DELETE" });
    return [get.status, del.status];
  }, ids[0]);
  expect(attempt).toEqual([404, 404]);

  // A's portfolio survived B's attempt.
  await a.page.reload({ waitUntil: "networkidle" });
  await expect(a.page.getByTestId("portfolio-card")).toContainText("E2E holdings");
  // B's two 404s above are deliberate, so only B's page is excused from the no-errors check.
  await a.ctx.close();
  await b.ctx.close();
});

// Every tab of both reports, opened one by one. A tab that throws takes the whole page down, and the
// tests above only look at the first tab (the Valuation tab crashed this way until 2026-10-07).
for (const id of ["DSE:NMB", "DSE:CRDB"]) {
  test(`every tab of the ${id} report opens without errors`, async ({ page }) => {
    const errors = watchErrors(page);
    await page.goto(`/report/${encodeURIComponent(id)}`, { waitUntil: "networkidle" });
    for (const name of ["Summary", "Financial statements", "Ratios", "Valuation", "Scenarios", "Technical", "Beta", "Risks", "Sources", "Research run"]) {
      await page.getByRole("button", { name, exact: true }).click();
      await expect(page.locator("main"), `${name} tab`).toBeVisible();
      expect(errors, `errors after opening ${name}`).toEqual([]);
    }
    await page.getByRole("button", { name: "Valuation", exact: true }).click();
    await expect(page.getByTestId("coe-alternatives")).toBeVisible();
  });
}

test("the technical tab shows computed indicators and says what it cannot compute", async ({ page }) => {
  await page.goto("/report/DSE%3ANMB", { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Technical", exact: true }).click();
  const t = page.getByTestId("technical");
  await expect(t).toContainText("RSI (14)");
  await expect(t).toContainText("200-day average");
  await expect(t).toContainText("not stored yet");          // ATR, ADX, VWAP need data we do not hold
  await expect(t).toContainText("not trading signals");
});

test("the copilot asks for sign-in, then answers honestly without an AI provider", async ({ browser }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto("/research-chat", { waitUntil: "networkidle" });
  await page.getByLabel("Question").fill("Why is this company valued this way?");
  await page.getByRole("button", { name: "Ask" }).click();
  await expect(page.getByText("to ask the copilot")).toBeVisible();

  const email = `e2e-copilot-${Date.now()}@afriedge.test`;
  await page.goto("/login", { waitUntil: "networkidle" });
  await page.getByRole("tab", { name: "Create account" }).click();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(`e2e-only-${Date.now()}`);
  await page.getByRole("button", { name: "Create account" }).last().click();
  await expect(page).toHaveURL(/\/dashboard$/);

  await page.goto("/research-chat", { waitUntil: "networkidle" });
  await page.getByLabel("Question").fill("Why is this company valued this way?");
  await page.getByRole("button", { name: "Ask" }).click();
  // No provider key is configured in local testing: the page must say so, not invent an answer.
  const reply = page.getByTestId("copilot-reply");
  await expect(reply).toHaveAttribute("data-status", "AI_UNAVAILABLE");
  await expect(reply).toContainText("research report itself is unaffected");
  await ctx.close();
});

test("portfolio analysis shows risk, stress tests and optimisation from stored prices", async ({ browser }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const errors = watchErrors(page);
  await page.goto("/login", { waitUntil: "networkidle" });
  await page.getByRole("tab", { name: "Create account" }).click();
  await page.getByLabel("Email").fill(`e2e-analysis-${Date.now()}@afriedge.test`);
  await page.getByLabel("Password").fill(`e2e-only-${Date.now()}`);
  await page.getByRole("button", { name: "Create account" }).last().click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.getByLabel("Portfolio name").fill("Two banks");
  await page.getByLabel("Security 1").selectOption("DSE:NMB");
  await page.getByLabel("Quantity 1").fill("1000");
  await page.getByRole("button", { name: "Add holding" }).click();
  await page.getByLabel("Security 2").selectOption("DSE:CRDB");
  await page.getByLabel("Quantity 2").fill("1000");
  await page.getByRole("button", { name: "Save portfolio" }).click();
  await page.getByRole("button", { name: "Analyse" }).click();
  const a = page.getByTestId("portfolio-analysis");
  await expect(a).toContainText("Volatility");
  await expect(a).toContainText("Bank shares fall 30%");
  await expect(a).toContainText("Minimum variance");
  await expect(a).toContainText("Needs expected returns");      // mean-variance refused, not guessed
  expect(errors).toEqual([]);
  await ctx.close();
});

test("markets shows DSE breadth and movers from stored closes, and Kenya and Uganda as not integrated", async ({ page }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  await page.goto("/markets", { waitUntil: "networkidle" });
  const movers = page.getByTestId("movers");
  await expect(movers).toContainText("did not trade");
  await expect(movers).toContainText("DSE-listed securities have stored prices");
  await expect(page.getByTestId("market-NSE")).toContainText("LICENSE_REVIEW_REQUIRED");
});
