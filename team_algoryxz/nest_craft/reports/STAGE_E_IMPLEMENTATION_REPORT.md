# NEST-CRAFT — Stage E: Implementation Report
## Geometry Integrity, Ingestion Reliability & Demo Excellence

**Project:** NEST-CRAFT — 2D Sheet-Metal Nesting Engine  
**Team:** Algoryxz · Odisha AI Hackathon 2026  
**Permanent Baseline Commit:** `24260d9e96760779708f860b07b5611948e00957`  
**Execution Date:** November 14, 2026  
**Status:** Verification Passed · Ready for Commit & Push  

---

### Executive Summary

Stage E resolves the remaining architectural and geometry-handling defects across CAD ingestion, enforces mathematical topology validation beyond raw surface area checks, elevates the Streamlit web dashboard to professional industrial standards, hardens DXF export with automated geometric and structural auditing, and adds 11 comprehensive automated tests.

---

### 1. Defect Resolution: Eliminating Remaining Component Reductions (DEF-01)

In previous stages, `Part.__init__` was remediated to support `MultiPolygon` geometries and reject unauthorized contour repairs. However, an audit of `team_algoryxz/nest_craft/src/dxf_io.py` identified two residual instances of silent largest-only reduction:
1. **`parse_esicup_txt` (line 107):** Ingested shapes and applied `max(poly.geoms, key=lambda g: g.area)` if a decomposed polygon emerged from `make_valid`.
2. **`parse_esicup_xml` (line 146):** Similarly discarded secondary components during XML geometry parsing.

#### Code Modifications
- **Eliminated `max(poly.geoms, ...)` reductions:** Both `parse_esicup_txt` and `parse_esicup_xml` now construct `Part` instances directly with the raw or decomposed geometry.
- **Strict Authorization Enforcement:** If an input contour has self-intersections or degenerate topology, it is strictly rejected with `CADTopologyError` unless `allow_repaired_topology=True` is explicitly passed.
- **Preservation of MultiPolygon Components:** When repair is authorized, all valid components ($area > 10^{-4}\text{ mm}^2$) are preserved as `MultiPolygon` objects, retaining total piece area and geometry.
- **Accurate Quantity and ID Mapping:** Maintained piece quantities (`p.quantity`) and discrete IDs across all parsed entities.

---

### 2. Enhanced Topology Validation in `Part.__init__`

Prior to Stage E, topology validation in `Part` primarily checked whether `abs(repaired.area - original.area) / original.area` exceeded a percentage threshold. While effective for massive distortions, area-only checking can miss critical manufacturing defects (e.g. a 100 mm needle-thin spike or deep notch collapsed to zero width has $\approx 0.00\text{ mm}^2$ area change, but destroys the physical part).

#### Implemented Enhancements (`src/geometry.py`)
1. **Hausdorff Boundary Deviation Metric:**
   - Implemented `compute_boundary_deviation(poly_orig, poly_repaired)` using `shapely.geometry.LineString.hausdorff_distance` across exterior boundaries and interior hole rings.
   - Triggers `feature_loss_detected = True` if boundary deviation exceeds tolerance (default 0.5 mm).
   - Rejects repair with `CADTopologyError` if feature loss occurs without explicit `metadata['allow_feature_loss']=True`.
2. **Hole Count Delta Tracking:**
   - Implemented `count_geometry_holes(geom)` to accurately tally interior cutouts across both `Polygon` and `MultiPolygon`.
   - Records `input_holes` vs. `repaired_holes` and flags `topology_altered = True` on any count mismatch.
3. **Component Count Delta Tracking:**
   - Detects whether automated repair split a single closed contour into multiple detached polygons (`input_components` vs. `repaired_components`).
4. **Non-Polygonal Element Detection:**
   - Flags `GeometryCollection` occurrences where `make_valid` produced dangling lines or isolated points.
5. **Structured Validation Record (`Part.validation_record`):**
   - Every `Part` records a structured diagnostic audit dictionary:
     ```python
     {
         "is_valid_original": bool,
         "is_valid_repaired": bool,
         "input_components": int,
         "repaired_components": int,
         "input_holes": int,
         "repaired_holes": int,
         "original_area": float,
         "repaired_area": float,
         "area_delta": float,
         "area_delta_pct": float,
         "hausdorff_distance": float,
         "feature_loss_detected": bool,
         "topology_altered": bool,
         "repair_authorized": bool,
         "notes": List[str]
     }
     ```

---

### 3. Trustworthy Streamlit UI & 9-Step Industrial Workflow (`app/app.py`)

The Streamlit interface was restructured into a clear 9-step industrial progression following the `industrial-ui-unslop` design system:

1. **Step 1: Sheet & Cutting Parameters** (Sheet Width, Height, Torch Clearance/Kerf Offset).
2. **Step 2: Optimization Parameters** (Simulated Annealing iterations, Orthogonal vs. Adaptive rotation, Grain constraints, Part-in-Part cavity nesting).
3. **Step 3: CAD Ingestion & DXF Batch Setup** (Multi-file AutoCAD DXF upload or 17-part industrial benchmark batch).
4. **Step 4: Batch Diagnostics & Pre-Flight Settings**
   - Per-file ingestion diagnostics table: File Name, Validation Status (✅ Valid / ❌ Rejected), Parts Extracted, Interior Cutouts, Unclosed Segments, Unsupported 3D Entities, and Error/Warning breakdowns.
   - Critical CAD error gate: Blocks optimization if malformed drawings are uploaded.
   - Pre-flight control expander with explicit topology authorization warning (default unchecked).
