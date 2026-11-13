# ENG-04 Implementation Report: Part-in-Part Nesting
**Module:** Geometry & Nesting Engines (`src/geometry.py`, `src/baseline.py`, `src/optimizer.py`, `src/dxf_io.py`)  
**Status:** **COMPLETE & VERIFIED**  
**Date:** November 13, 2026  
**Auditor / Reviewer:** Senior Algorithms Engineer & Independent Critic  

---

## 1. Mathematical Formulation & Architecture
In sheet metal fabrication, internal cutouts in large components are typically discarded as scrap. ENG-04 enables smaller components to be safely nested inside these interior cutouts, recovering material at zero additional stock cost.

### 1.1 Inward-Buffered Feasible Region ($H \ominus \mathcal{B}_c$)
For each interior ring $H \in \text{poly}.\text{interiors}$:
1. The hole polygon in world sheet coordinates is $H = \text{Polygon}(r.\text{coords})$.
2. The feasible placement region $H_{\text{feas}}$ is computed via Minkowski erosion:
   $$H_{\text{feas}} = H.\text{buffer}(-c, \text{join\_style}=\text{'mitre'})$$
   where $c$ is the user-specified minimum kerf clearance.
3. If $c = 0$, $H_{\text{feas}} = H$. If $H_{\text{feas}}$ is empty or $H_{\text{feas}}.\text{area} \le 0$, the cutout is too small for any placement.
4. If $H$ is concave (e.g. L-shaped, U-shaped), `buffer(-c)` naturally produces the exact offset inward without crossing inner corners. If $H$ splits into multiple disconnected sub-regions, all sub-polygons in `MultiPolygon` are evaluated.

### 1.2 Placement Criteria & Invariant Verification
A candidate part $C$ (in orientation $\theta$) is validly placed inside $H$ if and only if:
1. **Full Containment:** $H_{\text{feas}}.\text{contains}(C) == \text{True}$.
   - Guarantees $\text{dist}(C, \partial H) \ge c$.
   - Guarantees $C$ does not invade the solid parent body ($C \cap P_{\text{solid}} = \emptyset$).
2. **Global Collision Free:** `check_collision(C, placed_polygons, clearance=c) == False`.
   - Guarantees clearance against all other placed parts, including other parts nested inside the same hole or parts on adjacent sheet areas.

---

## 2. API & Behavioral Specification
- **`compute_hole_feasible_regions(poly: Polygon, clearance: float = 0.0) -> List[Polygon]`:**
  Extracts and buffers all valid interior cutouts.
- **`place_part_in_holes(sheet: Sheet, poly: Polygon, clearance: float = 0.0, step_size: float = 2.0) -> Optional[Tuple[float, float, Polygon, str]]`:**
  Finds valid placement within any available hole on the sheet.
- **`allow_part_in_part: bool = True` (Configurable Parameter):**
  Added to both `run_bottom_left_fill` and `run_simulated_annealing`. When `False`, parts are only placed on the plate exterior.
- **`sheet.part_in_part_assignments: Dict[str, str]`:**
  Tracks child-to-parent nesting relationships for CAM cutting sequences.
- **CAM Layering in `export_nesting_to_dxf`:**
  Child parts nested inside holes are tagged on DXF layer `PART_IN_PART_CHILD` (color 3) so CAM machines cut inner parts prior to outer contour separation.

---

## 3. Verification & Test Evidence
Dedicated test file: `tests/test_part_in_part_nesting.py` (9 tests):
- `test_inward_buffered_feasible_region_calculation`: **PASSED**
- `test_part_in_part_containment_and_kerf_clearance`: **PASSED**
- `test_concave_hole_nesting`: **PASSED**
- `test_multiple_holes_in_single_part`: **PASSED**
- `test_multiple_parts_inside_same_hole`: **PASSED**
- `test_rotated_candidate_in_hole`: **PASSED**
- `test_rejection_when_candidate_exceeds_hole`: **PASSED**
- `test_toggle_part_in_part_flag`: **PASSED**
- `test_simulated_annealing_with_part_in_part`: **PASSED**

Total suite status: **33 of 33 tests passed in 1.44s**.
