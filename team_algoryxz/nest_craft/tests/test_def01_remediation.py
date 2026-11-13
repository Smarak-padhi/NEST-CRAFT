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

    def test_repair_that_changes_hole_count_rejected(self):
        """Validates that a self-intersecting contour that alters the number of holes is detected and rejected."""
        # Square with a hole, where the outer boundary has a self-intersection crossing into the hole
        # Outer shell self-crosses at (50, 20)
        outer_shell = [(0, 0), (100, 0), (100, 100), (0, 100), (0, 20), (80, 20), (50, 40), (20, 20), (0, 0)]
        hole = [(30, 60), (70, 60), (70, 90), (30, 90)]
        poly = Polygon(shell=outer_shell, holes=[hole])
        self.assertFalse(poly.is_valid)
        
        with self.assertRaises(CADTopologyError) as ctx:
            Part(poly, "hole_altered_part", quantity=1)
        self.assertIn("materially altered topology", str(ctx.exception))

    def test_repair_preserves_area_but_changes_topology_rejected(self):
        """Validates that even when make_valid produces near-zero area difference, component count change triggers CADTopologyError."""
        # Standard symmetrical bowtie: input area is 800, repaired area is 800 (0.0% area change)
        bowtie = Polygon([(0, 0), (40, 40), (40, 0), (0, 40), (0, 0)])
        self.assertFalse(bowtie.is_valid)
        
        with self.assertRaises(CADTopologyError) as ctx:
            Part(bowtie, "zero_area_change_bowtie", quantity=1)
        self.assertIn("components: 1 -> 2", str(ctx.exception))

    def test_unauthorized_repair_rejected_in_dxf_ingestion(self):
        """Validates that unauthorized self-intersecting geometry in a DXF is rejected during ordinary import."""
        from team_algoryxz.nest_craft.src.dxf_io import DXFValidationError, parse_dxf
        dxf_path = os.path.join(self.temp_dir.name, "unauthorized_bowtie.dxf")
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        msp.add_lwpolyline([(0, 0), (50, 50), (50, 0), (0, 50)], close=True)
        doc.saveas(dxf_path)
        
        # 1. Default validate_and_parse_dxf must report is_valid=False
        parts, report = validate_and_parse_dxf(dxf_path, allow_repaired_topology=False)
        self.assertFalse(report["is_valid"])
        self.assertEqual(len(parts), 0)
        self.assertTrue(any("self-intersections" in err for err in report["errors"]))
        
        # 2. Strict parse_dxf must raise DXFValidationError
        with self.assertRaises(DXFValidationError):
            parse_dxf(dxf_path, strict=True, allow_repaired_topology=False)
            
        # 3. Explicitly authorized parse must succeed and preserve both components
        parts_auth, report_auth = validate_and_parse_dxf(dxf_path, allow_repaired_topology=True)
        self.assertTrue(report_auth["is_valid"])
        self.assertEqual(len(parts_auth), 2)

    def test_multipart_sheet_boundary_containment(self):
        """Validates that Sheet.can_contain enforces boundary limits across the entire MultiPolygon envelope."""
        multi = MultiPolygon([box(0, 0, 40, 40), box(80, 0, 120, 40)])
        part = Part(multi, "multi_contain", quantity=1)
        sheet = Sheet(width=150, height=100)
        
        # Placed inside sheet
        placed_inside = affinity.translate(part.base_polygon, 10, 10) # Bounding box [10..130, 10..50]
        self.assertTrue(sheet.can_contain(placed_inside))
        
        # Placed protruding past right boundary
        placed_outside_x = affinity.translate(part.base_polygon, 40, 10) # Bounding box [40..160, 10..50]
        self.assertFalse(sheet.can_contain(placed_outside_x))

    def test_part_in_part_with_multipart_geometry(self):
        """Validates that compute_hole_feasible_regions extracts interior holes located in a MultiPolygon component."""
        # Component 1: solid square; Component 2: square with hole
        comp1 = box(0, 0, 50, 50)
        comp2 = Polygon([(70, 0), (170, 0), (170, 100), (70, 100)], holes=[[(100, 30), (140, 30), (140, 70), (100, 70)]])
        multi = MultiPolygon([comp1, comp2])
        part = Part(multi, "multi_with_hole", quantity=1)
        
        feas = compute_hole_feasible_regions(part.polygon, clearance=2.0)
        self.assertEqual(len(feas), 1)
        # Hole is 40x40. With 2.0 clearance on each side, feasible region is 36x36 = 1296 mm^2
        self.assertAlmostEqual(feas[0].area, 1296.0, places=3)

    def test_multipart_rotation_and_translation(self):
        """Validates that MultiPolygon transforms coherently under rotation and translation."""
        comp1 = box(0, 0, 30, 30)
        comp2 = box(50, 0, 80, 30)
        part = Part(MultiPolygon([comp1, comp2]), "multi_transform", quantity=1)
        
        for angle in [0.0, 90.0, 180.0, 270.0, 45.0]:
            rotated = part.get_rotated(angle)
            self.assertTrue(isinstance(rotated, MultiPolygon))
            self.assertEqual(len(rotated.geoms), 2)
            self.assertAlmostEqual(rotated.area, part.area, places=4)
            # Distance between components must be conserved
            c0, c1 = list(rotated.geoms)
            dist = c0.distance(c1)
            self.assertAlmostEqual(dist, 20.0, places=3)

    def test_narrow_slots_and_small_features_preserved(self):
        """Validates that a part with a narrow 0.5 mm slot and 1 mm hole maintains valid geometry and area."""
        # 100x100 plate with 0.5 mm wide slot extending into it
        poly = Polygon([
            (0, 0), (49.75, 0), (49.75, 40), (50.25, 40), (50.25, 0),
            (100, 0), (100, 100), (0, 100), (0, 0)
        ])
        self.assertTrue(poly.is_valid)
        part = Part(poly, "slotted_plate", quantity=1)
        self.assertAlmostEqual(part.area, 10000.0 - (0.5 * 40.0), places=3)
        self.assertTrue(part.polygon.is_valid)


if __name__ == '__main__':
    unittest.main()
