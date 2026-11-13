# POST-PUBLICATION BENCHMARK AUDIT

**Project:** NEST-CRAFT (Team Algoryxz — Odisha AI Hackathon 2026)  
**Audit Date:** November 13, 2026  
**Auditor:** Team Algoryxz Independent Audit  
**Execution Environment:** Windows 11 · Python 3.12.10 · pytest 8.3.3  
**Status:** **REPRODUCED WITH BITWISE NUMERICAL IDENTITY**

---

## 1. Executive Summary

This audit investigates the benchmark evidence in the initial handoff documentation and reconciles it against the genuine historical Stage C baseline.

The previous handoff report contained documentation discrepancies, erroneously citing:
- "24 mixed parts" instead of the genuine **17-part industrial batch**
- "2,400 × 1,200 mm stock" instead of the genuine **800 × 500 mm sheet stock**
- "5.0 mm clearance" instead of the genuine **4.0 mm thermal kerf clearance**
- "Python 3.11.9" when the actual environment is **Python 3.12.10**

When evaluated under the exact historical parameters, the 5-seed benchmark was executed and achieved **100% bitwise reproduction** of the historical Stage C mean ($1,946.00\text{ mm}$) and per-seed results.

---

## 2. Benchmark Configuration & Input Provenance

### A. Dataset Identity
- **Dataset:** Industrial CAD Fabrication Batch
- **Source Files:**
  - `data/industrial_samples/gusset_plate.dxf` (SHA256: `0b3b674330c03979fb70f35a25cffd3384d3ad69f761d354783f2b82591fac68`) — Quantity: 4
  - `data/industrial_samples/l_bracket.dxf` (SHA256: `6a1355844dd6010e8d94ef40870dea7543096efc91f57e3346517883bdce81f2`) — Quantity: 6
  - `data/industrial_samples/flange_plate.dxf` (SHA256: `f24dff48be13b7bbeb8f09972195f956016e7a391d389743d485a224735d4162`) — Quantity: 4
  - `data/industrial_samples/notched_base_plate.dxf` (SHA256: `47317b23ae92e159f8db0c62b7c13036acd049be730090a79924dd76f3b29a37`) — Quantity: 3
- **Total Parts:** $4 + 6 + 4 + 3 = 17\text{ parts}$ (Total Net Part Area = $560,000.00\text{ mm}^2$).

### B. Stock and Algorithm Parameters
- **Stock Plate Dimensions:** $800.0\text{ mm} \times 500.0\text{ mm}$ (Gross Area per Sheet = $400,000.00\text{ mm}^2$).
- **Thermal Kerf Clearance:** $4.0\text{ mm}$.
- **Optimizer Hyperparameters:**
  - Max Iterations: 20
  - Initial Temperature: 100.0
  - Cooling Rate: 0.85
  - Grid Placement Step Size: 8.0 mm
  - Random Seeds Tested: `[42, 101, 202, 303, 404]`

---

## 3. Measured Experimental Results

### A. Bottom-Left-Fill (BLF Baseline)
- **Discrete Sheets Consumed:** 3 plates
- **Discrete Area Utilization:** 46.67%
- **Total Linear Extent:** 2,350.00 mm
- **Final Sheet Remnant Area:** 25,000.00 mm² ($50\text{ mm} \times 500\text{ mm}$, non-prime)
- **Runtime:** 3.59 seconds

### B. Simulated Annealing (Orthogonal Rotation Mode)
Allowed angles: `[0.0, 90.0, 180.0, 270.0]`.

| Seed | Discrete Sheets | Linear Extent (mm) | Linear Saved vs BLF | Area Util (%) | Remnant Area (mm²) | Prime Remnant? | Runtime (s) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **42** | 3 | 1,966.00 | +384.00 mm | 46.67% | 217,000.00 ($434 \times 500$) | **Yes** | 6.40s |
| **101** | 3 | 2,110.00 | +240.00 mm | 46.67% | 145,000.00 ($290 \times 500$) | **Yes** | 8.09s |
| **202** | 3 | 1,742.00 | +608.00 mm | 46.67% | 329,000.00 ($658 \times 500$) | **Yes** | 7.19s |
| **303** | 3 | 1,986.00 | +364.00 mm | 46.67% | 207,000.00 ($414 \times 500$) | **Yes** | 8.48s |
| **404** | 3 | 1,926.00 | +424.00 mm | 46.67% | 237,000.00 ($474 \times 500$) | **Yes** | 7.22s |
| **5-Seed Mean** | **3.00** | **1,946.00** | **+404.00 mm** | **46.67%** | **227,000.00** | **Prime** | **7.48s** |

