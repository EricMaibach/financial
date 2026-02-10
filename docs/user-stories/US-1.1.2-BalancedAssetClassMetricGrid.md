# User Story 1.1.2: Balanced Asset Class Metric Grid

**Epic:** Phase 1.1 - Homepage Overhaul
**Priority:** Critical
**Story Points:** 5
**Assigned To:** _Unassigned_

---

## User Story

**As a** SignalTrackers user,
**I want to** see a balanced grid of metrics organized by asset class (Credit, Equities, Rates, Safe Havens, Crypto, Dollar),
**So that** I can quickly assess conditions across ALL major market categories and understand that SignalTrackers provides comprehensive coverage.

---

## Background

The current homepage displays metrics in an unbalanced way that emphasizes credit/gold divergence. This story creates a new 6-card grid that gives equal visual weight to all asset classes, directly addressing the perception that SignalTrackers is a single-thesis platform.

---

## Acceptance Criteria

### AC1: Grid Layout
- [ ] Display 6 equally-sized cards in a responsive grid:
  - Desktop (>992px): 3 columns × 2 rows
  - Tablet (768-992px): 2 columns × 3 rows
  - Mobile (<768px): 1 column × 6 rows (stacked)
- [ ] All cards have identical dimensions within their breakpoint
- [ ] Cards are visually separated with consistent gutters (16-24px)

### AC2: Asset Class Categories
Each card represents one asset class with the following metrics:

| Category | Icon | Metric 1 | Metric 2 | Metric 3 |
|----------|------|----------|----------|----------|
| **Credit** | 💳 | HY Spread (bp) | IG Spread (bp) | CCC/HY Ratio |
| **Equities** | 📈 | S&P 500 | Russell 2000 | VIX |
| **Rates** | 📊 | 10Y Yield | 2Y Yield | Curve Spread (10Y-2Y) |
| **Safe Havens** | 🛡️ | Gold Price | Silver Price | TLT Price |
| **Crypto** | ₿ | Bitcoin Price | Ethereum Price | BTC Dominance % |
| **Dollar** | 💵 | DXY Index | EUR/USD | USD/JPY |

- [ ] Each card displays exactly 3 metrics
- [ ] Metrics show current value with appropriate formatting (currency, %, bp)
- [ ] Each metric shows 5-day change with directional indicator (▲/▼)

### AC3: Card Structure
Each card must contain:
```
┌─────────────────────────────────────┐
│ [Icon] CATEGORY NAME                │
│ ─────────────────────────────────── │
│ Metric 1:  $2,145      ▲ +1.2%     │
│ Metric 2:  $25.80      ▲ +0.8%     │
│ Metric 3:  $92.50      ▼ -0.3%     │
│                                     │
│ Status: [ELEVATED]                  │
│                                     │
│ [View Credit →]                     │
└─────────────────────────────────────┘
```

- [ ] Category header with icon (emoji or Font Awesome)
- [ ] Horizontal divider below header
- [ ] 3 metrics with current value and change
- [ ] Status badge showing market condition
- [ ] "View [Category] →" link to detailed page

### AC4: Status Badge Logic
Each category displays a calculated status badge based on current conditions:

**Credit Status:**
| Condition | Status | Badge Color |
|-----------|--------|-------------|
| HY Spread > 600bp | CRISIS | Red (danger) |
| HY Spread > 450bp | STRESSED | Orange (warning) |
| HY Spread > 350bp | TIGHT | Yellow (caution) |
| HY Spread < 300bp | CALM | Green (success) |
| Otherwise | NORMAL | Gray (secondary) |

**Equities Status:**
| Condition | Status | Badge Color |
|-----------|--------|-------------|
| VIX > 30 | FEAR | Red |
| VIX > 25 | RISK-OFF | Orange |
| VIX > 20 | CAUTIOUS | Yellow |
| VIX < 15 | RISK-ON | Green |
| Otherwise | NEUTRAL | Gray |

**Rates Status:**
| Condition | Status | Badge Color |
|-----------|--------|-------------|
| 10Y - 2Y < -50bp | DEEPLY INVERTED | Red |
| 10Y - 2Y < 0 | INVERTED | Orange |
| 10Y - 2Y > 100bp | STEEP | Yellow |
| 10Y - 2Y < 25bp | FLAT | Blue |
| Otherwise | NORMAL | Gray |

