# EdTech Language App — Visual Style Specification

A style guide for applying a consistent visual language across an app UI.
Written to be read by a coding agent: tokens first, then component recipes, then rules.

**Confidence key** — `[measured]` sampled directly from reference imagery · `[derived]` calculated from measured values · `[inferred]` judgment call, adjust freely.

---

## 1. Design DNA

Dark, near-black canvas. One hot coral accent doing almost all the heavy lifting. Big flat blocks of candy color — lime, marigold, sky, sage, indigo — dropped onto the dark as fully-rounded pills and large-radius cards. Every colored surface carries **black** text, never white. Type is a geometric sans with a tall x-height, set tight and heavy for display, generous and light for body. Playful without being childish: the color does the smiling, the layout stays disciplined.

The three things that make it recognizable:

1. **Black-on-color.** Colored surfaces always take near-black text. This single rule creates most of the look.
2. **Full pills.** Selectable things are `border-radius: 999px`, wide, and stacked with real air between them.
3. **Two-tone emphasis text.** Paragraphs mix white and grey mid-sentence, so the important words pop out of a dim line.

---

## 2. Color tokens

### Neutrals `[measured]`

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#232323` | Page / app background. Warm-neutral charcoal, **not** pure black. |
| `--bg-deep` | `#0A0A0A` | Inside device frames, immersive screens, modal scrims, media wells. |
| `--surface` | `#2C2C2C` | Cards and panels sitting on `--bg`. |
| `--surface-2` | `#3A3A3A` | Chips, inactive segments, input fields. |
| `--border` | `#3F3F3F` | Hairline dividers, 1px card outlines. |
| `--ink` | `#0A0A0A` | Text on colored surfaces. Always this, never `#000`. |
| `--text` | `#FFFFFF` | Primary text on dark. |
| `--text-muted` | `#9A9A9A` | Secondary text, de-emphasized words. |
| `--text-ghost` | `#4A4A4A` | Oversized background headings only. Never body copy. |

### Accents `[measured]`

| Token | Hex | Role |
|---|---|---|
| `--coral` | `#F65E4B` | **Primary.** CTAs, active state, highlights, brand blocks. |
| `--coral-deep` | `#D8452F` | Pressed state, button underside, secondary action wells. |
| `--yellow` | `#F9CD61` | Category color 2. |
| `--lime` | `#E1FFAC` | Category color 3. |
| `--sky` | `#BCF3FF` | Category color 4. |
| `--indigo` | `#7477FF` | Category color 5. Use sparingly — it's the loudest. |
| `--sage` | `#A3BAA9` | Category color 6. The calm one; good for large areas. |

### Semantic

| Token | Value | Note |
|---|---|---|
| `--success` | `#E1FFAC` | Reuse lime. Don't introduce a new green. |
| `--danger` | `#F65E4B` | Coral doubles as error. Distinguish by icon, not hue. |
| `--warning` | `#F9CD61` | Reuse yellow. |

Only coral, and only if the surrounding context makes destructive intent obvious. If an app needs frequent, unambiguous error states, add `#FF6B6B` as `--danger` and reserve coral for brand — but that's a deviation from the reference and should be a deliberate choice.

### The accent rotation rule `[measured]`

Lists of parallel items (languages, lesson categories, tags) cycle accents in fixed order:

```
coral → yellow → sky → lime → indigo → sage → repeat
```

Assign by **stable index**, not randomly, or colors will shuffle on re-render:

```js
const ACCENTS = ['coral', 'yellow', 'sky', 'lime', 'indigo', 'sage'];
const accent = ACCENTS[index % ACCENTS.length];
```

### Contrast — non-negotiable `[derived]`

Every accent has been checked. Ratios against `#0A0A0A`:

| Accent | vs `--ink` | vs white |
|---|---|---|
| coral | 6.24 ✅ | 3.17 ❌ |
| yellow | 13.14 ✅ | 1.51 ❌ |
| lime | 18.01 ✅ | 1.10 ❌ |
| sky | 16.41 ✅ | 1.21 ❌ |
| indigo | 5.49 ✅ | 3.60 ❌ |
| sage | 9.57 ✅ | 2.07 ❌ |

**White text fails WCAG AA on every accent in this palette.** Black text passes on all six. This is why the black-on-color rule exists — it's not just a style preference, it's the only accessible option for these hues.

