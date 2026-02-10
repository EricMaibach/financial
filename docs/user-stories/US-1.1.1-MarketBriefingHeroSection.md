# User Story 1.1.1: Market Briefing Hero Section

**Epic:** Phase 1.1 - Homepage Overhaul
**Priority:** Critical
**Story Points:** 5
**Assigned To:** _Unassigned_

---

## User Story

**As a** SignalTrackers user,
**I want to** see a prominent AI-generated market briefing as the first thing on the homepage,
**So that** I immediately understand today's key market conditions without scrolling or clicking through multiple pages.

---

## Background

The AI market briefing feature already exists but is positioned as one of many cards on the homepage. This story promotes it to "hero" status - the dominant visual element that communicates our core value proposition: AI-powered synthesis of market conditions.

---

## Acceptance Criteria

### AC1: Hero Placement and Visual Prominence
- [ ] The Market Briefing is the **first content section** below the navigation bar
- [ ] The section spans the **full width** of the content area
- [ ] The card has visual prominence through:
  - Gradient or solid color header bar (primary blue)
  - Elevated shadow (box-shadow)
  - Larger typography than other cards (heading: 24px, body: 18px)
- [ ] Clear visual hierarchy establishes this as the most important section

### AC2: Structured Briefing Content
- [ ] The briefing displays in a structured format:
  ```
  📊 Today's Market Briefing                    [Date: Feb 9, 2026]
  ───────────────────────────────────────────────────────────────
  [2-3 paragraph narrative summary]

  Key Points:
  • [Bullet point 1]
  • [Bullet point 2]
  • [Bullet point 3]
  • [Bullet point 4 - optional]
  • [Bullet point 5 - optional]

                                          Generated: 8:30 AM ET
  ```
- [ ] Narrative text has readable line height (1.6) and max-width for readability (800px)
- [ ] Key points are displayed as a bulleted list with check or bullet icons
- [ ] Attribution text: "AI-generated based on current market data" appears subtly

### AC3: Loading State
- [ ] While briefing is loading, display a skeleton loader:
  - Animated placeholder rectangles for heading and paragraphs
  - Subtle pulse animation (opacity 0.5 → 1.0)
  - Loading spinner icon with "Loading today's briefing..." text
- [ ] Loading state gracefully handles slow network conditions (up to 30 seconds)

### AC4: Error/Fallback State
- [ ] If briefing fails to load, display friendly message:
  - "Market briefing is being generated. Check back shortly."
  - "Retry" button to attempt reload
- [ ] If AI service is unavailable, display:
  - "AI briefing temporarily unavailable. View raw market data below."
- [ ] Error states do not break page layout or block other content

### AC5: Timestamp Display
- [ ] Display generation timestamp in format: "Generated: 8:30 AM ET"
- [ ] Timestamp appears in the bottom-right of the card
- [ ] If briefing is older than 24 hours, display warning: "⚠️ Briefing may be outdated"

### AC6: Regenerate Button (Optional Enhancement)
- [ ] "Regenerate Briefing" button appears for authenticated users
- [ ] Button is rate-limited (disabled with tooltip if used within last hour)
- [ ] Button shows loading spinner while regenerating
- [ ] On success, briefing updates without page reload
- [ ] Note: This is a nice-to-have; core acceptance is the display functionality

### AC7: Responsive Design
- [ ] On desktop (>992px): Full-width card with comfortable padding (32px)
- [ ] On tablet (768-992px): Full-width with reduced padding (24px)
- [ ] On mobile (<768px):
  - Full-width with minimal padding (16px)
  - Font sizes scale down (heading: 20px, body: 16px)
  - Key points remain readable and tappable

### AC8: Data Integration
- [ ] Briefing data is fetched from existing `/api/ai-summary` endpoint
- [ ] Data structure expected:
  ```json
  {
    "summary": "Narrative text...",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "generated_at": "2026-02-09T08:30:00Z"
  }
  ```
- [ ] If API returns legacy format (single string), parse into narrative only (no key points)

---

## Technical Notes

### Files to Modify

| File | Changes |
|------|---------|
| `signaltrackers/templates/index.html` | Move briefing section to top, restructure HTML |
| `signaltrackers/static/css/dashboard.css` | Add `.hero-briefing`, `.briefing-content` classes |
| `signaltrackers/static/js/dashboard.js` | Update `loadAISummary()` to handle structured data |

### HTML Structure

