# Ailtir Brand Reference — Plugin Outputs

> **Read this file before producing ANY visual output** — HTML dashboards, Excel workbooks, and any rendered artefact must comply. This is the extracted subset of the full Ailtir brand guidelines relevant to plugin outputs.
>
> Source: Ailtir Brand Guidelines v2026-04-24

---

## Colour Tokens

| Token | Hex | Usage in Plugin Outputs |
|---|---|---|
| **Navy 900** | `#0A1128` | Primary background (dashboards, headers) |
| **Navy 800** | `#0F1A3C` | Secondary background, alternating sections |
| **Navy 700** | `#1A2550` | Mid-depth surfaces, table headers |
| **Purple 600** | `#6D28D9` | Primary accent, gradient start, active fills |
| **Purple 500** | `#7C3AED` | Buttons, progress bars, active indicators |
| **Purple 400** | `#8B5CF6` | Highlights, hover states, icon accents |
| **Amber 400** | `#F59E0B` | Key statistics, urgency callouts, cost figures |
| **White** | `#FFFFFF` | All text on dark backgrounds |

**White opacity levels for text hierarchy (never use grey hex values):**

| Level | Opacity | Usage |
|---|---|---|
| Full | `rgba(255,255,255,1.0)` | Headlines, primary headings |
| Body | `rgba(255,255,255,0.70)` | Body copy, subheads |
| Secondary | `rgba(255,255,255,0.60)` | Supporting copy, descriptions |
| Muted | `rgba(255,255,255,0.50)` | Captions, labels |
| Ghost | `rgba(255,255,255,0.25)` | Micro-labels, axis labels |

**Semantic colour rules:**
- Negative indicators: **never red** — use `rgba(124,58,237,0.30)` (muted purple)
- Status: use amber for urgency/cost, purple for active/positive states
- Borders: `rgba(255,255,255,0.07)` standard, `rgba(124,58,237,0.35)` active card

---

## Typography

| Role | Font | Weight | Usage |
|---|---|---|---|
| **Display** | Space Grotesk | 500 (default), 700 (emphasis) | All headings h1–h4, section titles, KPI labels |
| **Body** | Inter | 400 (body), 600 (semibold) | Body copy, table cells, buttons, captions, eyebrows |

**Font loading for standalone HTML outputs:**
```html
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
```

**Type rules:**
- Space Grotesk for headings only — never Inter for headings
- Inter for all body text, labels, table cells, buttons
- `letter-spacing: -0.03em` on all headings
- No italic — use `font-weight: 700` for emphasis
- Numbers and statistics: `font-variant-numeric: tabular-nums`

---

## Excel Workbook Colours (for Python openpyxl outputs)

| Element | Hex | Usage |
|---|---|---|
| Header row background | `#0A1128` | All table header rows |
| Header row text | `#FFFFFF` | White, full opacity |
| Subheader / section row | `#1A2550` | Section dividers within sheets |
| Accent row (key figures) | `#6D28D9` | Total rows, summary rows |
| Amber highlight | `#F59E0B` | Key cost figures, urgency items |
| Alternating row (light) | `#F5F7FA` | Even rows in data tables |
| Body text | `#0A1128` | Dark navy on light rows |
| Border colour | `#E2E8F0` | Standard cell borders |

---

## Dashboard CSS Variables (for HTML Artifacts)

```css
:root {
  --navy-900: #0A1128;
  --navy-800: #0F1A3C;
  --navy-700: #1A2550;
  --purple-600: #6D28D9;
  --purple-500: #7C3AED;
  --purple-400: #8B5CF6;
  --amber-400: #F59E0B;
  --white: #FFFFFF;
  --text-body: rgba(255,255,255,0.70);
  --text-secondary: rgba(255,255,255,0.60);
  --text-muted: rgba(255,255,255,0.50);
  --border-standard: rgba(255,255,255,0.07);
  --border-active: rgba(124,58,237,0.35);
  --card-bg: rgba(255,255,255,0.03);
  --card-active-bg: rgba(109,40,217,0.10);
}
```

---

## Background Pattern (for HTML Dashboards)

Backgrounds must layer — never use flat single-colour fills:

```css
background-color: var(--navy-900);
background-image:
  radial-gradient(rgba(139,92,246,0.14) 1px, transparent 1px),
  radial-gradient(ellipse 50% 60% at 72% 50%, rgba(109,40,217,0.14), transparent);
background-size: 28px 28px, 100% 100%;
```

---

## Shadow System

```css
/* Button / CTA at rest */
box-shadow: 0 2px 8px rgba(124,58,237,0.3), 0 1px 3px rgba(124,58,237,0.2);

/* Button / CTA hover */
box-shadow: 0 4px 16px rgba(124,58,237,0.4), 0 2px 6px rgba(124,58,237,0.3);

/* Active card glow */
box-shadow: 0 0 24px rgba(109,40,217,0.18);
```

---

## Company Identity

| Field | Value |
|---|---|
| Name | Ailtir |
| Tagline | "Smarter Bids. Lower Risk. More Wins." |
| Domain | ailtir.ai |

---

## AEC Terminology Rules

| Use | Not |
|---|---|
| "programme" | "schedule" |
| "drawings" | "documents" (in construction context) |
| "subcontractor" | "sub" |
| "project" | "job" |
| "RFI" (spell out first use) | just "RFI" without explanation |

---

## Anti-Patterns (Non-Negotiable)

| Never | Instead |
|---|---|
| Teal `#00a896` or any non-brand colour | Navy/purple/amber palette only |
| Plain `shadow-md` / greyscale shadows | Colour-tinted purple shadows |
| Red for negative indicators | Muted purple `rgba(124,58,237,0.30)` |
| Grey text hex values | White at opacity levels |
| Flat single-colour backgrounds | Layered gradient + dot grid |
| Inter for headings | Space Grotesk for headings only |
| Italic type for emphasis | `font-weight: 700` on Space Grotesk |
