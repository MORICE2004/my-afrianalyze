import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

const SHOTS = path.resolve(__dirname, "../../../docs/screenshots");

const ROUTES: { path: string; name: string; expectText: RegExp }[] = [
  { path: "/", name: "home", expectText: /Research a listed company/i },
  { path: "/research", name: "research", expectText: /Full research available/i },
  { path: "/report/DSE:NMB", name: "report-nmb", expectText: /NMB Bank Plc/ },
  { path: "/report/DSE:CRDB", name: "report-crdb", expectText: /CRDB Bank Plc/ },
  { path: "/report/DSE:TBL", name: "report-tbl", expectText: /Research not available yet/ },
  { path: "/markets", name: "markets", expectText: /DSE All Share Index/ },
  { path: "/fixed-income", name: "fixed-income", expectText: /Bank of Tanzania/i },
  { path: "/portfolio", name: "portfolio", expectText: /Portfolio/i },
  { path: "/dashboard", name: "dashboard", expectText: /Sign in to see your portfolios/i },
  { path: "/watchlist", name: "watchlist", expectText: /Your watchlist is empty/i },
  { path: "/settings", name: "settings", expectText: /Appearance/i },
  { path: "/login", name: "login", expectText: /Research on listed African companies is open to read/i },
  { path: "/funds", name: "funds", expectText: /LICENSE_REVIEW_REQUIRED/ },
  { path: "/health", name: "health", expectText: /Used today/i },
  { path: "/admin", name: "admin", expectText: /Sign in to continue/i },
  { path: "/research-chat", name: "research-chat", expectText: /Every number in an answer is checked/i },
];

const TABS = ["Overview", "Financials", "Valuation", "Technical", "Risk", "Evidence", "Research"];
const API = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

async function nmbClose(): Promise<number> {
  const r = await fetch(`${API}/api/v1/securities/DSE:NMB/quote`);
  return Number((await r.json()).price);
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

// The company page streams its research; wait until the API has sent every stage.
async function openCompany(page: Page, id: string) {
  await page.goto(`/report/${encodeURIComponent(id)}`, { waitUntil: "networkidle" });
  await expect(page.getByTestId("research-progress")).toHaveAttribute("data-status", "done", { timeout: 30_000 });
}

async function signUp(page: Page, prefix: string) {
  const email = `e2e-${prefix}-${Date.now()}-${Math.floor(Math.random() * 1e6)}@afriedge.test`;
  await page.goto("/login", { waitUntil: "networkidle" });
  await page.getByRole("tab", { name: "Create account" }).click();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(`e2e-only-${Date.now()}`);
  await page.getByRole("button", { name: "Create account" }).last().click();
  await expect(page).toHaveURL(/\/dashboard$/);
  return email;
}

for (const r of ROUTES) {
  test(`${r.name} renders without errors or sideways scrolling`, async ({ page }, info) => {
    const errors = watchErrors(page);
    const res = await page.goto(r.path, { waitUntil: "networkidle" });
    expect(res?.status(), "HTTP status").toBeLessThan(400);
    if (r.path.startsWith("/report/")) {
      await expect(page.getByTestId("research-progress")).toHaveAttribute("data-status", "done", { timeout: 30_000 });
    }
    await expect(page.locator("main")).toContainText(r.expectText);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, "page wider than the screen").toBeLessThanOrEqual(1);
    await page.screenshot({ path: path.join(SHOTS, `${info.project.name}-${r.name}.png`), fullPage: true });
    // The admin page is refused to a signed-out visitor (a deliberate 401); nothing else may log an error.
    expect(errors.filter((e) => !(r.name === "admin" && /401/.test(e)))).toEqual([]);
  });
}