`--text-muted` at `#9A9A9A` gives 5.59:1 on `--bg`. The reference imagery uses a dimmer grey that would fail AA; `#9A9A9A` is the corrected value. Don't go below `#8C8C8C` (4.67:1) for anything at body size.

---

## 3. Typography

### Families `[inferred]`

The reference sets a geometric sans with a **double-storey `a`**, **single-storey `g`**, circular bowls, and a tall x-height — the Circular / Gilroy family of shapes. Display type is a heavier, tighter neo-grotesque with horizontally-cut terminals.

I can't read font metadata out of flat imagery, so these are shape-matched recommendations rather than a confirmed identification:

```css
--font-display: 'General Sans', 'Plus Jakarta Sans', 'Helvetica Now Display',
                system-ui, sans-serif;
--font-body:    'Plus Jakarta Sans', 'Figtree', 'General Sans',
                system-ui, sans-serif;
```

Ranked substitutes, closest first:

| Face | Source | Notes |
|---|---|---|
| **General Sans** | Fontshare (free) | Closest to the reference letterforms. Best default. |
| **Plus Jakarta Sans** | Google Fonts (free) | Excellent match, widest weight range, safest for web. |
| **Figtree** | Google Fonts (free) | Slightly friendlier, marginally wider. |
| **Manrope** | Google Fonts (free) | More geometric, tighter. Good for display role. |
| **Circular Std** | Commercial | Likely closest to the original. Requires a license. |

**Do not substitute Poppins, Montserrat, or Futura.** All three have a single-storey `a`, which visibly breaks the match. This is the single most common way this style gets approximated wrong.

Run display and body from the same family at different weights and tracking. Two families only if the display face is genuinely distinct — otherwise it reads as inconsistency, not pairing.

### Scale — app UI, 16px base `[derived]`

| Role | Size | Weight | Line height | Tracking |
|---|---|---|---|---|
| `display-xl` | 40px | 800 | 1.05 | `-0.03em` |
| `display-lg` | 32px | 700 | 1.10 | `-0.02em` |
| `title-lg` | 24px | 700 | 1.20 | `-0.015em` |
| `title-md` | 20px | 700 | 1.25 | `-0.01em` |
| `body-lg` | 17px | 500 | 1.50 | `0` |
| `body` | 15px | 500 | 1.55 | `0` |
| `label` | 13px | 600 | 1.35 | `0` |
| `caption` | 11px | 600 | 1.30 | `0.02em` |

Marketing / section headings on wide layouts scale to 56–72px at weight 800, tracking `-0.04em`. Tighten tracking as size increases — that inverse relationship is a core part of the look.

### Rules

- **Sentence case everywhere.** No `text-transform: uppercase` except on `caption`-size eyebrows.
- **Negative tracking on anything ≥20px.** Display type is set tight enough that letters nearly touch.
- **Weight jumps, not weight creep.** Use 500 / 700 / 800. Skip 400 and 600 for headings — the contrast between body and display should be obvious.
- Body copy caps at ~65 characters per line.

### Signature: two-tone emphasis `[measured]`

Paragraphs alternate white and grey within a single sentence. Key phrases go white at weight 700; connective tissue drops to `--text-muted` at weight 500.

```html
<p class="emphasis">
  <strong>This app</strong> allows users to explore new languages, track their
  <strong>learning progress, and complete</strong> lessons easily.
</p>
```

```css
.emphasis { color: var(--text-muted); font-weight: 500; }
.emphasis strong { color: var(--text); font-weight: 700; }
```

Emphasize **2–3 fragments per paragraph**. More than that and nothing reads as emphasized. Choose fragments that survive being read alone — someone skimming should get the gist from the white words only.

### Signature: marker highlight `[measured]`

A coral block sits behind a word or two, like a highlighter stroke. Used on one phrase per heading, maximum.

```css
.marker {
  background: var(--coral);
  color: var(--ink);
  padding: 0.08em 0.28em;
  border-radius: 4px;
  box-decoration-break: clone;
  -webkit-box-decoration-break: clone;
}
```

Note the small radius — 4px, not a pill. It should read as a printed marker stroke, not a tag.

### Ghost headings `[measured]`

Oversized headings in `--text-ghost` sit behind or above content as a structural layer. Display size or larger, weight 700, low contrast, deliberately quiet.

Set `aria-hidden="true"` only if the text is decorative and duplicated elsewhere. If it's the real section heading, leave it in the accessibility tree and accept that it's low contrast — WCAG exempts nothing here, so prefer duplicating: a visible ghost heading plus a properly-contrasted `sr-only` or adjacent label.

