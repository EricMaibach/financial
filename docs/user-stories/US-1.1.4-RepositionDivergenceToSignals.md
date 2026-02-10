# User Story 1.1.4: Reposition Divergence to Signals Section

**Epic:** Phase 1.1 - Homepage Overhaul
**Priority:** High
**Story Points:** 3
**Assigned To:** _Unassigned_

---

## User Story

**As a** SignalTrackers user,
**I want to** see the gold/credit divergence presented as one of several cross-market signals,
**So that** I understand it's a valuable indicator among many, not the sole focus of the platform.

---

## Background

The gold/credit divergence metric has become synonymous with SignalTrackers, leading to the perception that we're a single-thesis platform. This story repositions divergence within a new "Market Signals" section that presents it alongside other cross-market indicators, preparing the groundwork for the unified Signals page in Phase 2.1.

---

## Acceptance Criteria

### AC1: New Signals Section
- [ ] Create new "Market Signals" section on the homepage
- [ ] Section positioned **after** the Market Conditions Grid
- [ ] Section has clear header: "Market Signals"
- [ ] Subtitle: "Cross-market indicators worth watching"

### AC2: Display 3 Signal Cards
Display exactly 3 signal cards horizontally:

| Signal | Description | Data Source |
|--------|-------------|-------------|
| Gold/Credit Divergence | When gold rises but credit stays calm | Existing divergence calculation |
| Yield Curve Status | 10Y-2Y spread inversion state | Treasury yields |
| VIX Term Structure | Contango vs backwardation | VIX futures (or proxy) |

- [ ] All 3 signals displayed with equal visual weight
- [ ] Cards arranged in single row on desktop, stacked on mobile

### AC3: Signal Card Content
Each signal card displays:
```
┌─────────────────────────────────────┐
│ Gold/Credit Divergence              │  ← Signal name
│                                     │
│ ⚠️  ELEVATED                        │  ← Status icon + label
│                                     │
│ 78th Percentile                     │  ← Historical context
│ What it means: Gold pricing in      │  ← Brief explanation
│ risk that credit isn't...           │
└─────────────────────────────────────┘
```

- [ ] Signal name (header)
- [ ] Status with appropriate icon:
  - ✓ NORMAL (green check)
  - ⚠️ ELEVATED (yellow warning)
  - 🔴 CRITICAL (red circle)
- [ ] Percentile ranking (e.g., "78th Percentile" or "Top 22%")
- [ ] 1-2 sentence explanation of what the signal means

### AC4: Signal Status Logic

**Gold/Credit Divergence:**
| Condition | Status | Icon |
|-----------|--------|------|
| Divergence percentile > 90 | CRITICAL | 🔴 |
| Divergence percentile > 70 | ELEVATED | ⚠️ |
| Divergence percentile > 50 | NOTABLE | ℹ️ |
| Otherwise | NORMAL | ✓ |

**Yield Curve Status:**
| Condition | Status | Icon |
|-----------|--------|------|
| 10Y-2Y < -50bp | DEEPLY INVERTED | 🔴 |
| 10Y-2Y < 0 | INVERTED | ⚠️ |
| 10Y-2Y < 25bp | FLAT | ℹ️ |
| Otherwise | NORMAL | ✓ |

**VIX Term Structure:**
| Condition | Status | Icon |
|-----------|--------|------|
| Backwardation > 10% | FEAR SPIKE | 🔴 |
| Backwardation > 0% | STRESSED | ⚠️ |
| Contango < 5% | FLAT | ℹ️ |
| Otherwise | NORMAL | ✓ |

Note: If VIX term structure data is unavailable, use VIX level as proxy:
- VIX > 30: FEAR SPIKE
- VIX > 25: STRESSED
- VIX > 20: ELEVATED
- Otherwise: NORMAL

### AC5: Signal Explanations
Static explanatory text for each signal:

**Gold/Credit Divergence:**
> "When gold prices rise while credit spreads remain stable, it suggests gold is pricing in risks that credit markets haven't acknowledged yet."

**Yield Curve Status:**
> "An inverted yield curve (short rates higher than long rates) has historically preceded recessions. Currently tracking the 10Y-2Y spread."

**VIX Term Structure:**
> "When near-term VIX exceeds longer-term VIX (backwardation), it signals acute market stress and demand for immediate protection."

### AC6: "View All Signals" Link
- [ ] Link at bottom of section: "View All Signals →"
- [ ] Links to `/divergence` page (existing)
- [ ] Note: In Phase 2.1, this will link to new unified Signals page
- [ ] Tooltip or note: "More signals coming soon" (optional)

