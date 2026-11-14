"""
geometry.py
Geometric operations for irregular polygon nesting using Shapely.
Handles parsing, validation, rotation, translation, clearance buffering,
and collision checking.
"""

import math
from typing import List, Tuple, Optional, Dict, Any, Union
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection, Point, LineString, box
from shapely import affinity
from shapely.validation import make_valid

class CADTopologyError(ValueError):
    """Raised when CAD geometry has invalid self-intersections or undergoes unauthorized topology changes."""
    pass

class GeometryComparisonError(CADTopologyError):
    """Raised when geometric boundary deviation or topology comparison cannot be evaluated reliably."""
    pass

def count_geometry_holes(geom: Union[Polygon, MultiPolygon, GeometryCollection]) -> int:
    """Counts total interior holes across a Polygon, MultiPolygon, or GeometryCollection."""
    if hasattr(geom, 'geoms'):
        return sum(len(g.interiors) for g in geom.geoms if hasattr(g, 'interiors'))
    elif hasattr(geom, 'interiors'):
        return len(geom.interiors)
    return 0

def compute_boundary_deviation(poly_orig: Union[Polygon, MultiPolygon], 
                               poly_repaired: Union[Polygon, MultiPolygon, GeometryCollection],
                               fail_closed: bool = True) -> float:
    """
    Computes maximum boundary displacement (Hausdorff distance) between 
    the original input boundary and the repaired 2D boundary.
    Fails closed: If comparison fails, raises GeometryComparisonError (or returns float('inf')
    if fail_closed=False). Never returns 0.0 on comparison error.
    Explicitly enforces valid 2D polygonal types (Polygon, MultiPolygon) and rejects
    unsupported types (Point, LineString, etc.).
    If repaired geometry is a GeometryCollection, explicitly handles all components
    (including 1D LineStrings and 0D Points) in boundary evaluation without silently discarding them.
    """
    if poly_orig is None or poly_repaired is None:
        if fail_closed:
            raise GeometryComparisonError("Cannot compute boundary deviation: input geometry is None")
        return float('inf')

    # Explicit runtime type validation for original geometry
    if not isinstance(poly_orig, (Polygon, MultiPolygon)):
        if fail_closed:
            raise GeometryComparisonError(
                f"Unsupported original geometry type '{type(poly_orig).__name__}'. "
                "Only Polygon and MultiPolygon are supported."
            )
        return float('inf')

    # Explicit runtime type validation for repaired geometry
    if not isinstance(poly_repaired, (Polygon, MultiPolygon, GeometryCollection)):
        if fail_closed:
            raise GeometryComparisonError(
                f"Unsupported repaired geometry type '{type(poly_repaired).__name__}'. "
                "Only Polygon, MultiPolygon, and GeometryCollection are supported."
            )
        return float('inf')

    try:
        if poly_orig.is_empty or poly_repaired.is_empty:
            if fail_closed:
                raise GeometryComparisonError("Cannot compute boundary deviation: input or repaired geometry is empty")
            return float('inf')

        orig_b = poly_orig.boundary
        if isinstance(poly_repaired, GeometryCollection):
            polys = [g for g in poly_repaired.geoms if isinstance(g, (Polygon, MultiPolygon)) and not g.is_empty]
            non_polys = [g for g in poly_repaired.geoms if not isinstance(g, (Polygon, MultiPolygon)) and not g.is_empty]
            
            if not polys:
                if fail_closed:
                    raise GeometryComparisonError("Repaired geometry contains no 2D polygonal components")
                return float('inf')

            # Ensure all non-polygonal elements are valid recognized types (LineString, Point)
            for g in non_polys:
                if not isinstance(g, (LineString, Point)):
                    if fail_closed:
                        raise GeometryComparisonError(
                            f"Repaired GeometryCollection contains unsupported component type '{type(g).__name__}'"
                        )
                    return float('inf')

            flat_polys = []
            for p in polys:
                if isinstance(p, MultiPolygon):
                    flat_polys.extend(list(p.geoms))
                else:
                    flat_polys.append(p)
            rep_b = MultiPolygon(flat_polys).boundary if len(flat_polys) > 1 else flat_polys[0].boundary
        else:
            rep_b = poly_repaired.boundary

        if orig_b is None or rep_b is None or orig_b.is_empty or rep_b.is_empty:
            if fail_closed:
                raise GeometryComparisonError("Boundary geometry is missing or empty")
            return float('inf')

        dist = float(orig_b.hausdorff_distance(rep_b))
        if math.isnan(dist) or math.isinf(dist):
            if fail_closed:
                raise GeometryComparisonError(f"Hausdorff distance calculation produced non-finite value: {dist}")
            return float('inf')
        return dist
    except GeometryComparisonError:
        raise
    except Exception as e:
        if fail_closed:
            raise GeometryComparisonError(f"Boundary deviation comparison failed: {str(e)}") from e
        return float('inf')