---

## 4. Spacing, radius, elevation

### Spacing `[inferred]` — 4px base

```
2xs 4 · xs 8 · sm 12 · md 16 · lg 24 · xl 32 · 2xl 48 · 3xl 64 · 4xl 96
```

Screen gutter: **20px** mobile, 24px tablet, 64px+ desktop.
Gap between stacked pills/cards: **12px**.
Gap between sections: **48px** mobile, 96px desktop.

This layout is generous. When uncertain, take the next size up — cramped spacing is the fastest way to lose the feel.

### Radius `[measured]`

Corner radius was measured at ~1.7% of container width on the hero block, which resolves to 24px at typical layout widths.

| Token | Value | Applies to |
|---|---|---|
| `--r-pill` | `999px` | Buttons, selectors, tags, segmented controls, avatars. |
| `--r-lg` | `24px` | Hero blocks, large cards, media wells. |
| `--r-md` | `16px` | Standard cards, list rows, sheets. |
| `--r-sm` | `12px` | Inset image tiles, small containers. |
| `--r-xs` | `4px` | Marker highlight only. |

There is no `0`. Nothing in this system has a sharp corner.

### Elevation `[inferred]`

Depth comes from **color and offset**, not blur. Shadows are near-invisible on a `#232323` canvas, so don't lean on them.

```css
--shadow-sm: 0 1px 2px rgba(0,0,0,0.4);
--shadow-md: 0 8px 24px rgba(0,0,0,0.5);
--shadow-lift: 0 16px 40px rgba(0,0,0,0.55);   /* floating / dragged only */
```

The real elevation device is the **solid underside** on pressable elements — see the button recipe below.

---

## 5. Components

### Selector pill — the signature component `[measured]`

Full-width, fully-rounded, flat accent fill, black label left-aligned, circular badge floated right. A darker solid lip along the bottom gives it physical depth.

```css
.pill {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 56px;
  padding: 0 8px 0 24px;
  border: none;
  border-radius: var(--r-pill);
  background: var(--accent);
  box-shadow: inset 0 -4px 0 rgba(0,0,0,0.18);  /* the underside */
  color: var(--ink);
  font: 700 17px/1.2 var(--font-body);
  cursor: pointer;
  transition: transform 140ms cubic-bezier(0.2,0,0,1),
              box-shadow 140ms cubic-bezier(0.2,0,0,1);
}

.pill:active {
  transform: translateY(2px);
  box-shadow: inset 0 -2px 0 rgba(0,0,0,0.18);
}

.pill:focus-visible {
  outline: 3px solid #FFFFFF;
  outline-offset: 3px;
}

.pill__badge {
  width: 40px; height: 40px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}
```

Selected state: **do not** change the fill — that would break the color rotation. Instead add a ring:

```css
.pill[aria-pressed="true"] {
  box-shadow: inset 0 -4px 0 rgba(0,0,0,0.18),
              0 0 0 3px var(--bg), 0 0 0 6px #FFFFFF;
}
```

Use `<button aria-pressed>` for toggles, or `<input type="radio">` with a styled label for single-select groups. The pills are semantically controls, not decoration.

### Primary button `[measured]`

Coral pill with the label centered-left and a darker circular affordance at the trailing edge holding an arrow.

```css
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  padding: 0 8px 0 32px;
  border-radius: var(--r-pill);
  background: var(--coral);
  color: var(--ink);
  font: 700 17px/1 var(--font-body);
  box-shadow: inset 0 -4px 0 var(--coral-deep);
}

.btn-primary__arrow {
  display: grid; place-items: center;
  width: 40px; height: 40px;
  border-radius: 50%;
  background: var(--coral-deep);
  color: var(--ink);
  margin-left: auto;
}
```

Secondary: transparent fill, `1.5px solid var(--border)`, white label, no underside.
Ghost: no fill, no border, `--text-muted` label, coral on hover.
Disabled: `--surface-2` fill, `--text-ghost` label, no underside, `cursor: not-allowed`.

### Tag / chip `[measured]`

Small pill, accent fill, black label. Used in clusters for metadata and categories.

```css
.chip {
  display: inline-flex; align-items: center;
  height: 28px; padding: 0 14px;
  border-radius: var(--r-pill);
  background: var(--accent);
  color: var(--ink);
  font: 600 12px/1 var(--font-body);
}
```

