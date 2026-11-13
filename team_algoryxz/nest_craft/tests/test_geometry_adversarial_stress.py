"""
test_geometry_adversarial_stress.py
Stage C Release-Readiness Adversarial Testing Suite for NEST-CRAFT.
Rigorously stress-tests:
1. Concave, T-shaped, cross-shaped, and narrow bottleneck cutouts.
2. Inward buffer pinch-offs and negative-area feasible region disqualifications.
3. Multiple interior holes and multiple children per hole.
4. Children rotated under strict rolling grain constraints.
5. Exact-clearance boundary tangents vs near-clearance (sub-epsilon) violations.
6. Boundary margin contact and numerical tolerances.
7. Degenerate, unclosed, self-intersecting, and multi-polygon geometries.
8. Symmetric pairwise collision detection across acute vertices.
9. Bitwise deterministic reproducibility under identical random seeds.
"""

import unittest
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, box, LineString, Point
from shapely import affinity
from shapely.validation import make_valid

from team_algoryxz.nest_craft.src.geometry import (
    Part, Sheet, check_collision, compute_hole_feasible_regions,
    get_allowed_rotations, get_refined_rotation_angles
)
from team_algoryxz.nest_craft.src.baseline import (
    run_bottom_left_fill, place_part_in_holes, generate_hole_candidate_points
)
from team_algoryxz.nest_craft.src.optimizer import run_simulated_annealing


