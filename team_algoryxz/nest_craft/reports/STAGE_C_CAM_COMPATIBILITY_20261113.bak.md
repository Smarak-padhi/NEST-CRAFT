# Stage C — Manufacturing & CAM Compatibility Audit
**Project:** NEST-CRAFT (Team Algoryxz — Odisha AI Hackathon 2026)  
**Date:** 2026-11-13  
**Status:** Audit Completed — Geometric CAD/CAM Interchange Verified; Machine-Specific Toolpath Post-Processing Required  
**Export Files Audited:**  
- `team_algoryxz/nest_craft/reports/nested_cam_export.dxf`
- `team_algoryxz/nest_craft/reports/nested_part_in_part_cam_export.dxf`

---

## 1. Executive Summary & Disclaimer

> [!WARNING]
> **MANDATORY MANUFACTURING DISCLAIMER**  
> NEST-CRAFT outputs standard **AutoCAD R2010 DXF (AC1024)** geometric vector files. It does **NOT** generate machine-specific G-code (ISO 6983 / EIA-274-D), feed rates, pierce dwell cycles, cut sequencing, or lead-in/lead-out vectors.  
> Direct execution of these DXF files on a CNC laser, plasma, waterjet, or oxy-fuel cutting table without secondary CAM tooling post-processing (e.g. via Trumpf TruTops, Bystronic BySoft, CypCut, Pronest, or SheetCam) is **STRICTLY PROHIBITED** and poses risks of head collision, slug tipping, and thermal warping.

---

## 2. DXF Vector & Layer Audit (`ezdxf.audit()`)

Both exported DXFs were subjected to automated structural auditing via `ezdxf.audit()`:

```
Auditor Run:
- nested_cam_export.dxf: Errors = 0, Fixes = 0, Unclosed Polylines = 0
- nested_part_in_part_cam_export.dxf: Errors = 0, Fixes = 0, Unclosed Polylines = 0
```

### Layer Architecture & Entity Taxonomy

| Layer Name | ACI Color Code | Entity Type | Geometric Role | CAM Processing Rule |
| :--- | :---: | :---: | :--- | :--- |
| `0` | 7 (White) | `TEXT` | Legal & Engineering Disclaimer | Ignore or mark as engraving/comment; do not cut. |
| `SHEET_BOUNDARY` | 7 (White) | `LWPOLYLINE` (Closed) | Raw stock plate outer boundary | Machine bed alignment / clamp bounding box; do not cut. |
| `CUT_CONTOUR` | 2 (Yellow) | `LWPOLYLINE` (Closed) | Outer perimeter of primary/parent parts | Final exterior cut sequence. |
| `HOLE_CONTOUR` | 4 (Cyan) | `LWPOLYLINE` (Closed) | Internal cutouts and apertures | Pre-cut before exterior perimeter. |
| `PART_IN_PART_CHILD` | 3 (Green) | `LWPOLYLINE` (Closed) | Secondary part nested inside parent cutout | Pre-cut inside hole before parent exterior is cut. |

All contours are strictly closed `LWPOLYLINE` entities (`is_closed == True`). Vertices are coplanar ($Z=0$), and coordinate axes adhere to standard right-handed Cartesian space with zero degenerate zero-length segments.

---

## 3. Real-World Manufacturing & CAM Toolpath Realities

While the geometric interchange is clean and compliant, deployment to physical CNC cutting tables requires clear awareness of real-world manufacturing constraints:

### 3.1. Cutting Order Hierarchy (Inside-Out Rule)
In physical plate cutting, cutting the outer boundary first causes the part to separate from the skeleton sheet, losing electrical grounding and mechanical clamping. Any subsequent internal cuts would be ruined due to part movement or tipping.
- **NEST-CRAFT Distinction:** The layer tagging explicitly distinguishes `PART_IN_PART_CHILD` (Layer 3) and `HOLE_CONTOUR` (Layer 4) from `CUT_CONTOUR` (Layer 2).
- **CAM Post-Processor Requirement:** CAM software must strictly enforce:
  $$\text{Cut Sequence:} \quad \text{PART\_IN\_PART\_CHILD} \longrightarrow \text{HOLE\_CONTOUR} \longrightarrow \text{CUT\_CONTOUR}$$