class Part:
    """Represents a component/part to be nested. Supports both Polygon and MultiPolygon."""
    def __init__(self, polygon: Union[Polygon, MultiPolygon], part_id: str, quantity: int = 1, metadata: Optional[Dict[str, Any]] = None):
        self.metadata = metadata or {}
        
        is_valid_orig = polygon.is_valid
        num_input_components = len(polygon.geoms) if isinstance(polygon, MultiPolygon) else 1
        num_input_holes = count_geometry_holes(polygon)
        input_area = float(polygon.area)
        
        if not is_valid_orig:
            repaired = make_valid(polygon)
            num_repaired_components = len(repaired.geoms) if isinstance(repaired, (MultiPolygon, GeometryCollection)) else 1
            num_repaired_holes = count_geometry_holes(repaired)
            repaired_area = float(repaired.area)
            
            area_delta = abs(repaired_area - input_area)
            area_delta_pct = (area_delta / input_area) if input_area > 1e-6 else 0.0
            
            comparison_failed = False
            notes = []
            try:
                hausdorff_dist = compute_boundary_deviation(polygon, repaired, fail_closed=True)
            except GeometryComparisonError as e:
                hausdorff_dist = float('inf')
                comparison_failed = True
                notes.append(f"boundary deviation comparison error: {str(e)}")
            
            topology_altered = comparison_failed
            feature_loss_detected = comparison_failed
            
            if num_repaired_components != num_input_components:
                topology_altered = True
                notes.append(f"components: {num_input_components} -> {num_repaired_components}")
                
            if num_repaired_holes != num_input_holes:
                topology_altered = True
                notes.append(f"holes: {num_input_holes} -> {num_repaired_holes}")
                
            max_area_delta_pct = float(self.metadata.get("max_area_delta_pct", 0.01))
            if input_area > 1e-4 and area_delta_pct > max_area_delta_pct:
                topology_altered = True
                notes.append(f"area: {input_area:.2f} -> {repaired_area:.2f} (delta {area_delta_pct*100.0:.2f}%)")
                
            if isinstance(repaired, GeometryCollection):
                topology_altered = True
                notes.append("repair produced non-polygonal elements (GeometryCollection)")
                
            max_dev_threshold = float(self.metadata.get("max_boundary_deviation", 0.5))
            if hausdorff_dist > max_dev_threshold:
                feature_loss_detected = True
                if not comparison_failed:
                    notes.append(f"boundary deviation {hausdorff_dist:.3f}mm exceeds tolerance {max_dev_threshold:.3f}mm")
                
            repair_authorized = bool(self.metadata.get("allow_repaired_topology", False))
            
            active_overrides = [
                k for k in ["allow_repaired_topology", "allow_unverifiable_geometry", "allow_feature_loss"]
                if bool(self.metadata.get(k, False))
            ]
            self.validation_record = {
                "is_valid_original": False,
                "is_valid_repaired": repaired.is_valid,
                "input_components": num_input_components,
                "repaired_components": num_repaired_components,
                "input_holes": num_input_holes,
                "repaired_holes": num_repaired_holes,
                "original_area": round(input_area, 4),
                "repaired_area": round(repaired_area, 4),
                "area_delta": round(area_delta, 4),
                "area_delta_pct": round(area_delta_pct * 100.0, 3),
                "hausdorff_distance": round(hausdorff_dist, 4) if not math.isinf(hausdorff_dist) else float('inf'),
                "feature_loss_detected": feature_loss_detected,
                "topology_altered": topology_altered,
                "repair_authorized": repair_authorized,
                "active_overrides": active_overrides,
                "notes": notes
            }
            
            if comparison_failed:
                # Fails closed on comparison failure: cannot verify feature preservation
                allow_unverifiable = bool(self.metadata.get("allow_unverifiable_geometry", False))
                if not allow_unverifiable:
                    diag = "; ".join(notes) if notes else "boundary comparison failed"
                    raise GeometryComparisonError(
                        f"Geometry validation failed for part '{part_id}': Boundary deviation comparison failed ({diag}). "
                        f"Cannot verify feature preservation; failing closed to prevent authorizing damaged geometry."
                    )
            
            if (topology_altered or not is_valid_orig) and not repair_authorized:
                diag = "; ".join(notes) if notes else "Input contour is self-intersecting"
                raise CADTopologyError(
                    f"Geometry validation failed for part '{part_id}': Input contour is self-intersecting "
                    f"and repair via make_valid materially altered topology ({diag}). "
                    f"Geometry must be corrected in CAD or explicitly authorized via metadata['allow_repaired_topology']=True."
                )
                
            allow_feature_loss = bool(self.metadata.get("allow_feature_loss", False))
            if feature_loss_detected and not allow_feature_loss:
                dev_str = f"{hausdorff_dist:.3f} mm" if not math.isinf(hausdorff_dist) else "infinite/uncomputed"
                raise CADTopologyError(
                    f"Geometry validation failed for part '{part_id}': Critical feature loss or boundary deviation detected "
                    f"(Hausdorff distance {dev_str} exceeds tolerance {max_dev_threshold:.3f} mm). "
                    f"Automated repair collapsed physical features. Requires explicit metadata['allow_feature_loss']=True."
                )
                
            # If authorized, extract all polygon components without silently discarding any
            if isinstance(repaired, GeometryCollection):
                polys = [g for g in repaired.geoms if isinstance(g, (Polygon, MultiPolygon)) and g.area > 1e-4]
                flat_polys = []
                for p in polys:
                    if isinstance(p, MultiPolygon):
                        flat_polys.extend(list(p.geoms))
                    else:
                        flat_polys.append(p)
                if len(flat_polys) == 1:
                    polygon = flat_polys[0]
                elif len(flat_polys) > 1:
                    polygon = MultiPolygon(flat_polys)
                else:
                    raise CADTopologyError(f"Repaired geometry for part '{part_id}' contains no 2D polygonal area.")
            else:
                polygon = repaired
        else:
            active_overrides = [
                k for k in ["allow_repaired_topology", "allow_unverifiable_geometry", "allow_feature_loss"]
                if bool(self.metadata.get(k, False))
            ]
            self.validation_record = {
                "is_valid_original": True,
                "is_valid_repaired": True,
                "input_components": num_input_components,
                "repaired_components": num_input_components,
                "input_holes": num_input_holes,
                "repaired_holes": num_input_holes,
                "original_area": round(input_area, 4),
                "repaired_area": round(input_area, 4),
                "area_delta": 0.0,
                "area_delta_pct": 0.0,
                "hausdorff_distance": 0.0,
                "feature_loss_detected": False,
                "topology_altered": False,
                "repair_authorized": bool(self.metadata.get("allow_repaired_topology", False)),
                "active_overrides": active_overrides,
                "notes": []
            }
                
        # Preserve all valid components (whether Polygon or MultiPolygon)
        self.polygon = polygon
        self.part_id = part_id
        self.quantity = quantity
        self.area = polygon.area
        self.minx, self.miny, self.maxx, self.maxy = polygon.bounds
        self.width = self.maxx - self.minx
        self.height = self.maxy - self.miny
        
        # Normalize polygon to origin (0, 0)
        self.base_polygon = affinity.translate(polygon, xoff=-self.minx, yoff=-self.miny)
        
    def get_rotated(self, angle_degrees: float) -> Union[Polygon, MultiPolygon]:
        """Returns the base polygon rotated by angle_degrees and normalized to origin."""
        rotated = affinity.rotate(self.base_polygon, angle_degrees, origin='centroid')
        minx, miny, _, _ = rotated.bounds
        return affinity.translate(rotated, xoff=-minx, yoff=-miny)

