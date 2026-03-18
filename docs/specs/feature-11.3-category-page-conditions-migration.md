# Category Page Conditions Migration — Quadrant × Liquidity Context

**Issue:** #324
**Feature:** 11.3 — Category Page Conditions Migration
**Created:** 2026-03-17
**Status:** Draft

---

## Overview

Update all six category detail pages (Credit, Rates, Equities, Dollar, Crypto, Safe Havens) plus the Property page to use quadrant-based context sentences and signal annotations instead of the old regime-based ones.

The current system provides 4 context sentences per category (one per regime: Bull/Neutral/Bear/Recession Watch). The new system provides 12 context sentences per category (4 quadrants × 3 liquidity states), giving dramatically more specific and actionable guidance.

**Replaces:** `CATEGORY_REGIME_CONTEXT` and `SIGNAL_REGIME_ANNOTATIONS` in `regime_config.py`

---

## Current System

### Context Sentences (regime_config.py)

Each category has 4 sentences keyed by regime:
```python
'Credit': {
    'Bull': 'Spreads are tight; credit is a carry trade in this regime.',
    'Bear': 'Spreads widening; credit stress is building here.',
    ...
}
```

Displayed via `_regime_strip.html` below the regime badge.

### Signal Annotations (regime_config.py)

18 signals × 4 regimes = 72 annotation strings. Displayed via `{% from '_macros.html' import regime_annotation %}` on expanded metric cards.

---

## New System

### Context Sentences — Quadrant × Liquidity

