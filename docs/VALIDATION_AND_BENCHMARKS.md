# Validation and Benchmarks

The detailed reports under `team_algoryxz/nest_craft/reports/` are authoritative for raw tables and methodology. The summary below preserves the reported distinctions between metrics.

## Industrial 17-part batch

Reported setup: 17 parts; stock 800 × 500 mm; clearance 4 mm; total part area 560,000 mm².

| Method / seed | Sheets | Linear extent |
|---|---:|---:|
| BLF | 3 | 2,350 mm |
| SA orthogonal, seed 42 | 3 | 1,966 mm |
| SA orthogonal, seed 101 | 3 | 2,110 mm |
| SA orthogonal, seed 202 | 3 | 1,742 mm |
| SA orthogonal, seed 303 | 3 | 1,986 mm |
| SA orthogonal, seed 404 | 3 | 1,926 mm |
| SA orthogonal mean | 3 | 1,946 mm |

The reported 1,946 mm mean is 17.19% lower linear extent than BLF's 2,350 mm. It is not fewer sheets: both methods used three discrete sheets in this benchmark.

## Adaptive rotation

The Stage C reconciliation reports adaptive rotation mean extent of 2,509.34 mm on the industrial dataset versus 1,946 mm orthogonal; adaptive used 4 sheets on 3 of 5 seeds. On ESICUP, adaptive mean extent was 76.13 mm versus orthogonal 75.15 mm. Adaptive underperformed on both reported five-seed means.

## ESICUP

The report records a 43-part ESICUP instance with 40 × 70 stock, 0.5 mm clearance, two sheets, and 28.5% utilization. See the detailed report for exact run outputs.

## Stage D conservation fixture

Stage D report claims 11,700 mm² input net area, 4 components, 1 hole; exported net area 11,700 mm²; area delta 0.0000 mm²; DXF audit zero errors. One fixture is not universal proof for all CAD geometries.

## Reproduction

From repository root:

```bash
python -m pytest team_algoryxz/nest_craft/tests -q
python team_algoryxz/nest_craft/benchmarks/run_nesting_benchmarks.py
```

Capture console output, Python/package versions, seeds, and generated results. Do not compare runs with different datasets, stock dimensions, clearance, iterations, or seeds as equivalent experiments.

## Evidence labels

- **Reported:** stated in an included project report.
- **Reproduced:** rerun with command and raw output recorded.
- **Externally validated:** checked against customer workflow, commercial CAM, or physical machine.

The included Stage D report supplies reported results; a fresh checkout should reproduce them before stronger claims are made.
