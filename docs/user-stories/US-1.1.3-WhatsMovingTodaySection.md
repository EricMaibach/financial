# User Story 1.1.3: What's Moving Today Section

**Epic:** Phase 1.1 - Homepage Overhaul
**Priority:** High
**Story Points:** 3
**Assigned To:** _Unassigned_

---

## User Story

**As a** SignalTrackers user,
**I want to** see the top 5 metrics with the most unusual movements across all asset classes,
**So that** I can quickly identify what requires my attention today without manually checking each category.

---

## Background

The current homepage has a "Top Movers (5 Day)" section, but its positioning and design don't emphasize its value as a cross-market scanner. This story enhances and repositions this feature to be a prominent "What's Moving" section that immediately shows users the most statistically significant movements across ALL 50+ tracked metrics.

---

## Acceptance Criteria

### AC1: Section Position and Title
- [ ] Section appears **immediately after** the Market Briefing Hero section
- [ ] Section title: "What's Moving Today"
- [ ] Subtitle/helper text: "Top movers across all 50+ tracked metrics, ranked by statistical significance"
- [ ] Section has a distinct visual container (card or bordered section)

### AC2: Display Top 5 Movers
- [ ] Display exactly 5 mover cards in a horizontal row
- [ ] Movers are ranked by **absolute z-score** (highest deviation first)
- [ ] Movers can come from ANY asset class (credit, equities, rates, etc.)
- [ ] Include both positive and negative movers (direction doesn't affect ranking)

### AC3: Mover Card Content
Each mover card displays:
```
┌─────────────────┐
│ #1              │  ← Rank number
│ VIX             │  ← Metric name
│ 23.5            │  ← Current value
│ ▲ +15.2%        │  ← 5-day change with direction
│ z-score: 2.4    │  ← Statistical significance
│ [UNUSUAL]       │  ← Severity badge
└─────────────────┘
```

- [ ] Rank number (1-5) prominently displayed
- [ ] Metric name (human-readable label)
- [ ] Current value with appropriate formatting
- [ ] 5-day percentage change with direction indicator (▲/▼)
- [ ] Z-score value (1 decimal place)
- [ ] Severity badge based on z-score

### AC4: Severity Badge Logic
Based on absolute z-score:

| Z-Score | Badge | Color |
|---------|-------|-------|
| z > 2.5 | EXTREME | Red (danger) |
| z > 2.0 | UNUSUAL | Orange (warning) |
| z > 1.5 | ELEVATED | Yellow (caution) |
| z > 1.0 | NOTABLE | Blue (info) |
| z ≤ 1.0 | NORMAL | Gray (secondary) |

- [ ] Badge color corresponds to severity level
- [ ] Badge text is uppercase and bold

### AC5: Visual Direction Indicators
- [ ] Positive changes: Green color + ▲ arrow
- [ ] Negative changes: Red color + ▼ arrow
- [ ] Zero/no change: Gray color + "—" symbol
- [ ] Direction is based on 5-day change value

### AC6: Click Interaction
- [ ] Clicking a mover card navigates to the metric detail page
- [ ] URL pattern: `/explorer?metric={metric_id}`
- [ ] Card has hover state indicating clickability
- [ ] Cursor changes to pointer on hover

### AC7: Responsive Layout
Desktop (>992px):
```
┌───────┬───────┬───────┬───────┬───────┐
│  #1   │  #2   │  #3   │  #4   │  #5   │
└───────┴───────┴───────┴───────┴───────┘
```

Tablet (768-992px):
```
┌───────┬───────┬───────┐
│  #1   │  #2   │  #3   │
├───────┼───────┼───────┤
│  #4   │  #5   │       │
└───────┴───────┴───────┘
```

Mobile (<768px):
- Horizontal scroll enabled
- Cards maintain minimum width (140px)
- Scroll hint (fade on edges or arrows)

### AC8: Animation Enhancement (Optional)
- [ ] Cards with z-score > 2.5 have subtle pulse animation
- [ ] Animation draws attention to extreme moves
- [ ] Animation can be disabled via user preference (future)

### AC9: Data Requirements
- [ ] Data sourced from `/api/dashboard` → `top_movers` array
- [ ] Expected data structure per mover:
  ```json
  {
    "metric_id": "vix",
    "metric_name": "VIX (Volatility Index)",
    "current_value": 23.5,
    "change_5d": 15.2,
    "z_score": 2.4,
    "category": "equities"
  }
  ```
- [ ] If fewer than 5 movers available, display what's available
- [ ] If no movers data, display message: "Market movements loading..."

### AC10: Category Indicator (Optional Enhancement)
- [ ] Small category label or icon showing which asset class the metric belongs to
- [ ] Helps users quickly see diversity of movers
- [ ] Uses same color coding as Market Grid (credit=red, equities=blue, etc.)

---

## Technical Notes

### Files to Modify

| File | Changes |
|------|---------|
| `signaltrackers/templates/index.html` | Restructure top movers section |
| `signaltrackers/static/css/dashboard.css` | Mover card styles, badges |
| `signaltrackers/static/js/dashboard.js` | Update data binding, click handlers |

### HTML Structure

```html
<section class="whats-moving-section mb-4">
  <div class="section-header d-flex justify-content-between align-items-center mb-3">
    <div>
      <h3 class="section-title mb-0">What's Moving Today</h3>
      <small class="text-muted">Top movers across all 50+ metrics, ranked by statistical significance</small>
    </div>
    <a href="/explorer" class="btn btn-outline-secondary btn-sm">View All Metrics →</a>
  </div>

  <div class="movers-container">
    <div class="movers-row" id="top-movers-row">
      <!-- Mover cards injected by JavaScript -->
    </div>
  </div>
</section>
```

### Mover Card Template

```html
<div class="mover-card" onclick="navigateToMetric('${metric_id}')">
  <div class="mover-rank">#${rank}</div>
  <div class="mover-name">${metric_name}</div>
  <div class="mover-value">${formatted_value}</div>
  <div class="mover-change ${change_class}">
    ${direction_icon} ${change_5d}%
  </div>
  <div class="mover-zscore">z-score: ${z_score}</div>
  <span class="mover-badge badge ${badge_class}">${badge_text}</span>
</div>
```

### CSS Structure

```css
/* What's Moving Section */
.whats-moving-section {
  margin: 2rem 0;
}

.section-header {
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e9ecef;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
}

/* Movers Container */
.movers-container {
  overflow-x: auto;
  padding: 0.5rem 0;
}

.movers-row {
  display: flex;
  gap: 1rem;
  padding-bottom: 0.5rem;
}

/* Mover Card */
.mover-card {
  flex: 0 0 auto;
  min-width: 160px;
  max-width: 180px;
  padding: 1rem;
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mover-card:hover {
  border-color: #0d6efd;
  box-shadow: 0 4px 12px rgba(13, 110, 253, 0.15);
  transform: translateY(-2px);
}

.mover-rank {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6c757d;
  margin-bottom: 0.25rem;
}

.mover-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mover-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 0.25rem;
}

.mover-change {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.mover-change.positive { color: #198754; }
.mover-change.negative { color: #dc3545; }

.mover-zscore {
  font-size: 0.75rem;
  color: #6c757d;
  margin-bottom: 0.5rem;
}

.mover-badge {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Pulse animation for extreme movers */
@keyframes attention-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(220, 53, 69, 0); }
}

.mover-card.extreme {
  animation: attention-pulse 2s infinite;
}

/* Mobile scroll hint */
@media (max-width: 768px) {
  .movers-container {
    -webkit-overflow-scrolling: touch;
  }

  .movers-container::after {
    content: '';
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 40px;
    background: linear-gradient(to right, transparent, white);
    pointer-events: none;
  }
}
```

### JavaScript Implementation

```javascript
function renderTopMovers(movers) {
  const container = document.getElementById('top-movers-row');

  if (!movers || movers.length === 0) {
    container.innerHTML = '<p class="text-muted">Market movements loading...</p>';
    return;
  }

  // Sort by absolute z-score and take top 5
  const topMovers = movers
    .sort((a, b) => Math.abs(b.z_score) - Math.abs(a.z_score))
    .slice(0, 5);

  container.innerHTML = topMovers.map((mover, index) => {
    const rank = index + 1;
    const isPositive = mover.change_5d >= 0;
    const changeClass = isPositive ? 'positive' : 'negative';
    const directionIcon = isPositive ? '▲' : '▼';

    // Determine severity badge
    const absZ = Math.abs(mover.z_score);
    let badgeClass, badgeText;
    if (absZ > 2.5) {
      badgeClass = 'bg-danger';
      badgeText = 'EXTREME';
    } else if (absZ > 2.0) {
      badgeClass = 'bg-warning text-dark';
      badgeText = 'UNUSUAL';
    } else if (absZ > 1.5) {
      badgeClass = 'bg-info';
      badgeText = 'ELEVATED';
    } else if (absZ > 1.0) {
      badgeClass = 'bg-primary';
      badgeText = 'NOTABLE';
    } else {
      badgeClass = 'bg-secondary';
      badgeText = 'NORMAL';
    }

    const extremeClass = absZ > 2.5 ? 'extreme' : '';

    return `
      <div class="mover-card ${extremeClass}" onclick="navigateToMetric('${mover.metric_id}')">
        <div class="mover-rank">#${rank}</div>
        <div class="mover-name" title="${mover.metric_name}">${mover.metric_name}</div>
        <div class="mover-value">${formatValue(mover.current_value, mover.metric_id)}</div>
        <div class="mover-change ${changeClass}">
          ${directionIcon} ${Math.abs(mover.change_5d).toFixed(1)}%
        </div>
        <div class="mover-zscore">z-score: ${mover.z_score.toFixed(1)}</div>
        <span class="mover-badge badge ${badgeClass}">${badgeText}</span>
      </div>
    `;
  }).join('');
}

function navigateToMetric(metricId) {
  window.location.href = `/explorer?metric=${metricId}`;
}

function formatValue(value, metricId) {
  // Add formatting logic based on metric type
  if (metricId.includes('spread')) return `${value}bp`;
  if (metricId.includes('gold') || metricId.includes('bitcoin')) return `$${value.toLocaleString()}`;
  if (metricId.includes('vix')) return value.toFixed(1);
  return value.toLocaleString();
}
```

---

## Definition of Done

- [ ] Section displays in correct position (after hero)
- [ ] Exactly 5 movers shown, ranked by z-score
- [ ] All card content displays correctly
- [ ] Severity badges calculate and display properly
- [ ] Click navigation works to metric detail
- [ ] Responsive layout works on all breakpoints
- [ ] Horizontal scroll works smoothly on mobile
- [ ] Hover effects work correctly
- [ ] Code is reviewed and approved
- [ ] Manual testing on Chrome, Firefox, Safari
- [ ] No console errors
- [ ] Merged to main branch

---

## Dependencies

- Existing `/api/dashboard` endpoint must return `top_movers` array with z-scores
- Explorer page must accept `?metric=` query parameter

---

## Notes for Developer

1. The existing top movers implementation is around lines 100-150 in `index.html`
2. Current implementation already has z-score calculation - reuse this logic
3. The "Top Movers Chart" below this section can remain for now but may be considered for removal in a future cleanup
4. Ensure metric_id in the data matches what the Explorer page expects
5. Consider adding a tooltip that explains what z-score means: "How unusual this move is compared to historical volatility"
