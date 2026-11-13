# NEST-CRAFT — GitHub Handoff and Engineering Verification Report

**Project:** NEST-CRAFT (Team Algoryxz — Odisha AI Hackathon 2026)  
**Date:** November 13, 2026 (Updated Post-Publication Revision)  
**Repository:** [https://github.com/Smarak-padhi/NEST-CRAFT](https://github.com/Smarak-padhi/NEST-CRAFT)  
**Remote URL:** `https://github.com/Smarak-padhi/NEST-CRAFT.git`  
**Target Branch:** `main`  
**Audit Status:** Release-Ready & Verified (Stages A, B, C, C.1, C.2, D complete)  

> [!IMPORTANT]
> **Post-Publication Audit Notice (November 13, 2026):**  
> This initial handoff report contained documentation inaccuracies regarding benchmark configuration parameters (previously misstating 24 parts on 2,400 × 1,200 mm stock at 5.0 mm clearance, whereas the true historical benchmark was 17 parts on 800 × 500 mm stock at 4.0 mm clearance), execution environment versioning (previously citing Python 3.11.9 instead of the verified Python 3.12.10 environment), and assumed file tree paths (such as `app/main.py` instead of `app/app.py`).  
> These statements are officially superseded by [`POST_PUBLICATION_AUDIT.md`](POST_PUBLICATION_AUDIT.md) and [`POST_PUBLICATION_BENCHMARK_AUDIT.md`](POST_PUBLICATION_BENCHMARK_AUDIT.md). The corrected specifications are presented below.

---

## 1. Executive Summary

This handoff packages and publishes the complete codebase, test suite, validation benchmarks, and documentation of **NEST-CRAFT** to GitHub. The project has undergone rigorous audit phases ensuring mathematical precision, CAD topology integrity, zero collision tolerance, and strict truthfulness in engineering metrics.

### Key Milestones Achieved:
1. **Stage A:** Full architectural audit and baseline inspection across 6 repositories and the initial NEST-CRAFT codebase.
2. **Stage B:** Implementation of geometry-verified Part-in-Part nesting (`ENG-04`) with hole extraction, interior clearance buffering, and containment validation.
3. **Stage C & C.1:** Adversarial geometry fuzzing, CAM structural export validation, benchmark reconciliation (clarifying that linear compaction does not equal discrete plate purchase reduction, and rectifying adaptive rotation claims).
4. **Stage C.2:** Independent verification gate confirming all baseline benchmarks and reports without regression.
5. **Stage D & Post-Pub:** Remediation of `DEF-01` (preventing silent component loss during CAD ingestion) with full MultiPolygon support, explicit topology-change authorization via `CADTopologyError`, closed-loop DXF ingestion enforcement, and 15 dedicated regression tests (66 passed total).

---

## 2. Repository Layout & Structure

The repository root is organized for developer clarity, reproducible execution, and standard Git hygiene:

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
            ├── test_adaptive_rotation.py
            ├── test_def01_remediation.py
            ├── test_dxf_reliability.py
            ├── test_geometry_adversarial_stress.py
            ├── test_geometry_validation.py
            ├── test_nesting.py
            └── test_part_in_part_nesting.py
```

---

## 3. Verification & Benchmark Reproducibility

### A. Test Suite Status
Before publication, the full test suite was executed in the clean repository structure:
```bash
pytest team_algoryxz/nest_craft/tests
```
**Outcome:**
- **Environment:** Windows 11 · Python 3.12.10 · pytest 8.3.3
- **66 passed** in 4.37 seconds across 7 test modules.
- 100% assertion pass rate across unit, boundary, export, part-in-part, and Stage D regression suites.

### B. Benchmark Reproducibility (Industrial Dataset)
The standardized 5-seed benchmark was re-verified against the historical reconciliation baseline:
- **Dataset:** Industrial Dataset (17 parts: 4 gussets, 6 brackets, 4 flanges, 3 base plates).
- **Stock Plate:** $800.0\text{ mm} \times 500.0\text{ mm}$ ($400,000.0\text{ mm}^2$ per sheet).
- **Clearance:** $4.0\text{ mm}$ thermal kerf offset.
- **Seeds:** `[42, 101, 202, 303, 404]`.

| Algorithm | Seeds Tested | Mean Extent (mm) | Sheet Count | Area Utilization | Reusable Remnants |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BLF Baseline** | Deterministic | $2,350.00\text{ mm}$ | 3 discrete plates | 46.67% | $25,000\text{ mm}^2$ |
| **Simulated Annealing (Orthogonal)** | 5 seeds | **$1,946.00\text{ mm}$** | 3 discrete plates | 46.67% | **$227,000\text{ mm}^2$** |
| **Simulated Annealing (Adaptive 45°)** | 5 seeds | $2,509.34\text{ mm}$ | 3.60 discrete plates | 39.67% | $185,326\text{ mm}^2$ |

**Confirmed Engineering Facts:**
- Orthogonal Simulated Annealing achieves an average **$17.19\%$ linear compaction** ($2,350\text{ mm} \rightarrow 1,946\text{ mm}$) compared to BLF.
- Both algorithms require **exactly 3 stock plates** on the tested industrial part mix. Linear compaction frees contiguous prime remnant plate area ($227,000\text{ mm}^2$ vs $25,000\text{ mm}^2$), but does **not** reduce discrete plate purchase count.
- Adaptive rotation ($15^\circ$ coarse + $5^\circ$ fine) produces bounding-box overhangs on rectangular stock, yielding a $+28.95\%$ linear span penalty and requiring a 4th plate in 3 out of 5 seeds.

---

## 4. Truth in Engineering Declarations

1. **DXF Export vs G-code:**
   - NEST-CRAFT outputs standardized 2D DXF files containing parts, stock boundaries, and cut paths.
   - NEST-CRAFT does **not** generate CNC G-code (`G00`, `G01`, `M03`, etc.), nor does it control CNC machine feedrates, laser piercing routines, or lead-in/lead-out tabs.
2. **CAM Interoperability:**
   - DXF exports have been validated against AutoCAD R2018 / DXF R12 polygon structural requirements via `ezdxf.audit()`.
   - Commercial CAM import (e.g., CypCut, FastCAM, ProNest) has **not** been physically tested on live CNC cutting tables.
3. **Material Accounting:**
   - Linear compaction must never be conflated with plate purchase savings. Sheet purchases are discrete integers.
4. **Topology Guardrails:**
   - Multipart DXF geometries are never silently flattened or truncated. When geometry repairs alter topology, `CADTopologyError` halts execution unless explicitly authorized with `allow_repaired_topology=True`.

---

## 5. Teammate Quickstart

To run the application or tests locally:

```bash
# 1. Clone repository
git clone https://github.com/Smarak-padhi/NEST-CRAFT.git
cd NEST-CRAFT

# 2. Create virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify test suite (66 tests)
pytest team_algoryxz/nest_craft/tests

# 5. Launch UI
streamlit run team_algoryxz/nest_craft/app/app.py
```

---

## 6. Security and File Hygiene Audit

- **Credentials & API Keys:** 0 found. No personal access tokens, private keys, or passwords exist in the tree.
- **Environment Files:** No `.env` or sensitive configurations are tracked.
- **Cache Files:** All `__pycache__`, `.pytest_cache`, and `*.pyc` artifacts excluded via `.gitignore`.
- **Git Commit Integrity:** Linear history maintained; no force-push used.