**Safe Havens Status:**
| Condition | Status | Badge Color |
|-----------|--------|-------------|
| Gold 30d change > 8% | FLIGHT TO SAFETY | Red |
| Gold 30d change > 5% | ELEVATED DEMAND | Orange |
| Gold 30d change < -5% | RISK-ON | Green |
| Otherwise | NORMAL | Gray |

**Crypto Status:**
| Condition | Status | Badge Color |
|-----------|--------|-------------|
| BTC 30d change > 20% | EUPHORIC | Green |
| BTC 30d change > 10% | BULLISH | Blue |
| BTC 30d change < -20% | CAPITULATION | Red |
| BTC 30d change < -10% | BEARISH | Orange |
| Otherwise | NEUTRAL | Gray |

**Dollar Status:**
| Condition | Status | Badge Color |
|-----------|--------|-------------|
| DXY > 107 | VERY STRONG | Orange |
| DXY > 104 | STRONG | Blue |
| DXY < 100 | WEAK | Red |
| DXY < 97 | VERY WEAK | Green |
| Otherwise | NEUTRAL | Gray |

- [ ] Status is calculated client-side based on metric values
- [ ] Badge uses Bootstrap color classes for consistency
- [ ] Tooltip on badge explains the criteria (optional enhancement)

### AC5: Navigation Links
- [ ] Each card has a "View [Category] →" link at the bottom
- [ ] Links navigate to:
  - Credit → `/equity` (or future credit-specific page)
  - Equities → `/equity`
  - Rates → `/rates`
  - Safe Havens → `/safe-havens`
  - Crypto → `/crypto`
  - Dollar → `/dollar`
- [ ] Links use consistent styling (text-decoration, hover state)

### AC6: Category Accent Colors
Each card has a subtle accent color for visual differentiation:
- [ ] Credit: Red/Rose left border or header accent
- [ ] Equities: Blue left border or header accent
- [ ] Rates: Purple left border or header accent
- [ ] Safe Havens: Gold/Amber left border or header accent
- [ ] Crypto: Orange left border or header accent
- [ ] Dollar: Green left border or header accent

Implementation options (choose one):
- 4px colored left border on card
- Colored gradient at top of card header
- Colored icon background

### AC7: Data Binding
- [ ] Data sourced from existing `/api/dashboard` endpoint
- [ ] Dashboard data contains all required metrics
- [ ] If a metric is unavailable, display "--" as placeholder
- [ ] Grid loads after page load via JavaScript (not blocking)

### AC8: Hover Interaction
- [ ] Cards have subtle hover effect (shadow increase or slight lift)
- [ ] Hover state provides feedback that card is interactive
- [ ] Cursor shows pointer on "View →" link

### AC9: Responsive Behavior
Desktop (>992px):
```
┌─────────┬─────────┬─────────┐
│ Credit  │Equities │ Rates   │
├─────────┼─────────┼─────────┤
│ Havens  │ Crypto  │ Dollar  │
└─────────┴─────────┴─────────┘
```

Tablet (768-992px):
```
┌─────────┬─────────┐
│ Credit  │Equities │
├─────────┼─────────┤
│ Rates   │ Havens  │
├─────────┼─────────┤
│ Crypto  │ Dollar  │
└─────────┴─────────┘
```

Mobile (<768px):
```
┌─────────┐
│ Credit  │
├─────────┤
│Equities │
├─────────┤
│ Rates   │
├─────────┤
│ Havens  │
├─────────┤
│ Crypto  │
├─────────┤
│ Dollar  │
└─────────┘
```

---

## Technical Notes

### Files to Modify

| File | Changes |
|------|---------|
| `signaltrackers/templates/index.html` | Add new market grid section |
| `signaltrackers/static/css/dashboard.css` | Grid layout, card styles, accent colors |
| `signaltrackers/static/js/dashboard.js` | Status calculation, data binding |

### HTML Structure

