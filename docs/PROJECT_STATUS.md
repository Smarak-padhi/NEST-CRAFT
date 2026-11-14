# NEST-CRAFT — Project Status & Handover Ledger

**Current Engineering Stage:** Stage G.2 Completed & Verified (Parser Integrity & Documentation Closure)  
**Last Audit Date:** 2026-11-14  
**Repository Branch:** `main`

---

## 1. Executive Status Dashboard

| Dimension | Current State | Verifiable Evidence |
| :--- | :---: | :--- |
| **Automated Tests** | **138 / 138 Passing** (100%) | Verified via pytest in clean repository root (across 13 test suites). |
| **Geometry Engine** | **Strict Fail-Closed & Hardened** | `compute_boundary_deviation` strictly validates runtime types, rejects non-polygonal or empty components in `GeometryCollection`s, validates pure polygonal collections against overlaps, duplicates, nesting, and invalid MultiPolygon topologies, and safely flattens valid disjoint collections. `Part.__init__` rejects non-polygonal or sub-threshold components unless explicitly authorized via `metadata['allow_feature_loss']=True` and enforces valid `MultiPolygon` construction. |
| **Optimization Core** | **BLF & SA Operational** | BLF baseline and Simulated Annealing with Part-in-Part cavity nesting verified across fixed seeds. |
| **Benchmark Status** | **Locked & Proven** | Dedicated reproducibility test (`test_benchmark_reproducibility.py`) permanently locks the 17-part, 5-seed orthogonal baseline at **1,946.00 mm** (-17.19% compaction, 3 discrete sheets). |
| **CAD / DXF Ingestion** | **16-Case Test Corpus** | Evaluated against 16 synthetic edge cases in `SYNTHETIC_DXF_TEST_MATRIX.md` (splines, bulges, open contours, nested holes, narrow slots, large coordinates, R12/R2018). |
| **CAM Export Handoff** | **Protocol Defined** | 6 validated DXF export artifacts in `data/cam_export_samples/`. Full protocol and checklist defined in `CAM_INTEROPERABILITY_TEST_PROTOCOL.md`. |
| **Fabricator Validation** | **Prepared Package** | Non-commercial fabricator evaluation package and structured feedback survey authored in `FABRICATOR_FEEDBACK_TEMPLATE.md`. |
| **Hackathon Readiness** | **READY (VERIFIED)** | Approved for controlled prototype demonstration at Odisha AI Hackathon 2026. |
| **Industrial Pilot** | **PROTOCOL READY** | CAM import protocol ready for testing on external commercial CAM licenses (ProNest, CypCut, TruTops). |
| **Autonomous Production** | **NOT READY (DISCLAIMED)** | G-code generation, thermal dissipation modeling, and CNC vision feedback are out of scope. |

---

## 2. Completed Milestones (Stages A through F)

### Stage A: Codebase Audit & Baseline
- Audited 6 reference repositories and established strict security boundaries.
- Set up initial Bottom-Left-Fill (BLF) and Simulated Annealing (SA) baselines.

### Stage B: Core Feature Implementation
- **ENG-04 (Part-in-Part Nesting):** Inward negative buffering ($H.\text{buffer}(-c)$) to identify safe feasible cavities inside parent holes.
- **ENG-05 (Adaptive Rotation):** Coarse $15^\circ$ exploration with $5^\circ$ local refinement and rolling grain constraints.

### Stage C & C.1: Evidence Reconciliation & Rigor
- **Benchmark Reconciliation:** Proved that the 1,946.00 mm vs. 1,939.33 mm deviation was strictly a 5-seed vs. 3-seed arithmetic mean. Both are derived from identical deterministic runs.
- **Adversarial Stress Testing:** Built 9-test adversarial suite for concave cutouts, pinch-off necks, and sub-millimeter clearance checks down to $1\text{ \mu m}$.
- **Evidence Corrections (C.1):** Retracted unsubstantiated claims about adaptive rotation on irregular parts; disclosed that adaptive rotation performed worse on average across both datasets.

### Stage C.2: Independent Verification Gate
- Identified **DEF-01**: `Part.__init__` previously used `max(polygon.geoms, key=lambda g: g.area)`, silently discarding non-maximum components of `MultiPolygon`s and causing up to 50% material loss on bow-tie geometries.

### Stage D: DEF-01 Remediation
- Enabled `MultiPolygon` across area calculation, unit normalization, rotation, collision checking, sheet containment, Streamlit visualization, and DXF export.
- Introduced `CADTopologyError` to reject invalid geometry repairs that alter component count or area without explicit authorization.
- Added 8 dedicated regression tests (`test_def01_remediation.py`). Total project tests reached 66 passed.

### Stage E: Ingestion Reliability & Demo Excellence
- Closed residual DEF-01 component reductions in `parse_esicup_txt` and `parse_esicup_xml`.
- Enhanced topology validation with Hausdorff distance boundary deviation metric (`compute_boundary_deviation`), hole/component count delta tracking, and structured `Part.validation_record`.
- Upgraded Streamlit UI to a 9-step industrial progression with per-file CAD diagnostics table, pre-flight critical error blocking, placement completeness accounting ($17/17$ placed parts), and an illustrative financial scenario estimation model.
- Added `validate_exported_dxf` auditing reopenability, structural integrity, polyline closure, and net area conservation within $\Delta \le 0.05\text{ mm}^2$.
- Added 11 automated regression tests (`test_stage_e_integrity.py`), bringing total suite to 77 passed tests.