test("search finds NMB by ticker and CRDB despite a typo, and Enter opens the result", async ({ page }) => {
  await page.goto("/");
  const box = page.getByRole("combobox");
  await box.fill("nmb");
  await expect(page.getByRole("option").first()).toContainText("NMB Bank Plc");
  await box.fill("crdb bnk");
  await expect(page.getByRole("option").first()).toContainText("CRDB Bank Plc");
  await box.fill("zzzz");
  await expect(page.getByTestId("search-no-results")).toContainText("No company matched");
  await box.fill("nmb");
  await box.press("ArrowDown");
  await box.press("ArrowUp");
  await box.press("Enter");
  await expect(page).toHaveURL(/\/report\/DSE(%3A|:)NMB/);
  await expect(page.getByTestId("review-banner")).toBeVisible({ timeout: 30_000 });
});

test("the research streams in stage by stage, then shows the view, the price and the disclaimer", async ({ page }) => {
  await openCompany(page, "DSE:NMB");
  const progress = page.getByTestId("research-progress");
  await progress.getByRole("button").click();               // show the steps
  for (const step of ["company", "price", "sources", "validation", "valuation", "synthesis"]) {
    await expect(progress.locator(`[data-step="${step}"]`)).not.toHaveAttribute("data-state", "PENDING");
  }
  await expect(page.getByTestId("review-banner")).toContainText("Draft, not reviewed");
  await expect(page.getByTestId("data-as-of")).toContainText("31 Dec 2025");
  await expect(page.getByTestId("model-view")).toContainText("AfriEdge view");
  const close = await nmbClose();
  await expect(page.getByTestId("price")).toContainText(`TZS ${money(close)}`);
  await expect(page.getByTestId("quote-header")).toContainText(`TZS ${money(close)}`);
  await expect(page.getByTestId("currency")).toHaveText("TZS");
  await expect(page.getByTestId("price-attribution")).toContainText("Not live");
  await expect(page.getByTestId("status-counts")).toContainText("VERIFIED");
  const body = await page.locator("body").innerText();
  expect(body).toMatch(/not investment advice/i);
  expect(body).not.toMatch(/\bLIVE\b/);
  // A trade label may appear only when the view holds under every cost-of-equity method.
  const word = await page.getByTestId("view-word").innerText();
  if (/^(BUY|SELL|HOLD)$/.test(word)) await expect(page.getByTestId("model-view")).toContainText("Model view:");

  await page.getByRole("tab", { name: "Financials" }).click();
  const cor = page.getByTestId("ratios").locator("tr", { hasText: "Cost of risk" });
  await expect(cor).toContainText("CONFLICTING SOURCE");
  await expect(page.getByTestId("ratios")).toContainText("PV");

  await page.getByRole("tab", { name: "Evidence" }).click();
  await expect(page.getByTestId("source-issues")).toContainText("gross loans");
});

test("CRDB statements read the group columns and show their own publication date", async ({ page }) => {
  await openCompany(page, "DSE:CRDB");
  await expect(page.getByTestId("data-as-of")).toContainText("13 Mar 2026");
  await page.getByRole("tab", { name: "Financials" }).click();
  const bs = page.getByTestId("statement-BS");
  await expect(bs).toContainText("22,308,936");   // GROUP total assets 2025
  await expect(bs).not.toContainText("20,763,416"); // BANK total assets 2025
});

test("a statement value opens its evidence: document, page, period, validation and the source link", async ({ page }) => {
  await openCompany(page, "DSE:NMB");
  await page.getByRole("tab", { name: "Financials" }).click();
  await page.getByTestId("statement-BS").locator("button[data-source-page]").first().click();
  const card = page.getByTestId("evidence-card");
  await expect(card).toContainText("Document");
  await expect(card).toContainText("Page");
  await expect(card).toContainText("Validation");
  // The document opens in AfriEdge's page viewer at the cited page; the original file is never linked.
  await expect(card.getByTestId("view-source-page")).toHaveAttribute("href", /^\/sources\/\d+\?page=\d+$/);
  await expect(card.locator("a[href*='/api/v1/sources/']")).toHaveCount(0);
});

