const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5000';
const OUT_DIR = path.join(__dirname, 'screenshots', 'us269');

const VIEWPORTS = [
  { name: 'mobile-375', width: 375, height: 812 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'desktop-1280', width: 1280, height: 900 },
];

test.beforeAll(() => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
});

// Property page — empty/unavailable state
for (const vp of VIEWPORTS) {
  test(`Property page empty state at ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.goto(`${BASE_URL}/property`, { waitUntil: 'domcontentloaded' });
    // Wait for JS to run (expand sections on tablet+)
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-property-empty.png`),
      fullPage: true,
    });
  });
}

// Property page — with realistic stub data injected into the DOM
for (const vp of VIEWPORTS) {
  test(`Property page with data at ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.goto(`${BASE_URL}/property`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(500);

    await page.evaluate(() => {
      // Helper: expand all sections for screenshot
      document.querySelectorAll('.property-section__toggle').forEach(toggle => {
        toggle.setAttribute('aria-expanded', 'true');
        const contentId = toggle.getAttribute('aria-controls');
        const content = document.getElementById(contentId);
        if (content) content.hidden = false;
      });

      // --- Inject HPI card data ---
      const residentialContent = document.getElementById('residential-content');
      if (residentialContent) {
        const cards = residentialContent.querySelectorAll('.property-metric-card');
        // HPI card
        if (cards[0]) {
          const card = cards[0];
          const unavail = card.querySelector('.property-metric-card__secondary');
          if (unavail && unavail.textContent.trim() === 'Data unavailable') {
            unavail.remove();
          }
          const label = card.querySelector('.property-metric-card__label');
          if (label) {
            label.insertAdjacentHTML('afterend', `
              <div class="property-metric-card__value">318.7</div>
              <div style="margin-top: 0.5rem;">
                <span class="property-badge property-badge--success">&#9650; +4.2% YoY</span>
              </div>
              <div class="property-pct-bar">
                <div class="property-pct-bar__track" role="progressbar"
                     aria-valuenow="72" aria-valuemin="0" aria-valuemax="100"
                     aria-label="Case-Shiller HPI at 72nd percentile">
                  <div class="property-pct-bar__fill property-pct-bar__fill--info" style="width: 72%;"></div>
                </div>
                <div class="property-pct-bar__label">72nd percentile · above median</div>
              </div>
              <div class="property-metric-card__secondary" style="margin-top: 0.75rem;">January 2026</div>
            `);
          }
        }
        // CPI Rent card
        if (cards[1]) {
          const card = cards[1];
          const unavail = card.querySelector('.property-metric-card__secondary');
          if (unavail && unavail.textContent.trim() === 'Data unavailable') {
            unavail.remove();
          }
          const label = card.querySelector('.property-metric-card__label');
          if (label) {
            label.insertAdjacentHTML('afterend', `
              <div class="property-metric-card__value">+3.8%</div>
              <div class="property-metric-card__secondary">YoY change</div>
              <div style="margin-top: 0.25rem;">
                <span class="property-badge property-badge--warning">&#9660; -0.1% MoM</span>
              </div>
              <div class="property-pct-bar">
                <div class="property-pct-bar__track" role="progressbar"
                     aria-valuenow="54" aria-valuemin="0" aria-valuemax="100"
                     aria-label="CPI Rent at 54th percentile">
                  <div class="property-pct-bar__fill property-pct-bar__fill--neutral" style="width: 54%;"></div>
                </div>
                <div class="property-pct-bar__label">54th percentile · near average</div>
              </div>
              <div class="property-metric-card__secondary" style="margin-top: 0.75rem;">January 2026</div>
            `);
          }
        }
      }

      // --- Inject Vacancy Rate data ---
      const rentalContent = document.getElementById('rental-content');
      if (rentalContent) {
        const card = rentalContent.querySelector('.property-metric-card');
        if (card) {
          const unavail = card.querySelector('.property-metric-card__secondary');
          if (unavail && unavail.textContent.trim() === 'Data unavailable') {
            unavail.remove();
          }
          const label = card.querySelector('.property-metric-card__label');
          if (label) {
            label.insertAdjacentHTML('afterend', `
              <div class="property-metric-card__value">6.2%</div>
              <div style="margin-top: 0.5rem;">
                <span class="property-badge property-badge--warning">&#9660; Tightening (was 6.8% prior qtr)</span>
              </div>
              <div class="property-pct-bar">
                <div class="property-pct-bar__track" role="progressbar"
                     aria-valuenow="22" aria-valuemin="0" aria-valuemax="100"
                     aria-label="Vacancy Rate at 22nd percentile">
                  <div class="property-pct-bar__fill property-pct-bar__fill--warning" style="width: 22%;"></div>
                </div>
                <div class="property-pct-bar__label">22nd percentile · tight rental supply</div>
              </div>
              <div class="property-metric-card__secondary" style="margin-top: 0.75rem;">Q4 2025 · Quarterly</div>
            `);
          }
        }
      }

      // --- Inject Farmland data ---
      const farmlandContent = document.getElementById('farmland-content');
      if (farmlandContent) {
        const card = farmlandContent.querySelector('.property-metric-card');
        if (card) {
          const unavail = card.querySelector('.property-metric-card__secondary');
          if (unavail && unavail.textContent.includes('Data unavailable')) {
            unavail.remove();
          }
          const label = card.querySelector('.property-metric-card__label');
          if (label) {
            label.insertAdjacentHTML('afterend', `
              <dl class="property-farmland-dl">
                <div class="property-farmland-dl__row">
                  <dt>Farm RE:</dt>
                  <dd>$4,080</dd>
                </div>
                <div class="property-farmland-dl__row">
                  <dt>Cropland:</dt>
                  <dd>$5,460</dd>
                </div>
                <div class="property-farmland-dl__row">
                  <dt>Pasture:</dt>
                  <dd>$1,650</dd>
                </div>
              </dl>
              <div style="margin-top: 0.75rem;">
                <span class="property-badge property-badge--success">&#9650; +5.1% YoY (Farm RE)</span>
              </div>
              <div class="property-metric-card__secondary" style="margin-top: 0.75rem;">2025 · Annual</div>
            `);
          }
        }
      }

      // --- Inject interpretation block ---
      const existingInterp = document.querySelector('.property-interpretation');
      if (!existingInterp) {
        const main = document.querySelector('.property-page');
        if (main) {
          const interpDiv = document.createElement('div');
          interpDiv.className = 'property-interpretation';
          interpDiv.innerHTML = `
            <div class="property-interpretation__header">
              <i class="bi bi-lightbulb" style="color: var(--category-color); font-size: 0.875rem;" aria-hidden="true"></i>
              <span class="property-interpretation__label">Property Macro Outlook</span>
              <span style="font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; background: #dee2e6; color: #495057;">bull</span>
            </div>
            <p class="property-interpretation__body">
              In a bull macro regime with HPI appreciating steadily, real estate benefits from
              strong economic conditions and rising consumer wealth. CPI rent remains elevated
              but moderating, consistent with healthy housing demand. Tight vacancy rates
              confirm rental supply constraints. Farmland values continue climbing, reflecting
              both agricultural demand and inflation hedging. Current conditions favor real
              asset exposure, though watch for signs of overheating if appreciation accelerates.
            </p>
          `;
          main.appendChild(interpDiv);
        }
      }
    });

    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-property-with-data.png`),
      fullPage: true,
    });
  });
}

// Mobile — collapsed sections
test('Mobile collapsed sections', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto(`${BASE_URL}/property`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(500);

  // Ensure sections are collapsed on mobile
  await page.evaluate(() => {
    document.querySelectorAll('.property-section__toggle').forEach(toggle => {
      toggle.setAttribute('aria-expanded', 'false');
      const contentId = toggle.getAttribute('aria-controls');
      const content = document.getElementById(contentId);
      if (content) content.hidden = true;
    });
  });

  await page.screenshot({
    path: path.join(OUT_DIR, 'mobile-375-sections-collapsed.png'),
    fullPage: true,
  });
});
