---
name: industrial-ui-unslop
description: Industrial UI craftsmanship standards for NEST-CRAFT Streamlit interfaces, emphasizing high information density, precise engineering metrics, legible typography, and suppression of decorative AI slop.
license: CC-BY-4.0
---

# Industrial UI Unslop Skill for NEST-CRAFT

Use this skill when designing, reviewing, or styling UI components, dashboards, matplotlib/altair charts, and data tables in NEST-CRAFT.

## Anti-Slop Principles for Industrial CAD/CAM Tools

Shop floor operators and CNC programmers need clarity, contrast, and data density—not consumer-app marketing fluff.

1. **No Decorative AI Slop:**
   - Suppress purple/violet gradient glows, soft blurred backdrops, floating sparkles, emoji-heavy headers, and animated buzzword badges.
   - Use clean, functional colors:
     - CAD Plate: Dark Slate (`#1E222A`) or Blueprint Gray (`#2B303C`)
     - Part Contours: High-visibility Safety Amber (`#FFB300`), Cyan (`#00E5FF`), or Crisp White (`#FFFFFF`)
     - Kerf Separation / Margin: Translucent Orange (`rgba(255, 100, 0, 0.2)`)
     - Remnant Plate: Forest Green boundary with hatched fill (`#2E7D32`)

2. **Data-Dense Engineering Typography:**
   - Use monospace fonts (`Consolas`, `Roboto Mono`, `Source Code Pro`) for numerical readouts: dimensions, coordinates, runtimes, area percentages, and seed IDs.
   - Right-align numeric columns in data tables.
   - Display engineering units explicitly ($mm$, $mm^2$, $kg$, $s$, $\%$).

3. **Clear Information Hierarchy:**
   - Tier 1 (Vital Operational Status): Total Sheets Used, Part Count Nested vs Unplaced, Kerf Clearance, Run Time.
   - Tier 2 (Geometric Quality): Bounding Extent ($X_{\max}$), True Shape Area Utilization ($\%$), Remnant Dimensions ($W \times H$).
   - Tier 3 (Economic Audit): Virgin Remnant Salvage Value (₹), Net Material Efficiency ($\%$).

4. **Zero Node.js / Headless Browser Dependencies:**
   - Pure Python/Streamlit and native Matplotlib/SVG rendering.
   - No external screenshot automation or heavy headless browsers required in runtime environment.