```html
<section class="market-conditions-grid mb-4">
  <h3 class="section-title">Market Conditions</h3>
  <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
    <!-- Credit Card -->
    <div class="col">
      <div class="card market-card category-credit h-100">
        <div class="card-header">
          <span class="category-icon">💳</span>
          <span class="category-name">CREDIT</span>
        </div>
        <div class="card-body">
          <div class="metric-row">
            <span class="metric-label">HY Spread</span>
            <span class="metric-value" id="credit-hy-spread">--</span>
            <span class="metric-change" id="credit-hy-change">--</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">IG Spread</span>
            <span class="metric-value" id="credit-ig-spread">--</span>
            <span class="metric-change" id="credit-ig-change">--</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">CCC/HY Ratio</span>
            <span class="metric-value" id="credit-ccc-ratio">--</span>
            <span class="metric-change" id="credit-ccc-change">--</span>
          </div>
          <div class="status-row mt-3">
            <span class="status-label">Status:</span>
            <span class="badge" id="credit-status">--</span>
          </div>
        </div>
        <div class="card-footer">
          <a href="/equity" class="view-link">View Credit →</a>
        </div>
      </div>
    </div>
    <!-- Repeat for Equities, Rates, Safe Havens, Crypto, Dollar -->
  </div>
</section>
```

### CSS Structure

```css
/* Grid Layout */
.market-conditions-grid {
  margin: 2rem 0;
}

.market-conditions-grid .section-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #333;
}

/* Market Cards */
.market-card {
  border: none;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: all 0.2s ease;
}

.market-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transform: translateY(-2px);
}

.market-card .card-header {
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  font-weight: 600;
  padding: 0.75rem 1rem;
}

.market-card .card-body {
  padding: 1rem;
}

.market-card .card-footer {
  background: transparent;
  border-top: 1px solid #e9ecef;
  padding: 0.75rem 1rem;
}

/* Category Accent Colors (left border) */
.category-credit { border-left: 4px solid #dc3545; }
.category-equities { border-left: 4px solid #0d6efd; }
.category-rates { border-left: 4px solid #6f42c1; }
.category-havens { border-left: 4px solid #ffc107; }
.category-crypto { border-left: 4px solid #fd7e14; }
.category-dollar { border-left: 4px solid #198754; }

/* Metric Rows */
.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.metric-row:last-of-type {
  border-bottom: none;
}

.metric-label {
  color: #666;
  font-size: 0.875rem;
}

.metric-value {
  font-weight: 600;
  font-size: 1rem;
}

.metric-change {
  font-size: 0.875rem;
  min-width: 60px;
  text-align: right;
}

.metric-change.positive { color: #198754; }
.metric-change.negative { color: #dc3545; }

/* Status Badge */
.status-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-label {
  font-size: 0.875rem;
  color: #666;
}

/* View Link */
.view-link {
  color: #0d6efd;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
}

.view-link:hover {
  text-decoration: underline;
}
```

### JavaScript - Status Calculation

