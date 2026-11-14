# NEST-CRAFT — Stage F: Implementation & Verification Report
## Reliability Hardening & Real-World Validation Preparation

**Project:** NEST-CRAFT — 2D Sheet-Metal Nesting Engine  
**Team:** Algoryxz · Odisha AI Hackathon 2026  
**Baseline Commit:** `8e5ead8639aacc53eb76d02f186bf63aace4e37d`  
**Execution Date:** November 14, 2026  
**Target Commit Message:** `Stage F: harden validation and prepare real-world interoperability`  

---

### Executive Summary

Stage F transitions NEST-CRAFT from an algorithmic prototype toward a production-trustworthy manufacturing workflow. It eliminates fail-open geometry validation vulnerabilities, locks and reproduces the exact historical Stage C benchmark configuration, creates a 16-case real-world DXF edge-case test corpus, produces 6 structurally validated CAM export artifacts, defines an external CAM interoperability protocol, and provides a structured MSME fabricator feedback package with complete truthfulness disclosures.

---

### 1. Task 1: Fix Fail-Open Geometry Validation

#### Vulnerability Analysis
In `src/geometry.py`, `compute_boundary_deviation(poly_orig, poly_repaired)` previously caught generic exceptions or NaN values and returned `0.0`. This was a severe fail-open vulnerability: any internal calculation error, GEOS exception, or non-finite coordinate state masqueraded as $0.0\text{ mm}$ boundary displacement, allowing damaged or distorted geometry to pass verification unnoticed.

#### Fail-Closed Remediation
1. **Introduced `GeometryComparisonError(CADTopologyError)`**: Dedicated exception hierarchy for boundary evaluation failures.
2. **Defensive Pre-Condition Checks**: Checks for `None` or empty geometries and raises `GeometryComparisonError` (or returns `float('inf')` if `fail_closed=False`).
3. **Finite Metric Enforcement**: Asserts that Hausdorff distance is finite; rejects NaN and $\pm\infty$ values.
4. **Guarded `Part.__init__`**:
   * If boundary comparison fails, `hausdorff_dist = float('inf')`, `feature_loss_detected = True`, and `topology_altered = True`.
   * Calling code cannot accidentally authorize damaged geometry: even if `allow_repaired_topology=True` is provided, `Part` raises `GeometryComparisonError` unless an explicit, dedicated `metadata['allow_unverifiable_geometry']=True` is also provided.
5. **Audited Other Handlers**: Verified that `check_collision()`, `compute_hole_feasible_regions()`, and `validate_and_parse_dxf()` strictly reject invalid geometry without swallow-all handlers.
6. **Automated Verification**: Added 8 unit tests in `test_fail_closed_geometry.py` testing `None`, empty geometry, non-polygonal collections, GEOS exceptions, NaN returns, and authorized/unauthorized repair paths.

---

### 2. Task 2: Lock Historical Benchmark Configuration

#### Discrepancy Investigation
* **Observation:** The runner in `benchmarks/run_nesting_benchmarks.py` specified `max_iterations=20`, `initial_temp=100.0`, `cooling_rate=0.85`, and `step_size=8.0`, whereas text in `STAGE_C_BENCHMARK_RECONCILIATION.md` line 71 stated "(25 iterations each)".
* **Root Cause Found in Raw Audit Artifacts:** An audit of `team_algoryxz/nest_craft/reports/benchmark_reconciliation_raw.json` revealed that:
  * The ESICUP Shapes dataset was evaluated with **25 iterations**.
  * The Industrial DXF dataset was evaluated with **20 iterations**.
  * The markdown documentation author inadvertently copy-pasted the phrase "(25 iterations each)" into the industrial section header.
  * Running with 20 iterations under the specified parameters produces the exact historical per-seed sequence:
    * Seed 42: **1,966.0 mm** (Sheets: 3, Remnant: $434\text{ mm}$)
    * Seed 101: **2,110.0 mm** (Sheets: 3, Remnant: $290\text{ mm}$)
    * Seed 202: **1,742.0 mm** (Sheets: 3, Remnant: $658\text{ mm}$)
    * Seed 303: **1,986.0 mm** (Sheets: 3, Remnant: $414\text{ mm}$)
    * Seed 404: **1,926.0 mm** (Sheets: 3, Remnant: $474\text{ mm}$)
    * **5-Seed Mean: 1,946.00 mm** ($-17.19\%$ linear compaction vs. BLF $2,350.00\text{ mm}$).
* **Locking Test Created**: Built `tests/test_benchmark_reproducibility.py` (8 tests) that asserts configuration constants and asserts exact bitwise reproducibility across all 5 seeds and BLF baseline.

---

### 3. Task 3: Real-World DXF Validation Corpus

