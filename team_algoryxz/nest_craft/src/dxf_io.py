"""
dxf_io.py
Handles parsing of ESICUP benchmark files (.txt and .xml) and AutoCAD .dxf files.
Also generates exportable DXF layouts and standard industrial sample parts.
Provides comprehensive validation and entity parsing for LWPOLYLINE, POLYLINE,
LINE, ARC, CIRCLE, SPLINE, ELLIPSE, and interior hole extraction.
"""

import os
import re
import math
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict, Any, Optional, Set
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, GeometryCollection
from shapely.ops import polygonize, unary_union
from shapely import set_precision
from shapely.validation import make_valid
import ezdxf
from ezdxf import path

from .geometry import Part, CADTopologyError

class DXFValidationError(ValueError):
    """Raised when a DXF file cannot be validated or has fatal geometry errors."""
    pass

class DXFExportValidationError(ValueError):
    """Raised when an exported DXF fails structural audit or geometry conservation checks."""
    pass

SUPPORTED_2D_CONTOUR_TYPES = {
    'LWPOLYLINE', 'POLYLINE', 'CIRCLE', 'ARC', 'LINE', 'SPLINE', 'ELLIPSE'
}

ANNOTATION_ENTITY_TYPES = {
    'TEXT', 'MTEXT', 'DIMENSION', 'LEADER', 'MULTILEADER',
    'ATTRIB', 'ATTDEF', 'POINT', 'HATCH'
}

UNSUPPORTED_3D_ENTITY_TYPES = {
    '3DFACE', 'MESH', 'SOLID3D', 'SURFACE', 'BODY', 'REGION',
    'RAY', 'XLINE', 'VIEWPORT', 'CAMERA', 'LIGHT', 'HELIX'
}

IGNORE_LAYERS = {
    'SHEET_BOUNDARY', 'BORDER', 'MARGIN', 'TITLE_BLOCK', 'FRAME', 'DEFPOINTS'
}