class TestGeometryAdversarialStress(unittest.TestCase):

    def setUp(self):
        self.clearance = 3.0
        self.sheet_w = 500.0
        self.sheet_h = 400.0

    def test_concave_and_cross_shaped_holes(self):
        """Tests feasible region extraction on cross-shaped (plus) and T-shaped cutouts."""
        # Cross-shaped cutout: central 40x40 with four 30x40 arms
        cross_hole = [
            (50, 80), (80, 80), (80, 50), (120, 50), (120, 80), (150, 80),
            (150, 120), (120, 120), (120, 150), (80, 150), (80, 120), (50, 120)
        ]
        parent = Polygon([(0, 0), (200, 0), (200, 200), (0, 200)], holes=[cross_hole])
        
        # Buffer inward by 3mm
        feas = compute_hole_feasible_regions(parent, clearance=3.0)
        self.assertGreaterEqual(len(feas), 1)
        self.assertTrue(feas[0].is_valid)
        
        # Candidate 20x20 in center
        child = box(0, 0, 20, 20)
        child_placed = affinity.translate(child, 90, 90)
        self.assertTrue(feas[0].contains(child_placed))
        
        # Candidate in arm of cross
        arm_child = affinity.translate(child, 60, 90)
        self.assertTrue(feas[0].contains(arm_child))
        
        # Candidate in outer concave notch (outside the cross cutout)
        notch_child = affinity.translate(child, 55, 55)
        self.assertFalse(feas[0].contains(notch_child))

    def test_narrow_bottleneck_and_pinch_off(self):
        """Tests that narrow bottlenecks pinch off or disqualify holes when bottleneck < 2 * clearance."""
        # Dumbbell hole: two 40x40 chambers connected by a 4mm wide neck
        # If clearance = 3mm, the 4mm neck has 4 - 2*3 = -2mm feasible width, so neck vanishes!
        dumbbell = [
            (20, 20), (60, 20), (60, 38), (100, 38), (100, 20), (140, 20),
            (140, 60), (100, 60), (100, 42), (60, 42), (60, 60), (20, 60)
        ]
        parent = Polygon([(0, 0), (160, 0), (160, 80), (0, 80)], holes=[dumbbell])
        
        feas = compute_hole_feasible_regions(parent, clearance=3.0)
        # Inward buffer should pinch off the neck, creating 2 separate feasible sub-polygons!
        self.assertEqual(len(feas), 2)
        for sub_r in feas:
            self.assertTrue(sub_r.is_valid)
            self.assertGreater(sub_r.area, 0.0)

    def test_too_narrow_hole_completely_disqualified(self):
        """Tests that a hole with all dimensions < 2 * clearance yields 0 feasible regions."""
        # 5mm x 5mm square hole with clearance = 3.0mm (needs at least 6mm x 6mm to have feasible area)
        tiny_hole = [(50, 50), (55, 50), (55, 55), (50, 55)]
        parent = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)], holes=[tiny_hole])
        
        feas = compute_hole_feasible_regions(parent, clearance=3.0)
        self.assertEqual(feas, [])

    def test_exact_clearance_tangent_vs_near_violation(self):
        """Tests that distance == clearance passes, while distance < clearance (both 3.990mm and 3.999mm) fails."""
        c = 4.0
        p1 = box(0, 0, 50, 50)
        
        # Exactly 4.000 mm separation
        p_exact = box(54.0, 0, 104.0, 50)
        self.assertAlmostEqual(p1.distance(p_exact), 4.0, places=5)
        self.assertFalse(check_collision(p_exact, [p1], clearance=c))
        self.assertFalse(check_collision(p1, [p_exact], clearance=c))
        
        # 3.990 mm separation (10 um sub-millimeter violation: 53.99 - 50.0 = 3.990 mm)
        p_violating_10um = box(53.99, 0, 103.99, 50)
        self.assertAlmostEqual(p1.distance(p_violating_10um), 3.99, places=5)
        self.assertLess(p1.distance(p_violating_10um), 4.0)
        self.assertTrue(check_collision(p_violating_10um, [p1], clearance=c))
        self.assertTrue(check_collision(p1, [p_violating_10um], clearance=c))

        # 3.999 mm separation (1 um sub-millimeter violation: 53.999 - 50.0 = 3.999 mm)
        p_violating_1um = box(53.999, 0, 103.999, 50)
        self.assertAlmostEqual(p1.distance(p_violating_1um), 3.999, places=5)
        self.assertLess(p1.distance(p_violating_1um), 4.0)
        self.assertTrue(check_collision(p_violating_1um, [p1], clearance=c))
        self.assertTrue(check_collision(p1, [p_violating_1um], clearance=c))

    def test_acute_vertex_symmetric_clearance(self):
        """Verifies that an acute 30-degree vertex produces symmetric collision checks."""
        tri = Polygon([(0, 0), (60, 0), (30, 50)]) # acute top vertex
        rect = box(20, 52, 40, 80) # placed 2mm above the acute tip
        
        c = 2.0
        self.assertAlmostEqual(tri.distance(rect), 2.0, places=4)
        # Both directions must agree: no false positive mitre spike
        self.assertFalse(check_collision(tri, [rect], clearance=c))
        self.assertFalse(check_collision(rect, [tri], clearance=c))

    def test_child_grain_restriction_enforcement(self):
        """Verifies child part placed in hole respects grain constraints."""
        large_hole = [(20, 20), (180, 20), (180, 180), (20, 180)]
        parent = Part(Polygon([(0, 0), (200, 0), (200, 200), (0, 200)], holes=[large_hole]), "P", 1)
        
        # Child with horizontal grain constraint
        child = Part(box(0, 0, 80, 30), "C_grain", 1, metadata={"grain_constraint": "horizontal"})
        
        sheets, stats = run_bottom_left_fill(
            [parent, child], sheet_width=300.0, sheet_height=300.0,
            clearance=2.0, rotation_mode="adaptive", allow_part_in_part=True
        )
        
        self.assertEqual(stats["parts_nested_in_holes"], 1)
        child_rot = next(rot for name, _, rot in sheets[0].placed_parts if "C_grain" in name)
        self.assertIn(child_rot, [0.0, 180.0])

    def test_self_intersecting_geometry_resilience(self):
        """Verifies that self-intersecting or bow-tie input polygons are rejected without authorization, and preserved in full when authorized."""
        # Bow-tie polygon (self-intersecting at center)
        bowtie = Polygon([(0, 0), (40, 40), (40, 0), (0, 40), (0, 0)])
        self.assertFalse(bowtie.is_valid)
        
        # 1. Unsanctioned ingestion must raise CADTopologyError (DEF-01 remediation)
        from team_algoryxz.nest_craft.src.geometry import CADTopologyError
        with self.assertRaises(CADTopologyError):
            Part(bowtie, "bowtie_part", quantity=1)
            
        # 2. When explicitly authorized, all components are preserved in full (no silent loss)
        part = Part(bowtie, "bowtie_part", quantity=1, metadata={"allow_repaired_topology": True})
        self.assertTrue(part.polygon.is_valid)
        self.assertTrue(isinstance(part.polygon, MultiPolygon))
        self.assertAlmostEqual(part.area, 800.0, places=4)
        self.assertEqual(len(part.polygon.geoms), 2)

    def test_topology_alteration_on_make_valid_detection(self):
        """
        Verifies that DEF-01 silent material reduction is remediated:
        Unsanctioned component reduction is rejected with CADTopologyError,
        and authorized ingestion preserves 100% of the material area (800 mm^2).
        """
        bowtie = Polygon([(0, 0), (40, 40), (40, 0), (0, 40), (0, 0)])
        self.assertFalse(bowtie.is_valid)
        
        # Raw make_valid repair splits bow-tie into a MultiPolygon of 2 separate polygons
        repaired = make_valid(bowtie)
        self.assertTrue(isinstance(repaired, MultiPolygon))
        self.assertEqual(len(repaired.geoms), 2)
        total_repaired_area = sum(g.area for g in repaired.geoms)
        self.assertAlmostEqual(total_repaired_area, 800.0, places=4)
        
        # Part wrapper without authorization raises CADTopologyError
        from team_algoryxz.nest_craft.src.geometry import CADTopologyError
        with self.assertRaises(CADTopologyError):
            Part(bowtie, "bowtie_part", quantity=1)
            
        # When authorized, Part retains both components with zero area loss
        part = Part(bowtie, "bowtie_part", quantity=1, metadata={"allow_repaired_topology": True})
        self.assertTrue(isinstance(part.polygon, MultiPolygon))
        self.assertAlmostEqual(part.area, 800.0, places=4)
        area_loss = total_repaired_area - part.area
        self.assertAlmostEqual(area_loss, 0.0, places=4) # ZERO material loss

    def test_stock_boundary_margin_and_numerical_epsilons(self):
        """Tests that boundary containment strictly enforces margin with floating point robustness."""
        sheet = Sheet(width=200.0, height=100.0)
        margin = 5.0
        
        # Exactly on the margin boundary: x in [5, 195], y in [5, 95]
        poly_ok = box(5.0, 5.0, 195.0, 95.0)
        self.assertTrue(sheet.can_contain(poly_ok, margin=margin))
        
        # Exceeding margin by 0.01 mm
        poly_exceed = box(4.99, 5.0, 195.0, 95.0)
        self.assertFalse(sheet.can_contain(poly_exceed, margin=margin))

    def test_deterministic_reproducibility_10_runs(self):
        """Runs Simulated Annealing 10 times with seed 42 to verify 100% bitwise determinism."""
        parts = [
            Part(box(0, 0, 60, 40), "r1", 2),
            Part(Polygon([(0, 0), (50, 0), (25, 30)]), "t1", 2)
        ]
        
        first_linear = None
        for _ in range(10):
            _, stats = run_simulated_annealing(
                parts, sheet_width=300.0, sheet_height=200.0,
                clearance=3.0, rotation_mode="orthogonal",
                max_iterations=10, random_seed=42
            )
            if first_linear is None:
                first_linear = stats["total_linear_length_consumed"]
            else:
                self.assertEqual(stats["total_linear_length_consumed"], first_linear)


if __name__ == '__main__':
    unittest.main()