### C. Simulated Annealing (Adaptive Rotation Mode)
Exploration angles: 24 coarse angles ($15^\circ$ grid) + local $5^\circ$ refinement.

| Seed | Discrete Sheets | Linear Extent (mm) | Linear Penalty vs SA Ortho | Area Util (%) | Final Remnant (mm²) | Runtime (s) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **42** | 4 | 2,627.88 | +661.88 mm | 35.00% | 286,057.71 | 9.45s |
| **101** | 3 | 2,376.95 | +266.95 mm | 46.67% | 11,522.77 | 9.28s |
| **202** | 4 | 2,599.99 | +857.99 mm | 35.00% | 300,005.05 | 8.15s |
| **303** | 3 | 2,314.02 | +328.02 mm | 46.67% | 42,990.64 | 7.29s |
| **404** | 4 | 2,627.88 | +701.88 mm | 35.00% | 286,057.71 | 6.64s |
| **5-Seed Mean** | **3.60 avg** | **2,509.34** | **+563.34 mm (+28.95%)** | **39.67%** | **185,326.78** | **8.16s** |

---

## 4. Historical Comparison & Verification Status

| Metric | Stage C Baseline | Current Audit Reproduction | Status |
| :--- | :---: | :---: | :---: |
| **BLF Linear Extent** | 2,350.00 mm | 2,350.00 mm | **Exact Match (100%)** |
| **SA Ortho Seed 42** | 1,966.00 mm | 1,966.00 mm | **Exact Match (100%)** |
| **SA Ortho Seed 101** | 2,110.00 mm | 2,110.00 mm | **Exact Match (100%)** |
| **SA Ortho Seed 202** | 1,742.00 mm | 1,742.00 mm | **Exact Match (100%)** |
| **SA Ortho Seed 303** | 1,986.00 mm | 1,986.00 mm | **Exact Match (100%)** |
| **SA Ortho Seed 404** | 1,926.00 mm | 1,926.00 mm | **Exact Match (100%)** |
| **SA Ortho 5-Seed Mean** | **1,946.00 mm** | **1,946.00 mm** | **Exact Match (100%)** |
| **SA Adapt 5-Seed Mean** | **2,509.34 mm** | **2,509.34 mm** | **Exact Match (100%)** |
| **Linear Compaction** | **-17.19%** | **-17.19%** | **Exact Match (100%)** |

---

## 5. Engineering Declarations on Metrics

1. **Exact Meaning of 17.19%:**  
   The 17.19% figure establishes **ONLY** a $17.19\%$ reduction in linear nesting extent versus BLF on the specified 17-part, $800 \times 500\text{ mm}$, $4\text{ mm}$-clearance industrial benchmark ($2,350\text{ mm} \rightarrow 1,946\text{ mm}$).
2. **Discrete Procurement Semantics:**  
   Both BLF and Orthogonal Simulated Annealing require **exactly 3 stock sheets** ($1,200,000\text{ mm}^2$ gross material). Linear compaction frees contiguous prime remnant plate area ($227,000\text{ mm}^2$ vs $25,000\text{ mm}^2$), but does **NOT** reduce the number of discrete sheets purchased from the mill.
3. **Adaptive Rotation Underperformance:**  
   Adaptive rotation ($15^\circ$ coarse + $5^\circ$ fine) produced bounding-box overhang on rectangular sheet stock, increasing mean linear span to $2,509.34\text{ mm}$ (+28.95% penalty) and forcing the procurement of a 4th plate in 60% of runs (3 out of 5 seeds). Adaptive rotation is **not** a general improvement on rectilinear stock.
4. **Machine-Readable Raw Data:**  
   Complete per-run JSON data is preserved at:  
   `team_algoryxz/nest_craft/reports/post_publication_benchmark_results.json`
