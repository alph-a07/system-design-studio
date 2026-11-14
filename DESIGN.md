# Design System

<!-- impeccable:design-schema 1 -->

## World

Systems Engineering Workbench & Living Architectural Console.
A high-density, first-principles technical product aesthetic engineered for systems architects and software engineers. Clean wire hairlines, deep void surfaces, and active diode telemetry replace generic AI-generated card layouts and glowing halos.

## Typography

- **Display & Body:** `Archivo` (Google Fonts, weights 400, 500, 600, 700). High-impact grotesk with geometric clarity and structural authority. Avoids the overused default sans roster.
- **Code, Coordinates & Telemetry:** `Red Hat Mono` (Google Fonts, weights 400, 500, 600). High-legibility fixed-width face designed specifically for system metrics and terminal logs.

## Palette

- `--bg-void`: `#090a0f` (Deep obsidian background)
- `--bg-surface`: `#11131c` (Primary container background)
- `--bg-raised`: `#171a26` (Secondary panels and elevated headers)
- `--bg-hover`: `#1f2333` (Hover interaction states)
- `--bg-active`: `#262b3d` (Active tab background)

- `--border-wire`: `rgba(255, 255, 255, 0.08)` (Hairline structural borders)
- `--border-subtle`: `rgba(255, 255, 255, 0.14)` (Component perimeter highlights)
- `--border-focus`: `#10b981` (Accessible focus-visible rings with 3px offset)

- `--text-primary`: `#f3f4f8` (Contrast > 16:1 on void, strict WCAG AA compliant)
- `--text-secondary`: `#a4abb8` (Contrast 7.1:1 on void)
- `--text-muted`: `#8c94a4` (Contrast 5.2:1 on void)

- `--accent-diode`: `#10b981` (High-contrast active indicator; contrast 7.8:1)
- `--accent-diode-surface`: `rgba(16, 185, 129, 0.1)` (Subtle active pill backing)
- `--accent-amber`: `#f59e0b` (Alert and warning indicators)

## Surfaces & Components

- **Themed Browser Surfaces:**
  - `::selection`: `rgba(16, 185, 129, 0.28)` with `#ffffff` text.
  - Scrollbars: 8px slim obsidian track with `#171a26` rounded thumb.
  - Focus: Offset rings (`outline-offset: 3px`) preventing clipping.
- **Elevation:** Declared strictly once via surface shade and crisp hairline wire borders. Zero-offset glowing shadows (`dark-glow`) and ghost cards (simultaneous border + large shadow) are forbidden.
- **Scaffolding:** Strict refusal of kickers/eyebrows, non-sequential numbered prefixes, and gradient text masks. Headings stand on their own typographic weight.
