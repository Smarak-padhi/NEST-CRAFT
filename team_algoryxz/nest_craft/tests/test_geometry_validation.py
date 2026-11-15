"""
test_geometry_validation.py
Comprehensive automated test suite for NEST-CRAFT geometry engine, collision detection,
clearance buffer guarantees, boundary containment, hole mechanics, and reproducibility.
"""

import unittest
import math
import numpy as np
from shapely.geometry import Polygon, box, Point
from shapely import affinity

from team_algoryxz.nest_craft.src.geometry import Part, Sheet, check_collision
from team_algoryxz.nest_craft.src.baseline import run_bottom_left_fill, place_part_bottom_left
from team_algoryxz.nest_craft.src.optimizer import run_simulated_annealing
from team_algoryxz.nest_craft.src.calculator import calculate_remnant_plate_value

class TestGeometryValidation(unittest.TestCase):

    def test_strict_kerf_clearance_enforcement(self):
        """Validates that check_collision flags proximity violations within clearance distance."""
        polyA = box(0, 0, 100, 100)

        # Poly B at distance exactly 10mm along X: (110, 0) to (210, 100)
        polyB = box(110, 0, 210, 100)

        # Clearance = 5.0mm (distance 10mm > 5mm): no collision
        self.assertFalse(check_collision(polyB, [polyA], clearance=5.0))

        # Clearance = 10.0mm (distance 10mm == 10mm): contact boundary, area <= 1e-4 -> false
        self.assertFalse(check_collision(polyB, [polyA], clearance=10.0))

        # Clearance = 12.0mm (distance 10mm < 12mm): proximity violation -> collision
        self.assertTrue(check_collision(polyB, [polyA], clearance=12.0))

    def test_hole_clearance_and_collision(self):
        """Validates collision detection when a part is evaluated inside an interior hole."""
        # Outer 200x200 plate with a 100x100 hole from (50, 50) to (150, 150)
        outer_shell = [(0, 0), (200, 0), (200, 200), (0, 200)]
        hole = [(50, 50), (150, 50), (150, 150), (50, 150)]
        plate_with_hole = Polygon(shell=outer_shell, holes=[hole])

        # Small 40x40 part centered inside the hole from (80, 80) to (120, 120)
        # Distance to hole boundaries is 30mm on all sides
        small_part = box(80, 80, 120, 120)

        # With clearance = 5.0mm: fits comfortably inside hole without touching solid metal
        self.assertFalse(check_collision(small_part, [plate_with_hole], clearance=5.0))

        # Part that breaches clearance to the hole boundary:
        # 95x95 part from (52, 52) to (147, 147) has only 2mm clearance to hole wall (50, 50)
        tight_part = box(52, 52, 147, 147)
        # Clearance of 5.0mm should flag collision against hole wall
        self.assertTrue(check_collision(tight_part, [plate_with_hole], clearance=5.0))

    def test_stock_boundary_containment_and_margin(self):
        """Validates boundary containment for exact fit, fractional overflows, and edge margins."""
        sheet = Sheet(width=500.0, height=300.0, sheet_id=1)

        # Exact fit at boundary
        exact_box = box(0.0, 0.0, 500.0, 300.0)
        self.assertTrue(sheet.can_contain(exact_box))

        # 0.01mm width overflow
        overflow_x = box(0.0, 0.0, 500.01, 300.0)
        self.assertFalse(sheet.can_contain(overflow_x))

        # 0.01mm height overflow
        overflow_y = box(0.0, 0.0, 500.0, 300.01)
        self.assertFalse(sheet.can_contain(overflow_y))

        # Negative coordinate
        neg_coord = box(-0.01, 0.0, 400.0, 200.0)
        self.assertFalse(sheet.can_contain(neg_coord))

        # Margin testing: part at (4, 4) with 5mm sheet margin required
        margin_box = box(4.0, 4.0, 200.0, 200.0)
        self.assertTrue(sheet.can_contain(margin_box, margin=0.0))
        self.assertFalse(sheet.can_contain(margin_box, margin=5.0))

        # Part at (5, 5) with 5mm margin fits
        valid_margin_box = box(5.0, 5.0, 200.0, 200.0)
        self.assertTrue(sheet.can_contain(valid_margin_box, margin=5.0))

    def test_rotation_invariance_with_interior_holes(self):
        """Validates that rotating a part with holes maintains exact hole geometry, count, and area."""
        outer = [(0, 0), (120, 0), (120, 80), (0, 80)]
        hole1 = [(20, 20), (50, 20), (50, 50), (20, 50)]
        hole2 = [(70, 20), (100, 20), (100, 50), (70, 50)]
        poly = Polygon(outer, [hole1, hole2])
        part = Part(poly, "flange_2holes")

        self.assertEqual(len(part.base_polygon.interiors), 2)
        initial_area = part.area

        for angle in [90.0, 180.0, 270.0]:
            rotated = part.get_rotated(angle)
            self.assertEqual(len(rotated.interiors), 2)
            self.assertAlmostEqual(rotated.area, initial_area, places=4)
            # Normalization to (0, 0) check
            minx, miny, maxx, maxy = rotated.bounds
            self.assertAlmostEqual(minx, 0.0, places=4)
            self.assertAlmostEqual(miny, 0.0, places=4)

    def test_interlocking_concave_polygons(self):
        """Validates collision-free nesting for concave L-brackets interlocking."""
        # 100x100 L-bracket with 40mm arm thickness
        bracket = Polygon([(0, 0), (100, 0), (100, 40), (40, 40), (40, 100), (0, 100)])
        part1 = Part(bracket, "bracket_1")

        # Second bracket inverted (180 deg) and fitted into recess
        sheet = Sheet(width=300.0, height=200.0, sheet_id=1)
        # Place part 1 at (0, 0)
        sheet.placed_parts.append(("b1", part1.base_polygon, 0.0))

        # Place part 2 inverted at (40, 40)
        b2_rot = part1.get_rotated(180.0)
        b2_placed = affinity.translate(b2_rot, xoff=40.0, yoff=40.0)

        # Test collision with 2.0mm clearance -> overlapping arms should collide
        self.assertTrue(check_collision(b2_placed, [p for _, p, _ in sheet.placed_parts], clearance=2.0))

        # Shift b2 by 4mm clearance: (44, 44)
        b2_safe = affinity.translate(b2_rot, xoff=44.0, yoff=44.0)
        self.assertFalse(check_collision(b2_safe, [p for _, p, _ in sheet.placed_parts], clearance=2.0))

    def test_linear_extents_and_remnant_computation(self):
        """Validates computation of X max span, total linear length consumed, and remnant geometry."""
        sheet = Sheet(width=800.0, height=500.0, sheet_id=1)
        # Place part reaching up to X = 350.0
        p1 = box(10.0, 10.0, 350.0, 200.0)
        sheet.placed_parts.append(("p1", p1, 0.0))

        remnant = sheet.get_remnant_geometry()
        self.assertAlmostEqual(remnant["max_x_span"], 350.0)
        self.assertAlmostEqual(remnant["remnant_width"], 450.0) # 800 - 350
        self.assertAlmostEqual(remnant["remnant_height"], 500.0)
        self.assertAlmostEqual(remnant["remnant_area"], 450.0 * 500.0)
        self.assertTrue(remnant["estimated_geometric_remnant"]) # 450mm >= 100mm threshold (geometric margin)

    def test_reproducibility_with_fixed_seed(self):
        """Validates that Simulated Annealing produces bit-for-bit identical results with fixed random seed."""
        parts = [
            Part(box(0, 0, 50, 40), f"p_{i}", quantity=1) for i in range(5)
        ]

        sheets1, stats1 = run_simulated_annealing(
            parts, sheet_width=150.0, sheet_height=100.0, clearance=2.0,
            max_iterations=10, random_seed=999
        )
        sheets2, stats2 = run_simulated_annealing(
            parts, sheet_width=150.0, sheet_height=100.0, clearance=2.0,
            max_iterations=10, random_seed=999
        )

        self.assertEqual(stats1["sheets_used"], stats2["sheets_used"])
        self.assertEqual(stats1["utilization_pct"], stats2["utilization_pct"])
        self.assertEqual(stats1["total_linear_length_consumed"], stats2["total_linear_length_consumed"])

        energies1 = [h["best_energy"] for h in stats1["history"]]
        energies2 = [h["best_energy"] for h in stats2["history"]]
        self.assertEqual(energies1, energies2)

    def test_remnant_plate_valuation_calculator(self):
        """Validates indicative pricing of preserved geometric margin plate offcuts."""
        # 434mm x 500mm plate, 10mm mild steel (density 7850 kg/m3)
        res = calculate_remnant_plate_value(
            width_mm=434.0, height_mm=500.0, thickness_mm=10.0,
            material_density_kg_m3=7850.0,
            raw_plate_price_per_kg=65.0,
            scrap_sale_price_per_kg=32.0
        )

        self.assertTrue(res["meets_secondary_inventory_threshold"])
        self.assertTrue(res["is_prime_reusable_remnant"])
        # Area = 0.434 * 0.5 = 0.217 m2; Volume = 0.217 * 0.010 = 0.00217 m3
        # Weight = 0.00217 * 7850 = 17.0345 kg ~ 17.03 kg
        self.assertAlmostEqual(res["plate_weight_kg"], 17.03, places=1)
        # Net value saved vs scrap = 17.0345 kg * (65 - 32) = 17.0345 * 33 = ~562.14 INR
        self.assertAlmostEqual(res["net_value_saved_vs_scrap_inr"], 562.14, delta=5.0)

    def test_remnant_threshold_and_boolean_scope(self):
        """
        Validates the strict 100mm geometric threshold and independent boolean scope
        for per-sheet metrics versus final sheet remnant.
        """
        # Test sub-100mm threshold: part leaves 80mm margin
        sheet_sub = Sheet(width=800.0, height=500.0, sheet_id=1)
        p_narrow = box(0.0, 0.0, 720.0, 200.0)  # max_x = 720, rem_w = 80mm
        sheet_sub.placed_parts.append(("p_narrow", p_narrow, 0.0))
        rem_sub = sheet_sub.get_remnant_geometry()
        self.assertAlmostEqual(rem_sub["remnant_width"], 80.0)
        self.assertFalse(rem_sub["estimated_geometric_remnant"])

        # Test supra-100mm threshold: part leaves 150mm margin
        sheet_sup = Sheet(width=800.0, height=500.0, sheet_id=2)
        p_wide = box(0.0, 0.0, 650.0, 200.0)  # max_x = 650, rem_w = 150mm
        sheet_sup.placed_parts.append(("p_wide", p_wide, 0.0))
        rem_sup = sheet_sup.get_remnant_geometry()
        self.assertAlmostEqual(rem_sup["remnant_width"], 150.0)
        self.assertTrue(rem_sup["estimated_geometric_remnant"])

        # Verify multi-sheet scope independence in nesting stats:
        # Sheet 1 has 80mm remnant (False), Sheet 2 has 150mm remnant (True)
        from team_algoryxz.nest_craft.src.baseline import run_bottom_left_fill
        part1 = Part(box(0, 0, 720, 480), "large_1", quantity=1)
        part2 = Part(box(0, 0, 650, 480), "large_2", quantity=1)
        sheets, stats = run_bottom_left_fill(
            [part1, part2],
            sheet_width=800.0,
            sheet_height=500.0,
            clearance=4.0,
            step_size=8.0
        )
        self.assertEqual(len(sheets), 2)
        per_sheet = stats["per_sheet_metrics"]
        self.assertEqual(len(per_sheet), 2)
        # Sheet 1 should be False (remnant width ~80mm < 100mm)
        self.assertFalse(per_sheet[0]["estimated_geometric_remnant"])
        # Sheet 2 should be True (remnant width ~150mm >= 100mm)
        self.assertTrue(per_sheet[1]["estimated_geometric_remnant"])
        # Final sheet remnant must match Sheet 2's boolean exclusively
        self.assertTrue(stats["final_sheet_remnant"]["estimated_geometric_remnant"])
        self.assertEqual(
            stats["final_sheet_remnant"]["estimated_geometric_remnant"],
            per_sheet[-1]["estimated_geometric_remnant"]
        )

if __name__ == "__main__":
    unittest.main()
