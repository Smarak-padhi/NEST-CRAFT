# Stage C — Benchmark Reconciliation & Multimodal Evaluation Report
**Project:** NEST-CRAFT (Team Algoryxz — Odisha AI Hackathon 2026)  
**Date:** 2026-11-13  
**Status:** Complete & Reconciled  
**Verification Scope:** Mathematical reconciliation, input SHA256 integrity, per-seed multi-metric audit.

---

## 1. Executive Summary & Mathematical Reconciliation

### Historical vs. Recent Metric Reconciliation
During Stage A / Baseline benchmarking, the Simulated Annealing (Orthogonal Mode) baseline on the Industrial 17-part batch reported an average linear extent of **1,946.00 mm**. In the Stage B quick evaluation, a figure of **1,939.33 mm** was recorded.

An exhaustive audit of execution parameters and per-seed outputs reveals that both figures are derived from the exact same deterministic algorithm under identical constraints:

- **1,946.00 mm** represents the **5-seed arithmetic mean** across seeds `[42, 101, 202, 303, 404]`:
  $$\frac{1966.00 + 2110.00 + 1742.00 + 1986.00 + 1926.00}{5} = \frac{9730.00}{5} = 1946.00\text{ mm}$$
- **1,939.33 mm** represents the **3-seed arithmetic mean** evaluated across the initial seed subset `[42, 101, 202]`:
  $$\frac{1966.00 + 2110.00 + 1742.00}{3} = \frac{5818.00}{3} = 1939.333...\text{ mm}$$

Per-seed outputs are **100% bitwise identical and reproducible**:
- Seed 42: **1,966.00 mm** (Remnant: 434.00 mm, Runtime: ~2.44s)
- Seed 101: **2,110.00 mm** (Remnant: 290.00 mm, Runtime: ~2.69s)
- Seed 202: **1,742.00 mm** (Remnant: 658.00 mm, Runtime: ~2.39s)
- Seed 303: **1,986.00 mm** (Remnant: 414.00 mm, Runtime: ~2.64s)
- Seed 404: **1,926.00 mm** (Remnant: 474.00 mm, Runtime: ~2.38s)

There was zero algorithmic regression or inconsistency; the deviation was solely due to sample size (3 seeds vs. 5 seeds).

---

## 2. Input Dataset Integrity & Hashing

All benchmark datasets were verified with SHA256 cryptographic hashes prior to evaluation:

| Dataset | File Path | SHA256 Checksum |
| :--- | :--- | :--- |
| **ESICUP Shapes** | `team_algoryxz/nest_craft/data/esicup/shapes.txt` | `fea2dbd7d4dc8c617eb56ed2e194cc7dbddc4273696da1ce33a4feb055b64dc4` |
| **Industrial Batch** | `data/industrial_samples/gusset_plate.dxf` | `0b3b674330c03979fb70f35a25cffd3384d3ad69f761d354783f2b82591fac68` |
| | `data/industrial_samples/l_bracket.dxf` | `6a1355844dd6010e8d94ef40870dea7543096efc91f57e3346517883bdce81f2` |
| | `data/industrial_samples/flange_plate.dxf` | `f24dff48be13b7bbeb8f09972195f956016e7a391d389743d485a224735d4162` |
| | `data/industrial_samples/notched_base_plate.dxf` | `47317b23ae92e159f8db0c62b7c13036acd049be730090a79924dd76f3b29a37` |

---

## 3. Strict Separation of Multi-Objective Metrics

In strict accordance with the **nest-craft-remnant-accounting** standard:
1. **Linear extent compaction** measures continuous strip / guillotine shearing advance.
2. **Sheet count** measures discrete raw stock plate purchases.
3. **Area utilization** measures ratio of part area to sheet area.
4. **Reusable remnant area** measures physical offcut plates available for secondary production.

> **Economic Policy:** Linear extent compaction on an unfinished final plate is NEVER reported as discrete sheet procurement savings. When 3 discrete stock plates are consumed, purchasing 3 plates remains mandatory unless total linear extent drops below $2 \times \text{Sheet Length}$.

---

## 4. Benchmark Results: Industrial Batch (17 Parts)

- **Stock Dimensions:** $800.0\text{ mm} \times 500.0\text{ mm}$
- **Thermal Kerf Clearance:** $4.0\text{ mm}$
- **Total Part Area:** $560,000.0\text{ mm}^2$
- **Total Discrete Sheet Area:** $1,200,000.0\text{ mm}^2$ (for 3 sheets)

### A. Bottom-Left-Fill (BLF Baseline)
- **Sheets Used:** 3
- **Discrete Sheet Utilization:** 46.67%
- **Total Linear Extent:** 2,350.00 mm
- **Final Sheet Remnant Area:** 25,000.00 mm² ($50\text{ mm} \times 500\text{ mm}$, non-prime remnant)
- **Runtime:** 0.44 seconds

### B. Simulated Annealing — Mode A: Orthogonal Rotation ($0^\circ, 90^\circ, 180^\circ, 270^\circ$)
Tested across 5 seeds (25 iterations each):