class Sheet:
    """Represents the raw stock sheet of material."""
    def __init__(self, width: float, height: float, sheet_id: int = 0):
        self.width = width
        self.height = height
        self.sheet_id = sheet_id
        self.polygon = box(0, 0, width, height)
        self.area = width * height
        self.placed_parts: List[Tuple[str, Polygon, float]] = [] # (part_id, placed_polygon, rotation)
        self.part_in_part_assignments: Dict[str, str] = {} # child_part_name -> parent_part_name
        
    def can_contain(self, poly: Polygon, margin: float = 0.0) -> bool:
        """Checks if the sheet strictly contains the polygon within its boundaries with optional margin."""
        minx, miny, maxx, maxy = poly.bounds
        return (minx >= margin - 1e-6 and miny >= margin - 1e-6 and 
                maxx <= self.width - margin + 1e-6 and maxy <= self.height - margin + 1e-6)
        
    def get_utilized_area(self) -> float:
        """Sum of areas of parts placed on this sheet."""
        return sum(poly.area for _, poly, _ in self.placed_parts)
        
    def get_utilization_pct(self) -> float:
        """Returns material utilization percentage."""
        if self.area <= 0:
            return 0.0
        return (self.get_utilized_area() / self.area) * 100.0

    def get_max_x(self) -> float:
        """Maximum horizontal extent (span) of placed parts on this sheet."""
        return max((poly.bounds[2] for _, poly, _ in self.placed_parts), default=0.0)

    def get_max_y(self) -> float:
        """Maximum vertical extent (span) of placed parts on this sheet."""
        return max((poly.bounds[3] for _, poly, _ in self.placed_parts), default=0.0)

    def get_occupied_box_area(self) -> float:
        """Area of the bounding box spanning from (0,0) to (max_x, max_y)."""
        return self.get_max_x() * self.get_max_y()

    def get_remnant_geometry(self) -> Dict[str, Any]:
        """
        Calculates the intact rectangular virgin plate remaining on the right side of the sheet.
        Prime remnant threshold: remnant width >= 100mm.
        """
        max_x = self.get_max_x()
        rem_w = max(0.0, self.width - max_x)
        rem_h = self.height
        rem_area = rem_w * rem_h
        rem_pct = (rem_area / self.area * 100.0) if self.area > 0 else 0.0
        return {
            "max_x_span": round(max_x, 2),
            "max_y_span": round(self.get_max_y(), 2),
            "occupied_box_area": round(self.get_occupied_box_area(), 2),
            "remnant_width": round(rem_w, 2),
            "remnant_height": round(rem_h, 2),
            "remnant_area": round(rem_area, 2),
            "remnant_pct": round(rem_pct, 2),
            "is_prime_remnant": rem_w >= 100.0
        }

