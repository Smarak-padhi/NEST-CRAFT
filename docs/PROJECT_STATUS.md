# NEST-CRAFT — Project Status & Handover Ledger

**Current Engineering Stage:** Stage F Completed & Verified (Reliability Hardening & Real-World Validation Preparation)  
**Last Audit Date:** 2026-11-14  
**Repository Branch:** `main`

---

## 1. Executive Status Dashboard

| Dimension | Current State | Verifiable Evidence |
| :--- | :---: | :--- |
| **Automated Tests** | **109 / 109 Passing** (100%) | Verified via pytest in clean repository root (74.47s execution across 11 test suites). |
| **Geometry Engine** | **Fail-Closed & Hardened** | `compute_boundary_deviation` strictly fails closed (`GeometryComparisonError`), preventing unverified or corrupt geometry from passing as zero deviation. DEF-01 closed. |
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

### Stage F: Reliability Hardening & Real-World Validation Preparation (Current Master)
- **Fail-Closed Geometry Validation:** Resolved fail-open behavior in `compute_boundary_deviation()`. Replaced generic fallback to 0.0 with `GeometryComparisonError` and `float('inf')`. Guarded `Part.__init__` so comparison failures cannot accidentally authorize damaged geometry.
- **Locked Benchmark Configuration:** Identified and documented historical iteration typo (ESICUP used 25 iterations; Industrial used 20 iterations). Locked complete 17-part, 5-seed configuration in `test_benchmark_reproducibility.py` (mean $1,946.00\text{ mm}$, $17.19\%$ compaction, 3 sheets).
- **16-Case Synthetic DXF Test Corpus:** Built `data/dxf_test_corpus/` containing synthetic edge cases and documented all results in `SYNTHETIC_DXF_TEST_MATRIX.md`. Added 16 tests in `test_dxf_corpus.py`. Real-world drawings are governed by `REAL_WORLD_DXF_INTAKE_PROCESS.md`.
- **CAM Interoperability Protocol:** Produced 6 validated export DXF layouts in `data/cam_export_samples/` and defined step-by-step SOP in `CAM_INTEROPERABILITY_TEST_PROTOCOL.md`.
- **Fabricator Validation Package:** Created plain-language shop guide and structured evaluation survey in `FABRICATOR_FEEDBACK_TEMPLATE.md` with complete truthfulness disclosures.
- **Total Test Count:** **109 / 109 tests passing** across 11 test suites.

---

## 3. High-Priority Next Tasks (Roadmap Ahead)

1. **CAM Post-Processor Integration (P1):**
   - Partner with an industrial sheet metal fabrication shop to run the 6 exported DXF samples through an actual commercial CAM suite (e.g. Trumpf TruTops, Bystronic BySoft, CypCut, or Hypertherm ProNest) following `CAM_INTEROPERABILITY_TEST_PROTOCOL.md`.
   - Verify automated micro-tab injection to prevent child parts from dropping into table slats.
2. **Fabricator Field Trials (P1):**
   - Collect empirical feedback using `FABRICATOR_FEEDBACK_TEMPLATE.md` from at least 2 fabrication workshops.
3. **Continuous Integration (CI) Setup (P2):**
   - Add a GitHub Actions workflow (`.github/workflows/ci.yml`) to automatically run the 109 tests and benchmark checks on every pull request.