```javascript
function calculateMarketStatus() {
  const data = dashboardData; // Global from loadDashboard()

  // Credit Status
  const hySpread = data.hy_spread?.value || 0;
  let creditStatus = { text: 'NORMAL', class: 'bg-secondary' };
  if (hySpread > 600) creditStatus = { text: 'CRISIS', class: 'bg-danger' };
  else if (hySpread > 450) creditStatus = { text: 'STRESSED', class: 'bg-warning' };
  else if (hySpread > 350) creditStatus = { text: 'TIGHT', class: 'bg-info' };
  else if (hySpread < 300) creditStatus = { text: 'CALM', class: 'bg-success' };

  // Equities Status
  const vix = data.vix?.value || 0;
  let equitiesStatus = { text: 'NEUTRAL', class: 'bg-secondary' };
  if (vix > 30) equitiesStatus = { text: 'FEAR', class: 'bg-danger' };
  else if (vix > 25) equitiesStatus = { text: 'RISK-OFF', class: 'bg-warning' };
  else if (vix > 20) equitiesStatus = { text: 'CAUTIOUS', class: 'bg-info' };
  else if (vix < 15) equitiesStatus = { text: 'RISK-ON', class: 'bg-success' };

  // Rates Status
  const curveSpread = (data.treasury_10y?.value || 0) - (data.treasury_2y?.value || 0);
  let ratesStatus = { text: 'NORMAL', class: 'bg-secondary' };
  if (curveSpread < -0.5) ratesStatus = { text: 'DEEPLY INVERTED', class: 'bg-danger' };
  else if (curveSpread < 0) ratesStatus = { text: 'INVERTED', class: 'bg-warning' };
  else if (curveSpread > 1) ratesStatus = { text: 'STEEP', class: 'bg-info' };
  else if (curveSpread < 0.25) ratesStatus = { text: 'FLAT', class: 'bg-primary' };

  // Safe Havens Status
  const goldChange30d = data.gold?.change_30d || 0;
  let havensStatus = { text: 'NORMAL', class: 'bg-secondary' };
  if (goldChange30d > 8) havensStatus = { text: 'FLIGHT TO SAFETY', class: 'bg-danger' };
  else if (goldChange30d > 5) havensStatus = { text: 'ELEVATED DEMAND', class: 'bg-warning' };
  else if (goldChange30d < -5) havensStatus = { text: 'RISK-ON', class: 'bg-success' };

  // Crypto Status
  const btcChange30d = data.bitcoin?.change_30d || 0;
  let cryptoStatus = { text: 'NEUTRAL', class: 'bg-secondary' };
  if (btcChange30d > 20) cryptoStatus = { text: 'EUPHORIC', class: 'bg-success' };
  else if (btcChange30d > 10) cryptoStatus = { text: 'BULLISH', class: 'bg-primary' };
  else if (btcChange30d < -20) cryptoStatus = { text: 'CAPITULATION', class: 'bg-danger' };
  else if (btcChange30d < -10) cryptoStatus = { text: 'BEARISH', class: 'bg-warning' };

  // Dollar Status
  const dxy = data.dxy?.value || 100;
  let dollarStatus = { text: 'NEUTRAL', class: 'bg-secondary' };
  if (dxy > 107) dollarStatus = { text: 'VERY STRONG', class: 'bg-warning' };
  else if (dxy > 104) dollarStatus = { text: 'STRONG', class: 'bg-primary' };
  else if (dxy < 97) dollarStatus = { text: 'VERY WEAK', class: 'bg-success' };
  else if (dxy < 100) dollarStatus = { text: 'WEAK', class: 'bg-danger' };

  return {
    credit: creditStatus,
    equities: equitiesStatus,
    rates: ratesStatus,
    havens: havensStatus,
    crypto: cryptoStatus,
    dollar: dollarStatus
  };
}

function updateMarketGrid(data) {
  const status = calculateMarketStatus();

  // Update Credit Card
  updateMetric('credit-hy-spread', data.hy_spread?.value, 'bp');
  updateMetric('credit-ig-spread', data.ig_spread?.value, 'bp');
  updateMetric('credit-ccc-ratio', data.ccc_hy_ratio?.value, 'ratio');
  updateStatus('credit-status', status.credit);

  // ... similar for other categories
}
```

---

## Definition of Done

- [ ] All 6 asset class cards display correctly
- [ ] Grid is responsive across all breakpoints
- [ ] Status badges calculate correctly based on criteria
- [ ] All metrics display with proper formatting
- [ ] Navigation links work correctly
- [ ] Hover effects work smoothly
- [ ] Code is reviewed and approved
- [ ] Manual testing on Chrome, Firefox, Safari
- [ ] Responsive testing on mobile and tablet
- [ ] No console errors
- [ ] Merged to main branch

---

## Dependencies

- Existing `/api/dashboard` endpoint must return all required metrics
- Detailed pages for each category must exist (or links can be placeholders)

---

## Notes for Developer

1. The existing dashboard data structure should contain most metrics needed
2. Map existing data fields to the new grid:
   - `hy_spread` → Credit HY Spread
   - `gold_price` → Safe Havens Gold
   - `vix` → Equities VIX
   - etc.
3. If DXY or other metrics are missing from the API, check if they exist elsewhere or create placeholder values
4. The order of cards matters for visual balance - keep Credit/Equities/Rates on top row (most commonly referenced)
5. Consider extracting status calculation into a separate utility file for reuse in future features
