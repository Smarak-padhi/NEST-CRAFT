"""
generate_dxf_test_corpus.py
Constructs a comprehensive, reproducible CAD edge-case test corpus for NEST-CRAFT.
All files are synthetically generated using ezdxf with documented provenance.
Covers:
  1. Closed polylines
  2. Open contours (dangling lines with gaps)
  3. Bulged polylines and arcs
  4. Circles and concentric interior cutouts
  5. Splines (B-spline curves)
  6. Disconnected multiple components
  7. Nested holes / island-in-hole topology
  8. Very narrow slots (high aspect ratio)
  9. Small cutouts (sub-kerf apertures)
  10. Self-intersecting contours (bow-tie / figure-8)
  11. Unsupported 3D entities (3DFACE, MESH)
  12. Duplicate contours (superimposed lines)
  13. Overlapping contours
  14. Large-coordinate drawings (civil/GIS coordinates)
  15. AutoCAD Release 12 (AC1009 legacy format)
  16. AutoCAD 2018 (AC1032 modern format)
"""

import os
import math
import ezdxf

def generate_corpus(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []

    # Case 01: Standard Closed Polyline (Rectangular gusset with chamfer)
    doc01 = ezdxf.new('R2010')
    msp01 = doc01.modelspace()
    coords01 = [(0, 0), (150, 0), (150, 80), (120, 100), (0, 100)]
    msp01.add_lwpolyline(coords01, close=True)
    p01 = os.path.join(output_dir, "case01_closed_poly.dxf")
    doc01.saveas(p01)
    generated_files.append(p01)

    # Case 02: Open Contour (Unclosed with 3mm gap)
    doc02 = ezdxf.new('R2010')
    msp02 = doc02.modelspace()
    msp02.add_line((0, 0), (100, 0))
    msp02.add_line((100, 0), (100, 80))
    msp02.add_line((100, 80), (0, 80))
    msp02.add_line((0, 80), (0, 3.0)) # 3.0mm gap to (0, 0)
    p02 = os.path.join(output_dir, "case02_open_contour.dxf")
    doc02.saveas(p02)
    generated_files.append(p02)

    # Case 03: Bulged Polylines & Arcs (Rounded corner plate)
    doc03 = ezdxf.new('R2010')
    msp03 = doc03.modelspace()
    # (x, y, start_width, end_width, bulge)
    # bulge = tan(included_angle / 4). For 90-degree corner, bulge = tan(pi/8) ≈ 0.41421356
    b = math.tan(math.pi / 8.0)
    coords03 = [
        (0, 0, 0, 0, 0),
        (120, 0, 0, 0, b),
        (140, 20, 0, 0, 0),
        (140, 100, 0, 0, 0),
        (0, 100, 0, 0, 0)
    ]
    msp03.add_lwpolyline(coords03, format='xyseb', close=True)
    p03 = os.path.join(output_dir, "case03_bulged_arcs.dxf")
    doc03.saveas(p03)
    generated_files.append(p03)

    # Case 04: Circles & Holes (200x150 plate with two 30mm diameter circular cutouts)
    doc04 = ezdxf.new('R2010')
    msp04 = doc04.modelspace()
    msp04.add_lwpolyline([(0, 0), (200, 0), (200, 150), (0, 150)], close=True)
    msp04.add_circle((50, 75), radius=15.0)
    msp04.add_circle((150, 75), radius=15.0)
    p04 = os.path.join(output_dir, "case04_circles_holes.dxf")
    doc04.saveas(p04)
    generated_files.append(p04)

    # Case 05: Splines (Curved organic profile)
    doc05 = ezdxf.new('R2010')
    msp05 = doc05.modelspace()
    spline_pts = [
        (0, 0), (40, 20), (80, 5), (120, 30),
        (160, 10), (180, 60), (140, 90), (90, 70),
        (30, 85), (0, 50), (0, 0)
    ]
    msp05.add_spline(fit_points=spline_pts)
    p05 = os.path.join(output_dir, "case05_splines.dxf")
    doc05.saveas(p05)
    generated_files.append(p05)

    # Case 06: Multiple Disconnected Components (Two separate gusset brackets)
    doc06 = ezdxf.new('R2010')
    msp06 = doc06.modelspace()
    # Bracket A
    msp06.add_lwpolyline([(0, 0), (80, 0), (80, 60), (0, 60)], close=True)
    # Bracket B (50mm apart)
    msp06.add_lwpolyline([(130, 0), (210, 0), (210, 60), (130, 60)], close=True)
    p06 = os.path.join(output_dir, "case06_disconnected_components.dxf")
    doc06.saveas(p06)
    generated_files.append(p06)

    # Case 07: Nested Holes (Outer plate, large hole, solid island, inner hole)
    doc07 = ezdxf.new('R2010')
    msp07 = doc07.modelspace()
    # Depth 0: Outer boundary (300x300)
    msp07.add_lwpolyline([(0, 0), (300, 0), (300, 300), (0, 300)], close=True)
    # Depth 1: Hole (200x200) inside outer boundary
    msp07.add_lwpolyline([(50, 50), (250, 50), (250, 250), (50, 250)], close=True)
    # Depth 2: Solid island (140x140) inside hole
    msp07.add_lwpolyline([(80, 80), (220, 80), (220, 220), (80, 220)], close=True)
    # Depth 3: Hole (60x60) inside solid island
    msp07.add_lwpolyline([(120, 120), (180, 120), (180, 180), (120, 180)], close=True)
    p07 = os.path.join(output_dir, "case07_nested_holes.dxf")
    doc07.saveas(p07)
    generated_files.append(p07)

    # Case 08: Narrow Slots (200x100 plate with a 0.8mm x 60mm thermal expansion slot)
    doc08 = ezdxf.new('R2010')
    msp08 = doc08.modelspace()
    msp08.add_lwpolyline([(0, 0), (200, 0), (200, 100), (0, 100)], close=True)
    # Narrow slot cutout: x in [70, 130], y in [49.6, 50.4] -> 60mm long, 0.8mm wide
    msp08.add_lwpolyline([(70, 49.6), (130, 49.6), (130, 50.4), (70, 50.4)], close=True)
    p08 = os.path.join(output_dir, "case08_narrow_slots.dxf")
    doc08.saveas(p08)
    generated_files.append(p08)

    # Case 09: Small Cutouts (100x100 plate with 1.5mm diameter pilot holes)
    doc09 = ezdxf.new('R2010')
    msp09 = doc09.modelspace()
    msp09.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
    msp09.add_circle((20, 20), radius=0.75) # dia = 1.5mm
    msp09.add_circle((80, 20), radius=0.75)
    msp09.add_circle((50, 80), radius=0.75)
    p09 = os.path.join(output_dir, "case09_small_cutouts.dxf")
    doc09.saveas(p09)
    generated_files.append(p09)

    # Case 10: Self-Intersecting Contours (Bow-tie polygon)
    doc10 = ezdxf.new('R2010')
    msp10 = doc10.modelspace()
    msp10.add_lwpolyline([(0, 0), (100, 100), (0, 100), (100, 0)], close=True)
    p10 = os.path.join(output_dir, "case10_self_intersecting.dxf")
    doc10.saveas(p10)
    generated_files.append(p10)

    # Case 11: Unsupported 3D Entities (2D plate with 3DFACE and POINT)
    doc11 = ezdxf.new('R2010')
    msp11 = doc11.modelspace()
    msp11.add_lwpolyline([(0, 0), (120, 0), (120, 80), (0, 80)], close=True)
    msp11.add_3dface([(0, 0, 10), (50, 0, 20), (50, 50, 20), (0, 50, 10)])
    msp11.add_point((60, 40))
    p11 = os.path.join(output_dir, "case11_unsupported_3d.dxf")
    doc11.saveas(p11)
    generated_files.append(p11)

    # Case 12: Duplicate Superimposed Contours
    doc12 = ezdxf.new('R2010')
    msp12 = doc12.modelspace()
    # Identical 100x100 square drawn twice
    msp12.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
    msp12.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
    p12 = os.path.join(output_dir, "case12_duplicate_contours.dxf")
    doc12.saveas(p12)
    generated_files.append(p12)

    # Case 13: Overlapping Contours
    doc13 = ezdxf.new('R2010')
    msp13 = doc13.modelspace()
    msp13.add_lwpolyline([(0, 0), (100, 0), (100, 80), (0, 80)], close=True)
    msp13.add_lwpolyline([(50, 20), (150, 20), (150, 100), (50, 100)], close=True)
    p13 = os.path.join(output_dir, "case13_overlapping_contours.dxf")
    doc13.saveas(p13)
    generated_files.append(p13)

    # Case 14: Large Coordinate Frame (Civil/GIS coordinate scale: offset by 500,000 mm)
    doc14 = ezdxf.new('R2010')
    msp14 = doc14.modelspace()
    ox, oy = 500000.0, 800000.0
    msp14.add_lwpolyline([(ox, oy), (ox + 120, oy), (ox + 120, oy + 70), (ox, oy + 70)], close=True)
    p14 = os.path.join(output_dir, "case14_large_coordinates.dxf")
    doc14.saveas(p14)
    generated_files.append(p14)

    # Case 15: AutoCAD Release 12 Format (AC1009 legacy POLYLINE)
    doc15 = ezdxf.new('R12')
    msp15 = doc15.modelspace()
    msp15.add_polyline2d([(0, 0), (140, 0), (140, 90), (0, 90)], close=True)
    p15 = os.path.join(output_dir, "case15_dxf_version_r12.dxf")
    doc15.saveas(p15)
    generated_files.append(p15)

    # Case 16: Modern AutoCAD 2018 Format (AC1032)
    doc16 = ezdxf.new('R2018')
    msp16 = doc16.modelspace()
    msp16.add_lwpolyline([(0, 0), (160, 0), (160, 90), (0, 90)], close=True)
    p16 = os.path.join(output_dir, "case16_dxf_version_r2018.dxf")
    doc16.saveas(p16)
    generated_files.append(p16)

    return generated_files

if __name__ == "__main__":
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "dxf_test_corpus"))
    files = generate_corpus(out_dir)
    print(f"Successfully generated {len(files)} test corpus DXFs in: {out_dir}")
