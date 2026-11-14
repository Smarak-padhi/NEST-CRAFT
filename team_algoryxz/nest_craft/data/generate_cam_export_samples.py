"""
generate_cam_export_samples.py
Generates 6 representative nested layout DXF files for manual CAM interoperability testing:
  1. Simple rectangular parts
  2. Irregular concave parts
  3. Multipart geometry (MultiPolygon components)
  4. Parts with interior cutouts/holes
  5. Part-in-part nesting (child components inside parent apertures)
  6. Multi-sheet layout (multiple consecutive sheets with 100mm CAD gap)
All files are structurally validated using validate_exported_dxf.
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from shapely.geometry import Polygon, MultiPolygon

from team_algoryxz.nest_craft.src.geometry import Sheet
from team_algoryxz.nest_craft.src.dxf_io import export_nesting_to_dxf, validate_exported_dxf

def generate_cam_samples(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    created_files = []

    # 1. Simple Rectangular Parts
    s1 = Sheet(width=500, height=400, sheet_id=1)
    p_rect1 = Polygon([(0, 0), (150, 0), (150, 100), (0, 100)])
    p_rect2 = Polygon([(160, 0), (310, 0), (310, 100), (160, 100)])
    p_rect3 = Polygon([(0, 110), (200, 110), (200, 250), (0, 250)])
    s1.placed_parts.append(("rect_1", p_rect1, 0.0))
    s1.placed_parts.append(("rect_2", p_rect2, 0.0))
    s1.placed_parts.append(("rect_3", p_rect3, 0.0))
    f1 = os.path.join(output_dir, "export_01_rectangular.dxf")
    export_nesting_to_dxf([s1], f1, validate=True)
    created_files.append(f1)

    # 2. Irregular Concave Parts
    s2 = Sheet(width=600, height=400, sheet_id=1)
    # L-bracket 1
    p_l1 = Polygon([(0, 0), (180, 0), (180, 60), (60, 60), (60, 220), (0, 220)])
    # Interlocking L-bracket 2 (rotated 180 degrees)
    p_l2 = Polygon([(70, 70), (250, 70), (250, 290), (190, 290), (190, 130), (70, 130)])
    s2.placed_parts.append(("l_bracket_1", p_l1, 0.0))
    s2.placed_parts.append(("l_bracket_2", p_l2, 180.0))
    f2 = os.path.join(output_dir, "export_02_irregular_concave.dxf")
    export_nesting_to_dxf([s2], f2, validate=True)
    created_files.append(f2)

    # 3. Multipart Geometry (MultiPolygon components)
    s3 = Sheet(width=600, height=400, sheet_id=1)
    comp_a = Polygon([(0, 0), (80, 0), (80, 80), (0, 80)])
    comp_b = Polygon([(100, 0), (160, 0), (160, 80), (100, 80)])
    mp_part = MultiPolygon([comp_a, comp_b])
    s3.placed_parts.append(("multipart_bracket_1", mp_part, 0.0))
    f3 = os.path.join(output_dir, "export_03_multipart.dxf")
    export_nesting_to_dxf([s3], f3, validate=True)
    created_files.append(f3)

    # 4. Parts with Interior Cutouts / Holes
    s4 = Sheet(width=600, height=500, sheet_id=1)
    # Flange plate with central hole and 4 corner bolt holes
    outer_flange = [(0, 0), (200, 0), (200, 200), (0, 200)]
    center_hole = [(70, 70), (130, 70), (130, 130), (70, 130)]
    h1 = [(20, 20), (35, 20), (35, 35), (20, 35)]
    h2 = [(165, 20), (180, 20), (180, 35), (165, 35)]
    h3 = [(165, 165), (180, 165), (180, 180), (165, 180)]
    h4 = [(20, 165), (35, 165), (35, 180), (20, 180)]
    flange_poly = Polygon(outer_flange, [center_hole, h1, h2, h3, h4])
    s4.placed_parts.append(("flange_plate_1", flange_poly, 0.0))
    f4 = os.path.join(output_dir, "export_04_parts_with_holes.dxf")
    export_nesting_to_dxf([s4], f4, validate=True)
    created_files.append(f4)

    # 5. Part-in-Part Nesting (Child component inside parent cutout)
    s5 = Sheet(width=600, height=500, sheet_id=1)
    parent_poly = Polygon([(0, 0), (300, 0), (300, 300), (0, 300)], [[(50, 50), (250, 50), (250, 250), (50, 250)]])
    child_poly = Polygon([(70, 70), (200, 70), (200, 200), (70, 200)])
    s5.placed_parts.append(("parent_frame_1", parent_poly, 0.0))
    s5.placed_parts.append(("child_bracket_1", child_poly, 0.0))
    s5.part_in_part_assignments["child_bracket_1"] = "parent_frame_1"
    f5 = os.path.join(output_dir, "export_05_part_in_part.dxf")
    export_nesting_to_dxf([s5], f5, validate=True)
    created_files.append(f5)

    # 6. Multiple Sheets Layout (3 sheets)
    sheet_a = Sheet(width=500, height=400, sheet_id=1)
    sheet_a.placed_parts.append(("p1_s1", Polygon([(0, 0), (200, 0), (200, 200), (0, 200)]), 0.0))
    
    sheet_b = Sheet(width=500, height=400, sheet_id=2)
    sheet_b.placed_parts.append(("p2_s2", Polygon([(0, 0), (250, 0), (250, 250), (0, 250)]), 0.0))
    
    sheet_c = Sheet(width=500, height=400, sheet_id=3)
    sheet_c.placed_parts.append(("p3_s3", Polygon([(0, 0), (150, 0), (150, 150), (0, 150)]), 0.0))
    
    f6 = os.path.join(output_dir, "export_06_multiple_sheets.dxf")
    export_nesting_to_dxf([sheet_a, sheet_b, sheet_c], f6, validate=True)
    created_files.append(f6)

    return created_files

if __name__ == "__main__":
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "cam_export_samples"))
    files = generate_cam_samples(out_dir)
    print(f"Generated and validated {len(files)} CAM export sample DXFs in: {out_dir}")
    for f in files:
        print(f"  {os.path.basename(f)}: Generated and verified")
