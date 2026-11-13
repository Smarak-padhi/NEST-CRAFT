"""
test_dxf_reliability.py
Comprehensive automated test suite for DXF parsing reliability and CAD geometry validation.
Tests LWPOLYLINE, POLYLINE, LINE, ARC, CIRCLE, SPLINE, ELLIPSE, interior hole extraction,
unsupported entity reporting, and export round-trips.
"""

import os
import tempfile
import unittest
import math
from typing import Tuple, Any, List
import ezdxf
from shapely.geometry import Polygon

from team_algoryxz.nest_craft.src.geometry import Part, Sheet
from team_algoryxz.nest_craft.src.dxf_io import (
    validate_and_parse_dxf,
    parse_dxf,
    export_nesting_to_dxf,
    DXFValidationError
)

class TestDXFReliability(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        
    def tearDown(self):
        self.temp_dir.cleanup()
        
    def _create_temp_dxf(self, filename: str) -> Tuple[str, Any, Any]:
        path = os.path.join(self.temp_dir.name, filename)
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        return path, doc, msp
        
    def test_circle_entity_parsing(self):
        """Validates that CIRCLE entities are converted to closed polygons with accurate area."""
        path, doc, msp = self._create_temp_dxf("circle_washer.dxf")
        radius = 25.0
        msp.add_circle((50.0, 50.0), radius=radius)
        doc.saveas(path)
        
        parts, report = validate_and_parse_dxf(path)
        self.assertTrue(report["is_valid"])
        self.assertEqual(len(parts), 1)
        expected_area = math.pi * (radius ** 2)
        # Tessellated polygon area should be within 1.5% of exact analytical circle area
        self.assertAlmostEqual(parts[0].area, expected_area, delta=expected_area * 0.015)
        self.assertAlmostEqual(parts[0].width, 50.0, delta=0.5)
        self.assertAlmostEqual(parts[0].height, 50.0, delta=0.5)

    def test_lwpolyline_with_arc_bulge(self):
        """Validates that LWPOLYLINE with arc bulge preserves curved contours."""
        path, doc, msp = self._create_temp_dxf("curved_plate.dxf")
        # Rectangle with a semi-circular bulging side (bulge=1.0 on side from (20,0) to (20,20))
        points = [(0, 0), (20, 0, 0, 0, 1.0), (20, 20), (0, 20)]
        msp.add_lwpolyline(points, close=True)
        doc.saveas(path)
        
        parts, report = validate_and_parse_dxf(path)
        self.assertTrue(report["is_valid"])
        self.assertEqual(len(parts), 1)
        # Base rectangle is 20x20 = 400; semi-circle bulge radius 10 adds 0.5 * pi * 10^2 ~ 157
        self.assertGreater(parts[0].area, 500.0)
        self.assertGreater(parts[0].width, 25.0) # Width must exceed 20mm due to bulge

    def test_line_and_arc_stitching(self):
        """Validates that disconnected LINE and ARC entities are stitched into a closed polygon."""
        path, doc, msp = self._create_temp_dxf("stitched_cam.dxf")
        # Semicircular cam: ARC from 0 to 180 degrees at radius 30, and bottom LINE
        msp.add_arc((100, 100), radius=30, start_angle=0, end_angle=180)
        msp.add_line((130, 100), (70, 100))
        doc.saveas(path)
        
        parts, report = validate_and_parse_dxf(path)
        self.assertTrue(report["is_valid"])
        self.assertEqual(len(parts), 1)
        expected_area = 0.5 * math.pi * (30.0 ** 2) # ~1413.7
        self.assertAlmostEqual(parts[0].area, expected_area, delta=expected_area * 0.02)

    def test_spline_and_ellipse_parsing(self):
        """Validates that SPLINE and ELLIPSE entities are parsed into valid closed polygons."""
        path, doc, msp = self._create_temp_dxf("spline_ellipse.dxf")
        # Closed spline
        msp.add_spline([(0, 0), (40, 0), (40, 30), (0, 30), (0, 0)])
        # Ellipse
        msp.add_ellipse((150, 50), major_axis=(30, 0), ratio=0.6)
        doc.saveas(path)
        
        parts, report = validate_and_parse_dxf(path)
        self.assertTrue(report["is_valid"])
        self.assertEqual(len(parts), 2)
        for p in parts:
            self.assertTrue(p.polygon.is_valid)
            self.assertGreater(p.area, 500.0)

    def test_interior_hole_extraction(self):
        """Validates that concentric outer boundary and inner cutouts are extracted as a single part with holes."""
        path, doc, msp = self._create_temp_dxf("flange_with_holes.dxf")
        # Outer boundary: 120x120 square
        msp.add_lwpolyline([(0, 0), (120, 0), (120, 120), (0, 120)], close=True)
        # Center circular cutout: radius 25 at (60, 60)
        msp.add_circle((60, 60), radius=25)
        # 4 corner bolt holes: radius 4
        for bx, by in [(20, 20), (100, 20), (100, 100), (20, 100)]:
            msp.add_circle((bx, by), radius=4)
        doc.saveas(path)
        
        parts, report = validate_and_parse_dxf(path)
        self.assertTrue(report["is_valid"])
        # Must be 1 part with 5 interior holes, NOT 6 separate parts!
        self.assertEqual(len(parts), 1)
        self.assertEqual(len(parts[0].base_polygon.interiors), 5)
        self.assertEqual(report["holes_extracted_count"], 5)
        
        # Net area must be gross square minus cutout holes
        gross_area = 120 * 120 # 14400
        center_hole_area = math.pi * (25 ** 2) # ~1963.5
        bolt_holes_area = 4 * math.pi * (4 ** 2) # ~201.1
        expected_net = gross_area - center_hole_area - bolt_holes_area
        self.assertAlmostEqual(parts[0].area, expected_net, delta=expected_net * 0.02)

    def test_unsupported_3d_entities(self):
        """Validates that 3D entities like 3DFACE are flagged in validation report."""
        path, doc, msp = self._create_temp_dxf("mesh_drawing.dxf")
        msp.add_3dface([(0, 0, 0), (50, 0, 0), (50, 50, 0), (0, 50, 0)])
        doc.saveas(path)
        
        parts, report = validate_and_parse_dxf(path)
        self.assertIn("3DFACE", report["unsupported_3d_entities"])
        self.assertFalse(report["is_valid"]) # No 2D cutting contours
        self.assertEqual(len(parts), 0)

    def test_unclosed_segments_validation(self):
        """Validates that dangling, unclosed line segments are detected and reported."""
        path, doc, msp = self._create_temp_dxf("unclosed_box.dxf")
        # 3 sides of a rectangle, missing 4th side
        msp.add_line((0, 0), (100, 0))
        msp.add_line((100, 0), (100, 50))
        msp.add_line((100, 50), (0, 50))
        doc.saveas(path)
        
        parts, report = validate_and_parse_dxf(path)
        self.assertFalse(report["is_valid"])
        self.assertGreater(report["unclosed_segments_count"], 0)
        self.assertEqual(len(parts), 0)
        
        # In strict mode, parse_dxf should raise DXFValidationError
        with self.assertRaises(DXFValidationError):
            parse_dxf(path, strict=True)

    def test_corrupt_file_handling(self):
        """Validates that a corrupt non-DXF file returns clear validation errors."""
        corrupt_path = os.path.join(self.temp_dir.name, "corrupt.dxf")
        with open(corrupt_path, "w") as f:
            f.write("NOT A VALID DXF HEADER OR CONTENT")
            
        parts, report = validate_and_parse_dxf(corrupt_path)
        self.assertFalse(report["is_valid"])
        self.assertGreater(len(report["errors"]), 0)
        self.assertEqual(len(parts), 0)

    def test_export_round_trip_with_holes(self):
        """Validates that exporting nested parts with holes preserves hole contours upon re-import."""
        path, doc, msp = self._create_temp_dxf("plate_with_hole.dxf")
        msp.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        msp.add_circle((50, 50), radius=15)
        doc.saveas(path)
        
        parts = parse_dxf(path)
        self.assertEqual(len(parts), 1)
        self.assertEqual(len(parts[0].base_polygon.interiors), 1)
        
        # Place on sheet
        sheet = Sheet(width=300, height=200, sheet_id=1)
        sheet.placed_parts.append(("part_1", parts[0].base_polygon, 0.0))
        
        export_path = os.path.join(self.temp_dir.name, "exported_sheet.dxf")
        export_nesting_to_dxf([sheet], export_path)
        self.assertTrue(os.path.exists(export_path))
        
        # Re-import exported DXF and verify holes are present
        reimported_parts, re_report = validate_and_parse_dxf(export_path)
        # Should find sheet boundary (no holes) and placed part (with 1 hole)
        parts_with_holes = [p for p in reimported_parts if len(p.base_polygon.interiors) == 1]
        self.assertEqual(len(parts_with_holes), 1)
        self.assertAlmostEqual(parts_with_holes[0].area, parts[0].area, delta=parts[0].area * 0.02)

if __name__ == "__main__":
    unittest.main()
