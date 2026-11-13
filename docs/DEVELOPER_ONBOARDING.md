# Developer Onboarding Guide

Welcome to **NEST-CRAFT** (Team Algoryxz · Odisha AI Hackathon 2026). This guide provides step-by-step instructions for teammates to clone the repository, set up an isolated development environment, run the Streamlit application, execute tests, reproduce benchmarks, and safely contribute to the geometry engine.

---

## 1. Quickstart (Clone & Environment Setup)

### Prerequisites
- **Git** (configured with your GitHub credentials)
- **Python 3.12** (tested with Python 3.12.10 on 64-bit Windows/Linux/macOS)

### Step 1: Clone the Repository
```bash
git clone https://github.com/Smarak-padhi/NEST-CRAFT.git
cd NEST-CRAFT
```

### Step 2: Create a Virtual Environment
```bash
# On Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# On Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Core dependencies installed:
- `shapely>=2.0` (computational 2D geometry engine)
- `ezdxf>=1.4` (AutoCAD DXF parser and exporter)
- `streamlit>=1.43` (interactive web UI)
- `numpy>=2.0`, `pandas>=2.2`, `matplotlib>=3.8` (numerical processing and CAD rendering)
- `pytest>=8.3` (automated testing framework)

---

## 2. Running the Interactive Streamlit Application

Launch the local web dashboard from the repository root:
```bash
streamlit run team_algoryxz/nest_craft/app/app.py
```
Once started, the browser opens at `http://localhost:8501`.

### Recommended Demonstration Workflow (3 Minutes):
1. **Load Preloaded Batch:** In the sidebar, select **Preloaded Industrial Batch (17 Parts)**.
2. **Review Constraints:**
   - Sheet Dimensions: $800\text{ mm} \times 500\text{ mm}$
   - Thermal Kerf Clearance: $4.0\text{ mm}$
   - Sheet Margin: $5.0\text{ mm}$
   - Rotation Mode: **Orthogonal (0°, 90°, 180°, 270°)** *(Default)*
   - Part-in-Part Nesting: **Enabled**
3. **Execute Optimization:** Click **Run Optimization** to trigger Simulated Annealing.
4. **Inspect Metrics:**
   - Compare BLF baseline against Simulated Annealing.
   - Inspect **Remnant Plate Intelligence**: note the prime reusable offcut plate ($> 100\text{ mm} \times 100\text{ mm}$) remaining on Sheet 3.
   - Inspect **Part-in-Part Placements**: verify child brackets nested within the central cutout of the flange plate.
5. **Export CAD DXF:** Download the generated layout and open it in Autodesk Viewer, QCAD, or LibreCAD to inspect layer separation.

---

## 3. Running Automated Tests

Run the complete test suite from the repository root:
```bash
# On Windows PowerShell
$env:PYTHONPATH = "."
pytest team_algoryxz/nest_craft/tests

# On Linux/macOS
PYTHONPATH=. pytest team_algoryxz/nest_craft/tests
```

### Expected Output:
```
collected 59 items
team_algoryxz/nest_craft/tests/test_adaptive_rotation.py ........        [ 13%]
team_algoryxz/nest_craft/tests/test_def01_remediation.py ........        [ 27%]
team_algoryxz/nest_craft/tests/test_dxf_reliability.py .........         [ 42%]
team_algoryxz/nest_craft/tests/test_geometry_adversarial_stress.py ..... [ 50%]
.....                                                                    [ 59%]
team_algoryxz/nest_craft/tests/test_geometry_validation.py ........      [ 72%]
team_algoryxz/nest_craft/tests/test_nesting.py .......                   [ 84%]
team_algoryxz/nest_craft/tests/test_part_in_part_nesting.py .........    [100%]
============================= 59 passed in ~3s ==============================
```

All 59 unit, integration, adversarial stress, and DEF-01 remediation tests must pass without errors or warnings.

---

## 4. Reproducing Benchmarks

To reproduce the multi-seed optimization benchmarks comparing Bottom-Left-Fill (BLF) and Simulated Annealing:
```bash
python team_algoryxz/nest_craft/benchmarks/run_nesting_benchmarks.py
```

### Benchmark Reference Baseline (Industrial 17-Part Batch):
- Stock: $800 \times 500\text{ mm}$, Clearance: $4.0\text{ mm}$, Margin: $5.0\text{ mm}$.
- Discrete Sheet Procurement: Exactly **3 sheets** across 100% of orthogonal runs.

| Seed | Linear Extent | Discrete Sheets | Area Util (%) | Final Sheet Remnant |
| :---: | :---: | :---: | :---: | :---: |
| **42** | 1,966.00 mm | 3 | 46.67% | $434 \times 500\text{ mm}$ (Prime) |
| **101** | 2,110.00 mm | 3 | 46.67% | $290 \times 500\text{ mm}$ (Prime) |
| **202** | 1,742.00 mm | 3 | 46.67% | $658 \times 500\text{ mm}$ (Prime) |
| **303** | 1,986.00 mm | 3 | 46.67% | $414 \times 500\text{ mm}$ (Prime) |
| **404** | 1,926.00 mm | 3 | 46.67% | $474 \times 500\text{ mm}$ (Prime) |
| **5-Seed Mean** | **1,946.00 mm** | **3.00** | **46.67%** | **$227,000.00\text{ mm}^2$** |

*Note on Linear Extent:* The $17.19\%$ reduction represents linear guillotine compaction ($2,350\text{ mm} \to 1,946\text{ mm}$), NOT a $17.19\%$ sheet purchase savings (3 plates remain required).

---

## 5. Architecture & Geometry Pipeline

```
  [CAD Ingestion: dxf_io.py]
          │
          ▼  (Validates closed loops, extracts concentric holes)
  [Part Representation: geometry.py]
          │  - Supports Polygon & MultiPolygon
          │  - Rejects unsanctioned topology alterations via CADTopologyError
          │  - Origin normalization & centroid rotation
          ▼
  [Optimization Engine: optimizer.py & baseline.py]
          │  - BLF candidate point generation
          │  - Part-in-Part feasible hole region calculation (buffer(-c))
          │  - Simulated Annealing temperature schedule & swap mutations
          ▼
  [Results & Export: dxf_io.py & app.py]
          │  - Multi-layer DXF export (CUT_CONTOUR, HOLE_CONTOUR, PART_IN_PART_CHILD)
          │  - Remnant offcut plate intelligence (width, height, area, prime status)
          │  - Matplotlib interactive rendering with hole outlines
```

---

## 6. How to Contribute Safely

### Core Engineering Invariants:
1. **Never Silently Discard Geometry:** Every polygon component of a `MultiPolygon` and every interior hole must be preserved throughout placement, transformation, and export.
2. **Explicit Topology Rejection:** When `shapely.validation.make_valid` alters the genus or component count of an incoming invalid polygon, the system must raise `CADTopologyError` unless explicit user authorization (`metadata={"allow_repaired_topology": True}`) is passed.
3. **Discrete Stock Semantics:** Never describe fractional sheet averages (e.g. 3.6 sheets) as actual procurement savings. Sheets are purchased in integer units.
4. **CAM Boundaries:** NEST-CRAFT produces 2D CAD vector contours. It does **not** produce machine-ready G-code, lead-ins, or micro-tabs. Never claim production CNC readiness without secondary CAM post-processing and physical machine trials.

### Before Submitting a PR:
- Run the full test suite: `$env:PYTHONPATH="."; pytest team_algoryxz/nest_craft/tests`.
- Verify all 59 tests pass.
- Ensure no secret credentials, temporary files, or `__pycache__` artifacts are staged.
