const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5000';
const OUT_DIR = path.join(__dirname, 'screenshots', 'us267');

const VIEWPORTS = [
  { name: 'mobile-375', width: 375, height: 812 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'desktop-1280', width: 1280, height: 900 },
];

test.beforeAll(() => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
});

for (const vp of VIEWPORTS) {
  test(`News page frontend at ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });

    // News page: empty state (no pipeline data yet)
    await page.goto(`${BASE_URL}/news`, { waitUntil: 'domcontentloaded' });
    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-news-empty-state.png`),
      fullPage: true,
    });

    // Inject stub data into the DOM to show summary card + source cards layout
    // (simulates what the page looks like when pipeline has run)
    await page.evaluate(() => {
      const container = document.querySelector('.news-page');
      if (!container) return;

      const header = container.querySelector('.news-header');
      // Remove empty state
      const emptyState = container.querySelector('.news-empty-state');
      if (emptyState) emptyState.remove();

      // Build two-column layout with stub data
      const layout = document.createElement('div');
      layout.className = 'news-layout';

      layout.innerHTML = `
        <section class="news-summary-card" role="region" aria-label="AI-generated news summary">
          <h2 class="news-summary-card__label">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false"
                 style="display:inline-block;vertical-align:middle;margin-right:4px">
              <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6L12 2z" fill="currentColor"/>
            </svg>
            AI Summary
          </h2>
          <div class="news-summary-card__body">
            <p>Global equities faced broad selling pressure as the Federal Reserve signaled
            a more cautious approach to rate cuts amid sticky services inflation.
            Treasury yields rose across the curve, with the 10-year touching 4.65%, pressuring
            growth and technology stocks. Credit spreads widened modestly, reflecting a
            risk-off tone heading into month-end. Commodity markets saw mixed action: oil
            gained on OPEC supply discipline while gold retreated from recent highs as the
            dollar strengthened.</p>
          </div>
          <div class="news-summary-card__footer">
            Generated from 8 sources
          </div>
        </section>
        <section class="news-sources" aria-label="Source articles">
          <h2 class="news-sources__label">Sources (8)</h2>
          <div class="news-sources__list">
            ${[
              { headline: 'Fed signals caution on rate cuts as inflation proves sticky', domain: 'reuters.com', time: '2h ago' },
              { headline: 'Treasury yields climb to 4.65% on strong jobs data', domain: 'ft.com', time: '3h ago' },
              { headline: 'S&amp;P 500 falls as risk-off sentiment grips markets', domain: 'bloomberg.com', time: '4h ago' },
              { headline: 'OPEC holds firm on output, supporting oil prices', domain: 'wsj.com', time: '5h ago' },
              { headline: 'Dollar strengthens as safe-haven demand rises', domain: 'marketwatch.com', time: '6h ago' },
            ].map(s => `
              <a class="news-source-card" href="#" target="_blank" rel="noopener noreferrer"
                 aria-label="Read: ${s.headline} (opens in new tab)">
                <div class="news-source-card__content">
                  <span class="news-source-card__headline">${s.headline}</span>
                  <span class="news-source-card__meta">${s.domain} · ${s.time}</span>
                </div>
                <i class="bi bi-arrow-up-right news-source-card__arrow" aria-hidden="true"></i>
              </a>
            `).join('')}
          </div>
        </section>
      `;

      // Insert after header
      if (header && header.nextSibling) {
        container.insertBefore(layout, header.nextSibling);
      } else {
        container.appendChild(layout);
      }
    });

    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-news-with-summary.png`),
      fullPage: true,
    });

    // Stale banner state
    await page.evaluate(() => {
      const page_el = document.querySelector('.news-page');
      if (!page_el) return;
      const header = page_el.querySelector('.news-header');
      const banner = document.createElement('div');
      banner.className = 'news-stale-banner';
      banner.setAttribute('role', 'alert');
      banner.innerHTML = '<i class="bi bi-exclamation-triangle-fill" aria-hidden="true"></i> Showing news from March 11, 2026 — today\'s fetch is unavailable.';
      if (header && header.nextSibling) {
        page_el.insertBefore(banner, header.nextSibling);
      }
    });

    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-news-stale-banner.png`),
      fullPage: false,
    });
  });
}

// "News unavailable" empty state (is_stale=True, summary_text=None — no prior data exists)
// Captured at desktop-1280 only (one breakpoint sufficient per designer feedback)
test('News page — wifi-off empty state at desktop-1280', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(`${BASE_URL}/news`, { waitUntil: 'domcontentloaded' });

  // Replace the existing empty state content with the wifi-off state markup
  // (mirrors the {% elif is_stale %} branch in news.html)
  await page.evaluate(() => {
    const container = document.querySelector('.news-page');
    if (!container) return;

    // Remove any existing main content / empty states
    const toRemove = container.querySelectorAll('.news-empty-state, .news-layout');
    toRemove.forEach(el => el.remove());

    const unavailableState = document.createElement('div');
    unavailableState.className = 'news-empty-state';
    unavailableState.innerHTML = `
      <i class="bi bi-wifi-off news-empty-state__icon" aria-hidden="true"></i>
      <h2 class="news-empty-state__heading">News unavailable</h2>
      <p class="news-empty-state__body">
        We couldn't fetch today's news and have no prior summary to display.<br>
        The pipeline will retry automatically tomorrow.
      </p>
    `;
    container.appendChild(unavailableState);
  });

  await page.screenshot({
    path: path.join(OUT_DIR, 'desktop-1280-news-unavailable.png'),
    fullPage: true,
  });
});