5. **Step 5: Batch Summary & Pre-Flight Validation** (Total Requested Quantity, Unique CAD Profiles, Total Net Steel Area, Total Interior Cutouts).
6. **Step 6: Algorithm Execution** (Bottom-Left-Fill Baseline vs. Simulated Annealing).
7. **Step 7: Empirical Performance & Layout Inspection**
   - **Placement Completeness & Accounting:** Tracks requested vs. placed parts ($17/17$), guaranteeing zero silent part loss or duplication.
   - **Discrete Stock Purchase Tier:** Highlights physical integer plate requirements ($3\text{ plates}$ across both algorithms).
   - **Linear Compaction & Remnant Intelligence:** Quantifies linear span reduction ($-404\text{ mm}$, $-17.19\%$) and virgin offcut plate recovery ($227,000\text{ mm}^2$ prime remnant on Sheet 3).
   - **Process & Geometry Diagnostics:** Runtime ($< 8\text{s}$), rotation mode, grain constraints, and parts nested in cavities.
   - **High-Density Matplotlib Visualizations:** Renders sheet boundaries, parts, interior holes, and green-hatched prime remnant offcuts.
8. **Step 8: Validated DXF Export & CAM Handoff**
   - Automates post-export validation via `validate_exported_dxf`.
   - Displays real-time validation metric cards (Reopenability, Audit Errors, Exported Contours, Net Area Delta).
   - "Download Nesting DXF Layout" action button.
   - Prominent CAM handoff disclaimer (emphasizing requirement for secondary toolpathing, lead-ins, kerf calibration, and G-code generation).
9. **Step 9: Illustrative Financial Estimation Model (Exploratory Scenario)**
   - Explicitly framed as an exploratory ROI scenario model, not empirical customer savings.
   - Interactive parameters: Annual steel consumption, raw steel price, scrap resale value, baseline vs. optimized utilization, SaaS subscription fee.

---

### 4. DXF Export Trustworthiness & Automated Validation (`src/dxf_io.py`)

Added strict validation facilities to ensure exported DXF files are ready for downstream CAM processing:
- **`DXFExportValidationError(ValueError)`**: Specific exception raised if an exported file fails validation.
- **`validate_exported_dxf(output_file, sheets, area_tolerance=0.05)`**:
  1. *Reopenability:* Confirms `ezdxf.readfile` successfully parses the generated file.
  2. *Structural Audit:* Confirms `doc.audit().has_errors` is `False` ($0\text{ audit errors}$).
  3. *Layer Presence:* Confirms presence of `SHEET_BOUNDARY`, `CUT_CONTOUR`, `HOLE_CONTOUR`, and `PART_IN_PART_CHILD` layers.
  4. *Polyline Closure:* Audits every LWPOLYLINE and POLYLINE to verify `is_closed == True` with $\ge 3$ vertices.
  5. *Net Area Conservation:* Reconstructs the planar polygons from exported cut and hole layers, verifies that `gross_cut_area - hole_area` matches `expected_net_area` of placed parts within $\Delta \le 0.05\text{ mm}^2$.
- Integrated directly into `export_nesting_to_dxf(sheets, output_file, validate=True)`.

---

### 5. Automated Verification & Test Suite Growth

The test suite expanded from **66 to 77 tests** with the addition of `team_algoryxz/nest_craft/tests/test_stage_e_integrity.py`:
- `test_esicup_txt_valid_multipart_preserved`: Ingestion and preservation of multi-contour pieces in TXT format.
- `test_esicup_txt_unauthorized_invalid_rejected`: Strict `CADTopologyError` on unauthorized malformed TXT input.
- `test_esicup_xml_quantity_and_id_preservation`: Ingestion of XML lot pieces with exact quantity and piece ID preservation.
- `test_part_validation_record_schema`: Verification of structured `validation_record` on `Part`.
- `test_hausdorff_deviation_detection_on_boundary_alteration`: Verification of Hausdorff distance metric on collapsed features.
- `test_part_rejection_on_excessive_hausdorff_deviation`: Rejection of unauthorized feature loss during repair.
- `test_hole_count_calculation`: Exact counting across Polygon and MultiPolygon geometry.
- `test_export_nesting_dxf_clean_validation`: Successful end-to-end DXF export and verification.
- `test_validate_exported_dxf_detects_corrupt_file`: Detection of missing or non-DXF files.
- `test_validate_exported_dxf_detects_unclosed_contour`: Detection of open polylines on cutting layers.
- `test_validate_exported_dxf_detects_area_mismatch`: Detection of geometric area conservation discrepancies.

**Execution Result:**
`77 passed in 5.79s` (100% pass rate, 0 failures, 0 errors).

---

### 6. Benchmark Non-Regression Confirmation

Historical industrial benchmark parameters:
- Stock: $800 \times 500\text{ mm}$
- Torch Clearance: $4.0\text{ mm}$
- Random Seeds: `[42, 101, 202, 303, 404]`
- Total Parts: 17 parts (4 gussets, 6 brackets, 4 flanges, 3 base plates)

**Benchmark Results:**
- **BLF Baseline:** $2,350.00\text{ mm}$ total linear extent (3 sheets, $49.33\%$ discrete utilization).
- **Simulated Annealing (Orthogonal):** Mean linear extent $1,946.00\text{ mm}$ across all 5 seeds ($17.19\%$ linear reduction).
- **Discrete Stock Purchasing:** Exactly 3 sheets required across 100% of runs.
- **Prime Remnant Offcut:** Reclaims $227,000\text{ mm}^2$ virgin offcut plate on Sheet 3 (vs $25,000\text{ mm}^2$ unusable strip in BLF).
- Zero regression against established Stage C, C.1, and D baseline metrics.
