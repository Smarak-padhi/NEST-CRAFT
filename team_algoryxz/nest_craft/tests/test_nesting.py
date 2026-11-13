"""
test_nesting.py
Unit tests for NEST-CRAFT core geometric functions and optimization engine.
"""

import unittest
import numpy as np
from shapely.geometry import Polygon, box

from team_algoryxz.nest_craft.src.geometry import Part, Sheet, check_collision
from team_algoryxz.nest_craft.src.baseline import run_bottom_left_fill, place_part_bottom_left
from team_algoryxz.nest_craft.src.optimizer import run_simulated_annealing, calculate_solution_energy
from team_algoryxz.nest_craft.src.calculator import calculate_fabrication_savings

class TestNestingGeometry(unittest.TestCase):
    
    def setUp(self):
        # 100x50 rectangle
        self.rect_poly = Polygon([(0, 0), (100, 0), (100, 50), (0, 50)])
        self.part1 = Part(self.rect_poly, part_id="p1", quantity=1)
        self.sheet = Sheet(width=300.0, height=200.0, sheet_id=1)
        
    def test_part_normalization(self):
        # Shifted polygon should normalize to (0,0)
        shifted = Polygon([(50, 50), (150, 50), (150, 100), (50, 100)])
        p = Part(shifted, part_id="p_shift")
        self.assertAlmostEqual(p.base_polygon.bounds[0], 0.0)
        self.assertAlmostEqual(p.base_polygon.bounds[1], 0.0)
        self.assertAlmostEqual(p.width, 100.0)
        self.assertAlmostEqual(p.height, 50.0)
        
    def test_rotation(self):
        rot90 = self.part1.get_rotated(90.0)
        minx, miny, maxx, maxy = rot90.bounds
        self.assertAlmostEqual(minx, 0.0)
        self.assertAlmostEqual(miny, 0.0)
        self.assertAlmostEqual(maxx - minx, 50.0)
        self.assertAlmostEqual(maxy - miny, 100.0)
        
    def test_collision_detection(self):
        polyA = box(0, 0, 50, 50)
        polyB_disjoint = box(60, 0, 110, 50)
        polyC_overlap = box(25, 25, 75, 75)
        
        # Disjoint
        self.assertFalse(check_collision(polyB_disjoint, [polyA], clearance=0.0))
        # Overlapping
        self.assertTrue(check_collision(polyC_overlap, [polyA], clearance=0.0))
        # Clearance collision: polyB is 10mm away, clearance of 15mm should trigger collision
        self.assertTrue(check_collision(polyB_disjoint, [polyA], clearance=15.0))
        
    def test_sheet_containment(self):
        sheet = Sheet(100.0, 100.0)
        inside = box(10, 10, 50, 50)
        outside = box(80, 80, 120, 120)
        
        self.assertTrue(sheet.can_contain(inside))
        self.assertFalse(sheet.can_contain(outside))
        
    def test_bottom_left_fill_execution(self):
        parts = [
            Part(box(0, 0, 50, 40), "part_a", quantity=2),
            Part(box(0, 0, 30, 30), "part_b", quantity=3)
        ]
        sheets, stats = run_bottom_left_fill(
            parts, sheet_width=150.0, sheet_height=100.0, clearance=2.0
        )
        self.assertGreaterEqual(len(sheets), 1)
        self.assertEqual(stats["total_parts_nested"], 5)
        self.assertGreater(stats["utilization_pct"], 0.0)
        self.assertLessEqual(stats["utilization_pct"], 100.0)
        
    def test_simulated_annealing_optimizer(self):
        parts = [
            Part(box(0, 0, 60, 40), "part_1", quantity=2),
            Part(box(0, 0, 40, 30), "part_2", quantity=2)
        ]
        sheets, stats = run_simulated_annealing(
            parts, sheet_width=120.0, sheet_height=100.0,
            clearance=2.0, max_iterations=5, random_seed=42
        )
        self.assertGreaterEqual(len(sheets), 1)
        self.assertEqual(stats["total_parts_nested"], 4)
        self.assertGreater(stats["utilization_pct"], 0.0)
        
    def test_savings_calculator(self):
        res = calculate_fabrication_savings(
            annual_tonnes=100.0,
            steel_price_per_kg=60.0,
            scrap_sale_per_kg=30.0,
            baseline_utilization_pct=60.0,
            optimized_utilization_pct=75.0,
            software_monthly_fee_inr=3000.0
        )
        # 15 tonnes saved * 1000 kg * Rs 30/kg = Rs 4,50,000 gross savings
        self.assertAlmostEqual(res["results"]["annual_scrap_reduced_tonnes"], 15.0)
        self.assertAlmostEqual(res["results"]["gross_annual_savings_inr"], 450000.0)
        self.assertAlmostEqual(res["results"]["annual_software_subscription_cost_inr"], 36000.0)
        self.assertAlmostEqual(res["results"]["net_annual_profit_inr"], 414000.0)
        self.assertGreater(res["results"]["roi_multiple"], 10.0)

if __name__ == "__main__":
    unittest.main()
