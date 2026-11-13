# NEST-CRAFT — Post-Publication Audit and Documentation Correction Report

**Project:** NEST-CRAFT (Team Algoryxz — Odisha AI Hackathon 2026)  
**Date:** November 13, 2026  
**Auditor:** Team Algoryxz Independent Engineering Audit  
**Starting Commit:** `e2d6108976da75a4241e9e608715104c5ffba212`  
**Status:** Audit Complete · Inaccuracies Corrected · 66 Tests Passing · Benchmark Bitwise Verified  

---

## 1. Executive Summary

Following publication of commit `e2d6108`, an exhaustive independent audit was conducted across the committed codebase, documentation, test suite, and benchmark evidence.

This audit identified and resolved four critical issues:
1. **Benchmark Documentation Inaccuracy:** The previous handoff report conflated benchmark parameters, citing "24 mixed parts" on "2,400 × 1,200 mm stock" with "5.0 mm clearance", while citing the 1,946.00 mm extent result. The genuine historical benchmark was executed with the original **17 parts**, **800 × 500 mm stock**, and **4.0 mm clearance**. It has been **100% bitwise reproduced**.
2. **Python Environment Inconsistency:** The previous report cited Python 3.11.9. The actual tested and verified execution environment is **Python 3.12.10** with **pytest 8.3.3**.
3. **Repository Tree Inaccuracies:** The handoff report referenced non-existent paths (e.g., `app/main.py`, `src/algorithms.py`, `src/dxf_parser.py`). The true layout has been mapped and documented (`app/app.py`, `src/geometry.py`, `src/optimizer.py`, `src/dxf_io.py`, `src/baseline.py`, `src/calculator.py`).
4. **Stage D Ingestion Guardrail Defect:** In `src/dxf_io.py`, `validate_and_parse_dxf` hardcoded `"allow_repaired_topology": True`, allowing self-intersecting DXF contours to bypass rejection without caller authorization. This has been remediated and verified with 7 new regression tests (66 passed total).

---

## 2. Git State and Repository Integrity

- **Remote URL:** `https://github.com/Smarak-padhi/NEST-CRAFT.git`
- **Target Branch:** `main`
- **Starting Commit SHA:** `e2d6108976da75a4241e9e608715104c5ffba212`
- **Commit Preservation:** Zero force-push, zero rebase. All prior commits (`2c9b44a`, `5d5816c`, `e2d6108`) are strictly preserved in the parent history.

---

## 3. Actual Repository Architecture & Tree

The actual structure of the repository is:

```
NEST-CRAFT/
├── .gitignore                      # Pinned Git ignore (Python, pytest, virtualenvs, logs)
├── pytest.ini                      # Root pytest config (pythonpath = .)
├── README.md                       # Complete project overview, architecture, quickstart
├── CONTRIBUTING.md                 # Contributor guidelines and engineering standards
├── requirements.txt                # Exact project runtime dependencies
├── docs/                           # Architecture, validation, and onboarding documentation
│   ├── DEVELOPER_ONBOARDING.md     # 5-minute step-by-step setup and verification guide
│   ├── PROJECT_STATUS.md           # Current phase deliverables, status, and verification gates
│   ├── TEAM_HANDOFF.md             # Detailed engineering handoff and Stage D architecture
│   ├── TECHNICAL_ARCHITECTURE.md   # System pipeline, geometry engines, and module boundaries
│   ├── VALIDATION_AND_BENCHMARKS.md# Benchmark methodology, seeds, and reconciled metrics
│   ├── KNOWN_LIMITATIONS.md        # Technical boundaries (no G-code, 2D planar, CAM requirements)
│   ├── PROJECT_HISTORY.md          # Chronological audit log from hackathon start
│   └── ROADMAP.md                  # Prioritized engineering tasks (P0–P2)
└── team_algoryxz/
    └── nest_craft/
        ├── .agents/skills/         # Local specialized agent skills
        │   ├── industrial-ui-unslop/
        │   ├── nest-craft-geometry-qa/
        │   └── nest-craft-remnant-accounting/
        ├── app/                    # Streamlit Industrial UI application
        │   └── app.py
        ├── benchmarks/             # Benchmark test suites, datasets, and execution scripts
        │   └── run_nesting_benchmarks.py
        ├── data/                   # Validated DXF test files and synthetic profiles
        │   ├── dataset_inventory.md
        │   ├── download_sample_esicup.py
        │   ├── fetch_esicup.py
        │   ├── inspect_benchmarks.py
        │   ├── esicup/             # ESICUP benchmark instances (shapes.txt, swim.txt, etc.)
        │   ├── industrial_samples/ # 4 production-grade DXFs (gusset, bracket, flange, base plate)
        │   └── samples/            # Standard sample DXF suite
        ├── reports/                # Stage A through D audit reports, benchmarks, and handoff
        │   ├── GITHUB_HANDOFF_REPORT.md
        │   ├── POST_PUBLICATION_AUDIT.md
        │   ├── POST_PUBLICATION_BENCHMARK_AUDIT.md
        │   ├── post_publication_benchmark_results.json
        │   ├── STAGE_A_AUDIT_REPORT.md
        │   ├── STAGE_B_IMPLEMENTATION_REPORT.md
        │   ├── STAGE_C_BENCHMARK_RECONCILIATION.md
        │   ├── STAGE_C_CAM_COMPATIBILITY.md
        │   ├── STAGE_C_GEOMETRY_STRESS_TEST.md
        │   ├── STAGE_C_RELEASE_READINESS.md
        │   ├── STAGE_C_SECURITY_REVIEW.md
        │   ├── STAGE_C1_CHANGELOG.md
        │   ├── STAGE_C2_INDEPENDENT_VERIFICATION.md
        │   └── STAGE_D_DEF01_REMEDIATION.md
        ├── src/                    # Core NEST-CRAFT nesting engine
        │   ├── baseline.py         # Bottom-Left-Fill heuristic engine
        │   ├── calculator.py       # Metrics and remnant plate math
        │   ├── dxf_io.py           # DXF validation, entity parsing, and export
        │   ├── geometry.py         # Part, Sheet, MultiPolygon, CADTopologyError
        │   └── optimizer.py        # Simulated Annealing engine
        └── tests/                  # 7 test modules (66 passed tests)
            ├── test_adaptive_rotation.py              (8 tests)
            ├── test_def01_remediation.py             (15 tests)
            ├── test_dxf_reliability.py                (9 tests)
            ├── test_geometry_adversarial_stress.py   (10 tests)
            ├── test_geometry_validation.py            (8 tests)
            ├── test_nesting.py                        (7 tests)
            └── test_part_in_part_nesting.py           (9 tests)
```

---

## 4. Benchmark Reproduction & Truthfulness Audit

### Exact Benchmark Configuration
- **Dataset:** Industrial Batch (17 parts: 4 gussets, 6 brackets, 4 flanges, 3 base plates)
- **Stock Plate:** $800.0\text{ mm} \times 500.0\text{ mm}$
- **Thermal Kerf Clearance:** $4.0\text{ mm}$
- **Random Seeds:** `[42, 101, 202, 303, 404]`

### Measured Results:
- **BLF Baseline:**
  - Discrete Plates Consumed: **3**
  - Total Linear Extent: **2,350.00 mm**
  - Discrete Utilization: **46.67%**
  - Final Sheet Remnant: **25,000.00 mm²**
- **Simulated Annealing (Orthogonal Mode):**
  - Seed 42: 1,966.00 mm (3 sheets, +384.00 mm saved)
  - Seed 101: 2,110.00 mm (3 sheets, +240.00 mm saved)
  - Seed 202: 1,742.00 mm (3 sheets, +608.00 mm saved)
  - Seed 303: 1,986.00 mm (3 sheets, +364.00 mm saved)
  - Seed 404: 1,926.00 mm (3 sheets, +424.00 mm saved)
  - **5-Seed Mean Extent:** **1,946.00 mm** (3 discrete plates, 100% runs)
  - **Linear Compaction:** **-17.19%** relative to BLF
  - **Mean Remnant Offcut:** **227,000.00 mm²** (Prime reusable plate)
