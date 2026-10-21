// Screenshots and animation frames of the website for the README. Run through
// make_site_pictures.py, which serves site/ and turns the frames into GIFs.
//
//   node Docs/tools/site_shots.js http://127.0.0.1:8765/ /tmp/frames
//
// Needs Node and Playwright (npm i playwright). If a Chromium is installed somewhere other than
// Playwright's own folder, point CHROMIUM at it.
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const [url, out] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });

async function frames(page, name, clip, ms, act) {
  // Screenshots as fast as they come, each stamped with the time it was taken, so the GIF can
  // play back at the real speed whatever the machine.
  const dir = path.join(out, name);
  fs.mkdirSync(dir, { recursive: true });
  const times = [];
  const t0 = Date.now();
  let i = 0;
  const acting = act ? act() : Promise.resolve();
  while (Date.now() - t0 < ms) {
    await page.screenshot({ path: path.join(dir, `${String(i++).padStart(4, "0")}.png`), clip });
    times.push(Date.now() - t0);
  }
  await acting;
  fs.writeFileSync(path.join(dir, "times.json"), JSON.stringify(times));
}

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined, args: ["--no-sandbox"] });
  const shot = async (opts, fn) => {
    const ctx = await browser.newContext(opts);
    const page = await ctx.newPage();
    await page.goto(url);
    await page.waitForFunction(() => document.querySelector("[data-casefile]")?.getAttribute("aria-busy") === "false");
    await page.evaluate(() => document.fonts.ready);
    await fn(page);
    await ctx.close();
  };
  const desk = { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 };

  // The hero: string drawing from two clues to the one suspect they share.
  await shot({ ...desk, colorScheme: "light" }, async (page) => {
    const box = await page.locator("[data-hero]").boundingBox();
    const clip = { x: Math.round(box.x) - 24, y: Math.round(box.y) - 24, width: Math.round(box.width) + 48, height: Math.round(box.height) + 48 };
    await frames(page, "hero", clip, 2600);
    await page.screenshot({ path: path.join(out, "site-hero.png") });
  });
  await shot({ ...desk, colorScheme: "dark" }, async (page) => {
    await page.waitForTimeout(2200);
    await page.screenshot({ path: path.join(out, "site-hero-dark.png") });
  });

  // Playing a case: search twice, cross someone off, accuse the one who fits both clues.
  await shot({ ...desk, colorScheme: "light" }, async (page) => {
    await page.evaluate(() => document.querySelector("#play-title").scrollIntoView());
    await page.waitForTimeout(400);
    const box = await page.locator("[data-casefile]").boundingBox();
    const clip = { x: Math.round(box.x) - 8, y: 0, width: Math.round(box.width) + 16, height: 900 };
    await frames(page, "board", clip, 7600, async () => {
      const board = page.locator("[data-casefile]");
      await board.scrollIntoViewIfNeeded();
      await page.evaluate(() => scrollBy(0, document.querySelector("[data-board]").getBoundingClientRect().top - 150));
      await page.waitForTimeout(700);
      await page.click("[data-search]");
      await page.waitForTimeout(1300);
      await page.click("[data-search]");
      await page.waitForTimeout(1300);
      const fits = await page.$$eval(".suspect", (els) => els.map((e) => e.querySelector("[data-fits]").textContent));
      const culprit = fits.findIndex((f) => f === "Fits every clue");
      const other = fits.findIndex((f, i) => i !== culprit && f.startsWith("Fits none"));
      if (other >= 0) { await page.click(`.suspect[data-i="${other}"] [data-act=out]`); await page.waitForTimeout(900); }
      await page.click(`.suspect[data-i="${culprit}"] [data-act=accuse]`);
    });
    await page.waitForTimeout(600);
    await page.evaluate(() => scrollBy(0, document.querySelector("[data-board]").getBoundingClientRect().top - 150));
    await page.screenshot({ path: path.join(out, "site-board.png") });
  });

  // The picture link previews show when someone shares the site (og:image, 1200 by 630).
  await shot({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1, colorScheme: "light" }, async (page) => {
    await page.addStyleTag({ content: ".hero { min-height: 630px; align-items: center; padding: 0 64px !important; margin: 0 !important; max-width: none !important; } .top { display: none; } .cta { display: none; }" });
    await page.waitForTimeout(2200);
    await page.screenshot({ path: path.join(out, "site-share.png") });
  });

  // Phone width, light and dark.
  for (const scheme of ["light", "dark"]) {
    await shot({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, colorScheme: scheme }, async (page) => {
      await page.waitForTimeout(2200);
      await page.screenshot({ path: path.join(out, `site-phone-${scheme}.png`) });
    });
  }
  await browser.close();
})();
