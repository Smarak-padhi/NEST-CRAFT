# NEST-CRAFT — GitHub Handoff and Engineering Verification Report

**Project:** NEST-CRAFT (Team Algoryxz — Odisha AI Hackathon 2026)  
**Date:** November 13, 2026  
**Repository:** [https://github.com/Smarak-padhi/NEST-CRAFT](https://github.com/Smarak-padhi/NEST-CRAFT)  
**Remote URL:** `https://github.com/Smarak-padhi/NEST-CRAFT.git`  
**Target Branch:** `main`  
**Audit Status:** Release-Ready & Verified (Stages A, B, C, C.1, C.2, D complete)  

---

## 1. Executive Summary

This handoff packages and publishes the complete codebase, test suite, validation benchmarks, and documentation of **NEST-CRAFT** to GitHub. The project has undergone rigorous audit phases ensuring mathematical precision, CAD topology integrity, zero collision tolerance, and strict truthfulness in engineering metrics.

### Key Milestones Achieved:
1. **Stage A:** Full architectural audit and baseline inspection across 6 repositories and the initial NEST-CRAFT codebase.
2. **Stage B:** Implementation of geometry-verified Part-in-Part nesting (`ENG-04`) with hole extraction, interior clearance buffering, and containment validation.
3. **Stage C & C.1:** Adversarial geometry fuzzing, CAM structural export validation, benchmark reconciliation (clarifying that linear compaction does not equal discrete plate purchase reduction, and rectifying adaptive rotation claims).
4. **Stage C.2:** Independent verification gate confirming all baseline benchmarks and reports without regression.
5. **Stage D:** Remediation of `DEF-01` (preventing silent component loss during CAD ingestion) with full MultiPolygon support, explicit topology-change authorization via `CADTopologyError`, and 8 regression tests.

---

## 2. Repository Layout & Structure

The repository root is organized for developer clarity, reproducible execution, and standard Git hygiene:

```
NEST-CRAFT/
├── .gitignore                      # Pinned Git ignore (Python, pytest, virtualenvs, logs)
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
        │   └── main.py
        ├── benchmarks/             # Benchmark test suites, datasets, and execution scripts
        │   ├── benchmark_reconciliation_raw.json
        │   ├── benchmark_reconciliation_summary.csv
        │   ├── run_benchmarks.py
        │   └── run_reconciliation.py
        ├── data/                   # Validated DXF test files and synthetic profiles
        │   ├── bracket.dxf
        │   ├── flange.dxf
        │   ├── plate_sample.dxf
        │   └── triangle.dxf
        ├── reports/                # Stage A through D audit reports and backups
        │   ├── GITHUB_HANDOFF_REPORT.md
        │   ├── STAGE_A_AUDIT_REPORT.md
        │   ├── STAGE_B_IMPLEMENTATION_REPORT.md
        │   ├── STAGE_C_BENCHMARK_REPORT.md
        │   ├── STAGE_C_CAM_VALIDATION_REPORT.md
        │   ├── STAGE_C_GEOMETRY_ADVERSARIAL_REPORT.md
        │   ├── STAGE_C_TEST_EXECUTION_REPORT.md
        │   ├── STAGE_C_TRUTHFULNESS_REPORT.md
        │   ├── STAGE_C1_CHANGELOG.md
        │   ├── STAGE_C2_INDEPENDENT_VERIFICATION_REPORT.md
        │   └── STAGE_D_REMEDIATION_REPORT.md
        ├── src/                    # Core NEST-CRAFT nesting engine
        │   ├── __init__.py
        │   ├── algorithms.py       # BLF and Simulated Annealing with Part-in-Part nesting
        │   ├── dxf_export.py       # DXF nesting layout export with layer segregation
        │   ├── dxf_parser.py       # DXF ingestion (LWPOLYLINE, POLYLINE, LINE, ARC, CIRCLE)
        │   ├── geometry.py         # Part, Stock, MultiPolygon support, and topology guardrails
        │   ├── remnant.py          # Maximal Empty Rectangle (MER) remnant extraction
        │   └── utils.py
        └── tests/                  # 59 comprehensive unit, adversarial, and regression tests
            ├── test_algorithms.py
            ├── test_cad_boundary_matrix.py
            ├── test_def01_remediation.py
            ├── test_dxf_export.py
            ├── test_dxf_parser.py
            ├── test_edge_cases.py
            ├── test_geometry.py
            ├── test_part_in_part.py
            ├── test_remnant.py
            └── test_stage_c1_corrections.py
```

---

## 3. Verification & Benchmark Reproducibility

### A. Test Suite Status
Before handoff, the full test suite was executed in the clean repository structure:
```bash
pytest team_algoryxz/nest_craft/tests
```
**Outcome:**
- **59 passed** in 2.82 seconds.
- 100% assertion pass rate across unit, boundary, export, part-in-part, and Stage D regression suites.

### B. Benchmark Reproducibility (Industrial Dataset)
The standardized 5-seed benchmark was re-verified against the historical reconciliation baseline:
- **Dataset:** Industrial Dataset (24 mixed parts: brackets, flanges, triangles).
- **Stock Plate:** $2,400\text{ mm} \times 1,200\text{ mm}$ ($2.88\text{ m}^2$ per sheet).
- **Clearance:** $5.0\text{ mm}$ thermal kerf offset.
- **Seeds:** `[1966, 2110, 1742, 1986, 1926]`.

| Algorithm | Seeds Tested | Mean Extent (mm) | Sheet Count | Area Utilization | Reusable Remnants |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BLF Baseline** | Deterministic | $2,350.00\text{ mm}$ | 3 discrete plates | 48.74% | $0.85\text{ m}^2$ |
| **Simulated Annealing (Orthogonal)** | 5 seeds | **$1,946.00\text{ mm}$** | 3 discrete plates | 58.85% | **$1.42\text{ m}^2$** |
| **Simulated Annealing (Adaptive 45°)** | 5 seeds | $2,509.33\text{ mm}$ | 3.6 discrete plates | 45.62% | $0.62\text{ m}^2$ |

**Confirmed Engineering Facts:**
- Orthogonal Simulated Annealing achieves an average **$17.19\%$ linear compaction** ($2,350\text{ mm} \rightarrow 1,946\text{ mm}$) compared to BLF.
- Both algorithms require **exactly 3 stock plates** on the tested industrial part mix. Linear compaction frees contiguous prime remnant plate area ($1.42\text{ m}^2$ vs $0.85\text{ m}^2$), but does **not** reduce discrete plate purchase count.
- Adaptive rotation ($45^\circ$) produces bounding-box overhangs on rectangular stock, yielding a $+28.95\%$ linear span penalty and requiring a 4th plate in 3 out of 5 seeds.

---

## 4. Truth in Engineering Declarations

1. **DXF Export vs G-code:**
   - NEST-CRAFT outputs standardized 2D DXF files containing parts, stock boundaries, and cut paths.
   - NEST-CRAFT does **not** generate CNC G-code (`G00`, `G01`, `M03`, etc.), nor does it control CNC machine feedrates, laser piercing routines, or lead-in/lead-out tabs.
2. **CAM Interoperability:**
   - DXF exports have been validated against AutoCAD R2018 / DXF R12 polygon structural requirements.
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

# 4. Verify test suite
pytest team_algoryxz/nest_craft/tests

# 5. Launch UI
streamlit run team_algoryxz/nest_craft/app/main.py
```

---

## 6. Security and File Hygiene Audit

- **Credentials & API Keys:** 0 found. No personal access tokens, private keys, or passwords exist in the tree.
- **Environment Files:** No `.env` or sensitive configurations are tracked.
- **Cache Files:** All `__pycache__`, `.pytest_cache`, and `*.pyc` artifacts excluded via `.gitignore`.
- **Git Commit Integrity:** Linear history maintained; no force-push used.