def check_collision(candidate_poly: Polygon, 
                    placed_polygons: List[Polygon], 
                    clearance: float = 0.0) -> bool:
    """
    Checks if candidate_poly intersects with any already placed polygon.
    If clearance > 0, an offset buffer is applied ONCE to the candidate.
    """
    if clearance > 0.0:
        buffered_candidate = candidate_poly.buffer(clearance, join_style='round')
    else:
        buffered_candidate = candidate_poly
        
    c_minx, c_miny, c_maxx, c_maxy = buffered_candidate.bounds
    
    for placed in placed_polygons:
        # Fast bounding box rejection
        p_minx, p_miny, p_maxx, p_maxy = placed.bounds
        if c_maxx < p_minx or c_minx > p_maxx or c_maxy < p_miny or c_miny > p_maxy:
            continue
            
        # Exact irregular polygon intersection
        if buffered_candidate.intersects(placed):
            intersection = buffered_candidate.intersection(placed)
            if intersection.area > 1e-4:
                return True
    return False

def compute_hole_feasible_regions(poly: Union[Polygon, MultiPolygon], clearance: float = 0.0) -> List[Polygon]:
    """
    Computes inward-buffered feasible placement regions for each interior hole of a polygon (or multipolygon).
    For each interior ring H:
      H_poly = Polygon(H.coords)
      H_feas = H_poly.buffer(-clearance, join_style='mitre') if clearance > 0 else H_poly
    Returns a list of non-empty Polygon feasible regions.
    """
    feasible_regions = []
    sub_polys = poly.geoms if isinstance(poly, MultiPolygon) else [poly]
    for sub in sub_polys:
        if not hasattr(sub, 'interiors') or not sub.interiors:
            continue
            
        for interior in sub.interiors:
            hole_poly = Polygon(interior.coords)
            if not hole_poly.is_valid:
                hole_poly = make_valid(hole_poly)
                
            if clearance > 0.0:
                h_feas = hole_poly.buffer(-clearance, join_style='mitre')
            else:
                h_feas = hole_poly
                
            if not h_feas.is_empty and h_feas.area > 1e-4:
                if isinstance(h_feas, MultiPolygon):
                    for g in h_feas.geoms:
                        if g.area > 1e-4 and g.is_valid:
                            feasible_regions.append(g)
                elif h_feas.is_valid:
                    feasible_regions.append(h_feas)
                    
    return feasible_regions

