# Stage D — DEF-01 Geometry Integrity Remediation Report
**Project:** NEST-CRAFT (Team Algoryxz — Odisha AI Hackathon 2026)  
**Date:** 2026-11-13  
**Status:** Defect Fully Remediated & Verified (59/59 Automated Tests Passing)  
**Target Defect:** DEF-01 (Silent Component Reduction in `Part.__init__` on `MultiPolygon` and Invalid CAD Geometry)

---

## 1. Executive Summary

In Stage C.2, independent verification revealed defect **DEF-01**: when an input geometry was a `MultiPolygon`—either from legitimate multi-part CAD entities or from self-intersecting contours repaired via `make_valid`—the `Part.__init__` constructor executed:
```python
if isinstance(polygon, MultiPolygon):
    polygon = max(polygon.geoms, key=lambda g: g.area)
```
This silently selected only the single largest polygon component and discarded all remaining components without raising an error or warning, resulting in up to 50% silent material loss (e.g. on self-intersecting bow-ties).

In Stage D, a narrowly scoped, robust engineering remediation was implemented:
1. **Full `MultiPolygon` Support:** Legitimate multi-part components are now fully supported across the entire nesting pipeline—including area calculation, unit normalization, rotation, collision detection, sheet containment, UI visualization, and multi-layer DXF export. Zero components are discarded.
2. **Explicit Topology Alteration Guardrails:** Self-intersecting contours repaired via `make_valid` that undergo material topological alterations (such as splitting a single contour into multiple components or altering net area by $>5\%$) are explicitly detected and **REJECTED** with a descriptive `CADTopologyError(ValueError)` unless explicit user authorization (`metadata={"allow_repaired_topology": True}`) is provided.
3. **Zero Loss on Authorized Ingestion:** When repaired topology is explicitly authorized, all components are preserved in full ($100\%$ area retained, $0.00\text{ mm}^2$ lost).
4. **Zero Benchmark Regression:** The 5-seed orthogonal industrial benchmark was re-run and confirmed **100% identical to the historical 1,946.00 mm baseline** (3 discrete sheets in 5/5 runs).
5. **Full Test Suite Passing:** All 59 automated tests (including 8 new regression tests in `test_def01_remediation.py`) pass in 3.40 seconds.

---

## 2. Modified Production Files

Four production modules were updated with strictly scoped modifications:

| File Path | Function / Class Modified | Exact Nature of Modification |
| :--- | :--- | :--- |
| `team_algoryxz/nest_craft/src/geometry.py` | `CADTopologyError` (New) | Defined `class CADTopologyError(ValueError)` to provide structured, actionable exceptions for CAD topology defects. |
| `team_algoryxz/nest_craft/src/geometry.py` | `Part.__init__` | Replaced silent `max(...)` reduction. Valid `MultiPolygon`s are preserved in full. Unsanctioned topological alterations on invalid contours raise `CADTopologyError`. When authorized, all components are preserved. |
| `team_algoryxz/nest_craft/src/geometry.py` | `compute_hole_feasible_regions` | Updated to accept `Union[Polygon, MultiPolygon]`, extracting interior holes across all sub-components. |
| `team_algoryxz/nest_craft/src/baseline.py` | `place_part_in_holes` | Updated parent part interior inspection to handle `MultiPolygon` placed parts. |
| `team_algoryxz/nest_craft/src/dxf_io.py` | `export_nesting_to_dxf` | Updated export loop to iterate over all sub-polygons in `MultiPolygon`, exporting every exterior cutting contour and interior hole. |
| `team_algoryxz/nest_craft/src/dxf_io.py` | `validate_and_parse_dxf` | Removed all instances of `max(..., key=lambda g: g.area)`; preserved all valid sub-polygons during DXF parsing and hole extraction. |
| `team_algoryxz/nest_craft/app/app.py` | `plot_nesting_result` | Updated matplotlib rendering to loop over `sub_polys`, plotting every exterior boundary and interior hole for multipart geometries. |

---

## 3. Before vs. After Geometry Comparison

| Geometry Scenario | Input Geometry | Before Remediation (DEF-01) | After Remediation (Stage D) | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Valid MultiPolygon (Equal Components)** | Two $30 \times 30\text{ mm}$ boxes ($1,800.0\text{ mm}^2$ total) | Silently reduced to one box ($900.0\text{ mm}^2$). **50% material discarded.** | Both boxes preserved in full. Area = $1,800.0\text{ mm}^2$. Both rotate & export together. | **FIXED** |
| **Valid MultiPolygon (Unequal Components)** | $50 \times 50\text{ mm}$ box + $10 \times 10\text{ mm}$ tab ($2,600.0\text{ mm}^2$ total) | Silently discarded small $100.0\text{ mm}^2$ tab. | Both large box and small tab preserved. Area = $2,600.0\text{ mm}^2$. | **FIXED** |
| **Self-Intersecting Bow-Tie (Default)** | Self-intersecting bow-tie at $(20, 20)$ ($800.0\text{ mm}^2$ total) | Silently reduced to single triangle ($400.0\text{ mm}^2$). **400 mm² discarded.** | **REJECTED** with `CADTopologyError: Input contour is self-intersecting and repair via make_valid materially altered topology`. | **FIXED** |
| **Self-Intersecting Bow-Tie (Authorized)** | Same bow-tie with `allow_repaired_topology=True` | Silently reduced to single triangle ($400.0\text{ mm}^2$). | Both lobes preserved as `MultiPolygon` ($800.0\text{ mm}^2$). **0.00 mm² lost.** | **FIXED** |
| **Polygon with Interior Holes** | $120 \times 120\text{ mm}$ outer with $60 \times 60\text{ mm}$ hole | Preserved ($10,800.0\text{ mm}^2$). | Preserved ($10,800.0\text{ mm}^2$). Hole feasible regions extracted for child parts. | **VERIFIED** |
| **Triple-Lobe Self-Crossing** | Figure-8 with 2 crossings ($1 \to 3$ components) | Silently reduced to single largest lobe; 2 lobes discarded. | **REJECTED** with `CADTopologyError` (component split $1 \to 3$). | **FIXED** |
| **DXF Multiple Independent Parts** | 1 DXF with 3 parts (gusset, flange with hole, bracket) | Extracted 3 parts; holes preserved. | Extracted 3 parts; all holes preserved. Zero cross-part contamination. | **VERIFIED** |

