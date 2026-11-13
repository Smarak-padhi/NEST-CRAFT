# NEST-CRAFT

**Team Algoryxz · Odisha AI Hackathon 2026**

NEST-CRAFT is a Python/Streamlit prototype for 2D irregular sheet-metal nesting. It imports CAD/DXF contours, models parts and holes with Shapely, compares Bottom-Left-Fill (BLF) with Simulated Annealing (SA), supports part-in-part placement, and exports a layered DXF layout for downstream CAD/CAM review.

> **Manufacturing boundary:** DXF is CAD geometry, not G-code. No commercial CAM import or physical CNC cutting validation is evidenced in the supplied reports.

## Current status

The project archive records work through Stage D, which reports remediation of DEF-01 (silent loss of MultiPolygon components) and 59 passing tests. These are report claims from the supplied archive; reproduce them locally before treating them as independently verified.

- Orthogonal rotation is the current benchmark choice. Adaptive rotation underperformed on the reported five-seed means.
- The project is suitable for a controlled hackathon demo, with limitations.
- Industrial pilot and production CNC deployment are not approved by the current evidence.
- Customer savings, willingness to pay, and adoption are not validated.

## Read first

1. [Team handoff](docs/TEAM_HANDOFF.md)
2. [Project history](docs/PROJECT_HISTORY.md)
3. [Technical architecture](docs/TECHNICAL_ARCHITECTURE.md)
4. [Validation and benchmarks](docs/VALIDATION_AND_BENCHMARKS.md)
5. [Known limitations](docs/KNOWN_LIMITATIONS.md)
6. [Roadmap](docs/ROADMAP.md)

Detailed engineering reports are retained in `team_algoryxz/nest_craft/reports/`.

## Run locally

The source code is under `team_algoryxz/nest_craft/`. Create a Python 3.12 virtual environment, install dependencies, then from the repository root:

```bash
pip install -r requirements.txt
python -m pytest team_algoryxz/nest_craft/tests -q
streamlit run team_algoryxz/nest_craft/app/app.py
```

Run the benchmark script with:

```bash
python team_algoryxz/nest_craft/benchmarks/run_nesting_benchmarks.py
```

## Metric discipline

The reported 17.19% result is a reduction in linear extent versus BLF on a specified 17-part benchmark. It is not a 17.19% reduction in sheet purchases, total material cost, or customer spend. Discrete sheet count, utilization, linear extent, remnant area, and runtime are separate metrics.

Sample DXFs are not proof of customer-originated drawings. Remnant area is not automatically realized economic savings. See the validation and limitation documents before making claims.