### Stage F: Reliability Hardening & Real-World Validation Preparation
- **Fail-Closed Geometry Validation:** Resolved fail-open behavior in `compute_boundary_deviation()`. Replaced generic fallback to 0.0 with `GeometryComparisonError` and `float('inf')`. Guarded `Part.__init__` so comparison failures cannot accidentally authorize damaged geometry.
- **Locked Benchmark Configuration:** Identified and documented historical iteration typo (ESICUP used 25 iterations; Industrial used 20 iterations). Locked complete 17-part, 5-seed configuration in `test_benchmark_reproducibility.py` (mean $1,946.00\text{ mm}$, $17.19\%$ compaction, 3 sheets).
- **16-Case Synthetic DXF Test Corpus:** Built `data/dxf_test_corpus/` containing synthetic edge cases and documented all results in `SYNTHETIC_DXF_TEST_MATRIX.md`. Added 16 tests in `test_dxf_corpus.py`.
- **CAM Interoperability Protocol:** Produced 6 validated export DXF layouts in `data/cam_export_samples/` and defined step-by-step SOP in `CAM_INTEROPERABILITY_TEST_PROTOCOL.md`.
- **Fabricator Validation Package:** Created plain-language shop guide and structured evaluation survey in `FABRICATOR_FEEDBACK_TEMPLATE.md` with complete truthfulness disclosures.
- **Total Test Count:** 109 / 109 tests passing.

### Stage G: Runtime Type Validation, CI Workflow & Intake Process
- **Geometry Runtime Type Validation:** Enforced strict runtime type checking in `compute_boundary_deviation()`, rejecting `Point` and `LineString` inputs.
- **Continuous Integration (CI):** Implemented GitHub Actions CI workflow (`.github/workflows/ci.yml`) on Python 3.12 running the full test and benchmark suite.
- **Real-World Intake Framework:** Established 10-step customer drawing intake SOP (`REAL_WORLD_DXF_INTAKE_PROCESS.md`) and unpopulated living case matrix (`REAL_WORLD_DXF_TEST_MATRIX.md`).
- **Ingestion Override Tracking:** Surfaced active CAD safety overrides in validation reports and Streamlit dashboard.

### Stage G.1: GeometryCollection Integrity Closure & Strict Component Validation
- **GeometryCollection Integrity Closure:** Enforced fail-closed rejection in `compute_boundary_deviation()` for repaired `GeometryCollection`s containing non-polygonal (`LineString`, `Point`) or empty components. Pure polygonal collections are safely flattened into `MultiPolygon` and measured.
- **Strict Component Rejection in `Part.__init__`:** Prohibited silent omission of non-polygonal elements or sub-threshold polygons (area $\le 10^{-4}\text{ mm}^2$). Explicitly requires `metadata['allow_feature_loss']=True` to authorize omission of non-nestable components.
- **Multi-Loop ESICUP Parsing:** Enabled closed sub-loop parsing in `parse_esicup_txt` to construct genuine `MultiPolygon` parts directly from vertex coordinates without artificial self-intersections.
- **Total Test Count:** **121 / 121 tests passing** across 12 test suites.

### Stage G.2: Parser Integrity & Documentation Closure (Current Baseline)
- **Hardened ESICUP Multi-Loop Parser:** Eliminated silent fallback in `parse_esicup_txt()`. Enforced strict fail-closed rejection with clear diagnostics for unclosed final loops, malformed/self-intersecting loops, degenerate loops (<3 unique vertices), zero-area loops, overlapping/intersecting sub-loops, and duplicate sub-loops. Concentric loops are topologically nested as interior holes while disjoint loops become native `MultiPolygon`s.
- **Pure Polygonal GeometryCollection Validation:** Enforced strict fail-closed rejection in `compute_boundary_deviation()` for overlapping components, duplicate components, nested components, invalid resulting `MultiPolygon` topologies (such as shared edges), empty polygons, and invalid polygons.
- **Documentation & Link Hygiene:** Eliminated all absolute Windows `file:///` links across all active project reports, reconciled regression-test accounting, rigorously defined plate remnant categories (geometric unnested margin vs. prime remnant vs. offcut scrap), and corrected benchmark dataset provenance.
- **Total Test Count:** **138 / 138 tests passing** across 13 test suites.

---

## 3. High-Priority Next Tasks (Roadmap Ahead)

1. **CAM Post-Processor Integration (P1):**
   - Partner with an industrial sheet metal fabrication shop to run the 6 exported DXF samples through an actual commercial CAM suite (e.g. Trumpf TruTops, Bystronic BySoft, CypCut, or Hypertherm ProNest) following `CAM_INTEROPERABILITY_TEST_PROTOCOL.md`.
   - Verify automated micro-tab injection to prevent child parts from dropping into table slats.
2. **Fabricator Field Trials (P1):**
   - Collect empirical feedback using `FABRICATOR_FEEDBACK_TEMPLATE.md` from at least 2 fabrication workshops.
