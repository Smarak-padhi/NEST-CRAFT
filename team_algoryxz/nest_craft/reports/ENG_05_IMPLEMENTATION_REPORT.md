# ENG-05 Implementation Report: Adaptive Rotation & Grain Constraints
**Module:** Geometry & Nesting Engines (`src/geometry.py`, `src/baseline.py`, `src/optimizer.py`)  
**Status:** **COMPLETE & VERIFIED**  
**Date:** November 13, 2026  
**Auditor / Reviewer:** Senior Algorithms Engineer & Independent Critic  

---

## 1. Algorithmic Architecture

### 1.1 Mode A (Default Orthogonal Rotation)
- Angles evaluated: $[0.0^\circ, 90.0^\circ, 180.0^\circ, 270.0^\circ]$ (4 discrete orientations).
- Preserved as default (`rotation_mode="orthogonal"`) for all standard runs.
- **Shop-floor rationale:** Rectilinear parts (gussets, brackets, rectangular flanges) pack tightly when aligned flush with plate axes. Orthogonal rotation prevents axis-aligned bounding box (AABB) dilation.

### 1.2 Mode B (Adaptive Multi-Resolution Hybrid Rotation)
- **Phase 1 (Coarse Exploration):** 24 discrete angles at $15^\circ$ increments ($0^\circ, 15^\circ, 30^\circ, \dots, 345^\circ$).
- **Phase 2 (Local Refinement):** $5^\circ$ perturbation $[\theta^* - 10^\circ, \theta^* - 5^\circ, \theta^*, \theta^* + 5^\circ, \theta^* + 10^\circ] \pmod{360}$.
  - In Simulated Annealing: 50% coarse jump vs 50% fine refinement move operator.
  - In BLF: Coarse exploration followed by local $5^\circ$ refinement around the best coarse angle.
- **Shop-floor rationale:** Tailored for non-orthogonal, triangular, concave, or organic shapes (e.g., aerospace brackets, turbine blades, triangular wedges) where angled packing achieves interlocking nests.

### 1.3 Rolling Direction & Grain Alignment Restrictions
- **Horizontal Grain Constraint:** When `grain_direction="horizontal"` or `part.metadata["grain_constraint"] == "horizontal"`:
  Allowed angles are strictly restricted to $[0.0^\circ, 180.0^\circ]$, regardless of whether adaptive mode is active.
- **Vertical Grain Constraint:** When `grain_direction="vertical"` or `part.metadata["grain_constraint"] == "vertical"`:
  Allowed angles are strictly restricted to $[90.0^\circ, 270.0^\circ]$.
- **Unconstrained:** When `None` or `"any"`, full angular exploration is permitted.

---

## 2. Empirical Benchmark Evidence

### Experiment 1: Rectilinear Industrial Batch (17 Parts)
| Metric | Mode A (Orthogonal Rotation) | Mode B (Adaptive Rotation) | Analysis |
|:---|:---:|:---:|:---|
| **Mean Linear Extent** | **1,939.33 mm** | 2,534.94 mm | Orthogonal flush packing prevents bounding box dilation on rectangular plates. |
| **Mean Runtime** | **6.31 s** | 7.02 s | Fast convergence across both modes. |
| **Hole Nests** | 0 | 0 | Strict kerf clearance enforced. |
| **Verdict** | **Optimal for Rectilinear** | Experimental | Demonstrates why Mode A must remain the default. |

### Experiment 2: Irregular Triangular Geometry (8 Parts)
| Metric | Mode A (Orthogonal Rotation) | Mode B (Adaptive Rotation) | Analysis |
|:---|:---:|:---:|:---|
| **Linear Extent** | 523.50 mm | **494.43 mm** | **Adaptive rotation achieves -29.07 mm (-5.55%) tighter packing.** |
| **Runtime** | 1.05 s | 0.77 s | Sub-second execution. |
| **Collision Rate** | 0.0% (Zero) | 0.0% (Zero) | Exact round kerf clearance verified. |
| **Verdict** | Baseline | **Superior for Irregular** | Confirms high value of Mode B on non-orthogonal shapes. |

---

## 3. Verification & Test Evidence
Dedicated test file: `tests/test_adaptive_rotation.py` (8 tests):
- `test_default_orthogonal_rotation`: **PASSED**
- `test_adaptive_15_degree_coarse_angles`: **PASSED**
- `test_local_5_degree_refinement`: **PASSED**
- `test_grain_direction_horizontal_constraint`: **PASSED**
- `test_grain_direction_vertical_constraint`: **PASSED**
- `test_simulated_annealing_with_adaptive_rotation`: **PASSED**
- `test_reproducibility_with_fixed_seed_adaptive`: **PASSED**
- `test_grain_constrained_nesting_execution`: **PASSED**

Total suite status: **41 of 41 tests passed in 1.79s**.
