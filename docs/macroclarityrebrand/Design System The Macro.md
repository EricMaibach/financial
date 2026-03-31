# Design System: The Macro-Architect

## 1. Overview & Creative North Star
**The Creative North Star: "The Financial Atelier"**
This design system rejects the cluttered, frantic aesthetic of traditional trading platforms in favor of an editorial, high-net-worth experience. We are not building a tool for day traders; we are building a sanctuary for long-term wealth architects.

The system moves beyond the "standard dashboard" by employing **Editorial Asymmetry**. By utilizing a high-contrast typography scale (pairing the intellectual weight of Noto Serif with the precision of Inter) and replacing rigid grid lines with tonal layering, we create a digital environment that feels like a bespoke financial report. It is sophisticated, quiet, and authoritative—prioritizing "clarity over noise."

---

## 2. Colors & Surface Logic
The palette is anchored in deep oceanic navies and structural charcoals, designed to recede and allow data to emerge as the primary focus.

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders to define sections. A "boxed-in" UI feels cheap and constrained. Instead, define boundaries through:
- **Background Shifts:** Use `surface-container-low` (#eff4ff) to define a section against the `surface` background (#f8f9ff).
- **Tonal Transitions:** Contrast `surface-container-highest` (#d3e4fe) with `surface-container-lowest` (#ffffff) to create natural edges.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked, premium materials.
1. **The Base:** `surface` (#f8f9ff) – The expansive canvas.
2. **The Zone:** `surface-container-low` (#eff4ff) – Used for broad content groupings.
3. **The Focus:** `surface-container-lowest` (#ffffff) – Pure white cards or modules that "float" on the grey-blue base.

### The "Glass & Gradient" Rule
To elevate the experience, main Call-to-Actions (CTAs) and Hero metrics should utilize a **Signature Texture**. Instead of flat `primary` (#000000), use a subtle linear gradient from `primary` to `primary-container` (#131b2e) at 135 degrees. For floating navigation or context menus, apply `surface-container-lowest` at 80% opacity with a `24px` backdrop-blur to create a "frosted glass" effect.

---

## 3. Typography
We use a "Serif-to-Sans" hierarchy to bridge the gap between traditional financial heritage and modern digital precision.

* **Display & Headlines (Noto Serif):** Used for "The Narrative." Large titles and key financial summaries. This evokes the feeling of a premium broadsheet or a private banking terminal.
* *Headline-LG (2rem):* Reserved for page titles and major portfolio totals.
* **Titles & Body (Inter):** Used for "The Data." Inter provides the necessary legibility for complex figures and labels.
* *Title-MD (1.125rem):* Used for card headers and data categories.
* *Body-MD (0.875rem):* The workhorse for all financial analysis and descriptions.
* **Labels (Inter, All-Caps/Letter-Spaced):** Use `label-md` (0.75rem) with 0.05em tracking for table headers to create a sense of architectural rigor.

---

## 4. Elevation & Depth

### The Layering Principle
Depth is achieved through "Tonal Stacking" rather than shadows.
* **Level 0:** `surface` (The Floor)
* **Level 1:** `surface-container-low` (The Foundation)
* **Level 2:** `surface-container-lowest` (The Interactive Layer)

### Ambient Shadows
When a physical "lift" is required (e.g., a modal or an active selection), use a shadow that mimics natural studio lighting:
- **Shadow:** `0 20px 40px rgba(11, 28, 48, 0.06)`
- Use the `on-surface` (#0b1c30) color for the shadow tint, never pure black.

### The "Ghost Border" Fallback
If accessibility requires a border, use the `outline-variant` (#c6c6cd) at **15% opacity**. It should be felt, not seen.

---

## 5. Components

### Buttons
* **Primary:** A deep gradient from `#000000` to `#131b2e`. Border-radius: `md` (0.375rem). Use `label-md` typography.
* **Secondary:** `surface-container-high` (#dce9ff) background with `on-secondary-container` (#57657b) text. No border.
* **Tertiary:** Text-only in `on-surface` with a subtle `px` (1px) underline in `surface-variant` on hover.

### Cards & Lists
* **Rule:** Forbid divider lines.
* **Implementation:** Separate list items using `spacing-4` (1rem) of vertical whitespace. In tables, use alternating background tints (Zebra-striping) using `surface-container-low` and `surface-container-lowest` rather than lines.
* **Radius:** Cards must use `xl` (0.75rem) for a modern, soft feel.

### Input Fields
* **Resting:** `surface-container-highest` background, no border.
* **Active:** `surface-container-lowest` background with a 1px `primary` border.
* **Labeling:** Labels should use `label-sm` and be placed above the field with `spacing-1` (0.25rem) distance.

### Specialty Component: The Macro-Sparkline
A specialized chart component for this system. Use a 2px stroke width. The line color should be `on-tertiary-container` (#008cc7) with a subtle area-fill gradient beneath it (from 10% opacity to 0%).

---

## 6. Do’s and Don’ts

### Do:
* **Do** use asymmetrical layouts. A 1/3 vs 2/3 split is more editorial than a 50/50 split.
* **Do** use `spacing-12` (3rem) or `spacing-16` (4rem) between major sections. Generous white space is a sign of luxury.
* **Do** ensure all financial figures use a tabular-nums font feature (if available in Inter) to ensure decimal points align.

### Don’t:
* **Don’t** use pure black for text. Use `on-surface` (#0b1c30) to maintain a sophisticated navy-charcoal depth.
* **Don’t** use standard "Success Green." For financial growth, use the `tertiary-fixed-dim` (#89ceff) or a muted teal to maintain the "Professional Blue" palette.
* **Don’t** use more than one Serif heading per view. Overusing Noto Serif will make the UI feel like a blog rather than a dashboard. Use it for the "Hero" moment only.