### AC7: Remove Divergence Prominence Elsewhere
- [ ] Remove or demote "Gold-Implied Spread" from primary metrics section
- [ ] Remove any "Crisis Warning Score" prominent display
- [ ] Do NOT remove the divergence page itself - just reposition on homepage
- [ ] Keep divergence data in the API response

### AC8: Visual Styling
- [ ] Cards use muted/secondary styling (less prominent than hero and market grid)
- [ ] Consistent card height within the row
- [ ] Status icon is prominent within each card
- [ ] Percentile displayed with subtle background badge
- [ ] Section has subtle top border or background to separate from grid above

### AC9: Responsive Design
Desktop (>992px):
```
┌─────────────────┬─────────────────┬─────────────────┐
│ Gold/Credit     │ Yield Curve     │ VIX Term        │
│ Divergence      │ Status          │ Structure       │
└─────────────────┴─────────────────┴─────────────────┘
```

Mobile (<768px):
```
┌─────────────────┐
│ Gold/Credit     │
│ Divergence      │
├─────────────────┤
│ Yield Curve     │
│ Status          │
├─────────────────┤
│ VIX Term        │
│ Structure       │
└─────────────────┘
```

---

## Technical Notes

### Files to Modify

| File | Changes |
|------|---------|
| `signaltrackers/templates/index.html` | Add signals section, remove/demote divergence metrics |
| `signaltrackers/static/css/dashboard.css` | Signal card styles |
| `signaltrackers/static/js/dashboard.js` | Signal status calculation, data binding |

### HTML Structure

```html
<section class="market-signals-section mb-4">
  <div class="section-header mb-3">
    <h3 class="section-title">Market Signals</h3>
    <small class="text-muted">Cross-market indicators worth watching</small>
  </div>

  <div class="row g-3">
    <!-- Gold/Credit Divergence -->
    <div class="col-12 col-md-4">
      <div class="signal-card h-100">
        <div class="signal-header">Gold/Credit Divergence</div>
        <div class="signal-status" id="divergence-status">
          <span class="signal-icon">⚠️</span>
          <span class="signal-label">ELEVATED</span>
        </div>
        <div class="signal-percentile" id="divergence-percentile">
          78th Percentile
        </div>
        <div class="signal-description">
          When gold prices rise while credit spreads remain stable, it suggests
          gold is pricing in risks that credit markets haven't acknowledged yet.
        </div>
      </div>
    </div>

    <!-- Yield Curve Status -->
    <div class="col-12 col-md-4">
      <div class="signal-card h-100">
        <div class="signal-header">Yield Curve Status</div>
        <div class="signal-status" id="yieldcurve-status">
          <span class="signal-icon">⚠️</span>
          <span class="signal-label">INVERTED</span>
        </div>
        <div class="signal-percentile" id="yieldcurve-percentile">
          95th Percentile
        </div>
        <div class="signal-description">
          An inverted yield curve (short rates higher than long rates) has
          historically preceded recessions. Currently tracking the 10Y-2Y spread.
        </div>
      </div>
    </div>

    <!-- VIX Term Structure -->
    <div class="col-12 col-md-4">
      <div class="signal-card h-100">
        <div class="signal-header">VIX Term Structure</div>
        <div class="signal-status" id="vixterm-status">
          <span class="signal-icon">✓</span>
          <span class="signal-label">NORMAL</span>
        </div>
        <div class="signal-percentile" id="vixterm-percentile">
          45th Percentile
        </div>
        <div class="signal-description">
          When near-term VIX exceeds longer-term VIX (backwardation), it signals
          acute market stress and demand for immediate protection.
        </div>
      </div>
    </div>
  </div>

  <div class="section-footer mt-3 text-end">
    <a href="/divergence" class="view-link">View All Signals →</a>
  </div>
</section>
```

### CSS Structure

```css
/* Market Signals Section */
.market-signals-section {
  margin: 2rem 0;
  padding-top: 1.5rem;
  border-top: 1px solid #e9ecef;
}

.market-signals-section .section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #495057;
}

/* Signal Cards */
.signal-card {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1.25rem;
}

.signal-header {
  font-size: 0.9rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.75rem;
}

.signal-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.signal-icon {
  font-size: 1.25rem;
}

.signal-label {
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.signal-label.critical { color: #dc3545; }
.signal-label.elevated { color: #fd7e14; }
.signal-label.notable { color: #0d6efd; }
.signal-label.normal { color: #198754; }

.signal-percentile {
  font-size: 0.8rem;
  color: #6c757d;
  background: #e9ecef;
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.75rem;
}

.signal-description {
  font-size: 0.8rem;
  color: #666;
  line-height: 1.5;
}

.section-footer .view-link {
  color: #6c757d;
  text-decoration: none;
  font-size: 0.875rem;
}

.section-footer .view-link:hover {
  color: #0d6efd;
  text-decoration: underline;
}
```

