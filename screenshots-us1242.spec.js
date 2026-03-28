const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:5000';
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots', 'us1242');

test.beforeAll(() => {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
});

test.describe('US-12.4.2: Rate limit redirect screenshots', () => {

  test('chatbot rate limit - per-session (desktop)', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(BASE_URL + '/', { waitUntil: 'networkidle' });

    // Open chatbot
    await page.click('#chatbot-fab');
    await page.waitForSelector('#chatbot-panel', { state: 'visible', timeout: 5000 });
    await page.waitForTimeout(500);

    // Inject rate limit message via the widget's own method
    await page.evaluate(() => {
      const widget = document.querySelector('#chatbot-panel')?.__chatbot
        || window.__chatbotInstance;
      if (widget && widget.showRateLimitError) {
        widget.showRateLimitError(
          "You've reached the free message limit for this session. Sign up for a free account to continue using AI features.",
          '/register'
        );
      } else {
        // Fallback: inject DOM directly
        const messages = document.querySelector('.chatbot-messages');
        if (messages) {
          const el = document.createElement('div');
          el.className = 'chatbot-message chatbot-message--error chatbot-message--rate-limit';
          el.innerHTML = `
            <span aria-hidden="true">⚡</span>
            <div>
              <p style="margin:0">You've reached the free message limit for this session. Sign up for a free account to continue using AI features.</p>
              <a href="/register" class="chatbot-signup-cta">Sign up free</a>
            </div>
          `;
          messages.appendChild(el);
        }
      }
    });
    await page.waitForTimeout(300);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'chatbot-session-limit-desktop.png'),
      fullPage: false
    });
  });

  test('chatbot rate limit - global daily cap (desktop)', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(BASE_URL + '/', { waitUntil: 'networkidle' });

    await page.click('#chatbot-fab');
    await page.waitForSelector('#chatbot-panel', { state: 'visible', timeout: 5000 });
    await page.waitForTimeout(500);

    await page.evaluate(() => {
      const messages = document.querySelector('.chatbot-messages');
      if (messages) {
        const el = document.createElement('div');
        el.className = 'chatbot-message chatbot-message--error chatbot-message--rate-limit';
        el.innerHTML = `
          <span aria-hidden="true">⚡</span>
          <div>
            <p style="margin:0">AI features are temporarily unavailable due to high demand. Sign up for a free account to get higher limits.</p>
            <a href="/register" class="chatbot-signup-cta">Sign up free</a>
          </div>
        `;
        messages.appendChild(el);
      }
    });
    await page.waitForTimeout(300);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'chatbot-global-cap-desktop.png'),
      fullPage: false
    });
  });

  test('section AI rate limit inline message', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    // Navigate to a category page with section AI
    await page.goto(BASE_URL + '/rates', { waitUntil: 'networkidle' });

    // Open chatbot and trigger a section AI rate limit
    await page.click('#chatbot-fab');
    await page.waitForSelector('#chatbot-panel', { state: 'visible', timeout: 5000 });
    await page.waitForTimeout(500);

    await page.evaluate(() => {
      const messages = document.querySelector('.chatbot-messages');
      if (messages) {
        const el = document.createElement('div');
        el.className = 'chatbot-message chatbot-message--error chatbot-message--rate-limit';
        el.innerHTML = `
          <span aria-hidden="true">⚡</span>
          <div>
            <p style="margin:0">You've reached the free message limit for this session. Sign up for a free account to continue using AI features.</p>
            <a href="/register" class="chatbot-signup-cta">Sign up free</a>
          </div>
        `;
        messages.appendChild(el);
      }
    });
    await page.waitForTimeout(300);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'section-ai-rate-limit-desktop.png'),
      fullPage: false
    });
  });

  test('portfolio rate limit message', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });

    // Login first — portfolio requires authentication
    await page.goto(BASE_URL + '/login');
    await page.fill('input[name=username]', 'testuser');
    await page.fill('input[name=password]', 'testpassword');
    await page.click('button[type=submit]');
    await page.waitForLoadState('networkidle');

    await page.goto(BASE_URL + '/portfolio', { waitUntil: 'networkidle' });

    // Inject registered-user rate limit message (no signup CTA — they already have an account)
    await page.evaluate(() => {
      const contentDiv = document.getElementById('portfolio-summary-content');
      if (contentDiv) {
        contentDiv.innerHTML = '<p class="text-warning mb-0"><i class="bi bi-exclamation-triangle"></i> You\'ve reached your daily AI analysis limit. Your limit resets tomorrow at midnight UTC.</p>';
        contentDiv.classList.remove('d-none');
        const errorDiv = document.getElementById('portfolio-summary-error');
        if (errorDiv) errorDiv.classList.add('d-none');
      }
    });
    await page.waitForTimeout(300);

    // Scroll to portfolio summary section
    await page.evaluate(() => {
      const el = document.getElementById('portfolio-summary-content');
      if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
    });
    await page.waitForTimeout(200);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'portfolio-rate-limit-desktop.png'),
      fullPage: false
    });
  });

  test('chatbot disabled input state', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(BASE_URL + '/', { waitUntil: 'networkidle' });

    await page.click('#chatbot-fab');
    await page.waitForSelector('#chatbot-panel', { state: 'visible', timeout: 5000 });
    await page.waitForTimeout(500);

    // Inject rate limit + disable input
    await page.evaluate(() => {
      const messages = document.querySelector('.chatbot-messages');
      if (messages) {
        const el = document.createElement('div');
        el.className = 'chatbot-message chatbot-message--error chatbot-message--rate-limit';
        el.innerHTML = `
          <span aria-hidden="true">⚡</span>
          <div>
            <p style="margin:0">You've reached the free message limit for this session. Sign up for a free account to continue using AI features.</p>
            <a href="/register" class="chatbot-signup-cta">Sign up free</a>
          </div>
        `;
        messages.appendChild(el);
      }
      // Disable input
      const input = document.querySelector('.chatbot-input');
      if (input) {
        input.disabled = true;
        input.placeholder = 'Session limit reached';
      }
      const submitBtn = document.querySelector('.chatbot-submit');
      if (submitBtn) submitBtn.disabled = true;
    });
    await page.waitForTimeout(300);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'chatbot-disabled-input-desktop.png'),
      fullPage: false
    });
  });

  test('chatbot rate limit - mobile (375px)', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(BASE_URL + '/', { waitUntil: 'networkidle' });

    await page.click('#chatbot-fab');
    await page.waitForSelector('#chatbot-panel', { state: 'visible', timeout: 5000 });
    await page.waitForTimeout(500);

    await page.evaluate(() => {
      const messages = document.querySelector('.chatbot-messages');
      if (messages) {
        const el = document.createElement('div');
        el.className = 'chatbot-message chatbot-message--error chatbot-message--rate-limit';
        el.innerHTML = `
          <span aria-hidden="true">⚡</span>
          <div>
            <p style="margin:0">You've reached the free message limit for this session. Sign up for a free account to continue using AI features.</p>
            <a href="/register" class="chatbot-signup-cta">Sign up free</a>
          </div>
        `;
        messages.appendChild(el);
      }
      const input = document.querySelector('.chatbot-input');
      if (input) {
        input.disabled = true;
        input.placeholder = 'Session limit reached';
      }
      const submitBtn = document.querySelector('.chatbot-submit');
      if (submitBtn) submitBtn.disabled = true;
    });
    await page.waitForTimeout(300);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'chatbot-rate-limit-mobile.png'),
      fullPage: false
    });
  });

});
