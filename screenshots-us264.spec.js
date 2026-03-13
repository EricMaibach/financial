/**
 * Screenshots for US-258.4: Sentence-level drill-in — mobile tap flow
 *
 * Required screenshots:
 *   mobile-375-sentence-wrapped.png  — briefing text wrapped in ai-sentence spans (mobile view)
 *   mobile-375-amber-flash.png       — amber flash on a tapped sentence
 *   mobile-375-confirm-pill.png      — confirm pill appearing near a sentence
 *   mobile-375-chatbot-open.png      — chatbot open after confirm pill tap
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5000';
const OUT_DIR = path.join(__dirname, 'screenshots', 'us264');

const STUB_BRIEFING_HTML = `
<p>Global equities faced broad selling pressure as the Federal Reserve signaled a more
cautious approach to rate cuts amid sticky services inflation. Treasury yields rose across
the curve, with the 10-year touching 4.65%, pressuring growth and technology stocks.</p>
<p>Credit spreads widened modestly, reflecting a risk-off tone heading into month-end.
Commodity markets saw mixed action: oil gained on OPEC supply discipline while gold
retreated from recent highs as the dollar strengthened on safe-haven demand.</p>
`;

// Simulates pointer:coarse state via CSS injection so screenshots match mobile rendering.
async function addMobileOverrides(page) {
  await page.addStyleTag({
    content: `
      /* Replicate pointer:coarse media rules for screenshot */
      .ai-briefing-toolbar { display: none !important; }
      .ai-briefing-hint--desktop { display: none !important; }
      .ai-briefing-hint--mobile { display: flex !important; }
      /* Hide mobile nav sheet overlay if present */
      .section-quick-nav-sheet { display: none !important; }
      .section-quick-nav-sheet-backdrop { display: none !important; }
    `,
  });
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch();

  // ─── 1. mobile-375-sentence-wrapped.png ───────────────────────────────────
  // Shows briefing text wrapped in .ai-sentence spans — simulates what mobile
  // users see after ai-briefing-mobile.js has processed the content.
  {
    const page = await browser.newPage({ viewport: { width: 375, height: 812 } });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    await addMobileOverrides(page);

    // Inject stub briefing content and manually wrap into sentence spans
    await page.evaluate((html) => {
      const el = document.getElementById('briefing-narrative');
      if (!el) return;
      el.innerHTML = html;

      // Manually wrap sentences to simulate what ai-briefing-mobile.js does
      el.querySelectorAll('p').forEach((p) => {
        const text = p.textContent || '';
        const sentences = text.split(/(?<=[.!?])\s+(?=[A-Z])/);
        if (sentences.length <= 1) return;
        const frag = document.createDocumentFragment();
        sentences.forEach((s, i) => {
          const span = document.createElement('span');
          span.className = 'ai-sentence';
          span.style.cssText =
            'display: inline; cursor: pointer; border-radius: 4px; padding: 1px 0;';
          span.textContent = s.trim();
          frag.appendChild(span);
          if (i < sentences.length - 1) frag.appendChild(document.createTextNode(' '));
        });
        p.innerHTML = '';
        p.appendChild(frag);
      });

      // Make briefing-content visible
      const contentEl = document.getElementById('briefing-content');
      const loadingEl = document.getElementById('briefing-loading');
      if (contentEl) contentEl.style.display = 'block';
      if (loadingEl) loadingEl.style.display = 'none';
    }, STUB_BRIEFING_HTML);

    await page.waitForTimeout(300);

    const briefingSection = page.locator('#briefing-section');
    await briefingSection.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);

    const sectionBox = await briefingSection.boundingBox();
    await page.screenshot({
      path: path.join(OUT_DIR, 'mobile-375-sentence-wrapped.png'),
      clip: sectionBox
        ? { x: 0, y: sectionBox.y, width: 375, height: Math.min(sectionBox.height, 500) }
        : undefined,
    });
    await page.close();
  }

  // ─── 2. mobile-375-amber-flash.png ────────────────────────────────────────
  // Shows the amber background flash on a tapped sentence.
  {
    const page = await browser.newPage({ viewport: { width: 375, height: 812 } });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    await addMobileOverrides(page);

    await page.evaluate((html) => {
      const el = document.getElementById('briefing-narrative');
      if (!el) return;
      el.innerHTML = html;

      el.querySelectorAll('p').forEach((p) => {
        const text = p.textContent || '';
        const sentences = text.split(/(?<=[.!?])\s+(?=[A-Z])/);
        if (sentences.length <= 1) return;
        const frag = document.createDocumentFragment();
        sentences.forEach((s, i) => {
          const span = document.createElement('span');
          span.className = 'ai-sentence';
          span.style.cssText = 'display: inline; cursor: pointer; border-radius: 4px; padding: 1px 0;';
          span.textContent = s.trim();
          frag.appendChild(span);
          if (i < sentences.length - 1) frag.appendChild(document.createTextNode(' '));
        });
        p.innerHTML = '';
        p.appendChild(frag);
      });

      const contentEl = document.getElementById('briefing-content');
      const loadingEl = document.getElementById('briefing-loading');
      if (contentEl) contentEl.style.display = 'block';
      if (loadingEl) loadingEl.style.display = 'none';

      // Apply amber flash to the first sentence to simulate a tap
      const firstSentence = el.querySelector('.ai-sentence');
      if (firstSentence) {
        firstSentence.classList.add('is-flashing');
      }
    }, STUB_BRIEFING_HTML);

    await page.waitForTimeout(300);

    const briefingSection = page.locator('#briefing-section');
    await briefingSection.scrollIntoViewIfNeeded();
    await page.waitForTimeout(150);

    const sectionBox = await briefingSection.boundingBox();
    await page.screenshot({
      path: path.join(OUT_DIR, 'mobile-375-amber-flash.png'),
      clip: sectionBox
        ? { x: 0, y: sectionBox.y, width: 375, height: Math.min(sectionBox.height, 400) }
        : undefined,
    });
    await page.close();
  }

  // ─── 3. mobile-375-confirm-pill.png ──────────────────────────────────────
  // Shows confirm pill appearing near a tapped sentence.
  {
    const page = await browser.newPage({ viewport: { width: 375, height: 812 } });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    await addMobileOverrides(page);

    await page.evaluate((html) => {
      const el = document.getElementById('briefing-narrative');
      if (!el) return;
      el.innerHTML = html;

      el.querySelectorAll('p').forEach((p) => {
        const text = p.textContent || '';
        const sentences = text.split(/(?<=[.!?])\s+(?=[A-Z])/);
        if (sentences.length <= 1) return;
        const frag = document.createDocumentFragment();
        sentences.forEach((s, i) => {
          const span = document.createElement('span');
          span.className = 'ai-sentence';
          span.style.cssText = 'display: inline; cursor: pointer; border-radius: 4px; padding: 1px 0;';
          span.textContent = s.trim();
          frag.appendChild(span);
          if (i < sentences.length - 1) frag.appendChild(document.createTextNode(' '));
        });
        p.innerHTML = '';
        p.appendChild(frag);
      });

      const contentEl = document.getElementById('briefing-content');
      const loadingEl = document.getElementById('briefing-loading');
      if (contentEl) contentEl.style.display = 'block';
      if (loadingEl) loadingEl.style.display = 'none';
    }, STUB_BRIEFING_HTML);

    await page.waitForTimeout(300);

    const briefingSection = page.locator('#briefing-section');
    await briefingSection.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);

    // Get the first sentence span position and simulate the confirm pill appearing
    await page.evaluate(() => {
      const pill = document.getElementById('ai-briefing-confirm-pill');
      const firstSentence = document.querySelector('.ai-sentence');
      if (!pill || !firstSentence) return;

      const rect = firstSentence.getBoundingClientRect();
      // Position pill below the first sentence
      const pillW = 220;
      const margin = 8;
      const left = Math.max(margin, Math.min(rect.left + rect.width / 2 - pillW / 2, window.innerWidth - pillW - margin));
      const top = rect.bottom + window.scrollY + margin;

      pill.style.left = left + 'px';
      pill.style.top = top + 'px';
      pill.classList.add('is-visible');

      // Flash the sentence
      firstSentence.classList.add('is-flashing');
    });

    await page.waitForTimeout(150);

    const sectionBox = await briefingSection.boundingBox();
    await page.screenshot({
      path: path.join(OUT_DIR, 'mobile-375-confirm-pill.png'),
      clip: sectionBox
        ? { x: 0, y: sectionBox.y, width: 375, height: Math.min(sectionBox.height, 500) }
        : undefined,
    });
    await page.close();
  }

  // ─── 4. mobile-375-chatbot-open.png ──────────────────────────────────────
  // Shows chatbot open with tapped sentence as pre-loaded context + typing indicator.
  {
    const page = await browser.newPage({ viewport: { width: 375, height: 812 } });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    await addMobileOverrides(page);

    await page.evaluate(() => {
      const panel = document.getElementById('chatbot-panel');
      const messages = panel ? panel.querySelector('.chatbot-messages') : null;
      if (!panel || !messages) return;

      // Show chatbot panel
      panel.setAttribute('aria-hidden', 'false');
      if (panel.classList.contains('chatbot-panel--closed')) {
        panel.classList.remove('chatbot-panel--closed');
      }
      panel.style.display = 'flex';
      panel.style.visibility = 'visible';
      panel.style.opacity = '1';
      panel.style.transform = 'none';

      // Hide empty state
      const emptyState = messages.querySelector('.chatbot-empty-state');
      if (emptyState) emptyState.style.display = 'none';

      // Add user message (the tapped sentence)
      const userMsg = document.createElement('div');
      userMsg.className = 'chatbot-message chatbot-message--user';
      userMsg.innerHTML = `
        <span class="chatbot-message-label sr-only">You said:</span>
        <p class="chatbot-message-text">Please explain this from today's market briefing: "Treasury yields rose across the curve, with the 10-year touching 4.65%, pressuring growth and technology stocks."</p>
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

    const chatbotPanel = page.locator('#chatbot-panel');
    const panelBox = await chatbotPanel.boundingBox();
    await page.screenshot({
      path: path.join(OUT_DIR, 'mobile-375-chatbot-open.png'),
      clip: panelBox
        ? { x: panelBox.x, y: panelBox.y, width: panelBox.width, height: Math.min(panelBox.height, 600) }
        : undefined,
    });
    await page.close();
  }

  await browser.close();
  console.log('US-264 screenshots written to screenshots/us264/');
})();
