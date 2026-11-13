# Stage C.1 — Geometry Adversarial Stress Test & Invariant Verification Report
**Project:** NEST-CRAFT (Team Algoryxz — Odisha AI Hackathon 2026)  
**Date:** 2026-11-13 (Updated Stage C.1 Revision)  
**Status:** All 10 Adversarial Suites Passed (51/51 Total Project Tests Passed)  
**Test Suite Path:** `team_algoryxz/nest_craft/tests/test_geometry_adversarial_stress.py`

---

## 1. Scope & Objective

To verify the mathematical and geometric robustness of NEST-CRAFT under boundary and adversarial conditions, an independent 10-test adversarial test suite was authored and executed. This suite subjects the geometry engine, Part-in-Part module, and rotation solver to extreme geometric topologies that commonly cause crashes, numerical overflows, or false-positive/false-negative collision detections in industrial CAD/CAM pipelines.

---

## 2. Test Suite Architecture & Summary Table

| Test Identifier | Adversarial Condition Tested | Invariant Verified | Result | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| `test_concave_and_cross_shaped_holes` | Concave 12-sided cross (+) and T-shaped cutouts | Feasible region $H_{\text{feas}} = H.\text{buffer}(-c)$ preserves interior concavities; rejects placements outside cutout boundaries | **PASS** | 0.02s |
| `test_narrow_bottleneck_and_pinch_off` | Dumbbell cutout with bottleneck neck width $4\text{ mm} < 2 \times \text{clearance} (6\text{ mm})$ | Inward buffering cleanly pinches off the neck, decomposing into 2 disjoint valid `MultiPolygon` chambers | **PASS** | 0.01s |
| `test_too_narrow_hole_completely_disqualified` | Sub-clearance $5\text{ mm} \times 5\text{ mm}$ cutout with $c = 3\text{ mm}$ | Vanishing buffer correctly yields empty list `[]`; zero false placements | **PASS** | 0.01s |
| `test_exact_clearance_tangent_vs_near_violation` | Dual boundary tolerance testing: exact $4.000\text{ mm}$ vs $3.990\text{ mm}$ (10 µm invasion) and $3.999\text{ mm}$ (1 µm invasion) | Exact clearance $4.000\text{ mm}$ passes collision check; both sub-millimeter invasions ($3.990\text{ mm}$ and $3.999\text{ mm}$) strictly trigger collision detection | **PASS** | 0.01s |
| `test_acute_vertex_symmetric_clearance` | Sharp $30^\circ$ acute triangular wedge vs flat edge | Kerf expansion buffer uses circular caps (`cap_style=round`), preventing mitre-spike false positives; symmetric check | **PASS** | 0.01s |
| `test_child_grain_restriction_enforcement` | Nested child part with horizontal grain restriction inside hole | Candidate rotation angles restricted to $\{0^\circ, 180^\circ\}$; non-grain rotations strictly filtered out | **PASS** | 0.04s |
| `test_self_intersecting_geometry_resilience` | Self-intersecting "bow-tie" degenerate polygon | Automatic topological repair via Shapely `make_valid` recovers valid polygon without unhandled crash | **PASS** | 0.01s |
| `test_topology_alteration_on_make_valid_detection` | Quantitative audit of topological changes and material loss caused by `make_valid` | Multi-component decomposition splits bow-tie into two 400 mm² lobes; `Part` extracts only the largest component, discarding 50% of the material | **PASS** | 0.01s |
| `test_stock_boundary_margin_and_numerical_epsilons` | Exact bounding box margin boundary vs $0.01\text{ mm}$ overhang | Floating-point margins enforced with strict containment; overhang parts rejected | **PASS** | 0.01s |
| `test_deterministic_reproducibility_10_runs` | 10 consecutive Simulated Annealing runs with seed 42 | 100% bitwise identical objective value ($E$) and placement across all 10 runs | **PASS** | 0.45s |

---

## 3. Deep-Dive Invariant Verifications & Discrepancy Reconciliation

### 3.1. Reconciling the 3.990 mm vs. 3.999 mm Clearance Boundary Discrepancy
- **Audit Finding:** In the original Stage C report draft, Table 2 referenced testing at $3.999\text{ mm}$ (a $1\text{ \mu m}$ invasion), whereas the original code asserted `p_violating = box(53.99, 0, 103.99, 50)` against `box(0, 0, 50, 50)`, which corresponds to $53.99 - 50.0 = 3.990\text{ mm}$ (a $10\text{ \mu m}$ invasion). Section 3.3 of the report had noted $3.990\text{ mm}$, creating an internal document discrepancy.
- **Stage C.1 Test Enhancement & Execution:** In `test_exact_clearance_tangent_vs_near_violation`, both boundary cases are now explicitly instantiated and asserted:
  1. `p_exact = box(54.0, 0, 104.0, 50)`: Separation is exactly $4.00000\text{ mm}$. `check_collision` returns `False` symmetrically.
  2. `p_violating_10um = box(53.99, 0, 103.99, 50)`: Separation is $3.99000\text{ mm}$ ($10\text{ \mu m}$ invasion). `check_collision` returns `True`.
  3. `p_violating_1um = box(53.999, 0, 103.999, 50)`: Separation is $3.99900\text{ mm}$ ($1\text{ \mu m}$ sub-millimeter invasion). `check_collision` returns `True`.
