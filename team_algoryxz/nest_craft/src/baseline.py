"""
baseline.py
Implements genuine Bottom-Left-Fill (BLF) irregular polygon nesting baseline.
Uses exact Shapely geometric collision detection and containment checks.
"""

import time
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely import affinity

from .geometry import (
    Part, Sheet, check_collision, compute_hole_feasible_regions,
    get_allowed_rotations, get_refined_rotation_angles
)

def generate_hole_candidate_points(hole_feas: Polygon, 
                                   poly_w: float, 
                                   poly_h: float, 
                                   grid_step: float = 2.0) -> List[Tuple[float, float]]:
    """
    Generates potential placement coordinates (minx, miny) within a hole feasible region.
    Points are sorted by (y ascending, x ascending).
    """
    h_minx, h_miny, h_maxx, h_maxy = hole_feas.bounds
    max_x = h_maxx - poly_w
    max_y = h_maxy - poly_h
    
    if max_x < h_minx - 1e-6 or max_y < h_miny - 1e-6:
        return []
        
    pts = [(h_minx, h_miny), (max_x, h_miny), (h_minx, max_y), (max_x, max_y)]
    pts.append(((h_minx + max_x) / 2.0, (h_miny + max_y) / 2.0))
    
    x_steps = np.arange(h_minx, max_x + 1e-4, max(grid_step, 4.0))
    y_steps = np.arange(h_miny, max_y + 1e-4, max(grid_step, 4.0))
    for y in y_steps:
        for x in x_steps:
            pts.append((float(x), float(y)))
            
    valid_pts = [(x, y) for x, y in pts if h_minx - 1e-6 <= x <= max_x + 1e-6 and h_miny - 1e-6 <= y <= max_y + 1e-6]
    unique_dict = {}
    for x, y in valid_pts:
        k = (round(x, 2), round(y, 2))
        if k not in unique_dict:
            unique_dict[k] = (x, y)
            
    return sorted(unique_dict.values(), key=lambda pt: (pt[1], pt[0]))

def place_part_in_holes(sheet: Sheet, 
                        poly: Polygon, 
                        clearance: float = 0.0,
                        step_size: float = 2.0) -> Optional[Tuple[float, float, Polygon, str]]:
    """
    Searches for valid placement of poly inside any interior hole of any part already placed on the sheet.
    Returns (x, y, placed_candidate, parent_part_name) if placement succeeds, else None.
    """
    minx, miny, maxx, maxy = poly.bounds
    poly_w = maxx - minx
    poly_h = maxy - miny
    
    placed_polys = [p for _, p, _ in sheet.placed_parts]
    
    for parent_name, placed_poly, _ in sheet.placed_parts:
        sub_polys = placed_poly.geoms if isinstance(placed_poly, MultiPolygon) else [placed_poly]
        if not any(hasattr(sub, 'interiors') and len(sub.interiors) > 0 for sub in sub_polys):
            continue
            
        hole_regions = compute_hole_feasible_regions(placed_poly, clearance=clearance)
        for hole_feas in hole_regions:
            if hole_feas.area < poly.area:
                continue
            h_minx, h_miny, h_maxx, h_maxy = hole_feas.bounds
            if (h_maxx - h_minx) < poly_w - 1e-6 or (h_maxy - h_miny) < poly_h - 1e-6:
                continue
                
            candidate_points = generate_hole_candidate_points(hole_feas, poly_w, poly_h, grid_step=step_size)
            for x, y in candidate_points:
                candidate = affinity.translate(poly, xoff=x, yoff=y)
                # Strict containment check in inward-buffered feasible region
                if hole_feas.contains(candidate):
                    if not check_collision(candidate, placed_polys, clearance=clearance):
                        return (x, y, candidate, parent_name)
                        
    return None

