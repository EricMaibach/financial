/**
 * Screenshots for US-258.3: Sentence-level drill-in — desktop text selection toolbar
 *
 * Required screenshots:
 *   desktop-1280-toolbar-visible.png  — floating toolbar above a text selection in briefing block
 *   desktop-1280-hint.png             — discoverability hint visible below briefing card
 *   desktop-1280-chatbot-open.png     — chatbot open with selected text + typing indicator
 *   mobile-375-hint.png               — mobile hint copy visible; toolbar NOT present
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5000';
const OUT_DIR = path.join(__dirname, 'screenshots', 'us263');

const STUB_BRIEFING_HTML = `
<p>Global equities faced broad selling pressure as the Federal Reserve signaled a more
cautious approach to rate cuts amid sticky services inflation. Treasury yields rose across
the curve, with the 10-year touching 4.65%, pressuring growth and technology stocks.</p>
<p>Credit spreads widened modestly, reflecting a risk-off tone heading into month-end.
Commodity markets saw mixed action: oil gained on OPEC supply discipline while gold
retreated from recent highs as the dollar strengthened on safe-haven demand.</p>
`;

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch();

  // ─── 1. desktop-1280-toolbar-visible.png ──────────────────────────────────
  // The toolbar is position:fixed so it only appears in viewport screenshots.
  // We scroll the briefing section into view, then manually show + position
  // the toolbar using viewport-relative coordinates.
  {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });

    // Scroll the briefing section into view
    const briefingSection = page.locator('#briefing-section');
    await briefingSection.scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);

    // Get briefing section bounding box so we know where it sits in the viewport
    const sectionBox = await briefingSection.boundingBox();

    // Show the toolbar positioned over the first paragraph of the briefing,
    // using viewport-relative coordinates (correct for position:fixed elements).
    await page.evaluate((box) => {
      const narrative = document.getElementById('briefing-narrative');
      const toolbar = document.getElementById('ai-briefing-toolbar');
      if (!narrative || !toolbar) return;

      const firstP = narrative.querySelector('p');
      const targetRect = firstP ? firstP.getBoundingClientRect() : null;

      // Use first paragraph rect if available, otherwise use section top
      const refTop = targetRect ? targetRect.top : (box ? box.y : 200);
      const refLeft = targetRect ? targetRect.left : (box ? box.x : 40);
      const refWidth = targetRect ? targetRect.width : (box ? box.width : 900);

      const toolbarW = 180;
      const toolbarH = 34;

      // Position: viewport-relative (no scrollY offset — toolbar is fixed)
      const midX = refLeft + refWidth / 2;
      const topY = refTop + 40; // Place within the paragraph area, slightly below top
      const leftX = Math.max(8, Math.min(midX - toolbarW / 2, window.innerWidth - toolbarW - 8));

      toolbar.style.left = leftX + 'px';
      toolbar.style.top = topY + 'px';
      toolbar.classList.add('is-visible');

      // Add a highlight span around first ~8 words to show "selected" text
      if (firstP) {
        const text = firstP.textContent || '';
        const words = text.trim().split(/\s+/);
        const snippet = words.slice(0, 8).join(' ');
        if (snippet) {
          firstP.innerHTML = firstP.innerHTML.replace(
            snippet,
            `<mark style="background:rgba(99,102,241,0.18);border-radius:2px;padding:0 1px">${snippet}</mark>`
          );
        }
      }
    }, sectionBox);

    await page.waitForTimeout(150);

    // Take a viewport-level screenshot clipped to the briefing section area
    // so the fixed-position toolbar is included
    await page.screenshot({
      path: path.join(OUT_DIR, 'desktop-1280-toolbar-visible.png'),
      clip: sectionBox
        ? { x: sectionBox.x, y: sectionBox.y, width: sectionBox.width, height: Math.min(sectionBox.height, 450) }
        : undefined,
    });

    await page.close();
  }

  // ─── 2. desktop-1280-hint.png ─────────────────────────────────────────────
  {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });

    // Inject stub briefing text for a more realistic view
    await page.evaluate((html) => {
      const el = document.getElementById('briefing-narrative');
      if (el) el.innerHTML = html;
    }, STUB_BRIEFING_HTML);

    const briefingSection = page.locator('#briefing-section');
    await briefingSection.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);

    // Ensure the hint row is visible (it always renders on desktop, but scroll to it)
    const hints = page.locator('.ai-briefing-hints');
    await hints.scrollIntoViewIfNeeded();
    await page.waitForTimeout(150);

    // Capture just the briefing section so the hint is prominent
    await briefingSection.screenshot({
      path: path.join(OUT_DIR, 'desktop-1280-hint.png'),
    });

    await page.close();
  }

  // ─── 3. desktop-1280-chatbot-open.png ────────────────────────────────────
  {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });

    // Inject stub briefing text
    await page.evaluate((html) => {
      const el = document.getElementById('briefing-narrative');
      if (el) el.innerHTML = html;
    }, STUB_BRIEFING_HTML);

    // Open the chatbot panel and simulate the Ask AI drill-in state:
    // — expand the panel
    // — inject a user message (the "selected" sentence)
    // — show the typing indicator
    await page.evaluate(() => {
      const fab = document.getElementById('chatbot-fab');
      const panel = document.getElementById('chatbot-panel');
      const messages = panel ? panel.querySelector('.chatbot-messages') : null;
      if (!panel || !messages) return;

      // Expand chatbot
      if (fab) fab.setAttribute('aria-expanded', 'true');
      panel.setAttribute('aria-hidden', 'false');

      // Hide empty state
      const emptyState = messages.querySelector('.chatbot-empty-state');
      if (emptyState) emptyState.style.display = 'none';

      // Add user message (the "selected" sentence)
      const userMsg = document.createElement('div');
      userMsg.className = 'chatbot-message chatbot-message--user';
      userMsg.innerHTML = `
        <span class="chatbot-message-label sr-only">You said:</span>
        <p class="chatbot-message-text">Treasury yields rose across the curve, with the 10-year touching 4.65%, pressuring growth and technology stocks.</p>
      `;
      messages.appendChild(userMsg);

      // Show typing indicator
      const indicator = document.createElement('div');
      indicator.className = 'chatbot-typing';
      indicator.setAttribute('aria-label', 'AI is typing');
      indicator.innerHTML = `
        <span class="chatbot-typing-dot"></span>
        <span class="chatbot-typing-dot"></span>
        <span class="chatbot-typing-dot"></span>
      `;
      messages.appendChild(indicator);
    });

    await page.waitForTimeout(200);

    // Screenshot the chatbot panel
    const chatbotPanel = page.locator('#chatbot-panel');
    await chatbotPanel.screenshot({
      path: path.join(OUT_DIR, 'desktop-1280-chatbot-open.png'),
    });

    await page.close();
  }

  // ─── 4. mobile-375-hint.png ───────────────────────────────────────────────
  // Use 375px viewport. Inject CSS overrides to simulate pointer:coarse rules
  // (hides desktop hint, shows mobile hint, hides toolbar) without using
  // isMobile/hasTouch which triggers the mobile nav sheet overlay.
  {
    const page = await browser.newPage({ viewport: { width: 375, height: 812 } });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });

    // Inject CSS that replicates @media (pointer: coarse) behavior,
    // and hides the mobile nav sheet so it doesn't cover the briefing section.
    await page.addStyleTag({
      content: `
        .ai-briefing-toolbar { display: none !important; }
        .ai-briefing-hint--desktop { display: none !important; }
        .ai-briefing-hint--mobile { display: flex !important; }
        .section-quick-nav-sheet { display: none !important; }
        .section-quick-nav-sheet-backdrop { display: none !important; }
      `,
    });

    // Take a full-page screenshot scrolled to show the hints area.
    // Since the briefing section is long, we capture the area around the hint
    // by taking a full-page screenshot and then cropping to the hints area.
    await page.waitForTimeout(300);

    // Get the bounding box of the hints relative to the full page
    const hintsBox = await page.locator('.ai-briefing-hints').boundingBox();
    const hintsFullY = hintsBox ? hintsBox.y : 0;

    await page.screenshot({
      path: path.join(OUT_DIR, 'mobile-375-hint.png'),
      fullPage: true,
      clip: hintsBox
        ? {
            x: 0,
            y: Math.max(0, hintsFullY - 120),
            width: 375,
            height: hintsBox.height + 160,
          }
        : undefined,
    });

    await page.close();
  }

  await browser.close();
  console.log('US-263 screenshots written to screenshots/us263/');
})();
