# Homepage Conditions Redesign — Quadrant-Led Layout

**Issue:** #323
**Feature:** 11.2 — Homepage Conditions Redesign
**Created:** 2026-03-17
**Status:** Draft

---

## Overview

Redesign the homepage around the market conditions engine. The page answers one question in under 60 seconds: **"What's happening in the macro world right now, and what does it mean for my portfolio?"**

The AI briefing tells the story in words. The conditions model shows it in structure. Together they form a complete picture — narrative and data — telling the same story from two angles.

**Replaces:** The current 10-section homepage (Macro Regime Score, Recession Probability, Regime Implications, Sector Tone, Market Conditions at a Glance, Trade Pulse, AI Briefing, What's Moving, Market Signals, Prediction Market)

**Reference:** [MARKET-CONDITIONS-FRAMEWORK.md — Sections 7-8](../MARKET-CONDITIONS-FRAMEWORK.md)

---

## Homepage Structure

Three focused sections plus a lightweight footer strip:

| Position | Section | Purpose | Time to Absorb |
|----------|---------|---------|----------------|
| Strip | Conditions Strip | Persistent quadrant + dimensions (shared component, Feature #322) | 2 seconds |
| §0 | AI Briefing | Lead narrative — the daily hook | 30 seconds |
| §1 | Market Conditions | Quadrant hero + 2×2 dimension cards with expand-in-place | 10 sec (collapsed) / 2 min (expanded) |
| §2 | What This Means | Portfolio implications matrix — the actionable takeaway | 15 seconds |
| Footer | Today's Movers | Lightweight strip — daily pulse of biggest movers | 5 seconds |

**Target scroll length:** ~1600px mobile (3 screens), ~1200px desktop (1.5 screens). Under 60 seconds to absorb the full page without expanding any cards.

---

## Sections Removed from Homepage

| Current Section | Destination | Rationale |
|----------------|-------------|-----------|
| §0 Macro Regime Score | Removed — replaced by §1 quadrant | Old k-means model replaced by conditions engine |
| §0.5 Recession Probability | Single line in Risk expand + full panel on **Credit page** | Supporting data, not headline |
| §0.75 Regime Implications | Replaced by §2 implications matrix | New matrix is more transparent (shows per-dimension breakdown) |
| §1.5 Sector Management Tone | **Equities page** | Sector-level detail, not macro conditions |
| §1 Market Conditions at a Glance | Removed — signals absorbed into dimension expands | Redundant: each signal now appears in its dimension context |
| §1.3 Global Trade Pulse | Single line in Growth metrics + full panel on **Equities page** | Growth input, not standalone headline |
| §2 AI Briefing | Promoted to §0 | Was buried at position 7; now leads the page |
| §3 What's Moving | Demoted to lightweight footer strip | Daily pulse stays, but as secondary element |
| §4 Cross-Market Indicators | Removed — absorbed into dimension expands | Signals feed the model; show them in context |
| §5 Prediction Market | Removed | Feed unreliable; can return when source stabilizes |

---

## §0: AI Briefing

The AI briefing moves to the top of the page. It is the daily draw — the reason users come back every morning.

### Mobile (375px)

```
┌─────────────────────────────────────────┐
│                                         │
│  DAILY BRIEFING            Mar 17, 2026 │
│  ─────────────────────────────────────  │
│                                         │
│  Markets are in a Goldilocks environ-   │
│  ment with growth accelerating and      │
│  inflation moderating. Liquidity is     │
│  expanding as M2 growth turns positive. │
│                                         │
│  Risk indicators remain calm. Policy    │
│  is neutral-to-easing with markets      │
│  pricing two cuts by year-end.          │
│                                         │
│  This historically favors growth stocks │
│  and long bonds. Watch breakevens —     │
│  approaching the Reflation threshold.   │
│                                         │
└─────────────────────────────────────────┘
```

### Desktop (1280px)

Same content, constrained to ~65ch max-width for comfortable reading. Centered within the container.

### Design Details

- **Section header:** "DAILY BRIEFING" with date right-aligned. Same `section-header` pattern as existing sections. Icon: `bi-newspaper` (or existing AI sparkle icon from Feature 9.3).
- **Body:** 2-3 paragraphs, `text-base` (16px), `neutral-700`, `line-height: 1.6`
- **Container:** White card with subtle border (`neutral-200`), padding `space-5`
- **AI provenance:** Small "AI-generated" badge below the briefing text, same pattern as current briefing section
- **No progressive disclosure needed** — the briefing is short enough to display in full
- **Section ID:** `briefing-section`

### Data Source

Same as current: `ai_summary` from the AI briefing pipeline. No changes to the data model — only the position on the page changes.

---

## §1: Market Conditions

The core of the redesign. Shows the quadrant as the hero element with four supporting dimension cards in a 2×2 grid below.

### Mobile (375px)

```
┌─────────────────────────────────────────┐
│                                         │
│  MARKET CONDITIONS                      │
│  ─────────────────────────────────────  │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │                                 │    │
│  │  ● GOLDILOCKS                   │    │
│  │  Growth accelerating, inflation │    │
│  │  cooling — best environment     │    │
│  │  for portfolios                 │    │
│  │                                 │    │
│  │      Growth ↑                   │    │
│  │       │                         │    │
│  │  Refl │  Goldi                  │    │
│  │       │    ●←·←·                │    │
│  │  ─────┼──────── Infl ↓          │    │
│  │       │                         │    │
│  │  Stag │  Defl                   │    │
│  │       │                         │    │
│  │      Growth ↓                   │    │
│  │                                 │    │
│  │  Favored: Growth stocks, Long   │    │
│  │  bonds, Tech                    │    │
│  │  Watch: Breakevens near         │    │
│  │  Reflation threshold            │    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌───────────────┐ ┌───────────────┐    │
│  │ LIQUIDITY     │ │ RISK          │    │
│  │ [====●======] │ │ [●==========] │    │
│  │ Expanding  ↑  │ │ Calm          │    │
│  │        ⌄      │ │        ⌄      │    │
│  └───────────────┘ └───────────────┘    │
│  ┌───────────────┐ ┌───────────────┐    │
│  │ POLICY        │ │ ✦ CRYPTO      │    │
│  │ [========●==] │ │ Liquidity is  │    │
│  │ Easing    ↑   │ │ expanding ↑   │    │
│  │        ⌄      │ │  Favorable    │    │
│  └───────────────┘ └───────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

### Desktop (1280px)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  MARKET CONDITIONS                                                      │
│  ──────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  ┌──────────────────────────────────────┬──────────────────────────────┐│
│  │                                      │                              ││
│  │  ● GOLDILOCKS                        │        Growth ↑              ││
│  │  Growth accelerating, inflation      │         │                    ││
│  │  cooling — best environment          │   Refl  │  Goldi             ││
│  │  for portfolios                      │         │    ●←·←·←·         ││
│  │                                      │   ─────┼────────── Infl ↓   ││
│  │  Favored: Growth stocks, Long bonds  │         │                    ││
│  │  Watch: Breakevens near Reflation    │   Stag  │  Defl Risk         ││
│  │                                      │         │                    ││
│  │                                      │        Growth ↓              ││
│  │                                      │                              ││
│  └──────────────────────────────────────┴──────────────────────────────┘│
│                                                                          │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌───────────┐│
│  │ LIQUIDITY      │ │ RISK           │ │ POLICY         │ │ ✦ CRYPTO  ││
│  │ [====●=======] │ │ [●===========] │ │ [========●===] │ │ Liq: ↑   ││
│  │ Expanding   ↑  │ │ Calm           │ │ Easing      ↑  │ │ Favorable ││
│  │         ⌄      │ │         ⌄      │ │         ⌄      │ │      ⌄    ││
│  └────────────────┘ └────────────────┘ └────────────────┘ └───────────┘│
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Quadrant Hero Card

The largest element in §1. Contains:

1. **Quadrant name** — colored dot + name (e.g., "● GOLDILOCKS"), `text-xl`, `font-weight: 700`
2. **Plain-English description** — "Growth accelerating, inflation cooling — best environment for portfolios", `text-base`, `neutral-600`
3. **Quadrant visualization** — 2×2 grid with positioned dot showing current location + trajectory trail
4. **Favored / Watch strip** — 2 lines max, `text-sm`, `neutral-600`

**Quadrant visualization details:**
- SVG or CSS grid, ~300×250px on mobile (full card width), ~350×300px on desktop (right half of card)
- Four quadrant labels: Goldilocks (top-right), Reflation (top-left), Stagflation (bottom-left), Deflation Risk (bottom-right)
- Current position: filled dot (12px), quadrant color, positioned by `growth_composite` (Y axis) and `inflation_composite` (X axis, inverted — falling inflation is right)
- Trajectory trail: 3-6 previous monthly positions as smaller dots (8px) connected by a line, opacity fading from 80% (most recent) to 30% (oldest)
- Current quadrant at full opacity background; other three at 15% opacity
- Axis labels: "Growth ↑" (top), "Growth ↓" (bottom), "Inflation Falling →" (right), "← Inflation Rising" (left)
- Center crosshair: 1px lines, `neutral-300`

**Quadrant interaction:**
- Tap/hover any quadrant region → tooltip: "Goldilocks: Growth accelerating + inflation falling. Historically favors growth stocks and long bonds."
- Tap the current dot → show exact composite values: "Growth: +0.6 / Inflation: -0.4"

**Data source for trajectory:** `market_conditions_history.json` — last 3-6 monthly entries providing `growth_composite` and `inflation_composite` values.

**Quadrant plain-English descriptions:**

| Quadrant | Description |
|----------|-------------|
| Goldilocks | Growth accelerating, inflation cooling — best environment for portfolios |
| Reflation | Growth accelerating, inflation rising — rising tide, watch for overheating |
| Stagflation | Growth slowing, inflation rising — toughest environment for portfolios |
| Deflation Risk | Growth slowing, inflation falling — flight to safety territory |

**Desktop layout:** 2-column card — left column has text (name, description, favored/watch), right column has quadrant visualization. Approximately 50/50 split.

**Mobile layout:** Single column — text on top, quadrant visualization below, favored/watch at bottom.

**Card styling:**
- White background, `border-radius: 12px`, subtle shadow (`0 1px 3px rgba(0,0,0,0.08)`)
- 4px top border in quadrant color
- Padding: `space-5` mobile, `space-6` desktop
- Section ID: `conditions-section`

### Dimension Cards — Collapsed State

Four cards in a 2×2 grid (mobile) or 4-across row (desktop):

| Position | Card | Content |
|----------|------|---------|
| Top-left / 1st | **Liquidity** | Spectrum bar + state label + direction arrow |
| Top-right / 2nd | **Risk** | Spectrum bar + state label |
| Bottom-left / 3rd | **Policy** | Spectrum bar + direction label + arrow |
| Bottom-right / 4th | **✦ Crypto** | Liquidity state + "Favorable" / "Neutral" / "Unfavorable" |

**Spectrum bar component** (shared by Liquidity, Risk, Policy):
- 8px tall horizontal bar, `border-radius: 4px`
- Background: `neutral-200`
- Filled portion: gradient from dimension's favorable color to unfavorable color
- Position marker: 12px circle at current score position
- Width: 100% of card content area

**Spectrum bar color endpoints:**

| Dimension | Left (favorable) | Right (unfavorable) |
|-----------|-----------------|---------------------|
| Liquidity | `#2563EB` (blue-600) Expanding | `#D97706` (amber-600) Contracting |
| Risk | `#3B82F6` (blue-500) Calm | `#DC2626` (red-600) Stressed |
| Policy | `#16A34A` (green-600) Easing | `#D97706` (amber-600) Tightening |

**Crypto card** (different from the three spectrum-bar cards):
- ✦ sparkle icon + "CRYPTO" label
- "Liquidity is expanding ↑" (or contracting ↓, neutral)
- "Favorable" / "Neutral" / "Unfavorable" label
- No spectrum bar — instead, a simple state label colored by the Liquidity dimension colors

**Card styling (all four):**
- White background, `border-radius: 8px`, 1px border `neutral-200`
- Padding: `space-3` mobile, `space-4` desktop
- Min-height: 80px collapsed
- Chevron (⌄) bottom-right indicates expandability
- Chevron rotates 180° when expanded

**Grid layout:**
- Mobile: `grid-template-columns: 1fr 1fr`, gap `space-3`
- Desktop: `grid-template-columns: repeat(4, 1fr)`, gap `space-4`

### Dimension Cards — Expanded State

Each card expands in place when the chevron is tapped. The expansion pushes content below downward (standard accordion behavior).

**Shared expansion structure:**

1. **Header** — dimension name + state + spectrum bar (unchanged from collapsed)
2. **Divider** — 1px line, `neutral-200`
3. **Component metrics** — 3-5 rows, each row links to explorer page for that metric
4. **Visual element** — sparkline, segmented bar, or dimension-specific visualization
5. **Interpretive paragraph** — 2-3 sentences, `text-sm`, `neutral-600`
6. **Cross-links** — "See more:" with links to relevant category pages
7. **Collapse chevron** (⌃) at bottom

**Metric row pattern:**

```
│ Fed Net Liquidity   $5.84T   ↑+2.3%  → │
```

- Label: `text-sm`, `neutral-500`, left-aligned
- Value: `text-sm`, `font-weight: 600`, `neutral-800`
- Direction: `text-sm`, colored (green ↑ / red ↓ / neutral →)
- Entire row is a link to `/explorer?metric=[SERIES_ID]`
- Touch target: full-width row, 44px min-height
- Hover: `neutral-50` background, subtle transition

#### Liquidity — Expanded

```
┌─────────────────────────────────────┐
│ LIQUIDITY                Expanding  │
│ [========●==============>]       ↑  │
├─────────────────────────────────────┤
│                                     │
│ Fed Net Liquidity   $5.84T  ↑+2.3% →│
│ US M2 Growth        +3.1% YoY  ↑   →│
│ ECB Balance Sheet   €6.18T  → flat  →│
│ BOJ Balance Sheet   ¥684T   ↓-1.2%  →│
│                                     │
│ [14-week trend ~~╱~~~─~~╱~~]        │
│                                     │
│ Liquidity is expanding, driven by   │
│ US M2 turning positive and Fed      │
│ balance sheet stabilization. ECB    │
│ flat, BOJ modestly tightening.      │
│ Net effect: supportive for risk     │
│ assets over 1-3 months.             │
│                                     │
│ See more: Credit → Rates →          │
│                                ⌃    │
└─────────────────────────────────────┘
```

**Component metrics:**
| Label | Source | Link |
|-------|--------|------|
| Fed Net Liquidity | Computed: WALCL - WDTGAL - (RRPONTSYD×1000) | `/explorer?metric=WALCL` |
| US M2 Growth | M2SL YoY rate | `/explorer?metric=M2SL` |
| ECB Balance Sheet | ECBASSETSW × DEXUSEU | `/explorer?metric=ECBASSETSW` |
| BOJ Balance Sheet | JPNASSETS converted | `/explorer?metric=JPNASSETS` |

**Visual:** 14-week sparkline from `market_conditions_history.json` liquidity scores. SVG polyline, 100×32px viewBox, `neutral-500` stroke.

**Cross-links:** Credit, Rates (pages most affected by liquidity)

#### Risk — Expanded

```
┌─────────────────────────────────────┐
│ RISK                         Calm   │
│ [●================================] │
├─────────────────────────────────────┤
│                                     │
│ VIX                  14.8   Low    →│
│ VIX Term Structure   0.88  Contango→│
│ Stock-Bond Corr.    -0.35  Divers. →│
│ Recession Prob.      4.2%  Low     →│
│                                     │
│ Score: 1 / 7                        │
│ ┌─────┬───────┬──────────┬────────┐ │
│ │Calm │Normal │ Elevated │Stressed│ │
│ │ ●   │       │          │        │ │
│ └─────┴───────┴──────────┴────────┘ │
│                                     │
│ All risk indicators are benign.     │
│ VIX in contango (short-term fear    │
│ below long-term — normal). Bonds    │
│ are diversifying stocks (negative   │
│ correlation). No near-term drawdown │
│ signal.                             │
│                                     │
│ See more: Equities → Safe Havens →  │
│                                ⌃    │
└─────────────────────────────────────┘
```

**Component metrics:**
| Label | Source | Link |
|-------|--------|------|
| VIX | VIXCLS | `/explorer?metric=VIXCLS` |
| VIX Term Structure | VIXCLS / VXVCLS ratio | `/explorer?metric=VXVCLS` |
| Stock-Bond Corr. | Computed 63-day rolling | `/explorer?metric=SP500` |
| Recession Prob. | Highest of 3 models | Link to Credit page recession panel |

**Visual:** 4-segment bar showing Calm / Normal / Elevated / Stressed with dot positioned at current score. Color gradient from blue (Calm) to red (Stressed).

**Note:** The "Recession Prob." row links to the **full recession probability panel on the Credit page** (not the explorer). This is the single-line summary discussed in design sessions — the full 3-model panel with bar charts and confidence ranges lives on the Credit page.

**Cross-links:** Equities, Safe Havens (pages most affected by risk environment)

#### Policy — Expanded

```
┌─────────────────────────────────────┐
│ POLICY                      Easing  │
│ [===================●======>]    ↑  │
├─────────────────────────────────────┤
│                                     │
│ Fed Funds Rate       4.25%         →│
│ Taylor Rule Says     4.55%         →│
│ Gap                 -0.30%  Neutral →│
│ Direction            Easing  ↑      │
│ (2 cuts in last 3 months)           │
│                                     │
│ ┌──────────┬─────────┬───────────┐  │
│ │Accomm.   │ Neutral │Restrictive│  │
│ │          │    ●    │           │  │
│ └──────────┴─────────┴───────────┘  │
│                                     │
│ Policy is roughly where the Taylor  │
│ Rule prescribes, but the Fed is     │
│ actively easing — two cuts since    │
│ December. Direction matters more    │
│ than level: easing into Goldilocks  │
│ is historically very supportive.    │
│                                     │
│ Note: Taylor Rule estimates depend  │
│ on CBO projections subject to       │
│ revision.                           │
│                                     │
│ See more: Rates →                   │
│                                ⌃    │
└─────────────────────────────────────┘
```

**Component metrics:**
| Label | Source | Link |
|-------|--------|------|
| Fed Funds Rate | DFEDTARU | `/explorer?metric=DFEDTARU` |
| Taylor Rule Says | Computed | `/explorer?metric=PCEPILFE` |
| Gap | DFEDTARU - Taylor prescribed | `/explorer?metric=UNRATE` |

**Visual:** 3-segment bar showing Accommodative / Neutral / Restrictive with dot at current stance position.

**Note:** The Taylor Rule caveat line ("Note: Taylor Rule estimates depend on CBO projections...") is always shown. This was a design decision based on the framework identifying CBO revision risk as the highest-likelihood operational risk.

**Cross-links:** Rates (page most affected by policy stance)

#### Crypto — Expanded

```
┌─────────────────────────────────────┐
│ ✦ CRYPTO               Favorable   │
│   Liquidity is expanding ↑         │
├─────────────────────────────────────┤
│                                     │
│ WHY LIQUIDITY, NOT THE QUADRANT?    │
│                                     │
│ Bitcoin correlates 0.94 with global │
│ M2 money supply, with a ~90-day    │
│ lag. It does not follow the growth/ │
│ inflation cycle that drives stocks  │
│ and bonds.                          │
│                                     │
│ Liquidity State     Expanding  ↑   →│
│ Composite Score     +0.8           →│
│ Historical Accuracy  83%            │
│ (directional, per Lyn Alden)        │
│                                     │
│ Expanding liquidity has historically│
│ been favorable for Bitcoin. The     │
│ ~90-day lag means current liquidity │
│ conditions may take 1-3 months to   │
│ fully reflect in price.             │
│                                     │
│ See more: Crypto →                  │
│                                ⌃    │
└─────────────────────────────────────┘
```

**Note:** The Crypto card is conceptually different from the three dimension cards — it surfaces an asset-specific insight (Bitcoin tracks liquidity, not the macro quadrant) rather than a dimension state. It earns its place in the 2×2 grid by providing a unique, actionable signal and completing the visual layout. The "WHY LIQUIDITY, NOT THE QUADRANT?" explainer is educational content that differentiates the product.

**Cross-links:** Crypto page

### Expand Behavior

- **Mobile:** Expanding one card pushes everything below it down. Only one card expanded at a time (expanding a second collapses the first) to prevent excessive scroll length.
- **Desktop:** Expanding one card pushes §2 down. Multiple cards can be expanded simultaneously on desktop (screen real estate allows it).
- **Animation:** `max-height` transition, 300ms ease-out. Content fades in with 150ms delay.
- **ARIA:** `aria-expanded` on toggle, `aria-controls` pointing to expand panel, `role="region"` on expand content.

---

## §2: What This Means For Your Portfolio

The actionable takeaway. Shows how each asset class is affected, broken down by which dimension drives the signal.

### Mobile (375px)

```
┌─────────────────────────────────────────┐
│                                         │
│  WHAT THIS MEANS FOR YOUR PORTFOLIO     │
│  ─────────────────────────────────────  │
│                                         │
│  ┌─────────┬────────────────┬──────┐    │
│  │ ASSET   │ CONDITIONS SAY │ WHY  │    │
│  ├─────────┼────────────────┼──────┤    │
│  │Equities │ ✓✓ Favorable   │Quad+L│    │
│  │Bonds    │ ✓  Supportive  │Quad  │    │
│  │Gold     │ ─  Neutral     │      │    │
│  │Crypto   │ ✓  Favorable   │Liq   │    │
│  │Credit   │ ✓  Supportive  │Quad+L│    │
│  │Commod.  │ ─  Neutral     │      │    │
│  └─────────┴────────────────┴──────┘    │
│                                         │
│  In prior Goldilocks + Expanding        │
│  Liquidity periods (n=14), S&P 500      │
│  returned +8.2% annualized / 6 months.  │
│                                         │
│  Explore: Equities → Credit → Rates →   │
│                                         │
└─────────────────────────────────────────┘
```

### Desktop (1280px)

The table expands to show per-dimension breakdown:

```
┌─────────┬──────────┬────────┬────────┬────────┬────────┐
│ Asset   │ Overall  │ Quad   │ Liq    │ Risk   │ Policy │
├─────────┼──────────┼────────┼────────┼────────┼────────┤
│Equities │ ✓✓ Best  │ ✓ ++   │ ✓ +    │ ✓ Calm │ ✓      │
│Bonds    │ ✓  Good  │ ✓ +    │ ✓ +    │ ✓      │ ✓      │
│Gold     │ ─  Neut  │ ✗ -    │ ─      │ ✓      │ ─      │
│Crypto   │ ✓  Good  │ ─      │ ✓ ++   │ ✓      │ ─      │
│Credit   │ ✓  Good  │ ✓ +    │ ✓ +    │ ✓      │ ─      │
│Commod.  │ ─  Neut  │ ✗ -    │ ─      │ ✓      │ ─      │
└─────────┴──────────┴────────┴────────┴────────┴────────┘
```

### Design Details

**Signal icons:**
- `✓✓` — Strongly supportive (green-600)
- `✓` — Supportive (green-600)
- `─` — Neutral (neutral-500)
- `✗` — Headwind (amber-600)
- `✗✗` — Strong headwind (red-600)

**Colorblind safety:** Icons + text labels, never color alone. Each cell shows icon + text.

**"WHY" column (mobile):** Abbreviated dimension labels showing which dimensions drive the signal:
- `Quad` — Quadrant is the primary driver
- `Liq` — Liquidity is the primary driver (crypto)
- `Quad+L` — Quadrant and Liquidity both supportive
- Empty — No strong signal from any dimension

**Per-dimension columns (desktop):** Each cell shows the signal from that specific dimension for that asset class. The `─` means "this dimension doesn't have a strong opinion on this asset class."

**Key insight:** The Crypto row shows `─` under Quad because Bitcoin doesn't follow the macro quadrant. It shows `✓ ++` under Liq because that's what actually drives it. This is the per-dimension transparency that replaces the old opaque "strong_outperform / underperform" labels.

**Historical context sentence:** Below the table, a single sentence with historical data: "In prior [Quadrant] + [Liquidity State] periods (n=X since 2003), the S&P 500 returned +X.X% annualized over 6 months." This grounds the implications in evidence.

**Explore links:** Links to relevant category pages. Each asset name in the table is also a link to its category page.

**Data source:** `market_conditions_cache.json` → `asset_expectations` array provides direction and magnitude per asset. The per-dimension breakdown is computed from the individual dimension states.

**Section ID:** `implications-section`

---

## Footer: Today's Movers

A lightweight strip at the bottom of the page. Visually distinct from the three main sections — it is clearly secondary content, a daily bonus rather than part of the narrative.

### Mobile (375px)

```
├─────────────────────────────────────────┤
│                                         │
│  TODAY'S MOVERS              See all →  │
│                                         │
│  NVDA +4.2%   TLT -1.1%   GLD +0.8%   │
│  AAPL +2.1%   XLE -0.9%               │
│                                         │
└─────────────────────────────────────────┘
```

### Desktop (1280px)

Single horizontal row of 5-8 movers:

```
├──────────────────────────────────────────────────────────────────────────┤
│  TODAY'S MOVERS    NVDA +4.2%  ·  TLT -1.1%  ·  GLD +0.8%  ·  AAPL   │
│                    +2.1%  ·  XLE -0.9%                      See all →  │
└──────────────────────────────────────────────────────────────────────────┘
```

### Design Details

- **Background:** `neutral-100` (subtle distinction from white main content)
- **Top border:** 1px `neutral-200` separator
- **Typography:** `text-sm`, `neutral-600` for labels, `neutral-800` for tickers
- **Positive movers:** Green-600 text for percentage
- **Negative movers:** Red-600 text for percentage
- **"See all →":** Link, right-aligned. Links to Equities page (which will host the full movers section)
- **No section header icon** — deliberately lighter treatment than §0-§2
- **No progressive disclosure** — always fully visible
- **Content:** Top 5 movers by absolute % change (same data as current "What's Moving Today" section)
- **Section ID:** `movers-strip`

---

## Quick-Nav Updates

The desktop sticky pill row and mobile FAB/bottom-sheet (Feature 7.5) update to reflect the new section structure:

**Pills:** Briefing | Conditions | Implications | Movers

**Mobile bottom sheet items:** Same four items.

**Section targets:** `#briefing-section`, `#conditions-section`, `#implications-section`, `#movers-strip`

---

## CSS Architecture

### New Files

| File | Purpose |
|------|---------|
| `static/css/components/conditions-summary.css` | §1 container, quadrant hero card, dimension card grid |
| `static/css/components/quadrant-viz.css` | Quadrant 2×2 visualization with trajectory dots |
| `static/css/components/spectrum-bar.css` | Shared horizontal spectrum bar (Liquidity, Risk, Policy) |
| `static/css/components/dimension-card.css` | Collapsed + expanded dimension card states |
| `static/css/components/implications-matrix.css` | §2 portfolio implications table |
| `static/css/components/movers-strip.css` | Footer movers strip |

### Design Tokens (New)

Add to `:root` or `design-system.md`:

```css
/* Quadrant colors */
--quadrant-goldilocks: #0D9488;
--quadrant-reflation: #1E40AF;
--quadrant-deflation: #CA8A04;
--quadrant-stagflation: #DC2626;

/* Quadrant backgrounds (15% opacity for inactive quadrants) */
--quadrant-goldilocks-bg: #CCFBF1;
--quadrant-reflation-bg: #DBEAFE;
--quadrant-deflation-bg: #FEF3C7;
--quadrant-stagflation-bg: #FEE2E2;

/* Dimension spectrum endpoints */
--liquidity-favorable: #2563EB;
--liquidity-unfavorable: #D97706;
--risk-favorable: #3B82F6;
--risk-unfavorable: #DC2626;
--policy-favorable: #16A34A;
--policy-unfavorable: #D97706;

/* Implication signals */
--signal-supportive: #16A34A;
--signal-neutral: #64748B;
--signal-headwind: #D97706;
--signal-strong-headwind: #DC2626;
```

### Files Removed

After migration is complete (Feature #326):
- `static/css/components/regime-card.css` (if exists)
- Regime-specific CSS classes from `index.html`

---

## Accessibility

- All quadrant states distinguishable without color (text label always present)
- AAA contrast (7:1) on all text against backgrounds
- `aria-live="polite"` on quadrant state and dimension states
- Expand/collapse: `aria-expanded`, `aria-controls`, `role="region"` on expanded content
- `max-height` transitions (never `display: none` on content — screen reader safe)
- 44px minimum touch targets on all interactive elements
- Quadrant visualization: `role="img"` with `aria-label` describing current state and trajectory
- Implications table: proper `<table>` with `<thead>`, `<th scope="col">`, `<th scope="row">`
- Explorer links: descriptive `aria-label` on each metric row (e.g., "View Fed Net Liquidity in explorer")

---

## Data Sources

| Element | Source |
|---------|--------|
| AI Briefing | `ai_summary` (existing pipeline, no changes) |
| Quadrant state + description | `market_conditions_cache.json` → `dimensions.quadrant` |
| Quadrant visualization position | `market_conditions_cache.json` → `dimensions.quadrant.growth_composite`, `.inflation_composite` |
| Trajectory trail | `market_conditions_history.json` → last 3-6 entries |
| Liquidity / Risk / Policy states | `market_conditions_cache.json` → `dimensions.*` |
| Component metrics (expand cards) | `market_conditions_cache.json` → component-level data (engineer to extend cache if needed) |
| Liquidity sparkline | `market_conditions_history.json` → last 14 weeks of liquidity scores |
| Asset expectations (§2) | `market_conditions_cache.json` → `asset_expectations` |
| Historical context sentence (§2) | Pre-computed from backtest data (engineer to add to cache) |
| Today's Movers | Existing movers data (same source as current What's Moving section) |

---

## Responsive Breakpoints

| Breakpoint | Layout Changes |
|------------|---------------|
| < 768px (mobile) | Single-column briefing, full-width quadrant card, 2×2 dimension grid, compact implications table (3-column), movers in 2 rows |
| 768px–1023px (tablet) | Same as desktop but slightly tighter spacing |
| ≥ 1024px (desktop) | Briefing centered ~65ch, 2-column quadrant card (text + viz), 4-across dimension cards, full 6-column implications table, movers in single row |