def generate_candidate_points(sheet: Sheet, 
                             poly_w: float, 
                             poly_h: float, 
                             clearance: float = 0.0,
                             grid_step: float = 2.0) -> List[Tuple[float, float]]:
    """
    Generates potential bottom-left placement positions based on:
    1. Origin (clearance/2, clearance/2)
    2. Contact points adjacent to already placed parts (top and right edges)
    3. Intermediate grid points for tight fitting into recesses.
    Points are sorted by (y ascending, x ascending).
    """
    half_c = clearance / 2.0
    c_pts = [(half_c, half_c)]
    
    max_x = sheet.width - poly_w - half_c
    max_y = sheet.height - poly_h - half_c
    
    if max_x < half_c or max_y < half_c:
        return []
        
    for _, placed_poly, _ in sheet.placed_parts:
        minx, miny, maxx, maxy = placed_poly.bounds
        
        # Point to the right of placed part
        pt_x = maxx + clearance
        if half_c <= pt_x <= max_x:
            c_pts.append((pt_x, half_c))
            c_pts.append((pt_x, miny))
            if miny - poly_h - clearance >= half_c:
                c_pts.append((pt_x, miny - poly_h - clearance))
                
        # Point on top of placed part
        pt_y = maxy + clearance
        if half_c <= pt_y <= max_y:
            c_pts.append((half_c, pt_y))
            c_pts.append((minx, pt_y))
            if minx - poly_w - clearance >= half_c:
                c_pts.append((minx - poly_w - clearance, pt_y))
                
        # Corner contact
        if half_c <= pt_x <= max_x and half_c <= pt_y <= max_y:
            c_pts.append((pt_x, pt_y))

    # Add regular stepping points along the bottom and left edges
    x_steps = np.arange(half_c, max_x + 1e-4, max(grid_step, 5.0))
    y_steps = np.arange(half_c, max_y + 1e-4, max(grid_step, 5.0))
    for x in x_steps[:8]:
        c_pts.append((float(x), half_c))
    for y in y_steps[:8]:
        c_pts.append((half_c, float(y)))
        
    # Filter points within valid sheet bounds
    valid_pts = [(x, y) for x, y in c_pts if half_c <= x <= max_x and half_c <= y <= max_y]
    
    # Remove duplicates and sort by y ascending (bottom), then x ascending (left)
    # Round to avoid floating point duplicates
    unique_dict = {}
    for x, y in valid_pts:
        k = (round(x, 2), round(y, 2))
        if k not in unique_dict:
            unique_dict[k] = (x, y)
            
    sorted_pts = sorted(unique_dict.values(), key=lambda pt: (pt[1], pt[0]))
    return sorted_pts

def place_part_bottom_left(sheet: Sheet, 
                           poly: Polygon, 
                           clearance: float = 0.0,
                           step_x: float = 2.0, 
                           step_y: float = 2.0) -> Optional[Tuple[float, float, Polygon]]:
    """
    Searches for the lowest (bottom-most), then left-most position on the sheet
    where poly can be placed without collision and within sheet boundaries.
    """
    minx, miny, maxx, maxy = poly.bounds
    poly_w = maxx - minx
    poly_h = maxy - miny
    
    # Quick check if polygon exceeds sheet dimensions
    if poly_w + clearance > sheet.width or poly_h + clearance > sheet.height:
        return None
        
    placed_polys = [p for _, p, _ in sheet.placed_parts]
    
    # Generate anchor points
    candidate_points = generate_candidate_points(sheet, poly_w, poly_h, clearance, grid_step=step_x)
    
    for x, y in candidate_points:
        candidate = affinity.translate(poly, xoff=x, yoff=y)
        if sheet.can_contain(candidate):
            if not check_collision(candidate, placed_polys, clearance):
                return (x, y, candidate)
                
    return None