for (const id of ["DSE:NMB", "DSE:CRDB"]) {
  test(`every tab of the ${id} workspace opens without errors`, async ({ page }) => {
    const errors = watchErrors(page);
    await openCompany(page, id);
    for (const name of TABS) {
      await page.getByRole("tab", { name, exact: true }).click();
      await expect(page.getByRole("tab", { name, exact: true })).toHaveAttribute("aria-selected", "true");
      expect(errors, `errors after opening ${name}`).toEqual([]);
    }
    await page.getByRole("tab", { name: "Valuation", exact: true }).click();
    await expect(page.getByTestId("coe-alternatives")).toBeVisible();
    await expect(page.getByTestId("valuation-range")).toBeVisible();
  });
}

test("the technical tab shows indicators from published highs, lows and turnover, and is not a signal", async ({ page }) => {
  await openCompany(page, "DSE:NMB");
  await page.getByRole("tab", { name: "Technical", exact: true }).click();
  const t = page.getByTestId("technical");
  await expect(t).toContainText("RSI (14)");
  await expect(t).toContainText("200-day average");
  await expect(t).toContainText("Average true range (14)");
  await expect(t).toContainText("VWAP (20 days)");
  await expect(t).toContainText("not trading signals");
});

test("a company without research shows its price and says why there is no research", async ({ page }) => {
  await openCompany(page, "DSE:TBL");
  await expect(page.getByTestId("research-unavailable")).toContainText("annual reports");
  await expect(page.getByTestId("quote-header")).toContainText("TZS");
  await expect(page.getByTestId("model-view")).toHaveCount(0);
});

test("the theme toggle switches to dark and survives a reload", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  const theme = () => page.evaluate(() => document.documentElement.getAttribute("data-theme"));
  const start = await theme();
  await page.getByTestId("theme-toggle").click();
  const next = start === "dark" ? "light" : "dark";
  expect(await theme()).toBe(next);
  await page.reload({ waitUntil: "domcontentloaded" });
  expect(await theme()).toBe(next);
});

test("a company added to the watchlist appears on the watchlist and the dashboard", async ({ page }) => {
  await openCompany(page, "DSE:CRDB");
  await page.getByTestId("watch-toggle").click();
  await expect(page.getByTestId("watch-toggle")).toHaveAttribute("aria-pressed", "true");
  await page.goto("/watchlist", { waitUntil: "networkidle" });
  await expect(page.getByTestId("watchlist")).toContainText("CRDB Bank Plc");
  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page.getByTestId("watchlist-preview")).toContainText("CRDB Bank Plc");
  await expect(page.getByTestId("recently-viewed")).toContainText("CRDB Bank Plc");
});

test("Excel export is Pro: locked in the page and refused by the server", async ({ page }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  await openCompany(page, "DSE:NMB");
  // View-only: a reader without the export entitlement sees no export control at all.
  await expect(page.getByTestId("model-view")).toBeVisible();
  await expect(page.getByTestId("exports")).toHaveCount(0);
  await expect(page.getByTestId("download-pdf")).toHaveCount(0);
  expect((await page.request.get("/api/export/DSE:NMB?format=pdf")).status()).toBe(401);
  expect((await page.request.get(`${API}/api/v1/reports/DSE:NMB/pdf`)).status()).toBe(401);
  // Hiding a button is not the check: the server refuses a signed-out request and a Free account alike.
  expect((await page.request.get("/api/export/DSE:NMB")).status()).toBe(401);
  await signUp(page, "free");
  expect((await page.request.get("/api/export/DSE:NMB")).status()).toBe(403);
  expect((await page.request.get("/api/export/DSE:NMB?format=pdf")).status()).toBe(403);
  await openCompany(page, "DSE:NMB");
  await expect(page.getByTestId("exports")).toHaveCount(0);
});

