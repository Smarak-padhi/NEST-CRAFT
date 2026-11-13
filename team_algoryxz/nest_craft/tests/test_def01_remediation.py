"""
test_def01_remediation.py
Dedicated regression test suite for Stage D: DEF-01 Geometry Integrity Remediation.
Tests:
1. Valid MultiPolygon with two equal components (zero discarded material).
2. Valid MultiPolygon with unequal components.
3. Self-intersecting bow-tie producing two components (rejection vs authorized preservation).
4. Polygon with interior holes (full hole preservation).
5. Polygon repair that changes component count (detected & rejected).
6. Polygon repair that changes total area (detected & rejected).
7. DXF containing multiple independent parts (all parts & holes extracted).
8. Nesting and DXF export of every geometry type the application claims to support.
"""

import os
import math
import tempfile
import unittest
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, box, LineString
from shapely import affinity
import ezdxf

from team_algoryxz.nest_craft.src.geometry import (
    Part, Sheet, CADTopologyError, check_collision, compute_hole_feasible_regions
)
from team_algoryxz.nest_craft.src.baseline import run_bottom_left_fill
from team_algoryxz.nest_craft.src.optimizer import run_simulated_annealing
from team_algoryxz.nest_craft.src.dxf_io import validate_and_parse_dxf, export_nesting_to_dxf


