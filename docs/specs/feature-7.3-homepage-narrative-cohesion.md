# Homepage Narrative Cohesion — Regime Threading Design Spec

**Issue:** #179
**Created:** 2026-03-02
**Status:** Draft

## Overview

The SignalTrackers homepage has a strong latent narrative arc — Macro Regime Score → Recession Probability → Regime Implications → Market Conditions → Sector Tone → Today's Briefing → What's Moving — but each section is visually and textually isolated. A user entering mid-scroll has no regime context, and sections like the AI synthesis and briefing don't anchor their content to the current macro regime.

This spec designs lightweight regime-aware narrative threading across four target sections (§1, §1.5, §2, §3) to transform the homepage from a collection of independent data widgets into a cohesive, regime-conditioned investment story.

## Scope Decision

The issue proposes five approaches (A–E). This spec recommends implementing **A + B + C** as the core scope and deferring D and E:

| Approach | Description | Recommendation |
|----------|-------------|----------------|
| A | Regime-conditioned AI synthesis in §1 | **Include** — prompt change, no new UI |
| B | Bridge subtitle sentences in §1.5 and §2 | **Include** — low-risk, high narrative value |
| C | "What this Means" context note on §3 | **Include** — static copy, no dynamic risk |
| D | Regime pill in quick-nav | **Defer** — depends on Feature #171 (Homepage Quick-Nav) |
| E | Page section reorder | **Defer** — measure A+B+C impact first, then evaluate |

The existing §0.75 section header ("Regime Implications") already provides a visual anchor between the verdict and evidence — no additional bridge sentence is needed there.

---

## Current Homepage Audit

| Section | Lines (index.html) | Role | Gap |
|---------|-------------------|------|-----|
| §0 — Macro Regime Score | 13–168 | VERDICT | None |
| §0.5 — Recession Probability | 169–325 | CORROBORATING VERDICT | None |
| §0.75 — Regime Implications | 327–442 | IMPLICATIONS | None (section title is clear) |
| §1 — Market Conditions | 444–721 | EVIDENCE | AI synthesis text is regime-agnostic |
| §1.5 — Sector Tone | 723–826 | SECTOR EVIDENCE | No regime framing before card grid |
| §2 — Today's Briefing | 828–882 | NARRATIVE SYNTHESIS | No regime anchor visible to user |
| §3 — What's Moving | 884–956 | REAL-TIME SIGNAL | No regime context on movers |

---

## User Flow

1. User loads homepage — §0 immediately delivers the regime verdict (e.g., "Bear")
2. User scrolls through recession probability and regime implications
3. User reaches §1 — the AI synthesis text now opens with a regime anchor sentence
4. User scrolls to §1.5 — a regime bridge sentence appears before the sector cards
5. User scrolls to §2 — a regime badge appears visually before the briefing narrative; briefing text opens with regime reference
6. User scrolls to §3 — a muted regime context line under the section header frames the movers
7. A user entering mid-scroll at any of §1.5, §2, or §3 sees enough regime context to orient themselves without scrolling back up

---

## Component Specifications

### Regime Bridge Sentence

A shared text pattern used in §1.5 and §2.

**Visual design:**
- Text: `--text-sm` (14px), `--neutral-500` color
- Font style: normal (not italic)
- Margin: `--space-3` above (12px), `--space-4` below (16px), before the first content element
- Inline regime badge: reuse the existing `.regime-badge` chip component that appears in §0 (regime-conditioned color, regime name in uppercase, 3–4 chars)
- No box, card, or background — plain inline text within the section container

**Template pattern:**
```jinja2
{% if macro_regime %}
<p class="narrative-bridge">
  In a <span class="regime-badge regime-badge--{{ macro_regime_css }}">{{ macro_regime }}</span>
  regime, {{ regime_bridge_text[macro_regime] }}
</p>
{% endif %}
```

**Copy per regime** (defined as a static dict in the Python view — not AI-generated):

| Regime | Bridge text |
|--------|-------------|
| Bull | sector momentum typically confirms the regime. See how this quarter's tone aligns: |
| Neutral | sector signals diverge — watch for emerging conviction in either direction: |
| Bear | defensive positioning and cash flow quality tend to hold up better. See how tone has shifted: |
| Recession Watch | significant sector deterioration is common. Earnings guidance and credit spreads deserve close attention: |