Cluster them with `gap: 8px` and let them wrap. Neutral variant for non-categorical metadata: `--surface-2` fill, `--text-muted` label.

### Content card `[measured]`

The lesson-card pattern: accent-filled card containing a **white inset tile** holding a black line-art illustration, with title and subtitle to the side.

```css
.card {
  display: flex; align-items: center; gap: 16px;
  padding: 12px;
  border-radius: var(--r-lg);
  background: var(--accent);
  color: var(--ink);
}

.card__media {
  width: 96px; height: 96px;
  flex-shrink: 0;
  border-radius: var(--r-sm);
  background: #FFFFFF;      /* pure white, not off-white */
  display: grid; place-items: center;
  overflow: hidden;
}

.card__title    { font: 700 20px/1.2 var(--font-body); letter-spacing: -0.01em; }
.card__subtitle { font: 500 13px/1.4 var(--font-body); opacity: 0.72; }
```

The white tile is load-bearing. It's what keeps a stack of saturated cards from turning into mush — each one gets a bright neutral rest point. Don't tint it and don't drop it.

Cards stack with `gap: 12px` and rotate accents by index.

### Segmented control `[measured]`

```css
.segmented {
  display: inline-flex; padding: 4px;
  border-radius: var(--r-pill);
  background: var(--bg-deep);
}
.segmented__item {
  padding: 10px 24px;
  border-radius: var(--r-pill);
  color: var(--text-muted);
  font: 600 14px/1 var(--font-body);
}
.segmented__item[aria-selected="true"] {
  background: #FFFFFF;
  color: var(--ink);
}
```

Active segment is **white**, not coral. Coral is reserved for actions; white marks position. Keeping those two jobs separate is what stops the accent from going noisy.

Use `role="tablist"` / `role="tab"` when it switches views, or a radio group when it filters.

### List row `[measured]`

```css
.row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px;
  border-radius: var(--r-md);
  background: var(--surface);
}
.row__rank   { width: 24px; color: var(--text-muted); font: 600 13px/1 var(--font-body); }
.row__avatar { width: 40px; height: 40px; border-radius: 50%; }
.row__name   { flex: 1; color: var(--text); font: 600 15px/1.3 var(--font-body); }
.row__value  { color: var(--text-muted); font: 600 13px/1 var(--font-body); }
```

Rows separate by `gap: 8px` rather than dividers. If a dense table is genuinely needed, use `1px solid var(--border)` and drop the row radius to 0 — but prefer spaced cards.

### Podium / ranked highlight `[measured]`

Three rounded blocks, center tallest, each in a different accent, with a circular avatar overlapping the top edge and a crown or rank badge on the leader.

```css
.podium       { display: flex; align-items: flex-end; gap: 8px; }
.podium__col  {
  flex: 1; padding: 32px 8px 16px;
  border-radius: var(--r-md);
  background: var(--accent);
  color: var(--ink);
  text-align: center;
  position: relative;
}
.podium__col--first  { padding-top: 48px; }
.podium__avatar {
  position: absolute; top: -20px; left: 50%;
  transform: translateX(-50%);
  width: 48px; height: 48px;
  border-radius: 50%;
  border: 3px solid var(--accent);
}
```

Order columns 2 · 1 · 3 visually, but keep DOM order 1 · 2 · 3 and reorder with flexbox `order` so screen readers get the ranking correctly.

### Stat pill `[measured]`

Inline metrics — streak, points, hearts — as a small dark pill with an icon and a number. `--surface-2` fill, `--r-pill`, 12px semibold white numeral, icon in its semantic accent. Group with `gap: 8px` in the header.

### Progress bar `[measured]`

```css
.progress       { height: 8px; border-radius: var(--r-pill); background: var(--surface-2); }
.progress__fill { height: 100%; border-radius: var(--r-pill); background: var(--coral); }
```

Always `role="progressbar"` with `aria-valuenow` / `aria-valuemin` / `aria-valuemax`. Never communicate progress by color alone — pair with a numeric label.

### Navigation

**Back button:** 40px circle, `--surface` fill, white chevron, top-left, 20px from edges.
**Tab bar:** `--bg-deep` background, ~64px tall plus safe-area inset, icons at 24px. Active tab is coral; inactive is `--text-muted`. Active state needs a second signal beyond color — a filled icon variant or a dot.
**Overflow menu:** three dots in a 32px `--surface` circle.

