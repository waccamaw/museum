#!/usr/bin/env node
// museum QA crawler — loads every served page in headless chromium and reports
// broken assets (404 images/css/js), console errors, JS exceptions, and saves a
// full-page screenshot per page for visual review.
//
// Usage: node crawl.mjs [baseURL]   (default http://127.0.0.1:1313)
// Output: qa/report/report.json, qa/report/report.md, qa/report/screens/<slug>.png
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE = (process.argv[2] || 'http://127.0.0.1:1313').replace(/\/$/, '');
const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, 'report');
const SCREENS = resolve(OUT, 'screens');
mkdirSync(SCREENS, { recursive: true });

const IMG_EXT = /\.(png|jpe?g|gif|webp|svg|bmp|ico|tif?f)(\?|$)/i;
const slug = (u) => {
  const p = new URL(u).pathname.replace(/^\/|\/$/g, '') || 'home';
  return p.replace(/[^a-z0-9]+/gi, '_');
};
const isInternal = (u) => { try { return new URL(u).origin === new URL(BASE).origin; } catch { return false; } };

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, ignoreHTTPSErrors: true });

// Discover URLs: homepage + every internal link found on it (one level deep).
const seedPage = await ctx.newPage();
await seedPage.goto(BASE + '/', { waitUntil: 'load', timeout: 30000 }).catch(() => {});
let links = await seedPage.$$eval('a[href]', as => as.map(a => a.href));
await seedPage.close();
const urls = Array.from(new Set([BASE + '/', ...links.filter(isInternal).map(u => u.split('#')[0])]))
  .filter(u => !/\.(zip|rar|7z|exe|swf|mp3|mid|wav|avi|mp4|webm|iso|img|vhd)(\?|$)/i.test(u));

const results = [];
for (const url of urls) {
  const page = await ctx.newPage();
  const broken = [];     // failed or 4xx/5xx assets
  const consoleErrs = []; // console.error / warning
  const pageErrs = [];   // uncaught JS exceptions
  page.on('requestfailed', r => {
    const f = r.failure();
    broken.push({ url: r.url(), type: r.resourceType(), reason: f ? f.errorText : 'failed', img: IMG_EXT.test(r.url()) });
  });
  page.on('response', res => {
    if (res.status() >= 400) broken.push({ url: res.url(), type: res.request().resourceType(), reason: 'HTTP ' + res.status(), img: IMG_EXT.test(res.url()) });
  });
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') consoleErrs.push({ type: m.type(), text: m.text().slice(0, 300) }); });
  page.on('pageerror', e => pageErrs.push(String(e).slice(0, 300)));

  let status = 0;
  try {
    const resp = await page.goto(url, { waitUntil: 'load', timeout: 30000 });
    status = resp ? resp.status() : 0;
    await page.waitForTimeout(1500); // let late images/scripts settle
  } catch (e) {
    pageErrs.push('NAV: ' + String(e).slice(0, 200));
  }

  // Detect likely-unstyled page: a stylesheet that 404'd.
  const cssBroken = broken.filter(b => b.type === 'stylesheet' || /\.css(\?|$)/i.test(b.url));
  const imgBroken = broken.filter(b => b.img || b.type === 'image');

  const shot = resolve(SCREENS, slug(url) + '.png');
  try { await page.screenshot({ path: shot, fullPage: true }); } catch {}

  results.push({ url, status, brokenImages: imgBroken, brokenCss: cssBroken,
    otherBroken: broken.filter(b => !imgBroken.includes(b) && !cssBroken.includes(b)),
    consoleErrs, pageErrs, screenshot: shot.replace(OUT + '/', '') });
  await page.close();
  process.stderr.write(`. ${url} [${status}] img404=${imgBroken.length} css404=${cssBroken.length} jsErr=${pageErrs.length}\n`);
}
await browser.close();

writeFileSync(resolve(OUT, 'report.json'), JSON.stringify({ base: BASE, count: results.length, results }, null, 2));

// Markdown summary, problems first.
const flagged = results.filter(r => r.brokenImages.length || r.brokenCss.length || r.pageErrs.length || r.status >= 400);
let md = `# Museum QA crawl — ${BASE}\n\nPages crawled: **${results.length}** · Flagged: **${flagged.length}**\n\n`;
md += `## Flagged pages\n\n`;
if (!flagged.length) md += `None — no broken images, broken CSS, or JS exceptions detected.\n\n`;
for (const r of flagged) {
  md += `### ${r.url} ${r.status >= 400 ? `(HTTP ${r.status})` : ''}\n`;
  if (r.brokenCss.length) md += `- ⛔ **Broken CSS (${r.brokenCss.length})** — likely unstyled:\n` + r.brokenCss.map(b => `  - ${b.url} — ${b.reason}`).join('\n') + '\n';
  if (r.brokenImages.length) md += `- 🖼️ **Broken images (${r.brokenImages.length})**:\n` + r.brokenImages.slice(0, 25).map(b => `  - ${b.url} — ${b.reason}`).join('\n') + (r.brokenImages.length > 25 ? `\n  - …and ${r.brokenImages.length - 25} more` : '') + '\n';
  if (r.pageErrs.length) md += `- 💥 **JS exceptions (${r.pageErrs.length})**:\n` + r.pageErrs.map(e => `  - ${e}`).join('\n') + '\n';
  if (r.otherBroken.length) md += `- ⚠️ Other failed requests (${r.otherBroken.length}): ` + r.otherBroken.slice(0, 8).map(b => b.url + ' (' + b.reason + ')').join(', ') + '\n';
  md += `- 📷 \`${r.screenshot}\`\n\n`;
}
md += `## All pages\n\n| Page | HTTP | img404 | css404 | jsErr | console |\n|---|---|---|---|---|---|\n`;
for (const r of results) md += `| ${new URL(r.url).pathname} | ${r.status} | ${r.brokenImages.length} | ${r.brokenCss.length} | ${r.pageErrs.length} | ${r.consoleErrs.length} |\n`;
writeFileSync(resolve(OUT, 'report.md'), md);
console.log(`\nWrote ${OUT}/report.md and report.json — ${flagged.length}/${results.length} pages flagged.`);