def get_allowed_rotations(part: Optional[Part] = None,
                          rotation_mode: str = "orthogonal",
                          grain_direction: Optional[str] = None) -> List[float]:
    """
    Returns allowed rotation angles (degrees) based on rotation_mode and grain restrictions.
    
    rotation_mode:
      - 'orthogonal' (default): [0.0, 90.0, 180.0, 270.0]
      - 'adaptive': 15-degree coarse exploration [0.0, 15.0, ..., 345.0] (24 angles)
      - 'none': [0.0]
      
    grain_direction / part.metadata grain:
      - 'horizontal': restricted strictly to [0.0, 180.0]
      - 'vertical': restricted strictly to [90.0, 270.0]
      - None / 'any': unconstrained rolling direction
    """
    grain = None
    if part is not None and hasattr(part, 'metadata') and part.metadata:
        grain = part.metadata.get("grain_direction") or part.metadata.get("grain_constraint")
    if grain is None:
        grain = grain_direction
        
    if grain == "horizontal":
        return [0.0, 180.0]
    elif grain == "vertical":
        return [90.0, 270.0]
        
    if rotation_mode == "adaptive":
        return [float(a) for a in range(0, 360, 15)]
    elif rotation_mode == "none":
        return [0.0]
    else:  # default 'orthogonal'
        return [0.0, 90.0, 180.0, 270.0]

def get_refined_rotation_angles(best_angle: float,
                                grain_direction: Optional[str] = None) -> List[float]:
    """
    Generates 5-degree local refinement angles around a best coarse angle.
    [best - 10, best - 5, best, best + 5, best + 10] (mod 360).
    Respects grain restrictions.
    """
    if grain_direction in ("horizontal", "vertical"):
        return [best_angle]
    deltas = [-10.0, -5.0, 0.0, 5.0, 10.0]
    refined = set()
    for d in deltas:
        angle = (best_angle + d) % 360.0
        refined.add(round(angle, 1))
    return sorted(refined)
