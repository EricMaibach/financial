// Screenshots for US-238.3: Real Estate Summary Card
// Captures portfolio page at 3 viewports: empty state and with real estate holdings
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5000';
const OUT_DIR = path.join(__dirname, 'screenshots', 'us247');

async function login(page) {
    await page.goto(BASE_URL + '/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL(BASE_URL + '/');
}

async function run() {
    const browser = await chromium.launch();

    const viewports = [
        { name: 'mobile-375', width: 375, height: 812 },
        { name: 'tablet-768', width: 768, height: 1024 },
        { name: 'desktop-1280', width: 1280, height: 900 },
    ];

    for (const vp of viewports) {
        const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
        const page = await context.newPage();

        await login(page);
        await page.goto(BASE_URL + '/portfolio');
        await page.waitForLoadState('networkidle');

        // Empty state: real estate card shows 0% / No real estate holdings
        await page.screenshot({
            path: path.join(OUT_DIR, `${vp.name}-portfolio-empty.png`),
            fullPage: true,
        });

        await context.close();
    }

    // Desktop with real estate holdings injected via API
    const context2 = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page2 = await context2.newPage();
    await login(page2);
    await page2.goto(BASE_URL + '/portfolio');
    await page2.waitForLoadState('networkidle');

    // Inject three real estate holdings via the add-holding modal sequence
    // Use the JS console to POST directly for speed
    await page2.evaluate(async () => {
        const post = (data) => fetch('/api/portfolio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        await post({ asset_type: 'farmland', name: 'My Farm', symbol: '', percentage: 12 });
        await post({ asset_type: 'commercial_real_estate', name: 'Office Park', symbol: '', percentage: 5 });
        await post({ asset_type: 'residential_real_estate', name: 'Rental Home', symbol: '', percentage: 5 });
    });

    // Reload to get updated data
    await page2.reload();
    await page2.waitForLoadState('networkidle');

    await page2.screenshot({
        path: path.join(OUT_DIR, 'desktop-1280-with-real-estate.png'),
        fullPage: true,
    });

    await context2.close();
    await browser.close();
    console.log('Screenshots saved to', OUT_DIR);
}

run().catch(err => { console.error(err); process.exit(1); });