def parse_esicup_txt(file_path: str, allow_repaired_topology: bool = False) -> Tuple[List[Part], Dict[str, Any]]:
    """
    Parses classic ESICUP format (e.g. shapes.txt, swim.txt).
    Format:
    PIECE <id>
    QUANTITY
    <qty>
    NUMBER OF VERTICES
    <num_vertices>
    VERTICES (X,Y)
    x y
    ...
    """
    parts = []
    metadata = {
        "source": file_path, 
        "filename": os.path.basename(file_path),
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        
    # Split by "PIECE"
    pieces = re.split(r'PIECE\s+\d+', content, flags=re.IGNORECASE)
    # The first split might be empty or preamble
    piece_blocks = [p.strip() for p in pieces if p.strip()]
    
    for idx, block in enumerate(piece_blocks):
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        qty = 1
        num_vertices = 0
        coords = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            if "QUANTITY" in line.upper():
                i += 1
                if i < len(lines):
                    qty = int(lines[i])
            elif "NUMBER OF VERTICES" in line.upper():
                i += 1
                if i < len(lines):
                    num_vertices = int(lines[i])
            elif "VERTICES" in line.upper():
                i += 1
                while i < len(lines) and not any(kw in lines[i].upper() for kw in ["PIECE", "QUANTITY", "NUMBER"]):
                    parts_coord = lines[i].split()
                    if len(parts_coord) >= 2:
                        try:
                            x = float(parts_coord[0])
                            y = float(parts_coord[1])
                            coords.append((x, y))
                        except ValueError:
                            pass
                    i += 1
                continue
            i += 1
            
        if len(coords) >= 3:
            poly = Polygon(coords)
            meta = {
                "source_file": os.path.basename(file_path),
                "piece_index": idx + 1,
                "allow_repaired_topology": allow_repaired_topology
            }
            parts.append(Part(poly, part_id=f"piece_{idx+1}", quantity=qty, metadata=meta))
            
    metadata["total_pieces_extracted"] = len(parts)
    metadata["total_quantity"] = sum(p.quantity for p in parts)
    return parts, metadata

def parse_esicup_xml(file_path: str, allow_repaired_topology: bool = False) -> Tuple[List[Part], Dict[str, Any]]:
    """Parses ESICUP XML format (e.g. shapes0.xml)."""
    parts = []
    metadata = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Strip namespace if present
    ns = ""
    if "}" in root.tag:
        ns = root.tag.split("}")[0] + "}"
        
    metadata["name"] = root.findtext(f"{ns}name", default="Unknown")
    metadata["author"] = root.findtext(f"{ns}author", default="ESICUP")
    
    # Parse polygons pool
    polygons_dict = {}
    polygons_elem = root.find(f"{ns}polygons")
    if polygons_elem is not None:
        for poly_elem in polygons_elem.findall(f"{ns}polygon"):
            poly_id = poly_elem.attrib.get("id")
            lines_elem = poly_elem.find(f"{ns}lines")
            coords = []
            if lines_elem is not None:
                for seg in lines_elem.findall(f"{ns}segment"):
                    x0 = float(seg.attrib["x0"])
                    y0 = float(seg.attrib["y0"])
                    coords.append((x0, y0))
            if len(coords) >= 3:
                poly = Polygon(coords)
                polygons_dict[poly_id] = poly
                
    # Parse problem lot
    lot_elem = root.find(f"{ns}problem/{ns}lot")
    if lot_elem is not None:
        for piece_elem in lot_elem.findall(f"{ns}piece"):
            piece_id = piece_elem.attrib.get("id")
            qty = int(piece_elem.attrib.get("quantity", 1))
            comp = piece_elem.find(f"{ns}component")
            if comp is not None:
                id_poly = comp.attrib.get("idPolygon")
                if id_poly in polygons_dict:
                    raw_poly = polygons_dict[id_poly]
                    meta = {
                        "source_file": os.path.basename(file_path),
                        "piece_id": piece_id,
                        "allow_repaired_topology": allow_repaired_topology
                    }
                    parts.append(Part(raw_poly, part_id=piece_id, quantity=qty, metadata=meta))
                    
    metadata["total_pieces_extracted"] = len(parts)
    metadata["total_quantity"] = sum(p.quantity for p in parts)
    return parts, metadata

def validate_and_parse_dxf(file_path: str, allow_repaired_topology: bool = False) -> Tuple[List[Part], Dict[str, Any]]:
    """
    Validates and parses an AutoCAD DXF file with comprehensive reliability guarantees:
    1. Supports LWPOLYLINE (including arc bulges), POLYLINE, CIRCLE, ARC, LINE, SPLINE, ELLIPSE.
    2. Explodes INSERT block references to uncover nested cutting geometry.
    3. Stitches connected open LINE and ARC entities using precision network polygonization.
    4. Topologically detects concentric interior cutouts and assigns them as polygon holes.
    5. Flags unsupported 3D entities and unclosed line segments with explicit error/warning messages.
    
    Returns:
        (parts, validation_report)
    """
    report: Dict[str, Any] = {
        "file_path": file_path,
        "is_valid": True,
        "total_entities_inspected": 0,
        "entity_counts": {},
        "supported_contour_entities": 0,
        "annotation_entities": 0,
        "unsupported_3d_entities": [],
        "unclosed_segments_count": 0,
        "parts_extracted_count": 0,
        "holes_extracted_count": 0,
        "warnings": [],
        "errors": []
    }
    
    if not os.path.exists(file_path):
        report["is_valid"] = False
        report["errors"].append(f"File not found: {file_path}")
        return [], report
        
    try:
        doc = ezdxf.readfile(file_path)
    except Exception as e:
        report["is_valid"] = False
        report["errors"].append(f"Failed to read DXF file '{os.path.basename(file_path)}': {str(e)}")
        return [], report
        
    try:
        msp = doc.modelspace()
    except Exception as e:
        report["is_valid"] = False
        report["errors"].append(f"DXF modelspace unavailable: {str(e)}")
        return [], report

    # Gather entities, exploding INSERT block references if present
    raw_entities = list(msp)
    processed_entities = []
    
    for entity in raw_entities:
        dxftype = entity.dxftype()
        if dxftype == 'INSERT':
            try:
                exploded = entity.explode()
                processed_entities.extend(list(exploded))
            except Exception as e:
                report["warnings"].append(f"Could not explode block reference '{entity.dxf.name}': {str(e)}")
        else:
            processed_entities.append(entity)
            
    report["total_entities_inspected"] = len(processed_entities)
    
    closed_polys: List[Polygon] = []
    line_strings: List[LineString] = []
    
    for entity in processed_entities:
        dxftype = entity.dxftype()
        layer_name = entity.dxf.layer.upper() if hasattr(entity.dxf, 'layer') else ""
        if layer_name in IGNORE_LAYERS:
            continue
            
        report["entity_counts"][dxftype] = report["entity_counts"].get(dxftype, 0) + 1
        
        if dxftype in UNSUPPORTED_3D_ENTITY_TYPES:
            report["unsupported_3d_entities"].append(dxftype)
            report["warnings"].append(
                f"Unsupported entity type '{dxftype}' ignored. 2D nesting requires planar profiles."
            )
            continue
            
        if dxftype in ANNOTATION_ENTITY_TYPES:
            report["annotation_entities"] += 1
            continue
            
        if dxftype in SUPPORTED_2D_CONTOUR_TYPES:
            report["supported_contour_entities"] += 1
            try:
                p = path.make_path(entity)
                pts = [(v.x, v.y) for v in p.flattening(distance=0.1)]
                
                # Check if path is marked closed or is geometrically closed
                is_closed_geom = False
                if len(pts) >= 4 and math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-3:
                    is_closed_geom = True
                    
                if (p.is_closed or is_closed_geom) and len(pts) >= 3:
                    poly = Polygon(pts)
                    if not poly.is_valid:
                        if not allow_repaired_topology:
                            report["is_valid"] = False
                            report["errors"].append(
                                f"Contour in '{os.path.basename(file_path)}' has self-intersections or invalid topology. "
                                "Repair in CAD or explicitly authorize via allow_repaired_topology=True."
                            )
                            return [], report
                        poly = make_valid(poly)
                    if isinstance(poly, MultiPolygon):
                        closed_polys.extend([sub for sub in poly.geoms if sub.area > 1e-3])
                    elif poly.area > 1e-3:
                        closed_polys.append(poly)
                elif len(pts) >= 2:
                    line_strings.append(LineString(pts))
            except Exception as e:
                report["warnings"].append(f"Failed to tessellate entity '{dxftype}': {str(e)}")
        else:
            report["warnings"].append(f"Unrecognized entity type '{dxftype}' skipped.")
            
    # Stitch open LINE and ARC entities into closed loops using polygonize
    if line_strings:
        try:
            snapped_lines = [set_precision(l, grid_size=0.001) for l in line_strings]
            merged_network = unary_union(snapped_lines)
            stitched_polys = list(polygonize(merged_network))
            
            for poly in stitched_polys:
                if not poly.is_valid:
                    poly = make_valid(poly)
                if isinstance(poly, MultiPolygon):
                    closed_polys.extend([sub for sub in poly.geoms if sub.area > 1e-3])
                elif poly.area > 1e-3:
                    closed_polys.append(poly)
                    
            # Check for dangling segments that did not participate in any closed polygon
            if not stitched_polys:
                report["unclosed_segments_count"] = len(line_strings)
                report["warnings"].append(
                    f"{len(line_strings)} open line/arc segment(s) detected that do not form any closed cutting contour."
                )
            else:
                # Count unclosed lines by checking coverage against stitched polygon boundaries
                stitched_boundaries = unary_union([p.exterior for p in stitched_polys])
                dangling = 0
                for line in line_strings:
                    if not stitched_boundaries.distance(line) < 1e-3:
                        dangling += 1
                if dangling > 0:
                    report["unclosed_segments_count"] = dangling
                    report["warnings"].append(
                        f"{dangling} open line/arc segment(s) could not be stitched into closed cutting contours."
                    )
        except Exception as e:
            report["warnings"].append(f"Open contour network stitching failed: {str(e)}")
            
    # Filter valid non-degenerate polygons
    valid_polys = []
    for poly in closed_polys:
        if not poly.is_valid:
            if not allow_repaired_topology:
                report["is_valid"] = False
                report["errors"].append(
                    f"Contour in '{os.path.basename(file_path)}' has self-intersections or invalid topology. "
                    "Repair in CAD or explicitly authorize via allow_repaired_topology=True."
                )
                return [], report
            poly = make_valid(poly)
        if isinstance(poly, MultiPolygon):
            for sub in poly.geoms:
                if sub.area > 1e-3:
                    valid_polys.append(sub)
        elif poly.area > 1e-3:
            valid_polys.append(poly)
            
    if not valid_polys:
        report["is_valid"] = False
        report["errors"].append(
            f"No valid closed 2D cutting contours found in '{os.path.basename(file_path)}'. "
            "Ensure geometry contains closed polylines, circles, or connected boundary lines."
        )
        return [], report

    # Topological containment tree for hole and island extraction:
    # Sort polygons descending by area.
    valid_polys.sort(key=lambda p: p.area, reverse=True)
    
    # Compute immediate parent for each polygon (the smallest containing polygon)
    parents: Dict[int, Optional[int]] = {}
    for i, p_child in enumerate(valid_polys):
        parent_idx = None
        min_parent_area = float('inf')
        for j, p_parent in enumerate(valid_polys):
            if i != j and p_parent.area > p_child.area and p_parent.contains(p_child):
                if p_parent.area < min_parent_area:
                    min_parent_area = p_parent.area
                    parent_idx = j
        parents[i] = parent_idx
        
    # Compute nesting depth of each polygon
    depths: Dict[int, int] = {}
    for i in range(len(valid_polys)):
        d = 0
        curr = parents[i]
        while curr is not None:
            d += 1
            curr = parents[curr]
        depths[i] = d
        
    # Group immediate children by parent
    children: Dict[int, List[int]] = {i: [] for i in range(len(valid_polys))}
    for child_idx, parent_idx in parents.items():
        if parent_idx is not None:
            children[parent_idx].append(child_idx)
            
    # Solid contours are at even depths (0 = outer boundary, 2 = island in hole, etc.)
    # Their immediate children (at depth d + 1) are their interior holes.
    parts: List[Part] = []
    total_holes = 0
    
    for i, outer_poly in enumerate(valid_polys):
        if depths[i] % 2 == 0:
            immediate_hole_indices = children[i]
            candidate_holes = [valid_polys[h_idx] for h_idx in immediate_hole_indices]
            
            hole_rings = []
            if candidate_holes:
                try:
                    union_holes = unary_union(candidate_holes)
                    if union_holes.geom_type == 'Polygon':
                        hole_rings = [union_holes.exterior.coords]
                    elif union_holes.geom_type == 'MultiPolygon':
                        hole_rings = [h.exterior.coords for h in union_holes.geoms]
                    else:
                        hole_rings = [h.exterior.coords for h in candidate_holes]
                except Exception:
                    hole_rings = [h.exterior.coords for h in candidate_holes]
                    
            part_poly = Polygon(shell=outer_poly.exterior.coords, holes=hole_rings)
            if not part_poly.is_valid:
                part_poly = make_valid(part_poly)
            if isinstance(part_poly, GeometryCollection):
                sub_polys = [g for g in part_poly.geoms if isinstance(g, (Polygon, MultiPolygon)) and g.area > 1e-3]
                flat = []
                for sp in sub_polys:
                    if isinstance(sp, MultiPolygon):
                        flat.extend(list(sp.geoms))
                    else:
                        flat.append(sp)
                if len(flat) == 1:
                    part_poly = flat[0]
                elif len(flat) > 1:
                    part_poly = MultiPolygon(flat)
                    
            if isinstance(part_poly, (Polygon, MultiPolygon)) and part_poly.area > 1e-3:
                part_id = f"dxf_part_{len(parts) + 1}"
                sub_geoms = part_poly.geoms if isinstance(part_poly, MultiPolygon) else [part_poly]
                hole_count = sum(len(g.interiors) for g in sub_geoms)
                total_holes += hole_count
                
                metadata = {
                    "source_file": os.path.basename(file_path),
                    "holes_count": hole_count,
                    "gross_area": round(outer_poly.area, 2),
                    "net_area": round(part_poly.area, 2),
                    "allow_repaired_topology": allow_repaired_topology
                }
                try:
                    parts.append(Part(part_poly, part_id=part_id, quantity=1, metadata=metadata))
                except Exception as e:
                    report["is_valid"] = False
                    report["errors"].append(str(e))
        
    report["parts_extracted_count"] = len(parts)
    report["holes_extracted_count"] = total_holes
    return parts, report

def parse_dxf(file_path: str, strict: bool = False, allow_repaired_topology: bool = False) -> List[Part]:
    """
    Reads 2D boundary contours from an AutoCAD DXF file with backward-compatible API.
    If strict=True, raises DXFValidationError on fatal errors or missing parts.
    """
    parts, report = validate_and_parse_dxf(file_path, allow_repaired_topology=allow_repaired_topology)
    if strict and (not report["is_valid"] or not parts):
        err_msg = "; ".join(report["errors"]) if report["errors"] else "Failed to parse valid DXF parts"
        raise DXFValidationError(err_msg)
    return parts

def create_sample_industrial_dxfs(output_dir: str) -> List[str]:
    """
    Creates realistic industrial steel fabrication sample DXF files:
    1. Structural Gusset Plate
    2. Pipe Flange
    3. L-Bracket with stiffener notch
    4. Slotted Base Plate
    """
    os.makedirs(output_dir, exist_ok=True)
    created_paths = []
    
    # 1. Structural Gusset Plate
    doc1 = ezdxf.new('R2010')
    msp1 = doc1.modelspace()
    gusset_coords = [(0, 0), (250, 0), (250, 150), (120, 200), (0, 200)]
    msp1.add_lwpolyline(gusset_coords, close=True)
    p1 = os.path.join(output_dir, "gusset_plate.dxf")
    doc1.saveas(p1)
    created_paths.append(p1)
    
    # 2. L-Bracket
    doc2 = ezdxf.new('R2010')
    msp2 = doc2.modelspace()
    bracket_coords = [(0, 0), (180, 0), (180, 60), (60, 60), (60, 220), (0, 220)]
    msp2.add_lwpolyline(bracket_coords, close=True)
    p2 = os.path.join(output_dir, "l_bracket.dxf")
    doc2.saveas(p2)
    created_paths.append(p2)
    
    # 3. Flange with chamfers
    doc3 = ezdxf.new('R2010')
    msp3 = doc3.modelspace()
    flange_coords = [(20, 0), (160, 0), (180, 20), (180, 160), (160, 180), (20, 180), (0, 160), (0, 20)]
    msp3.add_lwpolyline(flange_coords, close=True)
    p3 = os.path.join(output_dir, "flange_plate.dxf")
    doc3.saveas(p3)
    created_paths.append(p3)
    
    # 4. Slotted Base Plate
    doc4 = ezdxf.new('R2010')
    msp4 = doc4.modelspace()
    base_coords = [(0, 0), (300, 0), (300, 40), (280, 70), (300, 100), (300, 140), (0, 140)]
    msp4.add_lwpolyline(base_coords, close=True)
    p4 = os.path.join(output_dir, "notched_base_plate.dxf")
    doc4.saveas(p4)
    created_paths.append(p4)
    
    return created_paths

def validate_exported_dxf(output_file: str, sheets: List[Any], area_tolerance: float = 0.05) -> Dict[str, Any]:
    """
    Validates an exported nesting DXF file for CNC cutting trustworthiness.
    Verifies:
      1. Reopenability via ezdxf.readfile without parsing errors.
      2. Document structural integrity via ezdxf audit (zero audit errors).
      3. Required layer presence (SHEET_BOUNDARY, CUT_CONTOUR if parts exist).
      4. Closure of all cutting, hole, and boundary polyline contours.
      5. Net part area conservation between in-memory placed parts and DXF exported geometry
         within area_tolerance (default 0.05 mm^2).
    Raises DXFExportValidationError if any check fails.
    """
    if not os.path.exists(output_file):
        raise DXFExportValidationError(f"Exported DXF file does not exist: {output_file}")
    
    try:
        doc = ezdxf.readfile(output_file)
    except Exception as e:
        raise DXFExportValidationError(f"Exported DXF failed reopenability check: {str(e)}")
        
    auditor = doc.audit()
    if auditor.has_errors:
        err_msgs = [getattr(err, 'message', str(err)) for err in auditor.errors]
        raise DXFExportValidationError(f"Exported DXF failed structural audit with {len(auditor.errors)} error(s): {'; '.join(err_msgs)}")
        
    msp = doc.modelspace()
    entities = list(msp)
    
    sheet_boundaries = []
    cut_contours = []
    hole_contours = []
    
    for ent in entities:
        dxftype = ent.dxftype()
        layer = ent.dxf.layer if hasattr(ent.dxf, 'layer') else '0'
        
        if dxftype in ('LWPOLYLINE', 'POLYLINE'):
            if not ent.is_closed:
                raise DXFExportValidationError(f"Polyline entity {getattr(ent.dxf, 'handle', 'UNKNOWN')} on layer '{layer}' is not closed.")
            
            pts = [(p[0], p[1]) for p in ent.get_points()]
            if len(pts) < 3:
                raise DXFExportValidationError(f"Polyline entity {getattr(ent.dxf, 'handle', 'UNKNOWN')} on layer '{layer}' has fewer than 3 vertices.")
                
            poly = Polygon(pts)
            if not poly.is_valid:
                poly = make_valid(poly)
                
            if layer == 'SHEET_BOUNDARY':
                sheet_boundaries.append(poly)
            elif layer in ('CUT_CONTOUR', 'PART_IN_PART_CHILD'):
                cut_contours.append(poly)
            elif layer == 'HOLE_CONTOUR':
                hole_contours.append(poly)

    # Layer presence checks
    if sheets and not sheet_boundaries:
        raise DXFExportValidationError("Exported DXF is missing expected SHEET_BOUNDARY layer polylines.")
        
    expected_net_area = 0.0
    expected_placed_count = 0
    for s in sheets:
        for p_id, p_poly, p_rot in s.placed_parts:
            expected_net_area += p_poly.area
            expected_placed_count += 1
            
    if expected_placed_count > 0 and not cut_contours:
        raise DXFExportValidationError("Exported DXF has placed parts but missing CUT_CONTOUR layer polylines.")
        
    # Net area conservation check
    gross_cut_area = sum(p.area for p in cut_contours)
    hole_area = sum(p.area for p in hole_contours)
    reconstructed_net_area = gross_cut_area - hole_area
    area_delta = abs(reconstructed_net_area - expected_net_area)
    
    if area_delta > area_tolerance:
        raise DXFExportValidationError(
            f"Net area conservation mismatch: expected {expected_net_area:.4f} mm², "
            f"reconstructed from DXF is {reconstructed_net_area:.4f} mm² "
            f"(delta: {area_delta:.4f} mm² exceeds tolerance {area_tolerance} mm²)."
        )
        
    return {
        "valid": True,
        "entity_count": len(entities),
        "sheet_boundary_count": len(sheet_boundaries),
        "cut_contour_count": len(cut_contours),
        "hole_contour_count": len(hole_contours),
        "expected_net_area": expected_net_area,
        "exported_net_area": reconstructed_net_area,
        "area_delta": area_delta,
        "audit_errors": len(auditor.errors),
        "audit_fixes": len(auditor.fixes)
    }

def export_nesting_to_dxf(sheets: List[Any], output_file: str, validate: bool = True) -> str:
    """
    Exports nested sheet layout to DXF format for CNC cutting machines.
    Writes exterior cutting contours to layer 'CUT_CONTOUR' (color 2: yellow/cyan)
    and interior hole contours to layer 'HOLE_CONTOUR' (color 4: cyan/magenta).
    Adds safety notice layer for CAM verification.
    If validate is True, validates the output with validate_exported_dxf.
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Add safety disclaimer in DXF text
    msp.add_text("DISCLAIMER: AI-Generated Nesting Layout. Verify machine-specific lead-ins & kerf offsets.", 
                 dxfattribs={'height': 15, 'color': 1}).set_placement((10, -30))
    
    x_sheet_offset = 0.0
    for s_idx, sheet in enumerate(sheets):
        # Draw sheet boundary
        sheet_box = [
            (x_sheet_offset, 0),
            (x_sheet_offset + sheet.width, 0),
            (x_sheet_offset + sheet.width, sheet.height),
            (x_sheet_offset, sheet.height)
        ]
        msp.add_lwpolyline(sheet_box, close=True, dxfattribs={'color': 7, 'layer': 'SHEET_BOUNDARY'})
        
        # Draw placed parts
        for part_id, poly, rot in sheet.placed_parts:
            # Check if this part was nested inside an interior hole of a parent part
            is_child = hasattr(sheet, 'part_in_part_assignments') and part_id in sheet.part_in_part_assignments
            cut_layer = 'PART_IN_PART_CHILD' if is_child else 'CUT_CONTOUR'
            cut_color = 3 if is_child else 2 # Green for child parts, yellow for exterior contours
            
            # Shift exterior poly by x_sheet_offset (supporting both Polygon and MultiPolygon)
            sub_polys = poly.geoms if isinstance(poly, MultiPolygon) else [poly]
            for sub_poly in sub_polys:
                ext_coords = [(x + x_sheet_offset, y) for x, y in sub_poly.exterior.coords]
                msp.add_lwpolyline(ext_coords, close=True, dxfattribs={'color': cut_color, 'layer': cut_layer})
                
                # Export interior holes on layer HOLE_CONTOUR
                for interior in sub_poly.interiors:
                    hole_coords = [(x + x_sheet_offset, y) for x, y in interior.coords]
                    msp.add_lwpolyline(hole_coords, close=True, dxfattribs={'color': 4, 'layer': 'HOLE_CONTOUR'})
            
        x_sheet_offset += sheet.width + 100.0 # 100mm gap between sheets in CAD view
        
    doc.saveas(output_file)
    if validate:
        validate_exported_dxf(output_file, sheets)
    return output_file