---

## 4. End-to-End Geometric Conservation Audit

To verify that zero geometry components or holes disappear between CAD ingestion, nesting optimization, visualization, and DXF export, an automated conservation test was executed:
- **Test Composition:**
  - Part 1: `MultiPolygon` (2 components, $30 \times 30\text{ mm}$ each, area = $1,800.0\text{ mm}^2$).
  - Part 2: `Polygon` with hole ($100 \times 100\text{ mm}$ outer, $40 \times 40\text{ mm}$ hole, net area = $8,400.0\text{ mm}^2$).
  - Part 3: Simple rectangle ($50 \times 30\text{ mm}$, area = $1,500.0\text{ mm}^2$).
- **Audit Metrics:**
  - Input: Total Area = $11,700.00\text{ mm}^2$, Cut Components = 4, Interior Holes = 1.
  - Nesting Result: Placed on 1 sheet, 0 unplaced parts.
  - Exported DXF: Audited via `ezdxf.audit()` (0 errors, 0 fixes).
  - Exported Entities: Gross Cut Area = $13,300.00\text{ mm}^2$, Hole Area = $1,600.00\text{ mm}^2$, **Exported Net Area = $11,700.00\text{ mm}^2$**.
  - **Area Conservation Delta:** **$0.0000\text{ mm}^2$**.
  - **Component Count Conservation:** Input = 4 $\longleftrightarrow$ Exported = 4.
  - **Hole Count Conservation:** Input = 1 $\longleftrightarrow$ Exported = 1.

---

## 5. Benchmark Non-Regression Verification

The 5-seed Industrial batch benchmark was re-run to guarantee zero regression:
- **Input Hash Integrity:** `shapes.txt`, `gusset_plate.dxf`, `l_bracket.dxf`, `flange_plate.dxf`, `notched_base_plate.dxf` hashes unchanged.
- **Stock Dimensions:** $800.0\text{ mm} \times 500.0\text{ mm}$, Clearance: $4.0\text{ mm}$.

| Benchmark Configuration | Random Seed | Discrete Sheets | Area Util (%) | Linear Extent (mm) | Final Remnant (mm²) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **BLF Baseline** | N/A | 3 | 46.67% | 2,350.00 | 25,000.00 |
| **SA Orthogonal** | 42 | 3 | 46.67% | 1,966.00 | 217,000.00 |
| | 101 | 3 | 46.67% | 2,110.00 | 145,000.00 |
| | 202 | 3 | 46.67% | 1,742.00 | 329,000.00 |
| | 303 | 3 | 46.67% | 1,986.00 | 207,000.00 |
| | 404 | 3 | 46.67% | 1,926.00 | 237,000.00 |
| **5-Seed Mean** | **Historical: 1,946.00 mm** | **3.00** | **46.67%** | **Reproduced: 1,946.00 mm** | **227,000.00 mm²** |

**Verdict:** Zero benchmark regression. All metrics match the historical baseline down to $0.00\text{ mm}$.

---

## 6. Complete Automated Test Suite Results

Command: `$env:PYTHONPATH="."; pytest team_algoryxz/nest_craft/tests`

```
platform win32 -- Python 3.12.10, pytest-8.3.3, pluggy-1.6.0
collected 59 items

team_algoryxz\nest_craft\tests\test_adaptive_rotation.py ........        [ 13%]
team_algoryxz\nest_craft\tests\test_def01_remediation.py ........        [ 27%]
team_algoryxz\nest_craft\tests\test_dxf_reliability.py .........         [ 42%]
team_algoryxz\nest_craft\tests\test_geometry_adversarial_stress.py ..... [ 50%]
.....                                                                    [ 59%]
team_algoryxz\nest_craft\tests\test_geometry_validation.py ........      [ 72%]
team_algoryxz\nest_craft\tests\test_nesting.py .......                   [ 84%]
team_algoryxz\nest_craft\tests\test_part_in_part_nesting.py .........    [100%]

============================= 59 passed in 3.40s ==============================
```

---

## 7. Sign-Off & Defect Status

Defect **DEF-01** is **RESOLVED**. No CAD geometry component or interior hole is silently discarded during ingestion, optimization, visualization, or DXF export.
