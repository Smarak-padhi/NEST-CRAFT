# Stage C.1 — Structural DXF Validation & CAM Boundary Audit
**Project:** NEST-CRAFT (Team Algoryxz — Odisha AI Hackathon 2026)  
**Date:** 2026-11-13 (Updated Stage C.1 Revision)  
**Status:** Audit Completed — Structural DXF Format Validation Verified; No Commercial CAM Import or Machine Execution Tested  
**Export Files Audited:**  
- `team_algoryxz/nest_craft/reports/nested_cam_export.dxf`
- `team_algoryxz/nest_craft/reports/nested_part_in_part_cam_export.dxf`

---

## 1. Executive Summary & Machine Boundary Disclaimers

> [!WARNING]
> **MANDATORY MANUFACTURING & CAM BOUNDARY DISCLAIMER**  
> 1. **No Commercial CAM Import or Physical Machine Execution Evidenced:** This audit evaluates **exclusively programmatic structural DXF vector validation** via the Python `ezdxf` library. No physical cutting machine execution and no file import into commercial CAM suites (such as Trumpf TruTops, Bystronic BySoft, CypCut, Hypertherm ProNest, or SheetCam) was conducted or evidenced.  
> 2. **Not G-Code Ready:** NEST-CRAFT outputs standard **AutoCAD R2010 DXF (AC1024)** CAD geometry. It does **NOT** generate machine-executable G-code (ISO 6983 / EIA-274-D), feed rates, spindle/laser power curves, pierce dwell cycles, cut sequencing, or lead-in/lead-out vectors.  
> 3. **Physical Hazard Warning:** Attempting to cut raw DXF files directly on a CNC laser, plasma, waterjet, or oxy-fuel table without secondary CAM tooling post-processing will cause head collisions, slug tipping, thermal distortion, and potential machine damage.

---

## 2. Programmatic DXF Structural Audit (`ezdxf.audit()`)

Both exported DXFs were analyzed using the automated structural auditing engine of `ezdxf`:

```
ezdxf.audit() Results:
- nested_cam_export.dxf: Errors = 0, Fixes = 0, Unclosed Polylines = 0
- nested_part_in_part_cam_export.dxf: Errors = 0, Fixes = 0, Unclosed Polylines = 0
```

### Layer Architecture & Entity Taxonomy

| Layer Name | ACI Color Code | Entity Type | Geometric Role | Downstream CAM Processing Rule |
| :--- | :---: | :---: | :--- | :--- |
| `0` | 7 (White) | `TEXT` | Legal & Engineering Disclaimer | Ignore or mark as non-cutting annotation; do not cut. |
| `SHEET_BOUNDARY` | 7 (White) | `LWPOLYLINE` (Closed) | Raw stock plate outer boundary | Machine bed alignment / clamp bounding box; do not cut. |
| `CUT_CONTOUR` | 2 (Yellow) | `LWPOLYLINE` (Closed) | Outer perimeter of primary/parent parts | Final exterior cut sequence. |
| `HOLE_CONTOUR` | 4 (Cyan) | `LWPOLYLINE` (Closed) | Internal cutouts and apertures | Pre-cut before exterior perimeter. |
| `PART_IN_PART_CHILD` | 3 (Green) | `LWPOLYLINE` (Closed) | Secondary part nested inside parent cutout | Pre-cut inside hole before parent exterior is cut. |

All exported contours are strictly closed `LWPOLYLINE` entities (`is_closed == True`). Vertices are planar ($Z=0$), and coordinate axes adhere to standard Cartesian space with zero degenerate zero-length segments.

---

## 3. Real-World Manufacturing Realities & Required Downstream Toolpath Operations

While the DXF data structure is mathematically and syntactically clean, transforming 2D CAD vectors into physical parts requires critical CAM toolpath post-processing operations that NEST-CRAFT does not perform:

### 3.1. Cutting Order Hierarchy (Inside-Out Rule)
In physical plate cutting, cutting an outer boundary first causes the part to separate from the skeleton sheet, losing mechanical clamping, electrical grounding, and dimensional stability. Any subsequent internal cuts would fail due to part movement or tipping.
- **NEST-CRAFT Distinction:** The layer tagging explicitly distinguishes `PART_IN_PART_CHILD` (Layer 3) and `HOLE_CONTOUR` (Layer 4) from `CUT_CONTOUR` (Layer 2).
- **CAM Post-Processor Requirement:** Downstream CAM post-processors must strictly enforce:
  $$\text{Cut Sequence:} \quad \text{PART\_IN\_PART\_CHILD} \longrightarrow \text{HOLE\_CONTOUR} \longrightarrow \text{CUT\_CONTOUR}$$

### 3.2. Slug Handling & Part Tipping Risks (Slat Table Hazards)
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
- **NEST-CRAFT Role:** NEST-CRAFT handles part-to-part thermal clearance (e.g., $4.0\text{ mm}$ default), but outputs nominal CAD geometry.
- **CNC Controller Role:** Tool diameter compensation (`G41` left / `G42` right) or CAM geometry offset must be applied to ensure final cut parts match nominal CAD dimensions.

### 3.5. Thermal Distortion & Heat Dissipation
- Nesting multiple small parts within a single cutout concentrates laser heat in localized zones. On thin sheet metal ($< 2\text{ mm}$), localized thermal expansion causes plate buckling ("oil-canning").
- CAM post-processors must interleave cuts across different sheet quadrants to allow cooling before adjacent contours are processed.

---

## 4. Unsupported Requirements Checklist

| Requirement | Supported by NEST-CRAFT? | Evidenced by Audit? | Responsible System |
| :--- | :---: | :---: | :--- |
| Multi-layer DXF CAD export | **YES** | **YES** (`ezdxf` audit) | NEST-CRAFT |
| Closed polyline topological integrity | **YES** | **YES** (`ezdxf` audit) | NEST-CRAFT |
| Minimum clearance enforcement | **YES** | **YES** (51 unit tests) | NEST-CRAFT |
| Distinct layers for child parts | **YES** | **YES** (`ezdxf` audit) | NEST-CRAFT |
| Commercial CAM application import test | **NO** | **NO** (Not tested) | Third-party CAM suite |
| Physical machine cutting execution | **NO** | **NO** (Not tested) | CNC machine operator |
| Micro-tab / Micro-joint injection | **NO** | **NO** (Unsupported) | CAM Toolpath Post-Processor |
| Lead-in / Lead-out vector generation | **NO** | **NO** (Unsupported) | CAM Toolpath Post-Processor |
| G-code generation (M-codes / G01/G02) | **NO** | **NO** (Unsupported) | Machine CNC Post-Processor |
| Slat collision & tip avoidance simulation | **NO** | **NO** (Unsupported) | CAM Simulation Engine |
| Automated thermal sequence scheduling | **NO** | **NO** (Unsupported) | CAM Toolpath Post-Processor |

---

## 5. Audit Conclusion

NEST-CRAFT serves strictly as an **AI-driven 2D geometric CAD pre-processor**. Its exported DXFs satisfy structural AutoCAD R2010 file specifications without syntax errors or unclosed contours. However, because no commercial CAM import or physical cutting trials were conducted, **no claim of verified industry CAM compatibility or production cutting readiness is made**. NEST-CRAFT outputs must be ingested into a certified CAM package for toolpath post-processing prior to manufacturing execution.
