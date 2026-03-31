const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const viewports = [
    { name: 'mobile', width: 375, height: 667 },      // iPhone SE
    { name: 'tablet', width: 768, height: 1024 },     // iPad
    { name: 'desktop', width: 1920, height: 1080 }    // Desktop
  ];

  const baseUrl = 'http://localhost:5000';

  // Login required — anonymous users cannot see chatbot (US-13.2.2)
  await page.goto(`${baseUrl}/login`);
  await page.fill('input[name=username]', 'testuser');
  await page.fill('input[name=password]', 'testpassword');
  await page.click('button[type=submit]');
  await page.waitForURL(`${baseUrl}/`);

  for (const viewport of viewports) {
    console.log(`Capturing chatbot on ${viewport.name}...`);

    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto(`${baseUrl}/`);

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Click the chatbot FAB
    await page.click('#chatbot-fab');

    // Wait for chatbot panel to be visible
    await page.waitForSelector('#chatbot-panel', { state: 'visible', timeout: 5000 });

    // Wait a bit for any animations to complete
    await page.waitForTimeout(500);

    // Take screenshot
    await page.screenshot({
      path: `screenshots/chatbot-expanded-${viewport.name}.png`,
      fullPage: true
    });

    console.log(`✓ Chatbot screenshot saved: chatbot-expanded-${viewport.name}.png`);

    // Close chatbot for next iteration (if there's a close button)
    // If the page reloads between viewports, this isn't necessary
  }

  await browser.close();
  console.log('\nAll chatbot screenshots complete!');
})();
