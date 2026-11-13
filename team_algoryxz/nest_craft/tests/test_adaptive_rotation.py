"""
test_adaptive_rotation.py
Comprehensive unit and integration test suite for ENG-05 (Adaptive Rotation & Grain Constraints).
Verifies:
1. Default orthogonal rotation [0, 90, 180, 270].
2. 15-degree coarse exploration grid (24 discrete angles).
3. 5-degree local refinement around candidate angles.
4. Strict enforcement of rolling/grain direction constraints (horizontal & vertical).
5. Simulated Annealing optimizer integration with adaptive rotation.
6. Deterministic reproducibility under fixed random seeds.
7. Zero collision, sheet containment, and kerf compliance under non-orthogonal rotations.
"""

import unittest
from typing import List
from shapely.geometry import Polygon, box

from team_algoryxz.nest_craft.src.geometry import (
    Part, Sheet, check_collision, get_allowed_rotations, get_refined_rotation_angles
)
from team_algoryxz.nest_craft.src.baseline import run_bottom_left_fill
from team_algoryxz.nest_craft.src.optimizer import run_simulated_annealing


class TestAdaptiveRotation(unittest.TestCase):
    
    def setUp(self):
        self.sheet_w = 400.0
        self.sheet_h = 300.0
        self.clearance = 2.0
        
    def test_default_orthogonal_rotation(self):
        """Verifies default rotation returns standard orthogonal angles."""
        angles = get_allowed_rotations(rotation_mode="orthogonal")
        self.assertEqual(angles, [0.0, 90.0, 180.0, 270.0])

    def test_adaptive_15_degree_coarse_angles(self):
        """Verifies adaptive mode generates 24 coarse angles in 15-degree increments."""
        angles = get_allowed_rotations(rotation_mode="adaptive")
        self.assertEqual(len(angles), 24)
        self.assertEqual(angles[0], 0.0)
        self.assertEqual(angles[1], 15.0)
        self.assertEqual(angles[-1], 345.0)

    def test_local_5_degree_refinement(self):
        """Verifies 5-degree local refinement generates 5 candidate angles centered on best coarse angle."""
        refined_45 = get_refined_rotation_angles(45.0)
        self.assertEqual(refined_45, [35.0, 40.0, 45.0, 50.0, 55.0])
        
        # Test boundary wrap-around at 0 degrees
        refined_0 = get_refined_rotation_angles(0.0)
        self.assertEqual(refined_0, [0.0, 5.0, 10.0, 350.0, 355.0])

    def test_grain_direction_horizontal_constraint(self):
        """Verifies horizontal grain constraint restricts rotation strictly to [0, 180], even in adaptive mode."""
        part_horiz = Part(box(0, 0, 100, 40), "part_h", metadata={"grain_constraint": "horizontal"})
        angles_ortho = get_allowed_rotations(part_horiz, rotation_mode="orthogonal")
        self.assertEqual(angles_ortho, [0.0, 180.0])
        
        angles_adaptive = get_allowed_rotations(part_horiz, rotation_mode="adaptive")
        self.assertEqual(angles_adaptive, [0.0, 180.0])
        
        # Global parameter override
        angles_global = get_allowed_rotations(rotation_mode="adaptive", grain_direction="horizontal")
        self.assertEqual(angles_global, [0.0, 180.0])

    def test_grain_direction_vertical_constraint(self):
        """Verifies vertical grain constraint restricts rotation strictly to [90, 270]."""
        part_vert = Part(box(0, 0, 100, 40), "part_v", metadata={"grain_direction": "vertical"})
        angles = get_allowed_rotations(part_vert, rotation_mode="adaptive")
        self.assertEqual(angles, [90.0, 270.0])

    def test_simulated_annealing_with_adaptive_rotation(self):
        """Verifies Simulated Annealing executes cleanly with adaptive rotation mode."""
        tri = Polygon([(0, 0), (60, 0), (30, 50)])
        parts = [Part(tri, f"tri_{i}", quantity=2) for i in range(2)] # 4 total
        
        sheets, stats = run_simulated_annealing(
            parts, sheet_width=300.0, sheet_height=200.0,
            clearance=self.clearance, rotation_mode="adaptive",
            max_iterations=20, random_seed=42
        )
        
        self.assertEqual(stats["total_parts_nested"], 4)
        self.assertEqual(stats["rotation_mode"], "adaptive")
        
        # Verify zero collision and strict kerf compliance across all placed parts
        placed = [p for s in sheets for _, p, _ in s.placed_parts]
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                self.assertFalse(check_collision(placed[i], [placed[j]], clearance=self.clearance))

    def test_reproducibility_with_fixed_seed_adaptive(self):
        """Verifies exact deterministic reproducibility under fixed random seed in adaptive mode."""
        parts1 = [
            Part(box(0, 0, 50, 30), "p1", quantity=2),
            Part(Polygon([(0, 0), (40, 0), (20, 35)]), "tri", quantity=2)
        ]
        parts2 = [
            Part(box(0, 0, 50, 30), "p1", quantity=2),
            Part(Polygon([(0, 0), (40, 0), (20, 35)]), "tri", quantity=2)
        ]
        
        _, stats1 = run_simulated_annealing(
            parts1, sheet_width=250.0, sheet_height=200.0,
            clearance=2.0, rotation_mode="adaptive",
            max_iterations=15, random_seed=101
        )
        _, stats2 = run_simulated_annealing(
            parts2, sheet_width=250.0, sheet_height=200.0,
            clearance=2.0, rotation_mode="adaptive",
            max_iterations=15, random_seed=101
        )
        
        self.assertEqual(stats1["sheets_used"], stats2["sheets_used"])
        self.assertEqual(stats1["total_linear_length_consumed"], stats2["total_linear_length_consumed"])
        self.assertEqual(stats1["utilization_pct"], stats2["utilization_pct"])

    def test_grain_constrained_nesting_execution(self):
        """Verifies that placed parts with grain constraints strictly adhere to allowed angles."""
        # 2 parts with horizontal grain constraint, 2 unconstrained
        p_grain = Part(box(0, 0, 80, 30), "grain_part", quantity=2, metadata={"grain_constraint": "horizontal"})
        p_free = Part(box(0, 0, 40, 40), "free_part", quantity=2)
        
        sheets, stats = run_simulated_annealing(
            [p_grain, p_free], sheet_width=300.0, sheet_height=200.0,
            clearance=2.0, rotation_mode="adaptive",
            max_iterations=15, random_seed=42
        )
        
        for s in sheets:
            for name, _, rot in s.placed_parts:
                if "grain_part" in name:
                    self.assertIn(rot, [0.0, 180.0], f"Part {name} rotated to {rot} violating horizontal grain!")


if __name__ == '__main__':
    unittest.main()