| Random Seed | Sheets Used | Area Util (%) | Linear Extent (mm) | Final Remnant (mm²) | Prime Remnant? | Runtime (s) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **42** | 3 | 46.67% | 1,966.00 | 217,000.00 ($434 \times 500$) | **Yes** (Prime) | 2.44 |
| **101** | 3 | 46.67% | 2,110.00 | 145,000.00 ($290 \times 500$) | **Yes** (Prime) | 2.69 |
| **202** | 3 | 46.67% | 1,742.00 | 329,000.00 ($658 \times 500$) | **Yes** (Prime) | 2.39 |
| **303** | 3 | 46.67% | 1,986.00 | 207,000.00 ($414 \times 500$) | **Yes** (Prime) | 2.64 |
| **404** | 3 | 46.67% | 1,926.00 | 237,000.00 ($474 \times 500$) | **Yes** (Prime) | 2.38 |
| **5-Seed Mean** | **3.00** | **46.67%** | **1,946.00** | **227,000.00** | **Prime** | **2.51** |
| **3-Seed Mean** | **3.00** | **46.67%** | **1,939.33** | **230,333.33** | **Prime** | **2.51** |

*Key finding:* SA Orthogonal reduces linear extent from 2,350.00 mm to 1,946.00 mm (**-17.19% compaction**). Furthermore, on Seed 202, Sheet 3 has only 142.00 mm occupied, generating a massive **$658.0\text{ mm} \times 500.0\text{ mm}$ prime reusable remnant plate** ($329,000.0\text{ mm}^2$).

### C. Simulated Annealing — Mode B: Adaptive Rotation ($15^\circ$ coarse + $5^\circ$ local)
Tested across 5 seeds (25 iterations each):

| Random Seed | Sheets Used | Area Util (%) | Linear Extent (mm) | Final Remnant (mm²) | Prime Remnant? | Runtime (s) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **42** | 4 | 35.00% | 2,627.88 | 286,057.71 | Prime | 2.79 |
| **101** | 3 | 46.67% | 2,376.95 | 11,522.77 | No | 2.86 |
| **202** | 4 | 35.00% | 2,599.99 | 300,005.05 | Prime | 2.58 |
| **303** | 3 | 46.67% | 2,314.02 | 42,990.64 | No | 2.71 |
| **404** | 4 | 35.00% | 2,627.88 | 286,057.71 | Prime | 2.65 |
| **5-Seed Mean** | **3.60** | **39.67%** | **2,509.34** | **185,326.78** | — | **2.72** |

### D. Critical Analysis of Orthogonal vs. Adaptive on Rectilinear Stock
The data demonstrates an important geometric reality:
- For predominantly rectangular and L-shaped structural plates (gusset plates, base plates, L-brackets), **Mode A (Orthogonal Rotation) is strictly superior**.
- When an axis-aligned rectangular part is rotated at an arbitrary non-orthogonal angle (e.g. $45^\circ$ or $75^\circ$), its bounding envelope expands by up to $\sqrt{2} \approx 1.414\times$.
- In Bottom-Left placement on an orthogonal sheet, this bounding expansion creates artificial voids, increasing sheet consumption from 3 sheets to 4 sheets in 60% of seeds.
- Conversely, for non-orthogonal freeform/triangular geometries (such as in the ESICUP benchmark), adaptive rotation provides tight interlocking packing.

---

## 5. Benchmark Results: ESICUP Shapes Benchmark (43 Parts)

- **Stock Dimensions:** $40.0 \times 70.0$ units
- **Clearance:** $0.5$ units
- **Total Part Area:** $1,596.0$ units²
- **Total Discrete Sheet Area:** $5,600.0$ units² (2 sheets of 2,800.0 units²)

| Algorithm / Configuration | Sheets | Area Util (%) | Linear Extent | Remnant Area | Runtime (s) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **BLF Baseline** | 2 | 28.50% | 77.75 | 157.50 | 12.28 |
| **SA Orthogonal (Seed 42)** | 2 | 28.50% | 75.75 | 297.50 | 27.59 |
| **SA Orthogonal (Seed 101)** | 2 | 28.50% | 74.75 | 367.50 | 30.93 |
| **SA Orthogonal (Seed 202)** | 2 | 28.50% | 76.25 | 262.50 | 23.56 |
| **SA Orthogonal (Seed 303)** | 2 | 28.50% | 75.25 | 332.50 | 26.33 |
| **SA Orthogonal (Seed 404)** | 2 | 28.50% | 73.75 | 437.50 | 24.01 |
| **SA Orthogonal (5-Seed Mean)** | **2** | **28.50%** | **75.15** | **339.50** | **26.48** |
| **SA Adaptive (Seed 42)** | 2 | 28.50% | 75.07 | 345.31 | 24.86 |
| **SA Adaptive (Seed 101)** | 2 | 28.50% | 76.40 | 251.90 | 25.71 |
| **SA Adaptive (Seed 202)** | 2 | 28.50% | 75.64 | 305.04 | 25.88 |
| **SA Adaptive (Seed 303)** | 2 | 28.50% | 75.86 | 290.04 | 27.71 |
| **SA Adaptive (Seed 404)** | 2 | 28.50% | 77.68 | 162.71 | 25.43 |
| **SA Adaptive (5-Seed Mean)** | **2** | **28.50%** | **76.13** | **271.00** | **25.92** |

---

## 6. Synthesis & Reconciliation Verdict

1. **Exact Mathematical Identity:** The historical 1,946.00 mm vs. 1,939.33 mm discrepancy is 100% reconciled as a sample size difference (5 seeds vs. 3 seeds) over deterministic, bitwise-reproducible runs.
2. **Deterministic Guarantee:** Given fixed seeds and identical parameters, the NEST-CRAFT optimization engine generates identical placements across runs.
3. **Reporting Compliance:** Discrete sheet counts, linear compaction, and physical remnant dimensions are cleanly partitioned without synthetic or misleading percentages.