### 3.2. Slug Handling & Part Tipping Risks (Slat Hazards)
- **Problem:** Small child parts nested inside cutouts (e.g., $50\text{ mm} \times 30\text{ mm}$ brackets) have low mass. When completely severed by the laser or plasma beam, they can tip vertically between the machine's supporting slats (comb table) or fall into the slag hopper below.
- **Collision Hazard:** If a part tips upward at an angle, the rapid-traverse cutting head will strike it at high speed, resulting in ceramic nozzle breakage or optical misalignment.
- **Remediation Gap:** NEST-CRAFT does **NOT** generate micro-joints (tabs) or bridge cuts. CAM operators must configure their CAM software to inject $0.5\text{ mm} - 1.2\text{ mm}$ break-away micro-tabs on all child parts.

### 3.3. Piercing, Lead-Ins, and Lead-Outs
- **Problem:** When a thermal beam pierces metal plate (especially thick steel $> 6\text{ mm}$), the initial puncture creates an irregular molten blowhole (pierce crater) with spatter and wide kerf.
- **CAM Post-Processor Requirement:** Cut contours must never be pierced directly on the part boundary. The CAM software must generate:
  - An off-contour lead-in arc or linear tangent ($2\text{ mm} - 8\text{ mm}$ long).
  - A lead-out or overlap to ensure clean corner separation.

### 3.4. Kerf Width Offsets
- **Kerf Compensation:** The laser, plasma, or oxy-fuel beam possesses physical width (kerf), ranging from $0.2\text{ mm}$ (fiber laser) to $1.5\text{ mm} - 3.0\text{ mm}$ (plasma/oxy-fuel).
- **NEST-CRAFT Role:** NEST-CRAFT handles part-to-part thermal clearance (e.g., $4.0\text{ mm}$ default), but outputs the exact CAD geometry of the parts.
- **CNC Controller Role:** Tool diameter compensation (`G41` left / `G42` right) or CAM geometry offset must be applied to ensure final parts match nominal CAD dimensions.

### 3.5. Thermal Distortion & Heat Dissipation
- Nesting multiple small parts within a single cutout concentrates laser heat in localized zones. On thin sheet metal ($< 2\text{ mm}$), localized thermal expansion causes plate buckling ("oil-canning").
- CAM post-processors must interleave cuts across different sheet quadrants to allow cooling before adjacent contours are processed.

---

## 4. Unsupported Requirements Checklist

| Requirement | Supported by NEST-CRAFT? | Responsible System |
| :--- | :---: | :--- |
| Multi-layer DXF CAD export | **YES** | NEST-CRAFT |
| Closed polyline topological integrity | **YES** | NEST-CRAFT |
| Minimum clearance enforcement | **YES** | NEST-CRAFT |
| Distinct layers for child parts | **YES** | NEST-CRAFT |
| Micro-tab / Micro-joint injection | **NO** | CAM Toolpath Post-Processor |
| Lead-in / Lead-out vector generation | **NO** | CAM Toolpath Post-Processor |
| G-code generation (M-codes / G01/G02) | **NO** | Machine CNC Post-Processor |
| Slat collision & tip avoidance simulation | **NO** | CAM Simulation Engine |
| Automated thermal sequence scheduling | **NO** | CAM Toolpath Post-Processor |

---

## 5. Audit Conclusion

NEST-CRAFT successfully serves as an **AI-driven 2D geometric nesting pre-processor**. Its exported DXFs import cleanly into industry-standard CAD/CAM systems without syntax errors, self-intersections, or layer ambiguities. However, it must be paired with downstream CAM post-processing software prior to physical sheet-metal fabrication.
