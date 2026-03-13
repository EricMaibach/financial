const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5000';
const OUT_DIR = path.join(__dirname, 'screenshots', 'us268');

const VIEWPORTS = [
  { name: 'mobile-375', width: 375, height: 812 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'desktop-1280', width: 1280, height: 900 },
];

test.beforeAll(() => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
});

// Navbar — Property link visible in Markets dropdown
for (const vp of VIEWPORTS) {
  test(`Navbar Property link at ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });

    if (vp.width >= 992) {
      // Desktop (lg+): hover the Markets dropdown to reveal Property link
      const marketsDropdown = page.locator('.nav-item.dropdown').filter({ hasText: 'Markets' }).first();
      await marketsDropdown.hover();
      await page.waitForTimeout(300);
    } else {
      // Mobile/tablet (< lg): open the hamburger menu, then expand Markets
      const toggler = page.locator('.navbar-toggler').first();
      if (await toggler.isVisible()) {
        await toggler.click();
        await page.waitForTimeout(400);
        // Expand the Markets dropdown inside the collapsed nav
        const marketsToggle = page.locator('.nav-item.dropdown').filter({ hasText: 'Markets' }).locator('.dropdown-toggle').first();
        if (await marketsToggle.isVisible()) {
          await marketsToggle.click();
          await page.waitForTimeout(300);
        }
      }
    }

    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-navbar-property-link.png`),
      fullPage: false,
    });
  });
}