---

### §1 — Market Conditions: Regime-Anchored AI Synthesis (Approach A)

No new visual UI elements. This is a **prompt change only**.

**Prompt addition:** The backend prompt that generates `market_synthesis_text` must be updated to include:

> "Begin your synthesis by explicitly naming the current macro regime (`{macro_regime}`) and briefly explaining whether current market conditions are consistent with or diverging from what is historically typical for this regime. Then proceed with your standard market conditions summary."

**Design constraint:** The synthesis text is rendered as plain prose inside `#market-synthesis-text` — no markup needed. The regime reference must be in the first sentence of the generated text.

**Fallback:** If `macro_regime` is `None` or `"Unknown"`, the prompt addition is omitted and the synthesis text remains as-is (regime-agnostic).

---

### §1.5 — Sector Tone: Regime Bridge Sentence (Approach B)

**Placement:** After the section header row (with quarter label) and regime link, before the mobile toggle button and card grid.

**Mobile (375px):**
```
┌─────────────────────────────────────┐
│ 📊 Sector Tone        Q4 2025       │  ← existing header
│ Aligned with [BEAR] regime          │  ← existing regime link (already in template ~line 736)
├─────────────────────────────────────┤
│ In a BEAR regime, defensive         │  ← NEW bridge sentence
│ positioning and cash flow quality   │
│ tend to hold up better. See how     │
│ tone has shifted:                   │
├─────────────────────────────────────┤
│ [▼ Show sector tone]                │  ← existing mobile toggle
├─────────────────────────────────────┤
│ (collapsed sector cards)            │
└─────────────────────────────────────┘
```

**Tablet+ (768px+):**
```
┌─────────────────────────────────────────────────────────┐
│ 📊 Sector Management Tone           Q4 2025             │
│ Aligned with [BEAR] regime                              │
│                                                         │
│ In a BEAR regime, defensive positioning and cash flow   │
│ quality tend to hold up better. See how tone has        │
│ shifted:                                                │
├─────────────────────────────────────────────────────────┤
│ [sector card grid — already expanded]                   │
└─────────────────────────────────────────────────────────┘
```

**Behavior:** The bridge sentence is rendered server-side from a static dict. It does not require an AI call. If `macro_regime` is `None`, hide the bridge sentence element silently (`{% if macro_regime %}`).

---

### §2 — Today's Briefing: Regime Anchor (Approach B)

Two complementary changes:

**Change 1 — Visual regime badge above briefing (static):**

A small regime pill appears between the section header and the briefing content (the loading/content/error state container). This gives users a visual anchor even before the briefing text loads.

**Mobile and desktop:**
```
┌─────────────────────────────────────┐
│ 📰 Today's Market Briefing          │  ← existing header
├─────────────────────────────────────┤
│ Current Regime: [BEAR]              │  ← NEW regime anchor line
├─────────────────────────────────────┤
│ [loading skeleton / briefing text]  │  ← existing #briefing-loading / #briefing-content
└─────────────────────────────────────┘
```

Visual spec for the anchor line:
- Label: "Current Regime:" in `--text-xs` (12px), `--neutral-500`
- Regime badge: same `.regime-badge` component as §1.5 bridge
- Full row alignment: left-aligned, `--space-3` margin above the content container
- No box or border

**Change 2 — AI briefing prompt addition (static):**

The backend prompt for `briefing_narrative` should be updated to include:

> "Open your briefing by naming the current macro regime (`{macro_regime}`) and in one sentence explaining what it means for investors today. Then proceed with your standard briefing content."

**Fallback:** If `macro_regime` is `None`, hide the regime anchor line and omit the prompt addition.

---

### §3 — What's Moving: Regime Context Note (Approach C)

**Placement:** Below the section header, above the movers list and chart container.

**Visual design:**
```
┌─────────────────────────────────────┐
│ 📈 What's Moving Today              │  ← existing header
│ In Bear regimes, watch for          │  ← NEW regime context note
│ defensive rotation and breadth      │
│ deterioration as warning signals.   │
├─────────────────────────────────────┤
│ [movers list]                       │  ← existing content
└─────────────────────────────────────┘
```