- **Simulated Annealing (Adaptive Mode):**
  - **5-Seed Mean Extent:** **2,509.34 mm** (+28.95% penalty)
  - **Discrete Plates Consumed:** **3.60 avg** (forced 4th plate in 3 of 5 runs)

### Metric Declarations:
- **Linear Compaction vs Discrete Stock Purchases:** The $17.19\%$ reduction applies strictly to continuous strip cutting advance along the final sheet. Both algorithms require **exactly 3 stock plates**. It is NOT a reduction in sheet purchases.
- **Adaptive Rotation Disclosure:** Adaptive non-orthogonal rotation degrades performance on rectangular stock due to bounding box expansion.

---

## 5. Commercial Claim Audit & Removal

All public-facing documentation has been audited. The following claims were removed or qualified:
1. **Removed:** "MSMEs face utilization rates as low as 40–55%." (Unsupported market claim; removed from README).
2. **Qualified:** The 17.19% figure is explicitly qualified as: *"17.19% reduction in linear nesting extent versus BLF on the specified 17-part, 800 × 500 mm, 4 mm-clearance industrial benchmark."*
3. **Clarified:** No claims of commercial adoption, cost savings, or production readiness are made. Commercial viability remains an unvalidated hypothesis requiring formal customer fabrication trials.

---

## 6. Stage D Ingestion Guardrail Audit & Remediation

### Defect Identified:
In `team_algoryxz/nest_craft/src/dxf_io.py`, `validate_and_parse_dxf` hardcoded `"allow_repaired_topology": True` when creating `Part` instances, and called `make_valid` on invalid closed polylines during entity extraction. Consequently, self-intersecting DXFs (such as bowties) were silently repaired and accepted without raising an error or requiring caller authorization.

### Remediation Applied:
1. Added `allow_repaired_topology: bool = False` to `validate_and_parse_dxf` and `parse_dxf`.
2. Self-intersecting contours encountered during DXF parsing now check `allow_repaired_topology`. When `False`, `report["is_valid"] = False` is set and `report["errors"]` records the failure. In `parse_dxf(strict=True)`, `DXFValidationError` is raised.
3. Enhanced `Part.__init__` topology alteration detection in `geometry.py`:
   - Checks interior hole count preservation before and after repair.
   - Checks component count preservation.
   - Tightened area alteration threshold to $0.01$ (1%).
4. Added 7 new regression tests in `test_def01_remediation.py`:
   - `test_repair_that_changes_hole_count_rejected`
   - `test_repair_preserves_area_but_changes_topology_rejected`
   - `test_unauthorized_repair_rejected_in_dxf_ingestion`
   - `test_multipart_sheet_boundary_containment`
   - `test_part_in_part_with_multipart_geometry`
   - `test_multipart_rotation_and_translation`
   - `test_narrow_slots_and_small_features_preserved`

---

## 7. Automated Test Suite Execution

Ran `pytest team_algoryxz/nest_craft/tests` from the repository root:

- **Command:** `pytest team_algoryxz/nest_craft/tests`
- **Environment:** Windows 11 · Python 3.12.10 · pytest 8.3.3
- **Configuration:** `pytest.ini` (`pythonpath = .`)
- **Total Tests Collected:** 66
- **Passed:** **66**
- **Failed:** 0
- **Skipped:** 0
- **Runtime:** 4.37 seconds

---

## 8. Remaining Known Limitations

1. **2D CAD Output Only:** Outputs AutoCAD DXF vector contours. Does NOT generate CNC machine G-code.
2. **No Physical Cutting Trials:** No physical CNC cutting trials (laser, plasma, waterjet) have been conducted.
3. **No Commercial CAM Post-Processor Testing:** DXF exports are verified structurally via `ezdxf.audit()`, but have not been imported into commercial CAM software (e.g. Trumpf TruTops, CypCut).
4. **Rectilinear Stock Bias:** Adaptive rotation is currently unsuited for rectangular stock plates and must not be used as the default mode.
5. **Hackathon Prototype Status:** The engine is an engineering demonstration prototype, not a certified commercial product.