// Property page — empty/unavailable state (no FRED data fetched yet)
for (const vp of VIEWPORTS) {
  test(`Property page empty state at ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.goto(`${BASE_URL}/property`, { waitUntil: 'domcontentloaded' });
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

    await page.evaluate(() => {
      // Inject HPI card data
      const hpiCards = document.querySelectorAll('.col-12.col-md-6');
      if (hpiCards.length >= 1) {
        const hpiCard = hpiCards[0].querySelector('.p-3');
        if (hpiCard) {
          const unavail = hpiCard.querySelector('.text-muted');
          if (unavail && unavail.textContent.trim() === 'Data unavailable') {
            unavail.remove();
          }
          const label = hpiCard.querySelector('.text-uppercase');
          if (label) {
            const valueEl = document.createElement('div');
            valueEl.className = 'mt-1';
            valueEl.style.cssText = 'font-size: 2rem; font-family: monospace; font-weight: 600;';
            valueEl.textContent = '318.7';

            const badgeEl = document.createElement('div');
            badgeEl.className = 'mt-1';
            badgeEl.innerHTML = '<span class="badge bg-success">▲ 4.2% YoY</span>';

            const progressEl = document.createElement('div');
            progressEl.className = 'mt-2';
            progressEl.innerHTML = `
              <div class="progress" style="height: 8px;" role="progressbar"
                   aria-valuenow="72" aria-valuemin="0" aria-valuemax="100"
                   aria-label="Case-Shiller HPI at 72nd percentile">
                <div class="progress-bar" style="width: 72%; background-color: #198754;"></div>
              </div>
              <div class="text-muted mt-1" style="font-size: 0.75rem;">72nd percentile · Elevated</div>
            `;

            const dateEl = document.createElement('div');
            dateEl.className = 'text-muted mt-2';
            dateEl.style.fontSize = '0.75rem';
            dateEl.textContent = 'Jan 2026';

            label.after(valueEl);
            valueEl.after(badgeEl);
            badgeEl.after(progressEl);
            progressEl.after(dateEl);
          }
        }
      }

      // Inject CPI Rent card data
      if (hpiCards.length >= 2) {
        const rentCard = hpiCards[1].querySelector('.p-3');
        if (rentCard) {
          const unavail = rentCard.querySelector('.text-muted');
          if (unavail && unavail.textContent.trim() === 'Data unavailable') {
            unavail.remove();
          }
          const label = rentCard.querySelector('.text-uppercase');
          if (label) {
            const valueEl = document.createElement('div');
            valueEl.className = 'mt-1';
            valueEl.style.cssText = 'font-size: 2rem; font-family: monospace; font-weight: 600;';
            valueEl.textContent = '+5.1%';

            const subEl = document.createElement('div');
            subEl.className = 'mt-1 text-muted';
            subEl.style.fontSize = '0.75rem';
            subEl.textContent = 'YoY change';

            const progressEl = document.createElement('div');
            progressEl.className = 'mt-2';
            progressEl.innerHTML = `
              <div class="progress" style="height: 8px;" role="progressbar"
                   aria-valuenow="81" aria-valuemin="0" aria-valuemax="100"
                   aria-label="CPI Rent at 81st percentile">
                <div class="progress-bar" style="width: 81%; background-color: #198754;"></div>
              </div>
              <div class="text-muted mt-1" style="font-size: 0.75rem;">81st percentile · Elevated</div>
            `;

            const dateEl = document.createElement('div');
            dateEl.className = 'text-muted mt-2';
            dateEl.style.fontSize = '0.75rem';
            dateEl.textContent = 'Jan 2026';

            label.after(valueEl);
            valueEl.after(subEl);
            subEl.after(progressEl);
            progressEl.after(dateEl);
          }
        }
      }

      // Inject Vacancy Rate data
      const vacancyCards = document.querySelectorAll('.card-body .p-3.border.border-secondary.rounded.d-inline-block');
      if (vacancyCards.length >= 1) {
        const vacCard = vacancyCards[0];
        const unavail = vacCard.querySelector('.text-muted');
        if (unavail && unavail.textContent.trim() === 'Data unavailable') {
          unavail.remove();
          const label = vacCard.querySelector('.text-uppercase');
          if (label) {
            const valueEl = document.createElement('div');
            valueEl.className = 'mt-1';
            valueEl.style.cssText = 'font-size: 2rem; font-family: monospace; font-weight: 600;';
            valueEl.textContent = '6.4%';

            const badgeEl = document.createElement('div');
            badgeEl.className = 'mt-1';
            badgeEl.innerHTML = '<span class="badge bg-warning text-dark">▼ Tightening (was 6.8% prior)</span>';

            const progressEl = document.createElement('div');
            progressEl.className = 'mt-2';
            progressEl.innerHTML = `
              <div class="progress" style="height: 8px;" role="progressbar"
                   aria-valuenow="64" aria-valuemin="0" aria-valuemax="100"
                   aria-label="Vacancy Rate at 64th percentile">
                <div class="progress-bar" style="width: 64%; background-color: #adb5bd;"></div>
              </div>
              <div class="text-muted mt-1" style="font-size: 0.75rem;">64th percentile · Moderate</div>
            `;

            const dateEl = document.createElement('div');
            dateEl.className = 'text-muted mt-2';
            dateEl.style.fontSize = '0.75rem';
            dateEl.textContent = 'Q4 2025 · Quarterly';

            label.after(valueEl);
            valueEl.after(badgeEl);
            badgeEl.after(progressEl);
            progressEl.after(dateEl);
          }
        }
      }

      // Inject Farmland data (second d-inline-block card)
      if (vacancyCards.length >= 2) {
        const farmCard = vacancyCards[1];
        const unavail = farmCard.querySelector('.text-muted');
        if (unavail && unavail.textContent.includes('Data unavailable')) {
          unavail.remove();
          const label = farmCard.querySelector('.text-uppercase');
          if (label) {
            const dlEl = document.createElement('dl');
            dlEl.className = 'mt-2 mb-0';
            dlEl.innerHTML = `
              <div class="d-flex gap-3">
                <dt class="text-muted" style="font-size: 0.875rem; min-width: 100px;">Farm RE:</dt>
                <dd class="mb-0" style="font-family: monospace; font-weight: 600;">$4,080</dd>
              </div>
              <div class="d-flex gap-3">
                <dt class="text-muted" style="font-size: 0.875rem; min-width: 100px;">Cropland:</dt>
                <dd class="mb-0" style="font-family: monospace; font-weight: 600;">$6,420</dd>
              </div>
              <div class="d-flex gap-3">
                <dt class="text-muted" style="font-size: 0.875rem; min-width: 100px;">Pasture:</dt>
                <dd class="mb-0" style="font-family: monospace; font-weight: 600;">$1,650</dd>
              </div>
            `;

            const badgeEl = document.createElement('div');
            badgeEl.className = 'mt-2';
            badgeEl.innerHTML = '<span class="badge bg-success">▲ +5.8% YoY (Farm RE)</span>';

            const dateEl = document.createElement('div');
            dateEl.className = 'text-muted mt-2';
            dateEl.style.fontSize = '0.75rem';
            dateEl.textContent = '2025 · Annual';

            label.after(dlEl);
            dlEl.after(badgeEl);
            badgeEl.after(dateEl);
          }
        }
      }

      // Inject regime interpretation block if not present
      const existingInterp = document.querySelector('[style*="border-left: 4px solid var(--category-color)"]');
      if (!existingInterp) {
        const container = document.querySelector('.container-fluid');
        if (container) {
          const interpDiv = document.createElement('div');
          interpDiv.className = 'mb-4';
          interpDiv.style.cssText = 'border-left: 4px solid #8B5CF6; background: rgba(255,255,255,0.04); border-radius: 0 8px 8px 0; padding: 1rem 1.25rem;';
          interpDiv.innerHTML = `
            <div class="text-uppercase text-muted mb-2" style="font-size: 0.75rem; letter-spacing: 0.1em;">
              <i class="bi bi-lightbulb" aria-hidden="true"></i>
              Property Macro Outlook
              <span class="ms-2 badge bg-secondary" style="font-size: 0.65rem;">Neutral</span>
            </div>
            <p class="mb-0" style="font-size: 0.875rem; line-height: 1.6;">
              In a neutral macro regime with HPI still appreciating at a moderate pace,
              real estate remains resilient but momentum is slowing. Elevated CPI rent
              is providing floor support for housing prices. Tightening vacancy rates
              suggest rental demand remains firm despite rate headwinds. Monitor for
              further deceleration in HPI as mortgage affordability constraints persist.
            </p>
          `;
          container.appendChild(interpDiv);
        }
      }
    });

    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-property-with-data.png`),
      fullPage: true,
    });
  });
}
