"""
test_part_in_part_nesting.py
Comprehensive unit and integration test suite for ENG-04 (Part-in-Part Placement).
Verifies:
1. Feasible region geometry calculation via inward buffering (H ⊖ B_c).
2. Strict kerf clearance and collision prevention with parent and sibling parts.
3. Concave hole topologies (L-shaped, T-shaped).
4. Multiple holes in a single parent part.
5. Multiple child parts nested inside the same hole.
6. Rotated candidate validation inside holes.
7. Candidate rejection when exceeding hole feasible region.
8. Independent configurability via allow_part_in_part flag.
9. Simulated Annealing optimizer integration with part-in-part nesting.
"""

import unittest
from typing import List, Tuple
from shapely.geometry import Polygon, box, Point
from shapely import affinity

from team_algoryxz.nest_craft.src.geometry import (
    Part, Sheet, check_collision, compute_hole_feasible_regions
)
from team_algoryxz.nest_craft.src.baseline import (
    run_bottom_left_fill, place_part_in_holes, generate_hole_candidate_points
)
from team_algoryxz.nest_craft.src.optimizer import run_simulated_annealing


class TestPartInPartNesting(unittest.TestCase):
    
    def setUp(self):
        # Standard sheet 400 x 300
        self.sheet_w = 400.0
        self.sheet_h = 300.0
        self.clearance = 3.0
        
    def test_inward_buffered_feasible_region_calculation(self):
        """Verifies mathematical correctness of H_feas = H.buffer(-c)."""
        # Hole 100 x 100
        hole_coords = [(20, 20), (120, 20), (120, 120), (20, 120)]
        parent = Polygon([(0, 0), (200, 0), (200, 200), (0, 200)], holes=[hole_coords])
        
        # Test c = 0.0
        feas_0 = compute_hole_feasible_regions(parent, clearance=0.0)
        self.assertEqual(len(feas_0), 1)
        self.assertAlmostEqual(feas_0[0].area, 10000.0, places=2)
        
        # Test c = 5.0 -> Dimensions should be 90 x 90, area = 8100.0
        feas_5 = compute_hole_feasible_regions(parent, clearance=5.0)
        self.assertEqual(len(feas_5), 1)
        self.assertAlmostEqual(feas_5[0].area, 8100.0, places=2)
        minx, miny, maxx, maxy = feas_5[0].bounds
        self.assertAlmostEqual(minx, 25.0, places=2)
        self.assertAlmostEqual(miny, 25.0, places=2)
        self.assertAlmostEqual(maxx, 115.0, places=2)
        self.assertAlmostEqual(maxy, 115.0, places=2)
        
        # Test part with no holes returns empty list
        solid_part = Polygon([(0, 0), (50, 0), (50, 50), (0, 50)])
        self.assertEqual(compute_hole_feasible_regions(solid_part, clearance=5.0), [])

    def test_part_in_part_containment_and_kerf_clearance(self):
        """Verifies candidate placed in hole has >= clearance to parent boundary and 0 collision."""
        hole_coords = [(50, 50), (150, 50), (150, 150), (50, 150)] # 100x100 hole
        parent_poly = Polygon([(0, 0), (250, 0), (250, 250), (0, 250)], holes=[hole_coords])
        sheet = Sheet(self.sheet_w, self.sheet_h)
        sheet.placed_parts.append(("parent_1", parent_poly, 0.0))
        
        # Child 40x40
        child_poly = box(0, 0, 40, 40)
        
        # Place child in hole
        placement = place_part_in_holes(sheet, child_poly, clearance=self.clearance, step_size=2.0)
        self.assertIsNotNone(placement)
        x, y, candidate, parent_name = placement
        self.assertEqual(parent_name, "parent_1")
        
        # Verify strict containment inside hole
        raw_hole = Polygon(hole_coords)
        self.assertTrue(raw_hole.contains(candidate))
        
        # Verify distance to hole boundary is >= clearance
        dist = candidate.distance(raw_hole.exterior)
        self.assertGreaterEqual(dist, self.clearance - 1e-4)
        
        # Verify zero collision with parent solid body
        self.assertFalse(check_collision(candidate, [parent_poly], clearance=self.clearance))

    def test_concave_hole_nesting(self):
        """Verifies placement inside concave (L-shaped) hole without invading convex outer corner."""
        # L-shaped hole
        # Outer corner is at (150, 150), but inner notch is at (90, 90)
        l_hole = [(30, 30), (150, 30), (150, 80), (80, 80), (80, 150), (30, 150)]
        parent_poly = Polygon([(0, 0), (200, 0), (200, 200), (0, 200)], holes=[l_hole])
        sheet = Sheet(self.sheet_w, self.sheet_h)
        sheet.placed_parts.append(("parent_L", parent_poly, 0.0))
        
        # Child 30x30
        child = box(0, 0, 30, 30)
        placement = place_part_in_holes(sheet, child, clearance=self.clearance, step_size=2.0)
        self.assertIsNotNone(placement)
        _, _, candidate, _ = placement
        
        # Candidate must be strictly contained inside the L-shaped hole
        hole_poly = Polygon(l_hole)
        self.assertTrue(hole_poly.contains(candidate))
        self.assertFalse(check_collision(candidate, [parent_poly], clearance=self.clearance))

    def test_multiple_holes_in_single_part(self):
        """Verifies two separate child parts nest into two different cutouts of the same parent."""
        h1 = [(30, 30), (100, 30), (100, 100), (30, 100)] # 70x70
        h2 = [(140, 30), (210, 30), (210, 100), (140, 100)] # 70x70
        parent_poly = Polygon([(0, 0), (250, 0), (250, 150), (0, 150)], holes=[h1, h2])
        
        parent = Part(parent_poly, "multi_hole_parent", quantity=1)
        child1 = Part(box(0, 0, 35, 35), "child_1", quantity=1)
        child2 = Part(box(0, 0, 35, 35), "child_2", quantity=1)
        
        sheets, stats = run_bottom_left_fill(
            [parent, child1, child2], sheet_width=300.0, sheet_height=200.0,
            clearance=self.clearance, allow_part_in_part=True
        )
        
        self.assertEqual(len(sheets), 1)
        self.assertEqual(stats["total_parts_nested"], 3)
        self.assertEqual(stats["parts_nested_in_holes"], 2)
        self.assertIn("child_1_1", stats["part_in_part_assignments"])
        self.assertIn("child_2_1", stats["part_in_part_assignments"])
        
        # Verify zero pairwise collision among all 3 parts
        placed = [p for _, p, _ in sheets[0].placed_parts]
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                self.assertFalse(check_collision(placed[i], [placed[j]], clearance=self.clearance))

    def test_multiple_parts_inside_same_hole(self):
        """Verifies that two small parts can nest inside the SAME large hole with clearance between them."""
        # 160 x 80 hole
        large_hole = [(20, 20), (180, 20), (180, 100), (20, 100)]
        parent_poly = Polygon([(0, 0), (220, 0), (220, 140), (0, 140)], holes=[large_hole])
        
        parent = Part(parent_poly, "parent_large_hole", quantity=1)
        # Two 40x40 parts can easily fit side by side inside 160x80 hole
        small1 = Part(box(0, 0, 40, 40), "small_a", quantity=1)
        small2 = Part(box(0, 0, 40, 40), "small_b", quantity=1)
        
        sheets, stats = run_bottom_left_fill(
            [parent, small1, small2], sheet_width=300.0, sheet_height=200.0,
            clearance=self.clearance, allow_part_in_part=True
        )
        
        self.assertEqual(len(sheets), 1)
        self.assertEqual(stats["parts_nested_in_holes"], 2)
        # Verify mutual clearance
        p_polys = [p for _, p, _ in sheets[0].placed_parts]
        self.assertEqual(len(p_polys), 3)
        self.assertFalse(check_collision(p_polys[1], [p_polys[2]], clearance=self.clearance))

    def test_rotated_candidate_in_hole(self):
        """Verifies that a part needing rotation (e.g. 20x70 into 75x30 hole) rotates to fit."""
        # Horizontal slot hole 80 x 30
        slot_hole = [(30, 30), (110, 30), (110, 60), (30, 60)]
        parent_poly = Polygon([(0, 0), (150, 0), (150, 100), (0, 100)], holes=[slot_hole])
        
        parent = Part(parent_poly, "slot_parent", quantity=1)
        # Part is defined as 20 wide, 60 tall (at 0 degrees, it does NOT fit into 30 tall hole!)
        # But rotated 90 degrees, it becomes 60 wide, 20 tall and fits!
        tall_part = Part(box(0, 0, 20, 60), "tall_part", quantity=1)
        
        # Test with allowed_rotations = [0.0, 90.0]
        sheets, stats = run_bottom_left_fill(
            [parent, tall_part], sheet_width=300.0, sheet_height=200.0,
            clearance=self.clearance, allowed_rotations=[0.0, 90.0],
            allow_part_in_part=True
        )
        
        self.assertEqual(stats["parts_nested_in_holes"], 1)
        # The placed rotation of tall_part must be 90.0
        placed_rot = next(rot for name, _, rot in sheets[0].placed_parts if "tall_part" in name)
        self.assertEqual(placed_rot, 90.0)

    def test_rejection_when_candidate_exceeds_hole(self):
        """Verifies that a candidate too large for a hole is rejected from the hole and placed outside."""
        # Small hole 40 x 40
        small_hole = [(30, 30), (70, 30), (70, 70), (30, 70)]
        parent_poly = Polygon([(0, 0), (120, 0), (120, 120), (0, 120)], holes=[small_hole])
        parent = Part(parent_poly, "parent_small", quantity=1)
        
        # Oversized candidate 50 x 50 (cannot fit in 40x40 hole)
        big_part = Part(box(0, 0, 50, 50), "big_part", quantity=1)
        
        sheets, stats = run_bottom_left_fill(
            [parent, big_part], sheet_width=300.0, sheet_height=200.0,
            clearance=self.clearance, allow_part_in_part=True
        )
        
        # Must NOT be nested in hole
        self.assertEqual(stats["parts_nested_in_holes"], 0)
        self.assertEqual(stats["total_parts_nested"], 2)
        # Placed on exterior with valid clearance
        placed = [p for _, p, _ in sheets[0].placed_parts]
        self.assertFalse(check_collision(placed[0], [placed[1]], clearance=self.clearance))

    def test_toggle_part_in_part_flag(self):
        """Verifies that setting allow_part_in_part=False completely disables hole nesting."""
        hole_coords = [(30, 30), (130, 30), (130, 130), (30, 130)]
        parent = Part(Polygon([(0, 0), (160, 0), (160, 160), (0, 160)], holes=[hole_coords]), "P", 1)
        child = Part(box(0, 0, 40, 40), "C", 1)
        
        # Disabled
        _, stats_off = run_bottom_left_fill(
            [parent, child], sheet_width=300.0, sheet_height=200.0,
            clearance=2.0, allow_part_in_part=False
        )
        self.assertEqual(stats_off["parts_nested_in_holes"], 0)
        self.assertEqual(len(stats_off["part_in_part_assignments"]), 0)
        
        # Enabled
        _, stats_on = run_bottom_left_fill(
            [parent, child], sheet_width=300.0, sheet_height=200.0,
            clearance=2.0, allow_part_in_part=True
        )
        self.assertEqual(stats_on["parts_nested_in_holes"], 1)
        self.assertIn("C_1", stats_on["part_in_part_assignments"])

    def test_simulated_annealing_with_part_in_part(self):
        """Verifies Simulated Annealing executes with part-in-part nesting enabled."""
        h1 = [(40, 40), (140, 40), (140, 140), (40, 140)]
        parent = Part(Polygon([(0, 0), (180, 0), (180, 180), (0, 180)], holes=[h1]), "frame", quantity=1)
        small1 = Part(box(0, 0, 40, 40), "insert_1", quantity=1)
        small2 = Part(box(0, 0, 30, 30), "insert_2", quantity=1)
        
        sheets, stats = run_simulated_annealing(
            [parent, small1, small2], sheet_width=250.0, sheet_height=250.0,
            clearance=2.0, max_iterations=15, random_seed=42,
            allow_part_in_part=True
        )
        
        self.assertEqual(stats["total_parts_nested"], 3)
        self.assertGreaterEqual(stats["parts_nested_in_holes"], 1)
        # Verify zero collision across all placed parts
        all_polys = [p for s in sheets for _, p, _ in s.placed_parts]
        for i in range(len(all_polys)):
            for j in range(i + 1, len(all_polys)):
                self.assertFalse(check_collision(all_polys[i], [all_polys[j]], clearance=2.0))


if __name__ == '__main__':
    unittest.main()
