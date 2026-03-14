const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const viewports = [
    { name: 'mobile-375', width: 375, height: 812 },
    { name: 'tablet-768', width: 768, height: 1024 },
    { name: 'desktop-1280', width: 1280, height: 900 }
  ];

  const pageUrl = 'http://localhost:5000/';

  for (const viewport of viewports) {
    console.log(`\n--- ${viewport.name} ---`);

    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto(pageUrl, { waitUntil: 'networkidle' });

    // Screenshot 1: Closed state — FAB visible
    await page.waitForSelector('#chatbot-fab', { state: 'visible', timeout: 5000 });
    await page.screenshot({
      path: `screenshots/bug287/closed-${viewport.name}.png`
    });
    console.log(`✓ closed-${viewport.name}.png (FAB visible)`);

    // Open chatbot
    await page.click('#chatbot-fab');
    await page.waitForSelector('#chatbot-panel', { state: 'visible', timeout: 5000 });
    await page.waitForTimeout(400);

    // Screenshot 2: Expanded state — FAB hidden, close button visible
    await page.screenshot({
      path: `screenshots/bug287/expanded-${viewport.name}.png`
    });
    console.log(`✓ expanded-${viewport.name}.png (FAB hidden, close button visible)`);
  }

  await browser.close();
  console.log('\nAll bug #287 screenshots complete!');
})();