test("source documents are read as pages inside AfriEdge; the original file is never served to a reader", async ({ page }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  const report = await (await page.request.get(`${API}/api/v1/reports/DSE:NMB`)).json();
  const doc = report.sources.documents[0];
  expect(doc.viewer_url).toMatch(/^\/sources\/\d+/);
  expect(JSON.stringify(report)).not.toMatch(/\/api\/v1\/sources\/\d+\/file|data\/raw/);
  // Signed out: the viewer asks to sign in; every document endpoint refuses.
  await page.goto(doc.viewer_url);
  await expect(page.getByTestId("viewer-signin")).toContainText("Sign in to read source documents");
  for (const p of [`/api/v1/sources/${doc.document_id}/file`, `/api/v1/sources/${doc.document_id}/pages/1`, `/api/v1/sources/${doc.document_id}`]) {
    expect((await page.request.get(`${API}${p}`)).status(), p).toBe(401);
  }
  expect((await page.request.get(`/api/source-page/${doc.document_id}/1`)).status()).toBe(401);
  // Signed in as an ordinary reader: pages render as images; the original file is still refused.
  await signUp(page, "viewer");
  await page.goto(`${doc.viewer_url}`);
  await expect(page.getByTestId("source-viewer")).toBeVisible();
  const img = page.getByTestId("source-page-image");
  await expect(img).toBeVisible();
  expect(await img.evaluate((e: HTMLImageElement) => e.complete && e.naturalWidth > 400)).toBe(true);
  const pageRes = await page.request.get(`/api/source-page/${doc.document_id}/1`);
  expect(pageRes.headers()["content-type"]).toBe("image/png");
  await expect(page.getByTestId("original-source")).toHaveAttribute("href", /^https?:\/\//);
});

test("the footer carries legal and information links only, not the main navigation", async ({ page }) => {
  await page.goto("/about");
  const footer = page.getByTestId("site-footer");
  for (const l of ["Privacy", "Cookies", "Risk disclaimer", "Data methodology", "About"]) await expect(footer.getByRole("link", { name: l, exact: true })).toBeVisible();
  for (const l of ["Markets", "Research", "Portfolio", "News"]) await expect(footer.getByRole("link", { name: l, exact: true })).toHaveCount(0);
  await footer.getByRole("link", { name: "Risk disclaimer" }).click();
  await expect(page.getByTestId("disclaimer-page")).toContainText("Not investment advice");
});

test("the administration page is refused to an ordinary account", async ({ page }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  await signUp(page, "notadmin");
  await page.goto("/admin", { waitUntil: "networkidle" });
  await expect(page.getByTestId("admin-refused")).toContainText("Administrators only");
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

  async function signUpAs(email: string) {
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

  const a = await signUpAs(`e2e-a-${run}@afriedge.test`);
  await a.page.getByLabel("Portfolio name").fill("E2E holdings");
  await a.page.getByLabel("Security 1").selectOption("DSE:NMB");
  await a.page.getByLabel("Quantity 1").fill("10");
  await a.page.getByRole("button", { name: "Save portfolio" }).click();
  const card = a.page.getByTestId("portfolio-card");
  await expect(card).toContainText("E2E holdings");
  await expect(card).toContainText(money((await nmbClose()) * 10));
  const ids: number[] = await a.page.evaluate(async () =>
    (await (await fetch("/api/portfolios")).json()).portfolios.map((p: { id: number }) => p.id));
  expect(a.errors).toEqual([]);

  const b = await signUpAs(`e2e-b-${run}@afriedge.test`);
  await expect(b.page.locator("main")).toContainText("No saved portfolios");
  const attempt = await b.page.evaluate(async (id) => {
    const get = await fetch(`/api/portfolios/${id}`);
    const del = await fetch(`/api/portfolios/${id}`, { method: "DELETE" });
    return [get.status, del.status];
  }, ids[0]);
  expect(attempt).toEqual([404, 404]);

  await a.page.reload({ waitUntil: "networkidle" });
  await expect(a.page.getByTestId("portfolio-card")).toContainText("E2E holdings");
  await a.ctx.close();
  await b.ctx.close();
});

test("the research assistant asks for sign-in, then answers honestly without an AI provider", async ({ browser }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto("/research-chat", { waitUntil: "networkidle" });
  await page.getByLabel("Question").fill("Why is this company valued this way?");
  await page.getByRole("button", { name: "Ask" }).click();
  await expect(page.getByText("to ask the research assistant")).toBeVisible();

  await signUp(page, "assistant");
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
  await signUp(page, "analysis");
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

test("markets shows the session, activity, movers and sectors, and Kenya and Uganda as not connected", async ({ page }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  await page.goto("/markets", { waitUntil: "networkidle" });
  await expect(page.locator("main")).toContainText("End of day · session of");
  await expect(page.getByTestId("activity")).toContainText("Value traded");
  await expect(page.getByTestId("movers")).toContainText("Largest rises");
  await expect(page.getByTestId("sectors")).toContainText("Banks, Finance & Investments");
  await expect(page.getByTestId("market-NSE")).toContainText("Kenya market data is not yet connected.");
  await expect(page.getByTestId("market-USE")).toContainText("Uganda market data is not yet connected.");
});

test("news lists official stories with source, time, relevance and a link out, and opens a story in context", async ({ page }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  const errors = watchErrors(page);
  await page.goto("/news", { waitUntil: "networkidle" });
  await expect(page.getByTestId("news-card").first()).toBeVisible();
  const body = await page.locator("main").innerText();
  expect(body).not.toMatch(/breaking|bullish|bearish/i);
  await expect(page.getByTestId("news-sources")).toContainText("Central Bank of Kenya");
  await page.getByRole("link", { name: "Kenya", exact: true }).click();
  await expect(page).toHaveURL(/country=KE/);
  await page.getByTestId("news-card").first().getByRole("heading").getByRole("link").click();
  await page.waitForURL(/\/news\/[0-9a-f]{40}$/, { timeout: 30000 });
  await expect(page.getByTestId("news-story")).toContainText("Why it may matter to East African markets");
  await expect(page.getByTestId("read-source")).toHaveAttribute("href", /^https:\/\//);
  expect(errors).toEqual([]);
});

test("the home page shows market-relevant news; Ctrl+K opens quick search and goes to a company", async ({ page }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page.getByTestId("home-news")).toContainText("Economic news");
  await page.keyboard.press("Control+k");
  await expect(page.getByTestId("command-palette")).toBeVisible();
  await page.keyboard.type("crdb");
  await expect(page.getByTestId("command-palette")).toContainText("CRDB Bank Plc");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/report\/DSE(%3A|:)CRDB/);
});

test("a withheld view explains itself and 'Review assumptions' opens the valuation", async ({ page }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  await openCompany(page, "DSE:NMB");
  const word = await page.getByTestId("view-word").innerText();
  test.skip(word !== "View unavailable", `NMB's view is ${word}`);
  await expect(page.getByTestId("model-view")).toContainText("Current valuation methods give conflicting results.");
  await page.getByTestId("review-assumptions").click();
  await expect(page.getByRole("tab", { name: "Valuation" })).toHaveAttribute("data-state", "active");
  await page.getByTestId("verification-badge").click();
  await expect(page.locator("body")).toContainText("two independent extraction methods");
});

test("with reduced motion the company page still shows every state, and the privacy page lists what is stored", async ({ browser }) => {
  test.skip(!!process.env.OFFLINE, "needs the API");
  const ctx = await browser.newContext({ reducedMotion: "reduce" });
  const page = await ctx.newPage();
  await openCompany(page, "DSE:NMB");
  await expect(page.getByTestId("model-view")).toBeVisible();
  await expect(page.getByTestId("quote-header")).toContainText("TZS");
  await page.goto("/privacy");
  await expect(page.locator("main")).toContainText("no analytics or advertising cookies");
  await ctx.close();
});