### JavaScript Implementation

```javascript
function updateSignalsSection(data) {
  // Gold/Credit Divergence
  const divergence = data.divergence || {};
  const divPercentile = divergence.percentile || 50;
  let divStatus = getSignalStatus(divPercentile, 'divergence');
  updateSignalCard('divergence', divStatus, divPercentile);

  // Yield Curve
  const curveSpread = (data.treasury_10y?.value || 4.0) - (data.treasury_2y?.value || 4.0);
  let yieldStatus = getYieldCurveStatus(curveSpread);
  const yieldPercentile = calculateYieldCurvePercentile(curveSpread);
  updateSignalCard('yieldcurve', yieldStatus, yieldPercentile);

  // VIX Term Structure (using VIX level as proxy if term structure unavailable)
  const vix = data.vix?.value || 15;
  let vixStatus = getVIXStatus(vix);
  const vixPercentile = data.vix?.percentile || 50;
  updateSignalCard('vixterm', vixStatus, vixPercentile);
}

function getSignalStatus(percentile, type) {
  if (percentile > 90) return { icon: '🔴', label: 'CRITICAL', class: 'critical' };
  if (percentile > 70) return { icon: '⚠️', label: 'ELEVATED', class: 'elevated' };
  if (percentile > 50) return { icon: 'ℹ️', label: 'NOTABLE', class: 'notable' };
  return { icon: '✓', label: 'NORMAL', class: 'normal' };
}

function getYieldCurveStatus(spread) {
  if (spread < -0.5) return { icon: '🔴', label: 'DEEPLY INVERTED', class: 'critical' };
  if (spread < 0) return { icon: '⚠️', label: 'INVERTED', class: 'elevated' };
  if (spread < 0.25) return { icon: 'ℹ️', label: 'FLAT', class: 'notable' };
  return { icon: '✓', label: 'NORMAL', class: 'normal' };
}

function getVIXStatus(vix) {
  if (vix > 30) return { icon: '🔴', label: 'FEAR SPIKE', class: 'critical' };
  if (vix > 25) return { icon: '⚠️', label: 'STRESSED', class: 'elevated' };
  if (vix > 20) return { icon: 'ℹ️', label: 'ELEVATED', class: 'notable' };
  return { icon: '✓', label: 'NORMAL', class: 'normal' };
}

function calculateYieldCurvePercentile(spread) {
  // Simplified percentile calculation
  // Historical range roughly: -1.0% to +2.5%
  // Inverted (negative) = high percentile (unusual)
  if (spread < -0.5) return 98;
  if (spread < 0) return 90;
  if (spread < 0.25) return 70;
  if (spread < 0.5) return 50;
  if (spread < 1.0) return 30;
  return 15;
}

function updateSignalCard(id, status, percentile) {
  const statusEl = document.getElementById(`${id}-status`);
  const percentileEl = document.getElementById(`${id}-percentile`);

  if (statusEl) {
    statusEl.innerHTML = `
      <span class="signal-icon">${status.icon}</span>
      <span class="signal-label ${status.class}">${status.label}</span>
    `;
  }

  if (percentileEl) {
    percentileEl.textContent = `${Math.round(percentile)}${getOrdinalSuffix(percentile)} Percentile`;
  }
}

function getOrdinalSuffix(n) {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return s[(v - 20) % 10] || s[v] || s[0];
}
```

---

## Definition of Done

- [ ] Signals section displays in correct position
- [ ] All 3 signal cards render correctly
- [ ] Status icons and labels update based on data
- [ ] Percentile rankings display correctly
- [ ] Explanatory text is readable and helpful
- [ ] "View All Signals" link works
- [ ] Gold-Implied Spread removed/demoted from primary metrics
- [ ] Responsive layout works on all breakpoints
- [ ] Code is reviewed and approved
- [ ] Manual testing on Chrome, Firefox, Safari
- [ ] No console errors
- [ ] Merged to main branch

---

## Dependencies

- Existing divergence data in `/api/dashboard`
- Treasury yield data for yield curve calculation
- VIX data for VIX term structure (or proxy)

---

## Notes for Developer

1. The existing divergence display is prominent in the current homepage - identify and demote those elements
2. The divergence PAGE (`/divergence`) should remain unchanged - we're only repositioning on the homepage
3. If VIX term structure data isn't available, use VIX level as a proxy (documented in AC4)
4. The percentile calculation for yield curve is simplified - consider improving accuracy in future iterations
5. This story prepares for Phase 2.1's unified Signals page - the structure should be extensible to add more signals later
6. Remove any "Crisis Score" or similar single-thesis branding from the homepage
