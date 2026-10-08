// Renders the brand SVGs to PNG with the installed Chrome (Playwright): app icons and the report logo.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "..");
const jobs = [
  { svg: "src/app/icon.svg", out: "src/app/icon.png", w: 512, h: 512 },
  { svg: "src/app/icon.svg", out: "src/app/apple-icon.png", w: 180, h: 180 },
  { svg: "public/brand/afriedge-logo.svg", out: "public/brand/afriedge-logo.png", w: 824, h: 192 },
  { svg: "public/brand/afriedge-mark.svg", out: "public/brand/afriedge-mark.png", w: 256, h: 256 },
];
(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL ?? "chrome" });
  for (const j of jobs) {
    const page = await browser.newPage({ viewport: { width: j.w, height: j.h } });
    const svg = fs.readFileSync(path.join(root, j.svg), "utf8");
    // The wordmark is drawn in IBM Plex Sans, the site's typeface, loaded for the render.
    await page.setContent(`<html><head><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@600&display=block"></head>
      <body style="margin:0;background:transparent">${svg.replace("<svg ", `<svg width="${j.w}" height="${j.h}" `)}</body></html>`, { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(root, j.out), omitBackground: true });
    await page.close();
    console.log("wrote", j.out);
  }
  await browser.close();
})();