### Header

Avatar (40px circle with a coral ring), name at `title-md` weight 700, stat pills to the right, overflow at the far right. Sits directly on `--bg` with no separator.

---

## 6. Illustration & iconography

`[measured]` from reference, `[inferred]` for production guidance.

**Illustration style:** monochrome black line art on white — sketch-like, hand-drawn contour weight, no fill, no color. Sits inside white tiles within colored cards. The restraint here is what lets the palette stay loud.

**Iconography:** rounded-stroke geometric outline icons, ~2px stroke at 24px, round caps and joins. Lucide, Phosphor (Regular/Bold), or Iconoir all fit. Icons on colored surfaces are `--ink`; on dark they're white or `--text-muted`.

**Circular badges:** flags, avatars, and similar identity marks are always perfect circles, 40px in pills and rows, 48px+ in featured positions.

**Emoji as accent:** small emoji appear inline in gamified contexts (crown on a leader, star beside points). Sparingly — one or two per screen. They should never carry meaning alone; pair with text.

**Mascot:** the reference uses a character mascot — a rounded, expressive figure with simple facial features, soft gradient shading, and a sparkle motif, rendered in a friendly semi-3D style.

A note on this: a mascot is original artwork and belongs to whoever drew it. This spec describes the *style* so a new character can be commissioned or generated in a compatible direction — it isn't a license to reproduce the original. Same applies to any custom illustration set in the source. Commission, license, or generate your own; match the treatment, not the drawing.

---

## 7. Motion

`[inferred]` — motion isn't observable in still imagery. These are choices that suit the visual language.

```css
--ease:      cubic-bezier(0.2, 0, 0, 1);
--ease-in:   cubic-bezier(0.4, 0, 1, 1);
--dur-fast:  140ms;   /* press, hover */
--dur-base:  240ms;   /* enter, expand */
--dur-slow:  400ms;   /* screen transition */
```

- Press = `translateY(2px)` plus a shrunk underside. This is the primary interaction feedback.
- Lists stagger in at 40ms intervals, `translateY(8px)` → `0` with fade.
- Celebration moments (streak, level-up) get a scale bounce — `1 → 1.06 → 1` over 400ms. Reserve for genuine achievements or it stops meaning anything.
- No parallax, no continuous ambient animation.

Always:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 8. Rules

### Do

- Black text on every colored surface, without exception.
- Full pills for anything selectable or pressable.
- Rotate accents by stable index across parallel items.
- Keep the white inset tile inside colored cards.
- Give the layout air — 20px gutters minimum, 12px between stacked items.
- Tighten letter-spacing as type gets larger.
- Reserve coral for actions and brand; use white for selection state.
- Two or three emphasized fragments per paragraph, no more.

### Don't

- White text on coral, yellow, lime, sky, indigo, or sage. Fails contrast on all six.
- Pure black (`#000`) as the app background. It's `#232323`, and the warmth matters.
- Sharp corners anywhere.
- Gradients on surfaces. Flat fills only — the depth comes from the solid underside.
- More than three accents visible in one viewport, outside a deliberate category grid.
- Poppins, Montserrat, or Futura as the body face — the single-storey `a` breaks the match.
- Color as the sole carrier of meaning. Every state needs a shape, icon, or text signal too.
- Coral for large background areas. It's an accent; at scale it overwhelms.
- Blur-heavy shadows. They disappear on dark and just cost render time.

---

## 9. CSS custom properties

```css
:root {
  /* neutrals */
  --bg:          #232323;
  --bg-deep:     #0A0A0A;
  --surface:     #2C2C2C;
  --surface-2:   #3A3A3A;
  --border:      #3F3F3F;
  --ink:         #0A0A0A;
  --text:        #FFFFFF;
  --text-muted:  #9A9A9A;
  --text-ghost:  #4A4A4A;

  /* accents */
  --coral:       #F65E4B;
  --coral-deep:  #D8452F;
  --yellow:      #F9CD61;
  --lime:        #E1FFAC;
  --sky:         #BCF3FF;
  --indigo:      #7477FF;
  --sage:        #A3BAA9;

  /* type */
  --font-display: 'General Sans', 'Plus Jakarta Sans', system-ui, sans-serif;
  --font-body:    'Plus Jakarta Sans', 'Figtree', system-ui, sans-serif;

  /* radius */
  --r-pill: 999px;
  --r-lg:   24px;
  --r-md:   16px;
  --r-sm:   12px;
  --r-xs:   4px;

  /* space */
  --sp-2xs:  4px;  --sp-xs:   8px;  --sp-sm:  12px;
  --sp-md:  16px;  --sp-lg:  24px;  --sp-xl:  32px;
  --sp-2xl: 48px;  --sp-3xl: 64px;  --sp-4xl: 96px;

  /* elevation */
  --shadow-sm:   0 1px 2px rgba(0,0,0,0.4);
  --shadow-md:   0 8px 24px rgba(0,0,0,0.5);
  --shadow-lift: 0 16px 40px rgba(0,0,0,0.55);

  /* motion */
  --ease:     cubic-bezier(0.2, 0, 0, 1);
  --dur-fast: 140ms;
  --dur-base: 240ms;
  --dur-slow: 400ms;
}
```

