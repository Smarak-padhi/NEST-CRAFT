# NEST-CRAFT Baseline Verification Report — Stage B
**Date:** November 13, 2026  
**Environment:** Windows 11, Python 3.12.10, Pytest 8.3.3, Shapely 2.0.7, ezdxf 1.4.5  
**Working Directory:** `c:\Users\smara\Desktop\Odisha AI hackathon\team_algoryxz\nest_craft`  
**Git Status:** Not a Git repository (untracked workspace preserved untouched).  

---

## 1. Unit Test Suite Execution
Command: `python -m pytest team_algoryxz/nest_craft/tests/ -v`

### Test Summary
- **Total Tests Collected:** 24
- **Passed:** 24
- **Failed:** 0
- **Duration:** 6.95s
- **Pass Rate:** 100.0%

### Detailed Breakdown
| Test Category | File | Test Count | Result |
|:---|:---|:---:|:---:|
| DXF Entity & Topology Reliability | `tests/test_dxf_reliability.py` | 9 | **9 / 9 PASSED** |
| Geometric Validation & Clearance | `tests/test_geometry_validation.py` | 8 | **8 / 8 PASSED** |
| Baseline BLF & SA Optimizer | `tests/test_nesting.py` | 7 | **7 / 7 PASSED** |

---

## 2. Multi-Seed Benchmark Baseline

### A. ESICUP SHAPES Instance (43 parts)
- Sheet size: $40.0 \times 70.0\text{ mm}$
- BLF Baseline: 2 sheets, $76.25\text{ mm}$ linear extent, $28.50\%$ discrete utilization, $7.88\text{s}$ runtime.
- Simulated Annealing across fixed seeds:
  - Seed 42: $75.75\text{ mm}$ ($+0.5\text{ mm}$ saved), $33.27\text{s}$
  - Seed 101: $76.25\text{ mm}$ ($+0.0\text{ mm}$ saved), $35.28\text{s}$
  - Seed 202: $73.75\text{ mm}$ ($+2.5\text{ mm}$ saved), $22.36\text{s}$
  - Seed 303: $73.75\text{ mm}$ ($+2.5\text{ mm}$ saved), $21.36\text{s}$
  - Seed 404: $74.25\text{ mm}$ ($+2.0\text{ mm}$ saved), $20.84\text{s}$
- **SA Mean Linear Extent:** $74.75\text{ mm}$ ($-1.50\text{ mm}$ saved, $-1.97\%$ compaction).
- **SA Mean Runtime:** $26.62\text{s}$.

### B. Industrial DXF Fabrication Batch (17 parts)
- Raw Sheet size: $800.0 \times 500.0\text{ mm}$
- BLF Baseline: 3 discrete sheets, $2,350.0\text{ mm}$ linear extent, $46.67\%$ discrete utilization, $0.398\text{s}$ runtime.
- Simulated Annealing across fixed seeds:
  - Seed 42: $1,966.0\text{ mm}$ ($+384.0\text{ mm}$ saved), $2.37\text{s}$
  - Seed 101: $2,110.0\text{ mm}$ ($+240.0\text{ mm}$ saved), $2.20\text{s}$
  - Seed 202: $1,742.0\text{ mm}$ ($+608.0\text{ mm}$ saved), $2.10\text{s}$
  - Seed 303: $1,986.0\text{ mm}$ ($+364.0\text{ mm}$ saved), $2.39\text{s}$
  - Seed 404: $1,926.0\text{ mm}$ ($+424.0\text{ mm}$ saved), $2.08\text{s}$
- **SA Mean Linear Extent:** $1,946.0\text{ mm}$ ($-404.0\text{ mm}$ saved, $-17.19\%$ linear compaction).
- **SA Mean Runtime:** $2.23\text{s}$.
- **Discrete Sheet Consumption:** 3 sheets for both BLF and SA ($46.67\%$ discrete plate utilization).
- **Remnant Geometry Salvage:**
  - BLF preserves only a $50.0 \times 500.0\text{ mm}$ strip (scrap offcut).
  - SA preserves a contiguous **$434.0 \times 500.0\text{ mm}$ virgin prime plate ($54.2\%$ of Sheet 3 preserved)**.

---

## 3. Baseline Verdict
The baseline is verified fully operational and reproducible. We are ready to proceed with **ENG-04 (Part-in-Part Nesting)**.
