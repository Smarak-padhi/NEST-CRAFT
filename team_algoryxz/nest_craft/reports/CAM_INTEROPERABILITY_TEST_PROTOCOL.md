# NEST-CRAFT — CAM Interoperability Test Protocol & Verification Checklist

**Document Purpose:** Standard Operating Procedure (SOP) and manual inspection protocol for evaluating NEST-CRAFT exported DXF layouts within external Computer-Aided Manufacturing (CAM) nesting and CNC cutting software.  
**Critical Boundary Disclaimer:** NEST-CRAFT generates 2D CAD vector placement layouts (AutoCAD R2010 DXF). It **DOES NOT generate machine-specific CNC G-code (ISO 6983)**. All exported files require CAM post-processing (lead-in/out placement, kerf offset compensation, pierce sequence optimization, and micro-tab assignment) prior to machine cutting.  
**Truthfulness Disclosure:** As of this stage, automated Python/ezdxf structural audits have verified $100\%$ topological compliance. **No live physical cutting trials or commercial CAM imports on proprietary software licenses (e.g. ProNest, CypCut, TruTops) have been conducted yet.** This document defines the protocol for conducting and recording those external trials.

---

## 1. Test Suite Artifacts (Export Samples)

The following 6 standardized test layouts are staged in `team_algoryxz/nest_craft/data/cam_export_samples/`:

| Artifact Name | Intended Geometric Condition | CAD Layers Present | Verification Check |
| :--- | :--- | :--- | :--- |
| **`export_01_rectangular.dxf`** | 3 simple rectangular plates on a single sheet ($500 \times 400\text{ mm}$) | `SHEET_BOUNDARY`, `CUT_CONTOUR` | Clean closed polylines, 0 holes. |
| **`export_02_irregular_concave.dxf`** | Interlocking concave L-brackets ($0^\circ$ and $180^\circ$ rotation) | `SHEET_BOUNDARY`, `CUT_CONTOUR` | $90^\circ$ re-entrant corners, 0 boundary intersections. |
| **`export_03_multipart.dxf`** | Disjoint MultiPolygon component bracket | `SHEET_BOUNDARY`, `CUT_CONTOUR` | Disjoint components grouped under common part ID. |
| **`export_04_parts_with_holes.dxf`** | Structural flange with center square cutout and 4 corner bolt holes | `SHEET_BOUNDARY`, `CUT_CONTOUR`, `HOLE_CONTOUR` | 1 outer boundary, 5 closed interior apertures. |
| **`export_05_part_in_part.dxf`** | Cavity nesting: child bracket placed inside interior cutout of parent | `SHEET_BOUNDARY`, `CUT_CONTOUR`, `HOLE_CONTOUR`, `PART_IN_PART_CHILD` | Layer separation between parent cutout and child exterior. |
| **`export_06_multiple_sheets.dxf`** | Multi-sheet layout across 3 consecutive plates ($100\text{ mm}$ spacing) | `SHEET_BOUNDARY`, `CUT_CONTOUR` | 3 distinct sheet boundaries with horizontal offset. |

---

## 2. Standardized CAM Import Protocol (Step-by-Step)

When testing exported layouts in commercial CAM software (e.g., Hypertherm ProNest, CypCut, FastCAM, SheetCAM, Trumpf TruTops, Bystronic BySoft):

### Step 1: Pre-Import Verification
1. Ensure the CAM software project units are set strictly to **Millimeters (mm)**.
2. Verify DXF import filter is set to AutoCAD R2000--R2018 or "Auto-Detect".
3. Disable automated boundary pre-scaling or auto-fitting to prevent dimensional distortion.

### Step 2: Layer & Contour Mapping
Inspect how the CAM software maps NEST-CRAFT DXF layers:
* `SHEET_BOUNDARY` (Color 7 / White): Must be mapped as **Reference Plate / Stock Boundary** (NO CUT).
* `CUT_CONTOUR` (Color 2 / Yellow): Must be mapped as **Exterior Cutting Toolpath**.
* `HOLE_CONTOUR` (Color 4 / Cyan): Must be mapped as **Interior Pierce & Cutout** (cut FIRST before exterior).
* `PART_IN_PART_CHILD` (Color 3 / Green): Must be mapped as **Interior Child Part Cut** (must be cut and micro-tabbed BEFORE parent exterior is severed).