Each category gets 12 context sentences: 4 quadrants × 3 liquidity states. These appear below the conditions strip (Feature #322) as a category-specific context paragraph.

**Max 120 characters per sentence** (slightly longer than current 100 to accommodate the richer context).

### New Config File: `conditions_config.py`

Replaces the regime-specific sections of `regime_config.py`. Structure:

```python
CATEGORY_CONDITIONS_CONTEXT = {
    'Credit': {
        ('Goldilocks', 'Expanding'): '...',
        ('Goldilocks', 'Neutral'): '...',
        ('Goldilocks', 'Contracting'): '...',
        ('Reflation', 'Expanding'): '...',
        ('Reflation', 'Neutral'): '...',
        ('Reflation', 'Contracting'): '...',
        ('Stagflation', 'Expanding'): '...',
        ('Stagflation', 'Neutral'): '...',
        ('Stagflation', 'Contracting'): '...',
        ('Deflation Risk', 'Expanding'): '...',
        ('Deflation Risk', 'Neutral'): '...',
        ('Deflation Risk', 'Contracting'): '...',
    },
    # ... 6 more categories
}
```

**Liquidity state simplification for context lookup:** The 5 liquidity states (Strongly Expanding, Expanding, Neutral, Contracting, Strongly Contracting) map to 3 for context sentence lookup:
- Strongly Expanding / Expanding → `'Expanding'`
- Neutral → `'Neutral'`
- Contracting / Strongly Contracting → `'Contracting'`

This keeps the sentence count manageable (12 per category, not 20) while still capturing the key distinction.

---

## Context Sentences by Category

### Credit (7 categories × 12 = 84 total sentences)

| Quadrant | Liquidity | Context Sentence |
|----------|-----------|-----------------|
| Goldilocks | Expanding | Credit spreads historically tighten further in Goldilocks with expanding liquidity — carry trades supported. |
| Goldilocks | Neutral | Goldilocks conditions support credit; spreads should remain well-behaved. |
| Goldilocks | Contracting | Goldilocks supports credit quality, but contracting liquidity may limit spread compression. |
| Reflation | Expanding | Rising inflation pressures credit quality, but expanding liquidity provides a cushion. |
| Reflation | Neutral | Rising inflation creates headwinds for lower-quality credit; favor investment grade. |
| Reflation | Contracting | Tightening liquidity and rising inflation create headwinds for lower-quality credit. |
| Stagflation | Expanding | Stagflation is historically tough for credit — expanding liquidity may cushion but doesn't fix fundamentals. |
| Stagflation | Neutral | Stagflation is the worst environment for credit — expect spread widening. |
| Stagflation | Contracting | Severe credit stress likely. Spreads at current levels may underestimate risk. |
| Deflation Risk | Expanding | Flight to quality benefits high-grade credit; expanding liquidity limits systemic risk. |
| Deflation Risk | Neutral | Flight to quality underway; focus on investment-grade credit, avoid high-yield. |
| Deflation Risk | Contracting | Credit contraction underway. Focus on balance sheet quality and short duration. |

### Rates

| Quadrant | Liquidity | Context Sentence |
|----------|-----------|-----------------|
| Goldilocks | Expanding | Falling inflation supports bonds; expanding liquidity adds a tailwind to duration. |
| Goldilocks | Neutral | Goldilocks supports bonds as inflation cools; duration is rewarded. |
| Goldilocks | Contracting | Inflation cooling supports bonds, but liquidity contraction may limit gains. |
| Reflation | Expanding | Rising inflation pressures bonds; expanding liquidity creates cross-currents in rates. |
| Reflation | Neutral | Rising inflation is a headwind for bonds; shorter duration reduces risk. |
| Reflation | Contracting | Rising inflation and contracting liquidity both weigh on bonds — shorten duration. |
| Stagflation | Expanding | Stagflation puts bonds under pressure from inflation; expanding liquidity partially offsets. |
| Stagflation | Neutral | Bonds struggle in stagflation — rising inflation and slowing growth create uncertainty. |
| Stagflation | Contracting | Worst case for bonds: rising inflation meets contracting liquidity. Minimize duration. |
| Deflation Risk | Expanding | Deflation risk drives flight to safety; bonds rally as rate cuts are priced in. |
| Deflation Risk | Neutral | Falling inflation and slowing growth support long bonds; rate cuts likely ahead. |
| Deflation Risk | Contracting | Flight to safety bid supports Treasuries despite liquidity contraction. |

### Equities

| Quadrant | Liquidity | Context Sentence |
|----------|-----------|-----------------|
| Goldilocks | Expanding | Best environment for equities: accelerating growth, cooling inflation, expanding liquidity. |
| Goldilocks | Neutral | Goldilocks favors equities broadly; growth stocks and tech historically outperform. |
| Goldilocks | Contracting | Growth and inflation favor equities, but contracting liquidity may cap upside. |
| Reflation | Expanding | Growth and liquidity support equities; watch for inflation eroding real returns. |
| Reflation | Neutral | Equities benefit from growth; cyclicals and commodities-linked sectors outperform. |
| Reflation | Contracting | Rising inflation with tightening liquidity creates rotation risk — favor pricing power. |
| Stagflation | Expanding | Stagflation is tough for equities; expanding liquidity may cushion but doesn't reverse headwinds. |
| Stagflation | Neutral | Worst quadrant for equity real returns — defensive sectors and pricing power outperform. |
| Stagflation | Contracting | Maximum headwinds for equities: slowing growth, rising inflation, tight liquidity. |
| Deflation Risk | Expanding | Equities face growth headwinds, but expanding liquidity signals policy response — watch for reversal. |
| Deflation Risk | Neutral | Slowing growth weighs on equities; defensive positioning and quality factors favored. |
| Deflation Risk | Contracting | Growth slowing with tight liquidity — risk of accelerating drawdowns. Preserve capital. |

### Dollar

| Quadrant | Liquidity | Context Sentence |
|----------|-----------|-----------------|
| Goldilocks | Expanding | Risk-on flows and expanding liquidity typically weaken the dollar; EM assets benefit. |
| Goldilocks | Neutral | Dollar range-bound in Goldilocks; no strong directional catalyst. |
| Goldilocks | Contracting | Contracting liquidity supports the dollar despite favorable growth conditions. |
| Reflation | Expanding | Rising inflation and loose liquidity weaken dollar purchasing power; commodities benefit. |
| Reflation | Neutral | Dollar mixed in reflation — inflation weakens, but rate hike expectations support. |
| Reflation | Contracting | Rate hike expectations from inflation plus tight liquidity support a stronger dollar. |
| Stagflation | Expanding | Dollar weakens as stagflation erodes confidence; liquidity flows seek alternatives. |
| Stagflation | Neutral | Dollar direction depends on whether markets price growth weakness or inflation first. |
| Stagflation | Contracting | Safe-haven dollar demand competes with stagflation erosion — volatile, range-bound. |
| Deflation Risk | Expanding | Policy response (liquidity expansion) fights deflationary dollar strength — watch Fed actions. |
| Deflation Risk | Neutral | Dollar strengthens on safe-haven demand; EM and carry trades face pressure. |
| Deflation Risk | Contracting | Strong dollar safe-haven bid; global dollar shortage risk for EM borrowers. |

### Crypto

| Quadrant | Liquidity | Context Sentence |
|----------|-----------|-----------------|
| Goldilocks | Expanding | Expanding liquidity is the primary crypto driver — historically favorable with ~90-day lag. |
| Goldilocks | Neutral | Liquidity neutral; crypto direction depends on cycle-specific factors, not macro quadrant. |
| Goldilocks | Contracting | Contracting liquidity is a headwind for crypto regardless of favorable macro conditions. |
| Reflation | Expanding | Expanding liquidity supports crypto; Bitcoin correlates 0.94 with M2, not growth/inflation. |
| Reflation | Neutral | Liquidity neutral; crypto may benefit from inflation hedge narrative but primary driver is flat. |
| Reflation | Contracting | Contracting liquidity weighs on crypto despite reflation narrative — M2 matters more than CPI. |
| Stagflation | Expanding | Expanding liquidity supports crypto even in stagflation — the M2 correlation dominates. |
| Stagflation | Neutral | Liquidity flat in stagflation; crypto driven by halving cycle and institutional flows. |
| Stagflation | Contracting | Contracting liquidity in stagflation is the worst combination for crypto risk assets. |
| Deflation Risk | Expanding | Policy-driven liquidity expansion (QE) historically triggers strong crypto recoveries. |
| Deflation Risk | Neutral | Liquidity neutral with deflation risk; crypto volatile but watch for policy response pivot. |
| Deflation Risk | Contracting | Contracting liquidity in deflation — maximum headwind for crypto. Watch for QE pivot. |

### Safe Havens

| Quadrant | Liquidity | Context Sentence |
|----------|-----------|-----------------|
| Goldilocks | Expanding | Safe havens underperform in Goldilocks; gold neutral, Treasuries supported by falling inflation. |
| Goldilocks | Neutral | Safe havens are secondary in Goldilocks; hold for diversification, not returns. |
| Goldilocks | Contracting | Goldilocks limits safe haven demand, but liquidity contraction adds a hedge rationale. |
| Reflation | Expanding | Gold benefits from inflation + liquidity expansion; Treasuries struggle with rising rates. |
| Reflation | Neutral | Gold outperforms on inflation hedge; Treasuries underperform. Mixed safe haven picture. |
| Reflation | Contracting | Gold mixed (inflation bullish, liquidity bearish); Treasuries face dual headwinds. |
| Stagflation | Expanding | Gold shines in stagflation — best quadrant historically. Expanding liquidity amplifies. |
| Stagflation | Neutral | Gold is the primary safe haven in stagflation; Treasuries hurt by rising inflation. |
| Stagflation | Contracting | Gold remains best haven in stagflation but liquidity headwind limits upside. |
| Deflation Risk | Expanding | Treasuries rally on flight to safety; gold mixed — benefits from uncertainty, hurt by deflation. |
| Deflation Risk | Neutral | Flight to safety drives Treasuries higher; gold benefits from uncertainty premium. |
| Deflation Risk | Contracting | Maximum flight to safety — Treasuries are the primary safe haven. Gold secondary. |

### Property

| Quadrant | Liquidity | Context Sentence |
|----------|-----------|-----------------|
| Goldilocks | Expanding | Best environment for property: growth supports rents, expanding liquidity supports prices. |
| Goldilocks | Neutral | Goldilocks supports property fundamentals; low rates and growth favor housing. |
| Goldilocks | Contracting | Growth supports property fundamentals but tightening liquidity may slow price appreciation. |
| Reflation | Expanding | Property benefits from inflation hedging; expanding liquidity supports mortgage availability. |
| Reflation | Neutral | Rising inflation supports property as a real asset; watch mortgage rate pressure. |
| Reflation | Contracting | Inflation supports property values but tightening liquidity restricts mortgage access. |
| Stagflation | Expanding | Property fundamentals challenged by slowing growth; expanding liquidity partially offsets. |
| Stagflation | Neutral | Slowing growth weakens rental demand; rising inflation supports real asset valuations. |
| Stagflation | Contracting | Tough environment for property: slowing growth, rising costs, tight financing. |
| Deflation Risk | Expanding | Deflation risk threatens property values; policy response (rate cuts) supports housing. |
| Deflation Risk | Neutral | Falling prices and slowing growth pressure property; watch for policy pivot. |
| Deflation Risk | Contracting | Maximum property headwinds: falling demand, tight credit, deflationary pressure. |

---

## Context Sentence Display

The context sentence appears below the conditions strip on each category page, replacing the current regime context line.

### Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ● GOLDILOCKS     Liquidity: Expanding ↑ │ Risk: Calm │ Policy: Easing ↑ │  ← strip
├──────────────────────────────────────────────────────────────────────────┤
│  Credit spreads historically tighten further in Goldilocks with          │  ← context
│  expanding liquidity — carry trades supported.                           │
└──────────────────────────────────────────────────────────────────────────┘
```

**Styling:**
- `text-sm`, `neutral-600`, `font-style: italic`
- Padding: `space-2` vertical, same horizontal as strip
- Background: same as strip (`neutral-100`)
- No border between strip and context — they read as one unit
- Max 120 characters, single line on desktop, wraps to 2 lines on mobile

### Template Change

In each category template, replace:
```jinja2
{% set page_category = 'Credit' %}
{% include '_regime_strip.html' %}
```

With:
```jinja2
{% set page_category = 'Credit' %}
{% include '_conditions_strip.html' %}
```

The `_conditions_strip.html` component (Feature #322) handles the context sentence display internally, using `page_category` to look up the appropriate sentence from the injected `category_conditions_context` dict.

---

## Signal Annotations — Quadrant-Based

### New Structure

Each signal gets annotations keyed by quadrant instead of regime. The annotation provides context for why this metric matters given the current quadrant.

**New config in `conditions_config.py`:**

```python
SIGNAL_CONDITIONS_ANNOTATIONS = {
    'high_yield_spread': {
        'Goldilocks': '✓ Tight spreads expected in Goldilocks; carry trade supported.',
        'Reflation': '─ Growth supports credit, but rising inflation pressures margins.',
        'Stagflation': '▲ Spreads typically widen in stagflation; default risk rises.',
        'Deflation Risk': '▲ Flight to quality widens HY spreads; avoid lower-rated credit.',
    },
    'investment_grade_spread': {
        'Goldilocks': '✓ IG spreads tight; investment-grade credit well-supported.',
        'Reflation': '─ IG credit stable; inflation risk mostly in lower quality.',
        'Stagflation': '▲ IG spreads widening; even quality credit faces pressure.',
        'Deflation Risk': '✓ IG benefits from flight to quality; relative safe haven.',
    },
    'ccc_spread': {
        'Goldilocks': '✓ CCC spreads tight; risk appetite elevated in Goldilocks.',
        'Reflation': '─ CCC credit mixed; growth helps, inflation hurts margins.',
        'Stagflation': '▲ CCC spreads widen sharply; highest default risk segment.',
        'Deflation Risk': '▲ Avoid CCC credit in deflation risk; defaults accelerate.',
    },
    'yield_curve_10y2y': {
        'Goldilocks': '✓ Steepening curve confirms accelerating growth outlook.',
        'Reflation': '─ Curve shape depends on whether Fed is behind inflation.',
        'Stagflation': '▲ Curve inversion risk as Fed fights inflation into slowdown.',
        'Deflation Risk': '▲ Inversion deepening; growth deceleration confirmed.',
    },
    'yield_curve_10y3m': {
        'Goldilocks': '✓ Positive slope confirms expansion; growth leading indicator.',
        'Reflation': '─ Slope depends on short-end rate expectations.',
        'Stagflation': '▲ Inversion likely as Fed tightens into slowdown.',
        'Deflation Risk': '▲ Deep inversion; recession probability elevated.',
    },
    'treasury_10y': {
        'Goldilocks': '─ Yields stable-to-falling as inflation cools; duration rewarded.',
        'Reflation': '▲ Rising yields reflect inflation expectations; duration penalized.',
        'Stagflation': '▲ Yields volatile — inflation pushes up, growth fears pull down.',
        'Deflation Risk': '✓ Yields fall on flight to safety and rate cut expectations.',
    },
    'nfci': {
        'Goldilocks': '✓ Loose conditions support Goldilocks; risk assets benefit.',
        'Reflation': '─ Conditions tightening as Fed responds to inflation.',
        'Stagflation': '▲ Tightening conditions amplify stagflation pain.',
        'Deflation Risk': '▲ Tight conditions accelerate growth slowdown.',
    },
    'initial_claims': {
        'Goldilocks': '✓ Low claims confirm healthy labor market and growth.',
        'Reflation': '✓ Low claims; labor market tight — inflation pressure.',
        'Stagflation': '▲ Rising claims signal growth deceleration is hitting jobs.',
        'Deflation Risk': '▲ Rising claims confirm growth slowdown is broadening.',
    },
    'continuing_claims': {
        'Goldilocks': '✓ Low continuing claims; labor market absorbing workers.',
        'Reflation': '✓ Low claims; tight labor market fueling wage inflation.',
        'Stagflation': '▲ Rising continuing claims; re-employment getting harder.',
        'Deflation Risk': '▲ Elevated claims; labor market deterioration underway.',
    },
    'consumer_confidence': {
        'Goldilocks': '✓ High confidence supports consumer spending and growth.',
        'Reflation': '─ Confidence mixed; growth helps but inflation erodes sentiment.',
        'Stagflation': '▲ Falling confidence; inflation and job fears compound.',
        'Deflation Risk': '▲ Low confidence; spending pullback likely.',
    },
    'vix': {
        'Goldilocks': '✓ Low VIX consistent with Goldilocks calm; complacency risk.',
        'Reflation': '─ VIX normal; markets pricing growth over inflation risk.',
        'Stagflation': '▲ Elevated VIX expected; stagflation uncertainty.',
        'Deflation Risk': '▲ VIX spikes on growth fears; hedging demand elevated.',
    },
    'gold': {
        'Goldilocks': '─ Gold neutral-to-weak in Goldilocks; risk assets preferred.',
        'Reflation': '✓ Gold benefits from inflation hedge demand.',
        'Stagflation': '✓ Gold outperforms in stagflation — best quadrant for gold.',
        'Deflation Risk': '─ Gold mixed; uncertainty supports, deflation headwind.',
    },
    'real_yield_10y': {
        'Goldilocks': '─ Real yields stable; no strong directional signal.',
        'Reflation': '▲ Rising real yields constrain gold and growth multiples.',
        'Stagflation': '─ Real yields volatile; depends on inflation vs. growth pricing.',
        'Deflation Risk': '✓ Falling real yields support gold and long-duration assets.',
    },
    'breakeven_inflation_10y': {
        'Goldilocks': '✓ Breakevens falling confirms inflation deceleration.',
        'Reflation': '▲ Rising breakevens signal accelerating inflation expectations.',
        'Stagflation': '▲ Elevated breakevens confirm sticky inflation despite slowdown.',
        'Deflation Risk': '✓ Falling breakevens confirm disinflation / deflation risk.',
    },
    'sp500': {
        'Goldilocks': '✓ Equities favored in Goldilocks; best real return quadrant.',
        'Reflation': '✓ Equities benefit from growth; real returns moderate.',
        'Stagflation': '▲ Worst quadrant for equity real returns historically.',
        'Deflation Risk': '▲ Growth slowdown weighs on equities; watch policy response.',
    },
    'fed_funds_rate': {
        'Goldilocks': '─ Rate level less important than direction in Goldilocks.',
        'Reflation': '▲ Rate hikes expected as Fed fights rising inflation.',
        'Stagflation': '▲ Fed trapped — hiking into slowdown historically ends badly.',
        'Deflation Risk': '✓ Rate cuts expected or underway; watch pace and market response.',
    },
    'fed_balance_sheet': {
        'Goldilocks': '─ Balance sheet stable; no active QE/QT signal.',
        'Reflation': '▲ QT likely as Fed fights inflation; liquidity withdrawal.',
        'Stagflation': '─ Fed policy uncertain; balance sheet direction a key variable.',
        'Deflation Risk': '✓ QE restart likely; liquidity injection supports recovery.',
    },
    'm2_money_supply': {
        'Goldilocks': '✓ M2 growth supports Goldilocks conditions.',
        'Reflation': '▲ M2 growth may fuel further inflation.',
        'Stagflation': '─ M2 direction is a key variable in resolving stagflation.',
        'Deflation Risk': '▲ Contracting M2 deepens deflation risk.',
    },
    'dollar_index': {
        'Goldilocks': '─ Dollar range-bound in Goldilocks; risk-on flows mild headwind.',
        'Reflation': '─ Dollar mixed; inflation weakens but rate expectations support.',
        'Stagflation': '─ Dollar direction depends on growth vs. inflation pricing.',
        'Deflation Risk': '▲ Dollar strengthens on safe-haven demand; EM pressure.',
    },
}
```

### Annotation Display

The `regime_annotation` macro in `_macros.html` is updated to use the new quadrant-based annotations:

**Current:**
```jinja2
{% set _text = signal_regime_annotations.get(signal_key, {}).get(macro_regime.state, '') %}
```

**New:**
```jinja2
{% set _text = signal_conditions_annotations.get(signal_key, {}).get(market_conditions.quadrant, '') %}
```

The label changes from "Regime Context" to "Conditions Context":
```jinja2
<span class="regime-annotation__label">Conditions Context</span>
```

The CSS class can stay as `regime-annotation` during migration or be renamed to `conditions-annotation` — engineer's discretion since it's a non-breaking internal name.

---

## Relocated Sections

### Recession Probability Panel → Credit Page

The full 3-model recession probability panel (currently homepage §0.5) moves to the Credit page. It appears after the existing credit metrics, before the chart section.

**Placement:** After the credit signal cards, as a new section with the existing recession panel markup unchanged. The section header and collapse behavior remain identical.

**Rationale:** Recession probability directly impacts credit spreads and default rates. A user looking at HY spreads and asking "should I be worried?" finds the answer right there.

**On the homepage:** A single line in the Risk dimension expand card shows the headline recession probability with a link to the Credit page panel. See Feature #323 spec (Risk expand card) for details.

### Sector Management Tone → Equities Page

The 11-GICS-sector tone panel (currently homepage §1.5) moves to the Equities page. It appears after the equity metrics section.

**Placement:** After the existing equity signal cards, as a new section. The sector grid, collapse behavior, and tone colors remain identical.

**Rationale:** Sector rotation is equity-specific analysis. Users viewing equity conditions will naturally want sector context.

### Global Trade Pulse → Equities Page

The trade pulse panel (currently homepage §1.3) moves to the Equities page. It appears after the Sector Tone section.

**Placement:** After the sector tone section. The percentile bar, interpretation block, and 16-combination copy remain identical.

**Rationale:** Trade balance is a growth signal that most directly affects corporate earnings and sector rotation.

**On the homepage:** A single line in the Growth×Inflation quadrant detail (if expanded) shows trade balance as one of the growth metrics with a link to the explorer. See Feature #323 spec for details.

---

## Crypto Page — Liquidity Leads

The Crypto page has a special behavior: the conditions strip shows Liquidity as the headline instead of the quadrant (Feature #322 handles the strip component). The context sentence also emphasizes liquidity:

All 12 Crypto context sentences (see above) lead with the liquidity state as the primary driver, with the quadrant as secondary context. This reflects the 0.94 correlation between Bitcoin and M2.

---

## Migration Checklist

### Templates to Update

| File | Changes |
|------|---------|
| `credit.html` | Replace `_regime_strip.html` include → `_conditions_strip.html`. Add recession probability panel section. |
| `rates.html` | Replace strip include. |
| `equity.html` | Replace strip include. Add sector tone section. Add trade pulse section. |
| `dollar.html` | Replace strip include. |
| `crypto.html` | Replace strip include. Set `conditions_strip_liquidity_leads = true`. |
| `safe_havens.html` | Replace strip include. |
| `property.html` | Replace strip include (if not already using new strip). |
| `_macros.html` | Update `regime_annotation` macro to read from `signal_conditions_annotations`. |

### Backend Changes

| File | Changes |
|------|---------|
| `conditions_config.py` (new) | All 84 context sentences + 18×4 signal annotations |
| `dashboard.py` | Update context processor to inject `category_conditions_context` and `signal_conditions_annotations` from new config alongside existing regime data |

### Files Unchanged

- All template CSS — no visual changes to signal cards, metric layouts, or page structure
- Chart components, time range controls, explorer links
- The actual signal data pipeline and metric display

---

## Accessibility

- Context sentences use same ARIA pattern as current regime context (`role="complementary"`)
- Signal annotations maintain existing expand/collapse ARIA (`aria-expanded`, `aria-controls`)
- No new interactive elements — same touch targets, keyboard navigation, and focus management
- All text meets existing AA contrast standards (no color changes to text)

---

## Dependencies

- **Feature #322 (Conditions Strip Component)** must be implemented first — the strip is the shared component these pages include
- **Phase 10 complete** — `market_conditions_cache.json` must be populated with current conditions data
- Relocated sections (Recession Probability → Credit, Sector Tone → Equities, Trade Pulse → Equities) can be implemented as part of this feature or as separate user stories at PM discretion