Generated 16 reproducible CAD edge-case files in `team_algoryxz/nest_craft/data/dxf_test_corpus/` using `generate_dxf_test_corpus.py` (all provenance synthetically documented; zero customer claims):
1. `case01_closed_poly.dxf`: Standard closed polyline with chamfer ($14,700.00\text{ mm}^2$).
2. `case02_open_contour.dxf`: Open segments with $3.0\text{ mm}$ gap (rejected fail-closed).
3. `case03_bulged_arcs.dxf`: Rounded corners via vertex bulge attributes ($13,912.64\text{ mm}^2$).
4. `case04_circles_holes.dxf`: Plate with 2 concentric circular cutouts ($28,594.97\text{ mm}^2$).
5. `case05_splines.dxf`: Organic B-spline curve cutting profile ($11,431.23\text{ mm}^2$).
6. `case06_disconnected_components.dxf`: Two separate brackets in one DXF ($9,600.00\text{ mm}^2$).
7. `case07_nested_holes.dxf`: 4-ring concentric island-in-hole topology ($66,000.00\text{ mm}^2$).
8. `case08_narrow_slots.dxf`: High-aspect-ratio $0.8\text{ mm} \times 60\text{ mm}$ thermal slot ($19,952.00\text{ mm}^2$).
9. `case09_small_cutouts.dxf`: Sub-kerf $\varnothing 1.5\text{ mm}$ pilot apertures ($9,994.83\text{ mm}^2$).
10. `case10_self_intersecting.dxf`: Bow-tie loop (rejected unauthorized, 2 parts authorized).
11. `case11_unsupported_3d.dxf`: 2D plate with 3DFACE and MESH entities (warned & ignored).
12. `case12_duplicate_contours.dxf`: Superimposed identical polylines ($20,000.00\text{ mm}^2$).
13. `case13_overlapping_contours.dxf`: Partially overlapping closed contours ($16,000.00\text{ mm}^2$).
14. `case14_large_coordinates.dxf`: Civil/GIS offset $(500000, 800000)$ normalized to origin.
15. `case15_dxf_version_r12.dxf`: Legacy AutoCAD R12 format (`AC1009`) with `POLYLINE`.
16. `case16_dxf_version_r2018.dxf`: Modern AutoCAD 2018 format (`AC1032`) with `LWPOLYLINE`.

*Deliverable:* Documented in [`reports/SYNTHETIC_DXF_TEST_MATRIX.md`](./SYNTHETIC_DXF_TEST_MATRIX.md) and automated via 16 tests in `tests/test_dxf_corpus.py`.

---

### 4. Task 4: DXF Export Interoperability & CAM Protocol

* **Representative Export Artifacts:** Generated 6 structurally validated DXF layouts in `team_algoryxz/nest_craft/data/cam_export_samples/` covering rectangular parts, concave L-brackets, multipart geometry, cutouts/holes, part-in-part cavity nesting, and multi-sheet layouts.
* **CAM Protocol SOP:** Authored [`reports/CAM_INTEROPERABILITY_TEST_PROTOCOL.md`](./CAM_INTEROPERABILITY_TEST_PROTOCOL.md) defining exact procedures for layer mapping (`SHEET_BOUNDARY`, `CUT_CONTOUR`, `HOLE_CONTOUR`, `PART_IN_PART_CHILD`), dimensional scale checks, pierce order prioritization, and micro-tab assignment in external CAM software.

---

### 5. Task 5: Fabricator Validation Package

* Authored [`reports/FABRICATOR_FEEDBACK_TEMPLATE.md`](./FABRICATOR_FEEDBACK_TEMPLATE.md) containing:
  1. Plain-language summary of what NEST-CRAFT does (packing, compaction, prime remnant recovery, part-in-part cavity nesting).
  2. Strict disclaimer of what it DOES NOT do (no G-code, no machine toolpaths, no micro-tabs, no kerf offset compensation).
  3. Operating guide for CAD diagnostics and remnant measurement.
  4. Structured 5-point evaluation survey for sheet-metal shop owners and CNC operators.
  5. Zero fabricated testimonials or unverified endorsements.

---

### 6. Five-Tier Truthfulness Disclosure

In strict accordance with engineering integrity standards:

1. **Automated Verification:** **$100\%$ PASS** — 109 automated unit, integration, adversarial, and regression tests passing in 80 seconds.
2. **Synthetic Test Coverage:** **$100\%$ PASS** — 16 synthetic DXF edge-case drawings and 6 export layouts verified through automated ezdxf and Shapely checks.
3. **Real External Software Testing:** **PENDING / NOT CONDUCTED** — Protocol defined in `CAM_INTEROPERABILITY_TEST_PROTOCOL.md`; awaiting manual import into commercial CAM software (e.g. ProNest, CypCut, TruTops).
4. **Fabricator Feedback:** **PENDING / NOT CONDUCTED** — Survey template created in `FABRICATOR_FEEDBACK_TEMPLATE.md`; awaiting real-world workshop trials.
5. **Physical Machine Testing:** **NOT CONDUCTED** — No physical cutting on CNC plasma, laser, or waterjet machines has occurred.