### Step 3: Topological & Geometry Inspection
1. **Contour Closure:** Verify that all cutting paths import as continuous closed loops. Flag any open nodes, micro-gaps, or unlinked vertices.
2. **Double Contours:** Inspect visual lines to verify no duplicate or superimposed vectors exist.
3. **Internal Hole Nesting:** Confirm that the child part inside `export_05_part_in_part.dxf` is recognized as an independent cutting part, not as an internal void.

### Step 4: Scale & Dimension Audit
Measure critical dimensions of imported parts using the CAM software's measurement tool:
* `export_01_rectangular.dxf`: Part 1 must measure exactly $150.00\text{ mm} \times 100.00\text{ mm}$.
* Sheet boundaries must match specified dimensions ($500.00 \times 400.00\text{ mm}$, $600.00 \times 400.00\text{ mm}$, etc.).

### Step 5: Cutting Simulation & Toolpath Generation
1. Apply machine lead-in/lead-out parameters (e.g. $3.0\text{ mm}$ straight or quarter-circle lead-in).
2. Generate automatic cutting sequence:
   * **Rule 1:** All `HOLE_CONTOUR` entities must be pierced and cut prior to parent `CUT_CONTOUR`.
   * **Rule 2:** `PART_IN_PART_CHILD` entities must be pierced and cut prior to releasing the parent part.
   * **Rule 3:** Micro-tabs (joints) must be applied to child parts to prevent tip-up or drop-through into table slats.
3. Run 2D cutting simulation and check for head collisions or premature sheet movement.

---

## 3. Commercial CAM Test Audit Log (Template)

| Field | Record / Observation |
| :--- | :--- |
| **Evaluator Name & Organization** | *Pending external fabricator trial* |
| **Date of Evaluation** | *Unscheduled* |
| **CAM Software & Exact Version** | *(e.g., Hypertherm ProNest 2024 / CypCut v6.3.8)* |
| **CAD File Tested** | *(e.g., `export_05_part_in_part.dxf`)* |
| **DXF Version Detected by CAM** | *(e.g., AutoCAD R2010 AC1024)* |
| **Units Interpreted Correctly?** | `[ ] Yes (1:1 mm)` / `[ ] No (Scaling error observed)` |
| **Layer Recognition** | `[ ] Automatic` / `[ ] Manual mapping required` |
| **Closed Contour Audit** | `[ ] 100% Closed` / `[ ] Gaps detected (record locations)` |
| **Missing or Dropped Contours** | `[ ] None` / `[ ] Missing entities observed` |
| **Part-in-Part Cutting Sequence** | `[ ] Child cut first safely` / `[ ] Parent cut first (collision risk)` |
| **Lead-in / Micro-tab Placement** | `[ ] Applied successfully` / `[ ] Errors encountered` |
| **Suitable for Machine Production?**| `[ ] Yes, ready for G-code post` / `[ ] Requires CAD remediation` |
| **Operator Comments** | *Detailed technician feedback...* |

---

## 4. Current Prototype Verification Status

* **ezdxf Document Audit:** $100\%$ PASS ($0\text{ errors}$, $0\text{ warnings}$ on all 6 exports).
* **Polyline Closure Audit:** $100\%$ PASS (all polylines closed with $\ge 3$ vertices).
* **Net Area Conservation:** $100\%$ PASS (reconstructed DXF net area matches in-memory geometry within $\Delta \le 0.05\text{ mm}^2$).
* **Commercial CAM License Blocker:** Proprietary commercial CAM suites (e.g., Hypertherm ProNest, CypCut, Trumpf TruTops, Bystronic BySoft) require specialized dongles or proprietary enterprise licenses that are not accessible within this local or CI development environment. Direct CAM validation is therefore blocked pending external trial with licensed fabricator partners.
* **Physical Cutting Blocker:** No physical cutting machine (laser, plasma, waterjet) has been operated. Physical cutting trials are strictly **NOT CONDUCTED** and **PENDING**.
* **Prototype Status:** **PENDING EXTERNAL VALIDATION** (Export protocol and structural integrity verified; proprietary CAM import pending licensed shop-floor access).
