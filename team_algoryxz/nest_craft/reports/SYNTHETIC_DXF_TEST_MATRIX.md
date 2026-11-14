# NEST-CRAFT — Synthetic DXF Edge-Case Test Matrix

> [!IMPORTANT]
> **PROVENANCE & INTEGRITY NOTICE:**
> All 16 DXF test files in this evaluation matrix were **synthetically generated** using `ezdxf` (version 1.4.5) to test geometric parser boundary conditions, topological edge cases, and fail-closed error handling across AutoCAD R12, R2010, and R2018 specifications.
> **None of these drawings are customer-provided, production fabricator drawings, or shop-floor production files.**
> This synthetic test suite does **not** constitute commercial fabricator validation. Real-world fabricator intake is governed separately by [`REAL_WORLD_DXF_INTAKE_PROCESS.md`](file:///c:/Users/smara/Desktop/Odisha%20AI%20hackathon/team_algoryxz/nest_craft/reports/REAL_WORLD_DXF_INTAKE_PROCESS.md) and tracked in [`REAL_WORLD_DXF_TEST_MATRIX.md`](file:///c:/Users/smara/Desktop/Odisha%20AI%20hackathon/team_algoryxz/nest_craft/reports/REAL_WORLD_DXF_TEST_MATRIX.md).

---

## 1. Corpus Summary Table

| Case ID | File Name | CAD Feature / Edge Case | Expected Behavior | Actual Behavior | Parts Extracted | Holes Extracted | Net Area ($\text{mm}^2$) | Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **TC-01** | `case01_closed_poly.dxf` | Standard closed LWPOLYLINE with chamfer | Ingest as 1 clean Part | Cleanly extracted | 1 | 0 | 14,700.00 | **PASS** |
| **TC-02** | `case02_open_contour.dxf` | Open LINE/ARC contour (3.0 mm gap) | Reject, warn about dangling lines | Rejected, 4 open lines warned | 0 | 0 | 0.00 | **PASS (Fail-Closed)** |
| **TC-03** | `case03_bulged_arcs.dxf` | LWPOLYLINE with arc bulge vertices | Tessellate circular arcs accurately | Clean curved boundary | 1 | 0 | 13,912.64 | **PASS** |
| **TC-04** | `case04_circles_holes.dxf` | Concentric circular cutouts (2x dia 30mm) | Extract outer boundary with 2 holes | 1 part, 2 interior cutouts | 1 | 2 | 28,594.97 | **PASS** |
| **TC-05** | `case05_splines.dxf` | Organic B-spline curve cutting profile | Tessellate smooth curve to polygon | Clean polygonized boundary | 1 | 0 | 11,431.23 | **PASS** |
| **TC-06** | `case06_disconnected_components.dxf` | Two separate closed brackets in one file | Extract 2 distinct parts | 2 independent parts extracted | 2 | 0 | 9,600.00 | **PASS** |
| **TC-07** | `case07_nested_holes.dxf` | Concentric rings (Outer, Hole, Island, Hole) | Extract 2 parts (depth 0 & 2), each 1 hole | 2 parts, 2 total holes | 2 | 2 | 66,000.00 | **PASS** |
| **TC-08** | `case08_narrow_slots.dxf` | High-aspect-ratio slot (0.8 mm x 60 mm) | Preserve narrow slot boundary | 1 part, 1 slot hole | 1 | 1 | 19,952.00 | **PASS** |
| **TC-09** | `case09_small_cutouts.dxf` | Sub-kerf pilot cutouts (3x dia 1.5mm) | Preserve small aperture rings | 1 part, 3 pilot holes | 1 | 3 | 9,994.83 | **PASS** |
| **TC-10** | `case10_self_intersecting.dxf` | Self-intersecting bow-tie contour | Reject unauthorized; split authorized | Unauth: Rejected; Auth: 2 parts | 0 / 2 | 0 | 0.00 / 5,000.00 | **PASS** |
| **TC-11** | `case11_unsupported_3d.dxf` | 2D plate with 3DFACE, MESH, and POINT | Extract 2D, warn on 3DFACE and MESH | 1 part, 3DFACE and MESH warned | 1 | 0 | 9,600.00 | **PASS** |
| **TC-12** | `case12_duplicate_contours.dxf` | Superimposed identical closed polylines | Extract both or dedup safely | 2 identical parts extracted | 2 | 0 | 20,000.00 | **PASS** |
| **TC-13** | `case13_overlapping_contours.dxf` | Partially overlapping closed contours | Ingest contours without crash | 2 overlapping parts extracted | 2 | 0 | 16,000.00 | **PASS** |
| **TC-14** | `case14_large_coordinates.dxf` | Offset coordinates (500,000, 800,000 mm) | Translate to local origin (0, 0) | 1 part, base at (0, 0) | 1 | 0 | 8,400.00 | **PASS** |
| **TC-15** | `case15_dxf_version_r12.dxf` | AutoCAD Release 12 legacy POLYLINE | Parse legacy 2D polyline vertices | 1 valid part extracted | 1 | 0 | 12,600.00 | **PASS** |
| **TC-16** | `case16_dxf_version_r2018.dxf` | AutoCAD 2018 modern AC1032 format | Parse modern LWPOLYLINE format | 1 valid part extracted | 1 | 0 | 14,400.00 | **PASS** |

---

## 2. Detailed Technical Breakdown & Edge Case Analysis

### TC-01: Standard Closed Polyline (`case01_closed_poly.dxf`)
* **Geometry Description:** 5-vertex polygon representing a $150 \times 100\text{ mm}$ structural gusset with a $30 \times 20\text{ mm}$ corner chamfer.
* **Entities:** Single `LWPOLYLINE`, `closed=True`.
* **Verification:** Reconstructed area equals $\frac{150 \times 100 - (30 \times 20)}{2} = 15,000 - 300 = 14,700.00\text{ mm}^2$.
* **CAM Handoff:** Standard closed contour, $100\%$ compatible with all 2D CAM nesting packages.

### TC-02: Open Contour with Gap (`case02_open_contour.dxf`)
* **Geometry Description:** 4 linear segments outlining a $100 \times 80\text{ mm}$ plate, with a deliberate $3.0\text{ mm}$ opening along the left edge.
* **Entities:** 4 separate `LINE` entities.
* **Fail-Closed Verification:** `polygonize()` correctly identifies that no closed topological loop exists. Ingestion rejects the file with:
  * Warning: `4 open line/arc segment(s) detected that do not form any closed cutting contour.`
  * Error: `No valid closed 2D cutting contours found in 'case02_open_contour.dxf'.`
* **CAM Implication:** Prevents CNC torch burn-outs from traversing disconnected segments.

### TC-03: Bulged Polylines & Circular Arcs (`case03_bulged_arcs.dxf`)
* **Geometry Description:** $140 \times 100\text{ mm}$ plate featuring a rounded $R=20\text{ mm}$ corner defined by a polyline vertex bulge factor $b = \tan(\pi / 8) \approx 0.41421356$.
* **Entities:** Single `LWPOLYLINE` with arc bulge.
* **Verification:** Area accurately reflects the subtracted circular corner ($13,912.64\text{ mm}^2$).
* **CAM Implication:** Arcs are properly tessellated for collision buffering while retaining vertex integrity for downstream post-processing.

### TC-04: Concentric Circles & Interior Holes (`case04_circles_holes.dxf`)
* **Geometry Description:** $200 \times 150\text{ mm}$ rectangular plate containing two $30\text{ mm}$ diameter circular clearance holes.
* **Entities:** 1 `LWPOLYLINE`, 2 `CIRCLE` entities.
* **Verification:** Concentric containment detects both circles inside the exterior boundary. Total net area is $30,000 - 2 \cdot \pi \cdot 15^2 = 28,586.3\text{ mm}^2$ (actual $28,594.97\text{ mm}^2$ due to circle chord tessellation).
* **CAM Implication:** Interior holes are categorized onto layer `HOLE_CONTOUR` for internal piercing prior to exterior contour severance.

### TC-05: B-Spline Curve Tessellation (`case05_splines.dxf`)
* **Geometry Description:** Closed organic curve defined by 11 cubic B-spline fit points.
* **Entities:** `SPLINE` entity.
* **Verification:** Tessellated to a non-self-intersecting 2D polygon with area $11,431.23\text{ mm}^2$.
* **CAM Implication:** CAM software requires polyline discretization or G02/G03 arc fitting for CNC machines that lack native NURBS interpolation.

### TC-06: Disconnected Multiple Components (`case06_disconnected_components.dxf`)
* **Geometry Description:** Two independent $80 \times 60\text{ mm}$ gusset brackets separated by a $50\text{ mm}$ gap in a single CAD file.
* **Entities:** 2 `LWPOLYLINE` entities.
* **Verification:** Engine cleanly extracts 2 individual `Part` instances, totaling $9,600.00\text{ mm}^2$.
* **CAM Implication:** Multiple distinct parts within a single assembly drawing are automatically split for individual nesting rather than locked together.

### TC-07: Nested Concentric Holes & Islands (`case07_nested_holes.dxf`)
* **Geometry Description:** Topological containment tree benchmark:
  * Depth 0: Outer rectangular boundary ($300 \times 300\text{ mm}$)
  * Depth 1: Large square aperture ($200 \times 200\text{ mm}$)
  * Depth 2: Solid interior island ($140 \times 140\text{ mm}$)
  * Depth 3: Small hole inside island ($60 \times 60\text{ mm}$)
* **Verification:** Produces exactly 2 valid parts:
  * Part 1 (Depth 0 with Depth 1 hole): Area $90,000 - 40,000 = 50,000\text{ mm}^2$.
  * Part 2 (Depth 2 with Depth 3 hole): Area $19,600 - 3,600 = 16,000\text{ mm}^2$.
  * Total Area = $66,000.00\text{ mm}^2$.
* **CAM Implication:** Prevents internal solid components from being discarded as scrap holes.

### TC-08: Narrow High-Aspect Ratio Thermal Slot (`case08_narrow_slots.dxf`)
* **Geometry Description:** $200 \times 100\text{ mm}$ base plate with a $0.8\text{ mm}$ wide, $60\text{ mm}$ long stress-relief slot.
* **Entities:** 1 outer `LWPOLYLINE`, 1 slot `LWPOLYLINE`.
* **Verification:** Correctly classifies the narrow slot as an interior cutout (Area $= 19,952.00\text{ mm}^2$).
* **CAM Implication:** Torch kerf diameter (typically $1.2\text{--}2.0\text{ mm}$ for plasma) may exceed the slot width ($0.8\text{ mm}$). Requires CAM laser cutting or kerf warning.

### TC-09: Small Pilot Holes (`case09_small_cutouts.dxf`)
* **Geometry Description:** $100 \times 100\text{ mm}$ plate with three $1.5\text{ mm}$ diameter pilot pierce holes.
* **Entities:** 1 outer `LWPOLYLINE`, 3 small `CIRCLE` entities.
* **Verification:** Successfully extracted without dropping small apertures. Net Area $= 9,994.83\text{ mm}^2$.
* **CAM Implication:** Requires center-punch or laser pierce cycle; plasma arc may blow out holes $< 2.0\text{ mm}$.

### TC-10: Self-Intersecting Bow-Tie (`case10_self_intersecting.dxf`)
* **Geometry Description:** 4-point loop where opposing edges cross at the centroid $(50, 50)$.
* **Entities:** 1 self-intersecting `LWPOLYLINE`.
* **Fail-Closed Verification:**
  * **Unauthorized:** Strictly rejected with `report["is_valid"] = False` and `CADTopologyError`.
  * **Authorized:** Repaired via `make_valid` into 2 separate triangular components, preserving total area of $5,000.00\text{ mm}^2$.

### TC-11: Unsupported 3D Entities (`case11_unsupported_3d.dxf`)
* **Geometry Description:** 2D plate ($120 \times 80\text{ mm}$) alongside non-planar 3D entities: a `3DFACE`, a 3D subdivision `MESH`, and a reference `POINT`.
* **Entities:** 1 planar `LWPOLYLINE`, 1 `3DFACE`, 1 `MESH`, 1 `POINT`.
* **Verification:** Ingests the 2D planar contour cleanly and logs explicit warnings for non-planar 3D entities:
  * `Unsupported entity type '3DFACE' ignored. 2D nesting requires planar profiles.`
  * `Unsupported entity type 'MESH' ignored. 2D nesting requires planar profiles.`
* **CAM Implication:** 2D sheet-metal profile is isolated safely without crashing CAM post-processors on non-cutting 3D wireframe or surface geometry.

### TC-12: Duplicate Superimposed Contours (`case12_duplicate_contours.dxf`)
* **Geometry Description:** Two identical $100 \times 100\text{ mm}$ squares drawn directly on top of each other.
* **Verification:** Both identical closed polygons are extracted as separate candidate parts ($2 \times 10,000 = 20,000\text{ mm}^2$).
* **CAM Implication:** Operator must verify whether drawing intended 2 pieces or duplicate CAD layers.

### TC-13: Partially Overlapping Contours (`case13_overlapping_contours.dxf`)
* **Geometry Description:** Two overlapping rectangles sharing a common area.
* **Verification:** Extracted as 2 independent parts.

### TC-14: Large Civil / GIS Coordinates (`case14_large_coordinates.dxf`)
* **Geometry Description:** Part drawn at offset $(X=500,000, Y=800,000\text{ mm})$.
* **Verification:** Ingestion parses global coordinates, and `Part` constructor normalizes the geometry to origin $(0, 0)$ for nesting, preventing floating-point precision degradation. Net area $8,400.00\text{ mm}^2$ preserved.

### TC-15 & TC-16: Version Compatibility (`case15_dxf_version_r12.dxf` & `case16_dxf_version_r2018.dxf`)
* **Verification:** Successfully parses legacy AutoCAD Release 12 (`AC1009`) using heavy `POLYLINE` entities and modern AutoCAD 2018 (`AC1032`) using `LWPOLYLINE` entities.
