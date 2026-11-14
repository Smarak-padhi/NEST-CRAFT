# NEST-CRAFT — AI-Assisted 2D Irregular Sheet-Metal Nesting Engine

**Team Algoryxz · Odisha AI Hackathon 2026**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-121%20passed-brightgreen.svg)](docs/PROJECT_STATUS.md)
[![Prototype Status](https://img.shields.io/badge/status-Hackathon%20Demo%20Ready-orange.svg)](docs/PROJECT_STATUS.md)

NEST-CRAFT is a Python and Streamlit engineering prototype designed to optimize 2D irregular sheet-metal nesting for manufacturing fabrication. It ingests CAD/DXF profiles, models complex polygonal parts and interior apertures using Shapely, executes heuristic Bottom-Left-Fill (BLF) and Simulated Annealing (SA) optimization, enables Part-in-Part cavity nesting, and exports multi-layer AutoCAD R2010 DXF files for downstream CAM toolpath generation.

> [!WARNING]
> **Manufacturing Boundary & Disclaimer:**  
> NEST-CRAFT outputs 2D CAD vector contours (AutoCAD DXF), **NOT CNC G-code** (ISO 6983). It does not generate machine-specific toolpaths, feed rates, pierce dwell cycles, micro-tabs/joints, or kerf diameter offsets. Direct execution of raw exported DXF files on a CNC cutting table without secondary CAM post-processing (e.g. Trumpf TruTops, Bystronic BySoft, CypCut, Hypertherm ProNest, or SheetCam) is strictly prohibited.

---

## 1. Why We Built NEST-CRAFT

In structural and job-shop fabrication, manual nesting of irregular parts on standardized sheet metal stock is time-consuming and often results in fragmented offcuts. Commercial enterprise nesting suites can be cost-prohibitive for smaller workshops. 

NEST-CRAFT was engineered as an open research and engineering prototype to explore how computational geometry and metaheuristic optimization can:
1. **Reduce Linear Cutting Extent:** Packing components tighter along continuous shearing lines to minimize wasted stock advance (achieving a **17.19% reduction in linear nesting extent versus BLF on the specified 17-part, 800 × 500 mm, 4 mm-clearance industrial benchmark**).
2. **Reclaim Offcut Remnant Plates:** Quantifying rectangular virgin offcuts ($> 100\text{ mm} \times 100\text{ mm}$) to enable secondary job scheduling rather than consigning large plate sections to the scrap bin.
3. **Exploit Part-in-Part Cavities:** Automatically placing smaller brackets inside the internal cutouts of larger flange and base plates, eliminating artificial voids.

---

## 2. Technology Stack

- **Core Geometry Engine:** [Shapely 2.1](https://shapely.readthedocs.io/) (GEOS C++ wrapper for robust 2D planar topology, polygon buffering, intersection testing, and containment).
- **CAD I/O Interchange:** [ezdxf 1.4](https://ezdxf.mozman.at/) (AutoCAD R2010 DXF parsing, entity tessellation, topological loop extraction, and structured layer generation).
- **Optimization Algorithms:** Python 3.12 standard library & NumPy (Bottom-Left-Fill heuristic, Simulated Annealing with adaptive cooling, sequence permutations, and grain direction filters).
- **Interactive UI Dashboard:** [Streamlit 1.43](https://streamlit.io/) with Matplotlib (real-time multi-sheet CAD layout preview, remnant intelligence cards, and DXF downloaders).
- **Automated Test Suite:** [pytest 8.3](https://docs.pytest.org/) (121 unit, integration, adversarial stress, and geometry conservation tests).

---

## 3. System Architecture

```
┌────────────────────────────────────────────────────────┐
│                   CAD / DXF Ingestion                  │
│  - Parses LWPOLYLINE, POLYLINE, LINE, ARC, CIRCLE      │
│  - Stitches open segments via polygonize               │
│  - Extracts concentric interior holes (containment)    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                  Part & Geometry Model                 │
│  - Supports Polygon & MultiPolygon (DEF-01 Resolved)   │
│  - Rejects unsanctioned topology alterations           │
│  - Normalizes coordinates & computes centroid rotation │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Optimization Engine                  │
│  - Bottom-Left-Fill (BLF) spatial search               │
│  - Part-in-Part nesting via inward buffering (-c)      │
│  - Simulated Annealing temperature decay & mutations   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Results & Export                     │
│  - Multi-layer DXF export (CUT, HOLE, PART_IN_PART)    │
│  - Remnant plate intelligence (virgin offcut tracking) │
│  - Streamlit high-density industrial dashboard         │
└────────────────────────────────────────────────────────┘
```

---

## 4. Installation & Local Setup

### Prerequisites
- Python 3.12 (64-bit recommended)
- Git

### Step-by-Step Installation:
```bash
# 1. Clone the repository
git clone https://github.com/Smarak-padhi/NEST-CRAFT.git
cd NEST-CRAFT

# 2. Create and activate a virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

---

## 5. Running the Application

Launch the local interactive Streamlit dashboard from the repository root:
```bash
streamlit run team_algoryxz/nest_craft/app/app.py
```
Open `http://localhost:8501` in your browser.

---

## 6. Running Tests & Reproducing Benchmarks

### Execute the 121-Test Automated Suite:
```bash
# Run pytest directly from repository root (configured via pytest.ini)
pytest team_algoryxz/nest_craft/tests
```
*Expected Result:* **121 passed** across 12 test suites (0 failures, 0 errors).

### Reproduce the Multi-Seed Optimization Benchmarks:
```bash
python team_algoryxz/nest_craft/benchmarks/run_nesting_benchmarks.py
```

### Industrial Benchmark Reference (17-Part Batch, 5 Seeds):
- Stock: $800 \times 500\text{ mm}$, Clearance: $4.0\text{ mm}$, Margin: $5.0\text{ mm}$.
- Discrete Sheet Procurement: Exactly **3 sheets** across 100% of orthogonal runs.
- Random Seeds: `[42, 101, 202, 303, 404]`.

| Metric | BLF Baseline | Simulated Annealing (Orthogonal) | Net Impact |
| :--- | :---: | :---: | :---: |
| **Total Linear Extent (Mean)** | 2,350.00 mm | **1,946.00 mm** | **-17.19% linear compaction** |
| **Discrete Sheets Required** | 3 plates | **3 plates** | Preserved (Zero extra stock) |
| **Average Unnested Remnant Zone** | 25,000 mm² | **227,000 mm²** | Contiguous unnested boundary area |
| **Average Runtime** | 3.59s | **7.48s** | Fast interactive feedback |

*Metric Truthfulness Disclosure:* The 17.19% reduction in linear cutting extent along the unfinished final plate is a benchmark-specific compaction metric. It does **NOT** constitute evidence of:
- Fewer purchased sheets (both BLF and SA required exactly 3 plates)
- Increased overall sheet utilization
- Material or financial savings
- Scrap resale value or scrap reduction
- Production performance across arbitrary real-world parts
When 3 discrete plates are consumed, 3 plates remain physically required. Fractional averages across seeds (e.g. 3.60 sheets) are statistical aggregation artifacts, not physical fractional purchases.

---

## 7. Current Development Status & Engineering Reports

| Engineering Stage | Description | Key Deliverables & Reports |
| :--- | :--- | :--- |
| **Stage A** | Initial Codebase Audit & Baseline | [`SKILLS_AUDIT.md`](team_algoryxz/nest_craft/reports/SKILLS_AUDIT.md) |
| **Stage B** | Core Feature Implementation | [`ENG_04_IMPLEMENTATION_REPORT.md`](team_algoryxz/nest_craft/reports/ENG_04_IMPLEMENTATION_REPORT.md), [`ENG_05_IMPLEMENTATION_REPORT.md`](team_algoryxz/nest_craft/reports/ENG_05_IMPLEMENTATION_REPORT.md) |
| **Stage C & C.1** | Reconciliation & Adversarial Testing | [`STAGE_C_BENCHMARK_RECONCILIATION.md`](team_algoryxz/nest_craft/reports/STAGE_C_BENCHMARK_RECONCILIATION.md), [`STAGE_C_GEOMETRY_STRESS_TEST.md`](team_algoryxz/nest_craft/reports/STAGE_C_GEOMETRY_STRESS_TEST.md), [`STAGE_C_CAM_COMPATIBILITY.md`](team_algoryxz/nest_craft/reports/STAGE_C_CAM_COMPATIBILITY.md) |
| **Stage C.2** | Independent Verification Gate | [`STAGE_C2_INDEPENDENT_VERIFICATION.md`](team_algoryxz/nest_craft/reports/STAGE_C2_INDEPENDENT_VERIFICATION.md) |
| **Stage D** | DEF-01 Geometry Integrity Remediation | [`STAGE_D_DEF01_REMEDIATION.md`](team_algoryxz/nest_craft/reports/STAGE_D_DEF01_REMEDIATION.md), [`test_def01_remediation.py`](team_algoryxz/nest_craft/tests/test_def01_remediation.py) |
| **Post-Publication** | Benchmark Audit & Guardrail Verification | [`POST_PUBLICATION_AUDIT.md`](team_algoryxz/nest_craft/reports/POST_PUBLICATION_AUDIT.md), [`POST_PUBLICATION_BENCHMARK_AUDIT.md`](team_algoryxz/nest_craft/reports/POST_PUBLICATION_BENCHMARK_AUDIT.md) |
| **Stage E** | Geometry Integrity, Ingestion Reliability & Demo Excellence | [`STAGE_E_IMPLEMENTATION_REPORT.md`](team_algoryxz/nest_craft/reports/STAGE_E_IMPLEMENTATION_REPORT.md), [`test_stage_e_integrity.py`](team_algoryxz/nest_craft/tests/test_stage_e_integrity.py) |
| **Stage F** | Reliability Hardening & Real-World Validation Preparation | [`STAGE_F_IMPLEMENTATION_REPORT.md`](team_algoryxz/nest_craft/reports/STAGE_F_IMPLEMENTATION_REPORT.md), [`SYNTHETIC_DXF_TEST_MATRIX.md`](team_algoryxz/nest_craft/reports/SYNTHETIC_DXF_TEST_MATRIX.md), [`CAM_INTEROPERABILITY_TEST_PROTOCOL.md`](team_algoryxz/nest_craft/reports/CAM_INTEROPERABILITY_TEST_PROTOCOL.md), [`FABRICATOR_FEEDBACK_TEMPLATE.md`](team_algoryxz/nest_craft/reports/FABRICATOR_FEEDBACK_TEMPLATE.md) |
| **Stage G** | Runtime Type Validation, CI Workflow & Intake Process | [`STAGE_G_IMPLEMENTATION_REPORT.md`](team_algoryxz/nest_craft/reports/STAGE_G_IMPLEMENTATION_REPORT.md), [`REAL_WORLD_DXF_INTAKE_PROCESS.md`](team_algoryxz/nest_craft/reports/REAL_WORLD_DXF_INTAKE_PROCESS.md), [`REAL_WORLD_DXF_TEST_MATRIX.md`](team_algoryxz/nest_craft/reports/REAL_WORLD_DXF_TEST_MATRIX.md) |
| **Stage G.1** | GeometryCollection Integrity Closure & Strict Component Validation | [`compute_boundary_deviation`](team_algoryxz/nest_craft/src/geometry.py), [`test_fail_closed_geometry.py`](team_algoryxz/nest_craft/tests/test_fail_closed_geometry.py) |

For complete documentation, refer to:
- [Developer Onboarding Guide](docs/DEVELOPER_ONBOARDING.md)
- [Team Handoff Document](docs/TEAM_HANDOFF.md)
- [Current Project Status](docs/PROJECT_STATUS.md)
- [Project History & Decision Log](docs/PROJECT_HISTORY.md)
- [Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md)
- [Validation & Benchmarks](docs/VALIDATION_AND_BENCHMARKS.md)
- [Known Limitations](docs/KNOWN_LIMITATIONS.md)
- [Development Roadmap](docs/ROADMAP.md)

---

## 8. Team Attribution

Developed by **Team Algoryxz** for the **Odisha AI Hackathon 2026**.