## 10. Tailwind config

```js
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: {
        bg:        { DEFAULT: '#232323', deep: '#0A0A0A' },
        surface:   { DEFAULT: '#2C2C2C', 2: '#3A3A3A' },
        border:    '#3F3F3F',
        ink:       '#0A0A0A',
        muted:     '#9A9A9A',
        ghost:     '#4A4A4A',
        coral:     { DEFAULT: '#F65E4B', deep: '#D8452F' },
        yellow:    '#F9CD61',
        lime:      '#E1FFAC',
        sky:       '#BCF3FF',
        indigo:    '#7477FF',
        sage:      '#A3BAA9',
      },
      fontFamily: {
        display: ['General Sans', 'Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        sans:    ['Plus Jakarta Sans', 'Figtree', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        pill: '999px',
        lg:   '24px',
        md:   '16px',
        sm:   '12px',
      },
      boxShadow: {
        underside:      'inset 0 -4px 0 rgba(0,0,0,0.18)',
        'underside-sm': 'inset 0 -2px 0 rgba(0,0,0,0.18)',
        lift:           '0 16px 40px rgba(0,0,0,0.55)',
      },
      transitionTimingFunction: {
        smooth: 'cubic-bezier(0.2, 0, 0, 1)',
      },
    },
  },
};
```

---

## 11. Applying this to an existing UI

Work in this order. Each step is visible on its own, so you can stop and check.

1. **Fonts.** Load the family, set `--font-body` globally. Biggest single shift for the least work.
2. **Neutrals.** Background to `#232323`, surfaces to `#2C2C2C`, text to white / `#9A9A9A`. The app should now read as the right *kind* of dark.
3. **Radius.** Global sweep — every button and input to `--r-pill`, every card to `--r-md` or `--r-lg`. Kill every sharp corner.
4. **Coral.** Replace the existing primary accent everywhere it appears. Add the underside shadow to buttons.
5. **Type scale.** Apply sizes and weights per section 3. Add negative tracking to headings.
6. **Spacing.** Widen gutters to 20px, set stack gaps to 12px, push section spacing to 48px+.
7. **Accent rotation.** Find the lists of parallel items and color them by index.
8. **Two-tone emphasis.** Apply to hero copy, empty states, and onboarding — the places where a paragraph needs to be scanned rather than read.
9. **Audit contrast.** Confirm nothing ended up white-on-accent. This is where the conversion usually breaks.
10. **Reduced motion.** Add the media query if it isn't already there.

**When adapting rather than copying:** the load-bearing pieces are the black-on-color rule, the full pills, the white inset tile, and the tight display tracking. Those four carry the identity. Everything else — exact spacing, the specific accent set, the podium treatment — can flex to fit the product without losing the look.

---

## 12. Caveats

- Hex values are sampled from compressed screenshots. Colors inside device mockups are affected by perspective, lighting, and the mockup's own shading — flat UI regions were preferred as sources, and mockup-derived values were discarded where a flat equivalent existed. Expect ±3 per channel against the designer's originals.
- The typeface is shape-matched, not identified. If the exact face matters, ask the original designer.
- Motion, hover states, dark/light theming, and error states aren't observable in stills. Those sections are informed guesses consistent with the visual language, not extracted facts.
- Spacing tokens are a coherent system fitted to the observed proportions, not measurements. The reference layout is generous; the scale reflects that.
- This describes a visual style — palettes, type treatment, and layout conventions aren't protectable, and building in a similar direction is normal practice. Original assets are a different matter: the mascot, custom illustrations, photography, and any logo belong to their creators. Commission or generate your own.