def run_bottom_left_fill(parts: List[Part], 
                         sheet_width: float, 
                         sheet_height: float, 
                         clearance: float = 0.0,
                         allowed_rotations: Optional[List[float]] = None,
                         rotation_mode: str = "none",
                         grain_direction: Optional[str] = None,
                         step_size: float = 2.0,
                         allow_part_in_part: bool = True) -> Tuple[List[Sheet], Dict[str, Any]]:
    """
    Executes standard Bottom-Left-Fill (BLF) heuristic across a list of parts.
    Allocates new sheets as needed.
    If allow_part_in_part is True, evaluates placing eligible parts into interior holes.
    Supports rotation_mode: 'none' (0 deg), 'orthogonal' (0, 90, 180, 270), or 'adaptive' (15 deg coarse + 5 deg fine).
    Respects grain_direction ('horizontal', 'vertical', or None).
    """
    start_time = time.time()
    sheets = [Sheet(sheet_width, sheet_height, sheet_id=1)]
    unplaced_count = 0
    
    # Flatten parts according to their quantity
    flat_parts = []
    for p in parts:
        for q in range(p.quantity):
            flat_parts.append((f"{p.part_id}_{q+1}", p))
            
    for part_name, part in flat_parts:
        placed = False
        
        # Determine candidate rotations for this part
        if allowed_rotations is not None:
            candidate_rotations = allowed_rotations
        else:
            candidate_rotations = get_allowed_rotations(part, rotation_mode=rotation_mode, grain_direction=grain_direction)
            
        # Priority 1: Try placing inside interior holes of parts already placed on existing sheets
        if allow_part_in_part:
            for sheet in sheets:
                best_hole_placement = None
                best_rot = 0.0
                for rot in candidate_rotations:
                    rot_poly = part.get_rotated(rot)
                    h_place = place_part_in_holes(sheet, rot_poly, clearance=clearance, step_size=step_size)
                    if h_place is not None:
                        if best_hole_placement is None or h_place[1] < best_hole_placement[1] or \
                           (h_place[1] == best_hole_placement[1] and h_place[0] < best_hole_placement[0]):
                            best_hole_placement = h_place
                            best_rot = rot
                            
                # Optional fine local refinement for adaptive mode
                if best_hole_placement is not None and rotation_mode == "adaptive" and allowed_rotations is None:
                    part_grain = part.metadata.get("grain_direction") or part.metadata.get("grain_constraint") or grain_direction
                    fine_angles = get_refined_rotation_angles(best_rot, grain_direction=part_grain)
                    for f_rot in fine_angles:
                        if f_rot in candidate_rotations:
                            continue
                        rot_poly = part.get_rotated(f_rot)
                        h_place = place_part_in_holes(sheet, rot_poly, clearance=clearance, step_size=step_size)
                        if h_place is not None:
                            if h_place[1] < best_hole_placement[1] or (h_place[1] == best_hole_placement[1] and h_place[0] < best_hole_placement[0]):
                                best_hole_placement = h_place
                                best_rot = f_rot
                                
                if best_hole_placement is not None:
                    _, _, final_poly, parent_name = best_hole_placement
                    sheet.placed_parts.append((part_name, final_poly, best_rot))
                    sheet.part_in_part_assignments[part_name] = parent_name
                    placed = True
                    break

        # Priority 2: Try standard exterior placement on existing sheets
        if not placed:
            for sheet in sheets:
                best_placement = None
                best_rot = 0.0
                
                for rot in candidate_rotations:
                    rot_poly = part.get_rotated(rot)
                    placement = place_part_bottom_left(sheet, rot_poly, clearance=clearance, 
                                                       step_x=step_size, step_y=step_size)
                    if placement is not None:
                        # Choose the lowest y, then left-most x
                        if best_placement is None or placement[1] < best_placement[1] or \
                           (placement[1] == best_placement[1] and placement[0] < best_placement[0]):
                            best_placement = placement
                            best_rot = rot
                            
                # Optional fine local refinement for adaptive mode
                if best_placement is not None and rotation_mode == "adaptive" and allowed_rotations is None:
                    part_grain = part.metadata.get("grain_direction") or part.metadata.get("grain_constraint") or grain_direction
                    fine_angles = get_refined_rotation_angles(best_rot, grain_direction=part_grain)
                    for f_rot in fine_angles:
                        if f_rot in candidate_rotations:
                            continue
                        rot_poly = part.get_rotated(f_rot)
                        placement = place_part_bottom_left(sheet, rot_poly, clearance=clearance, 
                                                           step_x=step_size, step_y=step_size)
                        if placement is not None:
                            if placement[1] < best_placement[1] or (placement[1] == best_placement[1] and placement[0] < best_placement[0]):
                                best_placement = placement
                                best_rot = f_rot
                                
                if best_placement is not None:
                    _, _, final_poly = best_placement
                    sheet.placed_parts.append((part_name, final_poly, best_rot))
                    placed = True
                    break
                    
        # If not placed, start a new sheet
        if not placed:
            new_sheet = Sheet(sheet_width, sheet_height, sheet_id=len(sheets) + 1)
            placed_on_new = False
            best_placement = None
            best_rot = 0.0
            for rot in candidate_rotations:
                rot_poly = part.get_rotated(rot)
                placement = place_part_bottom_left(new_sheet, rot_poly, clearance=clearance, 
                                                   step_x=step_size, step_y=step_size)
                if placement is not None:
                    if best_placement is None or placement[1] < best_placement[1] or \
                       (placement[1] == best_placement[1] and placement[0] < best_placement[0]):
                        best_placement = placement
                        best_rot = rot
                        
            if best_placement is not None and rotation_mode == "adaptive" and allowed_rotations is None:
                part_grain = part.metadata.get("grain_direction") or part.metadata.get("grain_constraint") or grain_direction
                fine_angles = get_refined_rotation_angles(best_rot, grain_direction=part_grain)
                for f_rot in fine_angles:
                    if f_rot in candidate_rotations:
                        continue
                    rot_poly = part.get_rotated(f_rot)
                    placement = place_part_bottom_left(new_sheet, rot_poly, clearance=clearance, 
                                                       step_x=step_size, step_y=step_size)
                    if placement is not None:
                        if placement[1] < best_placement[1] or (placement[1] == best_placement[1] and placement[0] < best_placement[0]):
                            best_placement = placement
                            best_rot = f_rot
                            
            if best_placement is not None:
                _, _, final_poly = best_placement
                new_sheet.placed_parts.append((part_name, final_poly, best_rot))
                placed_on_new = True
                    
            if placed_on_new:
                sheets.append(new_sheet)
            else:
                unplaced_count += 1
                
    elapsed_time = time.time() - start_time
    total_sheet_area = sum(s.area for s in sheets)
    total_used_area = sum(s.get_utilized_area() for s in sheets)
    overall_utilization = (total_used_area / total_sheet_area * 100.0) if total_sheet_area > 0 else 0.0
    
    # Calculate per-sheet linear extents and remnant metrics
    per_sheet_metrics = []
    for s_idx, s in enumerate(sheets):
        per_sheet_metrics.append({
            "sheet_id": s_idx + 1,
            "parts_placed": len(s.placed_parts),
            "utilized_area": round(s.get_utilized_area(), 2),
            "utilization_pct": round(s.get_utilization_pct(), 2),
            **s.get_remnant_geometry()
        })
        
    # Total linear length consumed across sheets (coil or discrete strip)
    if sheets:
        final_sheet = sheets[-1]
        final_max_x = final_sheet.get_max_x()
        total_linear_consumed = (len(sheets) - 1) * sheet_width + final_max_x
        total_linear_available = len(sheets) * sheet_width
        final_remnant = final_sheet.get_remnant_geometry()
        strip_area = sheet_height * total_linear_consumed if total_linear_consumed > 0 else 0.0
        continuous_strip_util_pct = (total_used_area / strip_area * 100.0) if strip_area > 0 else 0.0
    else:
        total_linear_consumed = 0.0
        total_linear_available = 0.0
        final_remnant = {}
        continuous_strip_util_pct = 0.0
        
    stats = {
        "algorithm": "Bottom-Left-Fill (BLF)",
        "sheets_used": len(sheets),
        "total_parts_nested": len(flat_parts) - unplaced_count,
        "total_parts_requested": len(flat_parts),
        "unplaced_parts": unplaced_count,
        "rotation_mode": rotation_mode,
        "grain_direction": grain_direction,
        "allow_part_in_part": allow_part_in_part,
        "parts_nested_in_holes": sum(len(s.part_in_part_assignments) for s in sheets),
        "part_in_part_assignments": {name: parent for s in sheets for name, parent in s.part_in_part_assignments.items()},
        "utilization_pct": round(overall_utilization, 2),
        "scrap_pct": round(100.0 - overall_utilization, 2),
        "total_sheet_area": round(total_sheet_area, 2),
        "utilized_area": round(total_used_area, 2),
        "runtime_seconds": round(elapsed_time, 3),
        "total_linear_length_consumed": round(total_linear_consumed, 2),
        "total_linear_stock_available": round(total_linear_available, 2),
        "continuous_strip_utilization_pct": round(continuous_strip_util_pct, 2),
        "final_sheet_remnant": final_remnant,
        "per_sheet_metrics": per_sheet_metrics
    }
    
    return sheets, stats
