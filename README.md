# NEST-CRAFT — AI-Assisted 2D Irregular Sheet-Metal Nesting Engine

**Team Algoryxz · Odisha AI Hackathon 2026**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-59%20passed-brightgreen.svg)](docs/PROJECT_STATUS.md)
[![Prototype Status](https://img.shields.io/badge/status-Hackathon%20Demo%20Ready-orange.svg)](docs/PROJECT_STATUS.md)

NEST-CRAFT is a Python and Streamlit engineering prototype designed to optimize 2D irregular sheet-metal nesting for manufacturing fabrication. It ingests CAD/DXF profiles, models complex polygonal parts and interior apertures using Shapely, executes heuristic Bottom-Left-Fill (BLF) and Simulated Annealing (SA) optimization, enables Part-in-Part cavity nesting, and exports multi-layer AutoCAD R2010 DXF files for downstream CAM toolpath generation.

> [!WARNING]
> **Manufacturing Boundary & Disclaimer:**  
> NEST-CRAFT outputs 2D CAD vector contours (AutoCAD DXF), **NOT CNC G-code** (ISO 6983). It does not generate machine-specific toolpaths, feed rates, pierce dwell cycles, micro-tabs/joints, or kerf diameter offsets. Direct execution of raw exported DXF files on a CNC cutting table without secondary CAM post-processing (e.g. Trumpf TruTops, Bystronic BySoft, CypCut, Hypertherm ProNest, or SheetCam) is strictly prohibited.

---

## 1. Why We Built NEST-CRAFT

In regional fabrication clusters across Odisha and India, micro, small, and medium enterprises (MSMEs) face material utilization rates as low as 40–55% when cutting structural components from standardized sheet metal stock. Commercial enterprise nesting suites often cost thousands of dollars per seat, pricing out smaller job shops. 

NEST-CRAFT was engineered to demonstrate that modern computational geometry and metaheuristic optimization can:
1. **Reduce Linear Cutting Extent:** Packing components tighter along continuous shearing lines to minimize wasted stock advance (achieving up to **-17.19% linear extent compaction** on standard industrial batches).
2. **Reclaim Offcut Remnant Plates:** Quantifying rectangular virgin offcuts ($> 100\text{ mm} \times 100\text{ mm}$) to enable secondary job scheduling rather than consigning large plate sections to the scrap bin.
3. **Exploit Part-in-Part Cavities:** Automatically placing smaller brackets inside the internal cutouts of larger flange and base plates, eliminating artificial voids.

---

## 2. Technology Stack

- **Core Geometry Engine:** [Shapely 2.1](https://shapely.readthedocs.io/) (GEOS C++ wrapper for robust 2D planar topology, polygon buffering, intersection testing, and containment).
- **CAD I/O Interchange:** [ezdxf 1.4](https://ezdxf.mozman.at/) (AutoCAD R2010 DXF parsing, entity tessellation, topological loop extraction, and structured layer generation).
- **Optimization Algorithms:** Python 3.12 standard library & NumPy (Bottom-Left-Fill heuristic, Simulated Annealing with adaptive cooling, sequence permutations, and grain direction filters).
- **Interactive UI Dashboard:** [Streamlit 1.43](https://streamlit.io/) with Matplotlib (real-time multi-sheet CAD layout preview, remnant intelligence cards, and DXF downloaders).
- **Automated Test Suite:** [pytest 8.3](https://docs.pytest.org/) (59 unit, integration, adversarial stress, and geometry conservation tests).

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

### Execute the 59-Test Automated Suite:
```bash
# Set PYTHONPATH to repository root
$env:PYTHONPATH = "."
pytest team_algoryxz/nest_craft/tests
```
*Expected Result:* **59 passed in ~3 seconds** (0 failures, 0 errors).

### Reproduce the Multi-Seed Optimization Benchmarks:
```bash
python team_algoryxz/nest_craft/benchmarks/run_nesting_benchmarks.py
```

### Industrial Benchmark Reference (17-Part Batch, 5 Seeds):
- Stock: $800 \times 500\text{ mm}$, Clearance: $4.0\text{ mm}$, Margin: $5.0\text{ mm}$.
- Discrete Sheet Procurement: Exactly **3 sheets** across 100% of orthogonal runs.

| Metric | BLF Baseline | Simulated Annealing (Orthogonal) | Net Impact |
| :--- | :---: | :---: | :---: |
| **Total Linear Extent (Mean)** | 2,350.00 mm | **1,946.00 mm** | **-17.19% compaction** |
| **Discrete Sheets Required** | 3 plates | **3 plates** | Preserved (Zero extra stock) |
| **Average Prime Remnant Offcut** | 25,000 mm² | **227,000 mm²** | **+808% usable remnant** |
| **Average Runtime** | 0.44s | **2.51s** | Fast interactive feedback |

*Metric Truthfulness Disclosure:* Compaction of linear extent along an unfinished final plate does **NOT** equal discrete sheet purchase savings. When 3 discrete plates are consumed, 3 plates remain physically required. Fractional averages across seeds (e.g. 3.60 sheets) are statistical aggregation artifacts, not physical fractional purchases.

---

## 7. Current Development Status & Engineering Reports

| Engineering Stage | Description | Key Deliverables & Reports |
| :--- | :--- | :--- |
| **Stage A** | Initial Codebase Audit & Baseline | [`SKILLS_AUDIT.md`](team_algoryxz/nest_craft/reports/SKILLS_AUDIT.md) |
| **Stage B** | Core Feature Implementation | [`ENG_04_IMPLEMENTATION_REPORT.md`](team_algoryxz/nest_craft/reports/ENG_04_IMPLEMENTATION_REPORT.md), [`ENG_05_IMPLEMENTATION_REPORT.md`](team_algoryxz/nest_craft/reports/ENG_05_IMPLEMENTATION_REPORT.md) |
| **Stage C & C.1** | Reconciliation & Adversarial Testing | [`STAGE_C_BENCHMARK_RECONCILIATION.md`](team_algoryxz/nest_craft/reports/STAGE_C_BENCHMARK_RECONCILIATION.md), [`STAGE_C_GEOMETRY_STRESS_TEST.md`](team_algoryxz/nest_craft/reports/STAGE_C_GEOMETRY_STRESS_TEST.md), [`STAGE_C_CAM_COMPATIBILITY.md`](team_algoryxz/nest_craft/reports/STAGE_C_CAM_COMPATIBILITY.md) |
| **Stage C.2** | Independent Verification Gate | [`STAGE_C2_INDEPENDENT_VERIFICATION.md`](team_algoryxz/nest_craft/reports/STAGE_C2_INDEPENDENT_VERIFICATION.md) |
| **Stage D** | DEF-01 Geometry Integrity Remediation | [`STAGE_D_DEF01_REMEDIATION.md`](team_algoryxz/nest_craft/reports/STAGE_D_DEF01_REMEDIATION.md), [`test_def01_remediation.py`](team_algoryxz/nest_craft/tests/test_def01_remediation.py) |

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