class TestDEF01Remediation(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_multipolygon_two_equal_components(self):
        """Validates that a legitimate MultiPolygon with two equal components preserves all components."""
        box1 = box(0, 0, 30, 30)
        box2 = box(50, 0, 80, 30)
        multi = MultiPolygon([box1, box2])
        self.assertTrue(multi.is_valid)
        self.assertEqual(len(multi.geoms), 2)
        
        part = Part(multi, "multi_equal", quantity=1)
        self.assertTrue(isinstance(part.polygon, MultiPolygon))
        self.assertEqual(len(part.polygon.geoms), 2)
        # Total area must be 900 + 900 = 1800.0 mm^2 (Zero material discarded)
        self.assertAlmostEqual(part.area, 1800.0, places=4)
        self.assertAlmostEqual(part.width, 80.0, places=4)
        self.assertAlmostEqual(part.height, 30.0, places=4)
        
        # Test rotation: both components rotate together
        rotated = part.get_rotated(90.0)
        self.assertTrue(isinstance(rotated, MultiPolygon))
        self.assertEqual(len(rotated.geoms), 2)
        self.assertAlmostEqual(rotated.area, 1800.0, places=4)
        
        # Test collision detection: detects collision on both component locations
        sheet = Sheet(300, 300)
        # Place part at (10, 10): box1 at [10..40, 10..40], box2 at [60..90, 10..40]
        placed = affinity.translate(part.base_polygon, 10, 10)
        
        # Test collision on component 1
        coll_probe1 = box(15, 15, 25, 25)
        self.assertTrue(check_collision(coll_probe1, [placed], clearance=2.0))
        
        # Test collision on component 2
        coll_probe2 = box(65, 15, 75, 25)
        self.assertTrue(check_collision(coll_probe2, [placed], clearance=2.0))
        
        # In-between gap [40..60] has no material, probe should NOT collide if clearance permits
        probe_gap = box(44, 15, 56, 25) # 4mm away from each component
        self.assertFalse(check_collision(probe_gap, [placed], clearance=2.0))

    def test_valid_multipolygon_unequal_components(self):
        """Validates that a MultiPolygon with unequal components preserves both large and small components."""
        large_box = box(0, 0, 50, 50) # 2500 mm^2
        small_box = box(70, 0, 80, 10) # 100 mm^2
        multi = MultiPolygon([large_box, small_box])
        
        part = Part(multi, "multi_unequal", quantity=1)
        self.assertTrue(isinstance(part.polygon, MultiPolygon))
        self.assertEqual(len(part.polygon.geoms), 2)
        self.assertAlmostEqual(part.area, 2600.0, places=4)
        
        # Verify the small component was NOT dropped
        small_geom = min(part.polygon.geoms, key=lambda g: g.area)
        self.assertAlmostEqual(small_geom.area, 100.0, places=4)

    def test_self_intersecting_bowtie_two_components(self):
        """Validates that self-intersecting bow-tie is rejected by default, and preserved in full when authorized."""
        # Bow-tie polygon self-intersecting at (20, 20), nominal lobes total 800 mm^2
        bowtie = Polygon([(0, 0), (40, 40), (40, 0), (0, 40), (0, 0)])
        self.assertFalse(bowtie.is_valid)
        
        # 1. Unsanctioned ingestion MUST raise CADTopologyError
        with self.assertRaises(CADTopologyError) as ctx:
            Part(bowtie, "bowtie_unauthorized", quantity=1)
        self.assertIn("Geometry validation failed", str(ctx.exception))
        self.assertIn("materially altered topology", str(ctx.exception))
        
        # 2. Explicitly authorized ingestion preserves BOTH lobes as a MultiPolygon
        part = Part(bowtie, "bowtie_authorized", quantity=1, metadata={"allow_repaired_topology": True})
        self.assertTrue(isinstance(part.polygon, MultiPolygon))
        self.assertEqual(len(part.polygon.geoms), 2)
        self.assertAlmostEqual(part.area, 800.0, places=4)

    def test_polygon_with_interior_holes(self):
        """Validates that legitimate interior holes are 100% preserved and available for Part-in-Part nesting."""
        outer = [(0, 0), (120, 0), (120, 120), (0, 120)]
        hole = [(30, 30), (90, 30), (90, 90), (30, 90)]
        poly_with_hole = Polygon(shell=outer, holes=[hole])
        self.assertTrue(poly_with_hole.is_valid)
        
        part = Part(poly_with_hole, "plate_hole", quantity=1)
        self.assertTrue(isinstance(part.polygon, Polygon))
        self.assertEqual(len(part.polygon.interiors), 1)
        self.assertAlmostEqual(part.area, 14400.0 - 3600.0, places=4)
        
        # Hole feasible region extraction
        feas = compute_hole_feasible_regions(part.polygon, clearance=3.0)
        self.assertEqual(len(feas), 1)
        self.assertAlmostEqual(feas[0].area, (60 - 6) * (60 - 6), places=4) # 54x54 = 2916 mm^2

    def test_polygon_repair_changes_component_count(self):
        """Validates that a complex self-intersecting polygon decomposing into 3 components is rejected."""
        # Figure-8 with 2 waist crossings producing 3 lobes
        coords = [
            (0, 0), (20, 20), (40, 0), (60, 20), (80, 0),
            (80, 40), (60, 20), (40, 40), (20, 20), (0, 40), (0, 0)
        ]
        poly = Polygon(coords)
        self.assertFalse(poly.is_valid)
        
        with self.assertRaises(CADTopologyError) as ctx:
            Part(poly, "three_lobe_part", quantity=1)
        self.assertIn("materially altered topology", str(ctx.exception))

    def test_polygon_repair_changes_total_area(self):
        """Validates that a self-intersecting polygon whose repair changes area by >5% is rejected."""
        # Self-intersecting overlap that alters area
        coords = [(0, 0), (50, 0), (50, 50), (20, 50), (20, 20), (70, 20), (70, 70), (0, 70), (0, 0)]
        poly = Polygon(coords)
        self.assertFalse(poly.is_valid)
        
        with self.assertRaises(CADTopologyError):
            Part(poly, "area_altered_part", quantity=1)

    def test_dxf_containing_multiple_independent_parts(self):
        """Validates that a DXF drawing containing multiple independent parts extracts each part separately with holes."""
        dxf_path = os.path.join(self.temp_dir.name, "multi_part_drawing.dxf")
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Part 1: Gusset plate at (0, 0)
        msp.add_lwpolyline([(0, 0), (100, 0), (100, 80), (0, 80)], close=True)
        # Part 2: Flange with hole at (150, 0)
        msp.add_lwpolyline([(150, 0), (270, 0), (270, 120), (150, 120)], close=True)
        msp.add_circle((210, 60), radius=20) # Hole in Part 2
        # Part 3: Small bracket at (320, 0)
        msp.add_lwpolyline([(320, 0), (380, 0), (380, 40), (320, 40)], close=True)
        doc.saveas(dxf_path)
        
        parts, report = validate_and_parse_dxf(dxf_path)
        self.assertTrue(report["is_valid"])
        self.assertEqual(len(parts), 3) # Exactly 3 parts
        self.assertEqual(report["holes_extracted_count"], 1)
        
        # Part 2 must contain the circular hole
        part_with_hole = next(p for p in parts if len(p.polygon.interiors) == 1)
        self.assertAlmostEqual(part_with_hole.area, (120 * 120) - (math.pi * 20**2), delta=50.0)

    def test_nesting_and_dxf_export_all_supported_geometries(self):
        """
        Comprehensive test nesting all claimed geometry types:
        - Simple Polygon
        - Polygon with Holes
        - Valid MultiPolygon (equal components)
        - Valid MultiPolygon (unequal components)
        - Authorized repaired MultiPolygon
        Verifies end-to-end nesting, zero component loss, and valid DXF export.
        """
        parts = [
            Part(box(0, 0, 80, 60), "simple_rect", quantity=1),
            Part(Polygon([(0, 0), (100, 0), (100, 100), (0, 100)], holes=[[(20, 20), (80, 20), (80, 80), (20, 80)]]), "parent_with_hole", quantity=1),
            Part(MultiPolygon([box(0, 0, 30, 30), box(40, 0, 70, 30)]), "multi_equal", quantity=1),
            Part(MultiPolygon([box(0, 0, 40, 40), box(50, 0, 60, 20)]), "multi_unequal", quantity=1),
            Part(Polygon([(0, 0), (30, 30), (30, 0), (0, 30), (0, 0)]), "repaired_bowtie", quantity=1, metadata={"allow_repaired_topology": True}),
            Part(box(0, 0, 35, 35), "child_in_hole", quantity=1) # Eligible to nest inside parent hole
        ]
        
        total_input_area = sum(p.area for p in parts)
        
        sheets, stats = run_bottom_left_fill(
            parts, sheet_width=400.0, sheet_height=300.0,
            clearance=3.0, allow_part_in_part=True
        )
        
        self.assertEqual(stats["unplaced_parts"], 0)
        self.assertGreaterEqual(stats["parts_nested_in_holes"], 1)
        
        # Export to DXF
        export_path = os.path.join(self.temp_dir.name, "all_geometries_export.dxf")
        export_nesting_to_dxf(sheets, export_path)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify exported DXF structure via ezdxf audit
        doc = ezdxf.readfile(export_path)
        auditor = doc.audit()
        self.assertEqual(len(auditor.errors), 0)
        self.assertEqual(len(auditor.fixes), 0)
        
        msp = doc.modelspace()
        layers = {e.dxf.layer for e in msp}
        self.assertIn("SHEET_BOUNDARY", layers)
        self.assertIn("CUT_CONTOUR", layers)
        self.assertIn("HOLE_CONTOUR", layers)
        self.assertIn("PART_IN_PART_CHILD", layers)
        self.assertIn("0", layers) # Disclaimer text
        
        # Verify all LWPOLYLINE contours are closed
        for e in msp:
            if e.dxftype() == 'LWPOLYLINE':
                self.assertTrue(e.is_closed)


if __name__ == '__main__':
    unittest.main()