- Same text styling as Regime Bridge Sentence: `--text-sm`, `--neutral-500`, no badge inline (regime name in plain text, capitalized)
- Margin: `--space-2` above (8px), `--space-4` below (16px)
- **No regime badge pill in §3** — keep it lighter here, plain text only

**Static copy per regime:**

| Regime | Context note |
|--------|-------------|
| Bull | In Bull regimes, momentum leaders often widen their lead. Watch for broad participation across sectors as a confirmation signal. |
| Neutral | In Neutral regimes, cross-sector dispersion creates selective opportunities. Focus on relative strength rather than broad market direction. |
| Bear | In Bear regimes, defensive rotation and breadth deterioration are key warning signals. Cash flow quality and dividend safety take precedence. |
| Recession Watch | In Recession Watch regimes, capital preservation matters most. Watch for credit spread widening and earnings guidance cuts as leading signals. |

**Implementation:** Static Jinja2 dict/macro in the template — no AI call, no backend changes beyond passing `macro_regime` to the template (which is already available).

---

## Responsive Behavior

All four changes are mobile-first and additive:

| Breakpoint | Behavior |
|------------|----------|
| 375px (mobile) | Bridge sentences and context notes display as block text; regime badge wraps naturally |
| 768px (tablet+) | Same text, same placement — no layout changes needed |
| 1280px+ (desktop) | Same; these are inline/block text elements, not grid-aware |

No new breakpoint behavior is required.

---

## Accessibility Requirements

- Regime bridge sentences and context notes are plain paragraph text — no special ARIA needed
- Regime badge pills (`.regime-badge`) already meet color contrast and must include `aria-label="Current regime: [name]"` if used as standalone elements without surrounding text context (in §2 anchor line they have a preceding label, so no extra ARIA needed there)
- Color contrast: `--neutral-500` on white background — verify meets 4.5:1 (currently passes in existing design system usage)
- Touch targets: no interactive elements added; existing toggle buttons are unaffected

---

## Copy Tone Guidelines

Regime bridge sentences and context notes follow these tone rules:
- **Factual, not alarmist** — describe historical patterns, not predictions
- **"Historically" or "tend to" framing** where possible — avoids implying certainty
- **Second-person aware** — these are investor-facing, use "watch for" not "you should"
- **Consistent with §0.75 Regime Implications panel tone** — this spec is the narrative complement to the panel's quantitative signals

---

## Implementation Notes

### New Python / Jinja2 Data Requirements

| Variable | Already Available | Action Needed |
|----------|------------------|---------------|
| `macro_regime` | Yes — already in template context | None |
| `macro_regime_css` | Yes — already in template context | None |
| Bridge sentence copy dict | No | Engineer defines static dict in `views.py` or as a Jinja2 macro |
| AI prompt additions | No — prompts are in backend generation code | Engineer updates prompt strings in relevant generation functions |

### Files Engineer Will Likely Modify
- `signaltrackers/templates/index.html` — §1.5, §2, §3 additions
- `signaltrackers/views.py` or equivalent — AI prompt additions (§1 synthesis, §2 briefing)
- `signaltrackers/static/css/` — minimal or none; `.regime-badge` and `--neutral-500` are existing components

### Design System References
- Regime badges: `.regime-badge`, `.regime-badge--bull`, `.regime-badge--bear`, `.regime-badge--neutral`, `.regime-badge--recession-watch` (existing in §0)
- Text sizes: `--text-xs` (12px), `--text-sm` (14px)
- Colors: `--neutral-500` for muted secondary text
- Spacing: `--space-2` (8px), `--space-3` (12px), `--space-4` (16px)

---

## Open Questions for PM

1. **Approach E (section reorder):** Should this be evaluated as a follow-on story after A+B+C ship, or is it explicitly out of scope for this feature?
2. **Approach D (regime pill in quick-nav):** Confirm this is blocked on Feature #171 and should not be included here.
3. **Copy tone review:** PM to confirm the bridge sentence and context note copy above matches the product voice before engineer implementation begins.