```html
<section class="hero-briefing mb-4">
  <div class="card shadow-lg">
    <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
      <h2 class="mb-0">
        <i class="fas fa-chart-line me-2"></i>Today's Market Briefing
      </h2>
      <span class="badge bg-light text-dark" id="briefing-date">Feb 9, 2026</span>
    </div>
    <div class="card-body briefing-content">
      <div id="briefing-loading" class="briefing-skeleton">
        <!-- Loading skeleton -->
      </div>
      <div id="briefing-content" style="display: none;">
        <div id="briefing-narrative" class="briefing-narrative mb-4">
          <!-- AI narrative paragraphs -->
        </div>
        <div id="briefing-key-points" class="briefing-key-points">
          <h5>Key Points</h5>
          <ul id="key-points-list">
            <!-- Bullet points -->
          </ul>
        </div>
      </div>
      <div id="briefing-error" style="display: none;">
        <!-- Error message -->
      </div>
    </div>
    <div class="card-footer text-muted d-flex justify-content-between">
      <small id="briefing-attribution">AI-generated based on current market data</small>
      <small id="briefing-timestamp">Generated: --</small>
    </div>
  </div>
</section>
```

### CSS Classes

```css
.hero-briefing {
  margin-bottom: 2rem;
}

.hero-briefing .card {
  border: none;
  border-radius: 12px;
}

.hero-briefing .card-header {
  background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%);
  border-radius: 12px 12px 0 0;
  padding: 1.25rem 1.5rem;
}

.hero-briefing .card-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
}

.briefing-content {
  padding: 2rem;
  max-width: 900px;
}

.briefing-narrative {
  font-size: 1.125rem;
  line-height: 1.7;
  color: #333;
}

.briefing-key-points ul {
  list-style: none;
  padding-left: 0;
}

.briefing-key-points li {
  padding: 0.5rem 0;
  padding-left: 1.5rem;
  position: relative;
}

.briefing-key-points li::before {
  content: "•";
  color: #0d6efd;
  font-weight: bold;
  position: absolute;
  left: 0;
}

.briefing-skeleton {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
```

### JavaScript Updates

```javascript
async function loadAISummary() {
  const loadingEl = document.getElementById('briefing-loading');
  const contentEl = document.getElementById('briefing-content');
  const errorEl = document.getElementById('briefing-error');

  try {
    loadingEl.style.display = 'block';
    contentEl.style.display = 'none';
    errorEl.style.display = 'none';

    const response = await fetch('/api/ai-summary');
    const data = await response.json();

    if (data.summary) {
      document.getElementById('briefing-narrative').innerHTML =
        data.summary.split('\n\n').map(p => `<p>${p}</p>`).join('');

      if (data.key_points && data.key_points.length > 0) {
        const pointsList = document.getElementById('key-points-list');
        pointsList.innerHTML = data.key_points
          .map(point => `<li>${point}</li>`)
          .join('');
        document.getElementById('briefing-key-points').style.display = 'block';
      }

      if (data.generated_at) {
        const timestamp = new Date(data.generated_at);
        document.getElementById('briefing-timestamp').textContent =
          `Generated: ${timestamp.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            timeZoneName: 'short'
          })}`;
      }

      loadingEl.style.display = 'none';
      contentEl.style.display = 'block';
    }
  } catch (error) {
    loadingEl.style.display = 'none';
    errorEl.style.display = 'block';
    errorEl.innerHTML = `
      <div class="alert alert-warning">
        <p>Market briefing is being generated. Check back shortly.</p>
        <button class="btn btn-sm btn-outline-primary" onclick="loadAISummary()">
          Retry
        </button>
      </div>
    `;
  }
}
```

---

## Definition of Done

- [ ] All acceptance criteria are met
- [ ] Code is reviewed and approved
- [ ] Manual testing on Chrome, Firefox, Safari
- [ ] Responsive testing on mobile (iPhone, Android) and tablet
- [ ] No console errors
- [ ] Loading state works correctly
- [ ] Error handling works correctly
- [ ] Merged to main branch

---

## Dependencies

- Existing `/api/ai-summary` endpoint must be functional
- AI service (OpenAI/Anthropic) must be configured

---

## Notes for Developer

1. The existing briefing implementation in `index.html` can be found around lines 50-80
2. The existing `loadAISummary()` function is in `dashboard.js`
3. Consider whether the API response needs to be updated to return structured key_points - if not available, the story can be completed with narrative-only display
4. The gradient header color should match the primary brand color used elsewhere