- Both tests execute cleanly, proving that collision detection is sensitive down to $1\text{ \mu m}$ $(10^{-3}\text{ mm})$.

### 3.2. Quantitative Audit of `make_valid` Topological Alteration
- **Engineering Risk:** Automatic geometric repair using `shapely.validation.make_valid` resolves topological self-intersections (such as bow-ties or figure-eights). However, if an incoming contour decomposes into multiple disjoint polygons, taking only the largest polygon silently discards part geometry.
- **Test Evidence (`test_topology_alteration_on_make_valid_detection`):**
  - Input: Degenerate bow-tie contour `[(0, 0), (40, 40), (40, 0), (0, 40), (0, 0)]`.
  - Nominal geometry: Two triangular lobes intersecting at $(20, 20)$, each with base 40 mm and height 20 mm. Total area = $800.0\text{ mm}^2$.
  - `make_valid(bowtie)` returns a `MultiPolygon` with 2 distinct polygon components ($400.0\text{ mm}^2$ each).
  - When instantiated into `Part(bowtie)`, the class executes:
    ```python
    if isinstance(polygon, MultiPolygon):
        polygon = max(polygon.geoms, key=lambda g: g.area)
    ```
    This extracts exactly ONE lobe ($400.0\text{ mm}^2$) and silently discards the second lobe, resulting in an exact **50% material area loss ($400.0\text{ mm}^2$)**.
- **Mandatory Quality Assurance Rule:** Repaired geometry must **NEVER be silently accepted in production CAD ingestion** if its topology materially changes (e.g., splitting into multiple components or losing area beyond a $0.1\%$ numerical threshold). Production CAD loaders must raise an explicit validation warning or reject the drawing to prevent the cutting of incomplete components.

### 3.3. Concave & Cross-Shaped Cutouts
- In `test_concave_and_cross_shaped_holes`, a 12-vertex cross-shaped cutout was tested. Placing a $20\text{ mm} \times 20\text{ mm}$ child inside the central core or within one of the four rectangular arms succeeded, whereas placing it in the concave exterior corner was strictly rejected (`contains == False`).

### 3.4. Bottleneck Pinch-Off Topology
- A dumbbell-shaped hole consisting of two $40\text{ mm} \times 40\text{ mm}$ chambers connected by a $4\text{ mm}$ wide canal was tested with clearance $c = 3.0\text{ mm}$ (minimum safe passage = $6.0\text{ mm}$).
- The inward buffer operation $H.\text{buffer}(-3.0)$ properly vanished the neck ($4.0 - 6.0 = -2.0\text{ mm}$), splitting the single hole into two independent, valid child polygons. NEST-CRAFT successfully extracted both chambers without generating invalid geometry.

### 3.5. Acute Vertices & Circular Joint Buffer
- NEST-CRAFT relies on circular round caps (`join_style='round'`), ensuring that distance checks to sharp acute vertices ($30^\circ$) measure true Euclidean radial clearance rather than miter overhang spikes.

### 3.6. Rolling Grain Direction Constraints in Nested Cavities
- Child parts nested inside parent cavities with `metadata={"grain_constraint": "horizontal"}` only explore rotations of $0^\circ$ and $180^\circ$. $90^\circ$ and $270^\circ$ orientations were completely suppressed.

### 3.7. 10-Run Bitwise Deterministic Reproducibility
- 10 consecutive runs of `run_simulated_annealing` on identical input parts with `random_seed=42` yielded identical linear extents of `230.00 mm` across all 10 runs with zero stochastic drift.

---

## 4. Test Execution Verdict

All 10 adversarial tests passed seamlessly within **0.96 seconds**. The complete test suite now stands at **51/51 passing tests** across 6 test modules:
- `test_nesting.py`: 7 passed
- `test_geometry_validation.py`: 8 passed
- `test_dxf_reliability.py`: 9 passed
- `test_part_in_part_nesting.py`: 9 passed
- `test_adaptive_rotation.py`: 8 passed
- `test_geometry_adversarial_stress.py`: 10 passed

**Verdict:** The geometric kernel of NEST-CRAFT satisfies all verified topological and clearance invariants, with documented caveats regarding `make_valid` multi-component decomposition.
