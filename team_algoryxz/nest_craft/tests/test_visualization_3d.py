"""
test_visualization_3d.py
Unit and integration tests for NEST-CRAFT 3D CAD visualization and extrusion module.
Covers polygon extrusion, MultiPolygon extrusion, interior-hole preservation,
multi-sheet isolation, coordinate/rotation preservation, invalid geometry rejection,
and thickness validation.
"""

import unittest
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, box, Point, LineString

from team_algoryxz.nest_craft.src.geometry import Part, Sheet
from team_algoryxz.nest_craft.src.visualization_3d import (
    extrude_polygon_3d,
    extrude_single_polygon,
    triangulate_polygon_2d,
    build_sheet_3d_scene,
    create_sheet_bed_mesh,
    create_remnant_box_mesh,
    create_3d_viewport_figure,
    create_multi_sheet_3d_figure,
    ExtrudedPart3D,
    InvalidGeometry3DError,
    MissingThicknessError,
    MILD_STEEL_DENSITY_KG_MM3
)


class Test3DVisualization(unittest.TestCase):

    def setUp(self):
        # 100 x 50 rectangular solid
        self.rect_poly = Polygon([(0, 0), (100, 0), (100, 50), (0, 50)])

        # 100 x 100 square with 40 x 40 centered interior hole
        self.hole_poly = Polygon(
            [(0, 0), (100, 0), (100, 100), (0, 100)],
            [[(30, 30), (70, 30), (70, 70), (30, 70)]]
        )

        # MultiPolygon with two disjoint components
        poly1 = Polygon([(0, 0), (30, 0), (30, 30), (0, 30)])
        poly2 = Polygon([(50, 50), (90, 50), (90, 90), (50, 90)])
        self.multipoly = MultiPolygon([poly1, poly2])

        # Standard test sheet
        self.sheet = Sheet(width=800.0, height=500.0, sheet_id=1)

    # 1. Polygon extrusion test
    def test_polygon_extrusion(self):
        thickness = 8.0
        z_base = 0.0
        mesh = extrude_polygon_3d(self.rect_poly, thickness=thickness, z_base=z_base, part_id="test_rect")

        self.assertIsInstance(mesh, ExtrudedPart3D)
        self.assertEqual(mesh.part_id, "test_rect")
        self.assertAlmostEqual(mesh.thickness, 8.0)
        self.assertAlmostEqual(mesh.area_2d, 5000.0)

        expected_vol = 5000.0 * 8.0
        self.assertAlmostEqual(mesh.volume_3d, expected_vol)
        expected_weight = expected_vol * MILD_STEEL_DENSITY_KG_MM3
        self.assertAlmostEqual(mesh.weight_kg, round(expected_weight, 4))

        # Check vertex coordinates bounds in 3D
        v = mesh.vertices
        self.assertGreater(len(v), 0)
        self.assertAlmostEqual(float(np.min(v[:, 0])), 0.0)
        self.assertAlmostEqual(float(np.max(v[:, 0])), 100.0)
        self.assertAlmostEqual(float(np.min(v[:, 1])), 0.0)
        self.assertAlmostEqual(float(np.max(v[:, 1])), 50.0)
        self.assertAlmostEqual(float(np.min(v[:, 2])), 0.0)
        self.assertAlmostEqual(float(np.max(v[:, 2])), 8.0)

        # Check Plotly mesh export
        p_mesh = mesh.to_plotly_mesh()
        self.assertIsNotNone(p_mesh)
        self.assertEqual(p_mesh.name, "test_rect")

    # 2. MultiPolygon extrusion test
    def test_multipolygon_extrusion(self):
        thickness = 5.0
        mesh = extrude_polygon_3d(self.multipoly, thickness=thickness, part_id="test_multipoly")

        self.assertIsInstance(mesh, ExtrudedPart3D)
        expected_area = 30*30 + 40*40  # 900 + 1600 = 2500
        self.assertAlmostEqual(mesh.area_2d, expected_area)
        self.assertAlmostEqual(mesh.volume_3d, expected_area * thickness)

        # Spans both components: X from 0 to 90, Y from 0 to 90
        v = mesh.vertices
        self.assertAlmostEqual(float(np.min(v[:, 0])), 0.0)
        self.assertAlmostEqual(float(np.max(v[:, 0])), 90.0)
        self.assertAlmostEqual(float(np.min(v[:, 1])), 0.0)
        self.assertAlmostEqual(float(np.max(v[:, 1])), 90.0)
        self.assertAlmostEqual(float(np.max(v[:, 2])), 5.0)

    # 3. Interior-hole preservation test
    def test_interior_hole_preservation(self):
        thickness = 10.0
        mesh = extrude_polygon_3d(self.hole_poly, thickness=thickness, part_id="test_with_hole")

        self.assertEqual(mesh.holes_count, 1)
        expected_net_area = 10000.0 - 1600.0  # 8400.0
        self.assertAlmostEqual(mesh.area_2d, expected_net_area)
        self.assertAlmostEqual(mesh.volume_3d, expected_net_area * thickness)

        # Verify interior hole wireframe edges exist
        hole_edges = [
            (p1, p2) for p1, p2 in mesh.edge_lines
            if (30.0 <= p1[0] <= 70.0 and 30.0 <= p1[1] <= 70.0)
        ]
        self.assertGreater(len(hole_edges), 0, "Hole boundary wireframe edges must be preserved")

        # Test multi-hole polygon (flange plate with 4 bolt holes)
        flange_poly = Polygon(
            [(0, 0), (200, 0), (200, 200), (0, 200)],
            [
                [(20, 20), (40, 20), (40, 40), (20, 40)],
                [(160, 20), (180, 20), (180, 40), (160, 40)],
                [(160, 160), (180, 160), (180, 180), (160, 180)],
                [(20, 160), (40, 160), (40, 180), (20, 180)]
            ]
        )
        flange_mesh = extrude_polygon_3d(flange_poly, thickness=6.0, part_id="flange_4holes")
        self.assertEqual(flange_mesh.holes_count, 4)
        expected_flange_area = 40000.0 - 4 * 400.0  # 38400.0
        self.assertAlmostEqual(flange_mesh.area_2d, expected_flange_area)
        self.assertAlmostEqual(flange_mesh.volume_3d, 38400.0 * 6.0)

    # 4. Multiple-sheet visualization test
    def test_multiple_sheet_visualization(self):
        sheet1 = Sheet(width=800.0, height=500.0, sheet_id=1)
        sheet2 = Sheet(width=800.0, height=500.0, sheet_id=2)

        p1_placed = box(10, 10, 110, 60)
        p2_placed = box(20, 20, 120, 70)
        sheet1.placed_parts.append(("p1", p1_placed, 0.0))
        sheet2.placed_parts.append(("p2", p2_placed, 90.0))

        # Build individual scenes
        scene1 = build_sheet_3d_scene(sheet1, part_thickness=6.0)
        scene2 = build_sheet_3d_scene(sheet2, part_thickness=6.0)

        self.assertEqual(scene1["sheet_id"], 1)
        self.assertEqual(scene2["sheet_id"], 2)
        self.assertEqual(len(scene1["part_meshes"]), 1)
        self.assertEqual(len(scene2["part_meshes"]), 1)
        self.assertEqual(scene1["part_meshes"][0].part_id, "p1")
        self.assertEqual(scene2["part_meshes"][0].part_id, "p2")

        # Multi-sheet combined figure
        fig_multi = create_multi_sheet_3d_figure([sheet1, sheet2], part_thickness=6.0)
        self.assertIsNotNone(fig_multi)
        # Should have traces for sheet 1 bed, border, parts, and sheet 2 bed, border, parts
        self.assertGreaterEqual(len(fig_multi.data), 4)

    # 5. Coordinate and orientation preservation test
    def test_coordinate_and_orientation_preservation(self):
        from shapely import affinity
        # Place part at offset (250, 150) and rotate 45 degrees
        base = Polygon([(0, 0), (80, 0), (80, 40), (0, 40)])
        rotated = affinity.rotate(base, 45.0, origin=(0, 0))
        translated = affinity.translate(rotated, xoff=250.0, yoff=150.0)

        mesh = extrude_polygon_3d(
            translated,
            thickness=6.0,
            part_id="rotated_part_45",
            rotation_deg=45.0
        )

        self.assertEqual(mesh.rotation_deg, 45.0)
        minx, miny, maxx, maxy = translated.bounds
        self.assertAlmostEqual(mesh.bounds[0], minx, places=3)
        self.assertAlmostEqual(mesh.bounds[1], miny, places=3)
        self.assertAlmostEqual(mesh.bounds[2], maxx, places=3)
        self.assertAlmostEqual(mesh.bounds[3], maxy, places=3)

        # Test part-in-part parent-child relationship
        sheet = Sheet(width=800.0, height=500.0, sheet_id=1)
        parent_poly = Polygon([(0, 0), (200, 0), (200, 200), (0, 200)], [[(50, 50), (150, 50), (150, 150), (50, 150)]])
        child_poly = Polygon([(60, 60), (140, 60), (140, 140), (60, 140)])

        sheet.placed_parts.append(("parent_p1", parent_poly, 0.0))
        sheet.placed_parts.append(("child_p2", child_poly, 0.0))
        sheet.part_in_part_assignments["child_p2"] = "parent_p1"

        scene = build_sheet_3d_scene(sheet, part_thickness=6.0)
        self.assertEqual(scene["nested_in_holes_count"], 1)

        child_mesh = next(m for m in scene["part_meshes"] if m.part_id == "child_p2")
        self.assertTrue(child_mesh.is_child)
        self.assertEqual(child_mesh.parent_id, "parent_p1")

    # 6. Invalid geometry handling test
    def test_invalid_geometry_handling(self):
        # None geometry
        with self.assertRaises(InvalidGeometry3DError):
            extrude_polygon_3d(None, thickness=5.0)

        # Empty geometry
        with self.assertRaises(InvalidGeometry3DError):
            extrude_polygon_3d(Polygon(), thickness=5.0)

        # Non-polygonal geometry (LineString, Point)
        with self.assertRaises(InvalidGeometry3DError):
            extrude_polygon_3d(Point(10, 10), thickness=5.0)

        with self.assertRaises(InvalidGeometry3DError):
            extrude_polygon_3d(LineString([(0, 0), (10, 10)]), thickness=5.0)

        # Zero area polygon
        with self.assertRaises(InvalidGeometry3DError):
            zero_area = Polygon([(0, 0), (10, 0), (0, 0)])
            extrude_polygon_3d(zero_area, thickness=5.0)

    # 7. Missing thickness handling test
    def test_missing_thickness_handling(self):
        # None thickness
        with self.assertRaises(MissingThicknessError):
            extrude_polygon_3d(self.rect_poly, thickness=None)

        # Zero thickness
        with self.assertRaises(MissingThicknessError):
            extrude_polygon_3d(self.rect_poly, thickness=0.0)

        # Negative thickness
        with self.assertRaises(MissingThicknessError):
            extrude_polygon_3d(self.rect_poly, thickness=-4.0)

        # Non-finite thickness
        with self.assertRaises(MissingThicknessError):
            extrude_polygon_3d(self.rect_poly, thickness=float('nan'))

        with self.assertRaises(MissingThicknessError):
            extrude_polygon_3d(self.rect_poly, thickness=float('inf'))

    # 8. Viewport figure and camera preset test
    def test_viewport_figure_and_presets(self):
        self.sheet.placed_parts.append(("p1", box(10, 10, 100, 60), 0.0))

        for preset in ["isometric", "top", "front", "side"]:
            fig = create_3d_viewport_figure(
                self.sheet,
                part_thickness=6.0,
                sheet_thickness=2.0,
                camera_preset=preset,
                show_sheet_plate=True,
                show_remnant=True,
                show_edges=True
            )
            self.assertIsNotNone(fig)
            self.assertIn("scene", fig.layout)

        # Test part visibility filter
        fig_filtered = create_3d_viewport_figure(
            self.sheet,
            part_thickness=6.0,
            visible_part_ids=[]  # Hide all parts
        )
        part_trace_names = [t.name for t in fig_filtered.data if hasattr(t, "name")]
        self.assertNotIn("p1", part_trace_names)


if __name__ == "__main__":
    unittest.main()
