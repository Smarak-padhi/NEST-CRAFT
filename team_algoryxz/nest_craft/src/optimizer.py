"""
optimizer.py
Simulated Annealing metaheuristic for irregular polygon nesting.
Optimizes placement sequence and part rotation angles using Metropolis acceptance.
"""

import time
import math
import random
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from shapely.geometry import Polygon

from .geometry import (
    Part, Sheet, get_allowed_rotations, get_refined_rotation_angles
)
from .baseline import run_bottom_left_fill, place_part_bottom_left, place_part_in_holes

def calculate_solution_energy(sheets: List[Sheet]) -> float:
    """
    Computes energy to minimize:
    Lower energy = fewer sheets, tighter compact packing, higher utilization.
    """
    if not sheets:
        return float('inf')
        
    num_sheets = len(sheets)
    total_area = sum(s.area for s in sheets)
    used_area = sum(s.get_utilized_area() for s in sheets)
    utilization_ratio = used_area / total_area if total_area > 0 else 0.0
    
    # Maximum x extent on the last sheet (encourages parts to hug the left edge)
    last_sheet = sheets[-1]
    max_x = 0.0
    for _, poly, _ in last_sheet.placed_parts:
        max_x = max(max_x, poly.bounds[2])
    span_fraction = max_x / last_sheet.width if last_sheet.width > 0 else 1.0
    
    # Energy: Primary weight on sheet count, secondary on span, negative bonus on utilization
    energy = (num_sheets * 500.0) + (span_fraction * 100.0) - (utilization_ratio * 150.0)
    return energy

def run_simulated_annealing(parts: List[Part],
                            sheet_width: float,
                            sheet_height: float,
                            clearance: float = 0.0,
                            allowed_rotations: Optional[List[float]] = None,
                            rotation_mode: str = "orthogonal",
                            grain_direction: Optional[str] = None,
                            max_iterations: int = 40,
                            initial_temp: float = 100.0,
                            cooling_rate: float = 0.90,
                            step_size: float = 2.0,
                            random_seed: Optional[int] = 42,
                            allow_part_in_part: bool = True) -> Tuple[List[Sheet], Dict[str, Any]]:
    """
    Simulated Annealing optimization over part ordering and discrete rotation angles.
    If allow_part_in_part is True, evaluates placing eligible parts into interior holes.
    Supports rotation_mode: 'orthogonal' (0, 90, 180, 270) or 'adaptive' (15-deg coarse + 5-deg fine).
    Respects grain_direction ('horizontal', 'vertical', or None).
    """
    start_time = time.time()
    if random_seed is not None:
        random.seed(random_seed)
        np.random.seed(random_seed)
        
    # Flatten parts
    flat_parts = []
    for p in parts:
        for q in range(p.quantity):
            # (part_id, Part_obj, initial_rotation)
            p_rots = allowed_rotations if allowed_rotations is not None else get_allowed_rotations(
                p, rotation_mode=rotation_mode, grain_direction=grain_direction
            )
            rot = random.choice(p_rots)
            flat_parts.append({"name": f"{p.part_id}_{q+1}", "part": p, "rot": rot})
            
    # Initial evaluation
    def evaluate_state(state):
        # Pack state in sequential order
        sheets = [Sheet(sheet_width, sheet_height, sheet_id=1)]
        
        for item in state:
            p = item["part"]
            rot = item["rot"]
            rot_poly = p.get_rotated(rot)
            placed = False
            
            # Priority 1: Check hole placement
            if allow_part_in_part:
                for s in sheets:
                    h_place = place_part_in_holes(s, rot_poly, clearance=clearance, step_size=step_size)
                    if h_place is not None:
                        s.placed_parts.append((item["name"], h_place[2], rot))
                        s.part_in_part_assignments[item["name"]] = h_place[3]
                        placed = True
                        break
                        
            # Priority 2: Check exterior placement
            if not placed:
                for s in sheets:
                    placement = place_part_bottom_left(s, rot_poly, clearance=clearance, 
                                                       step_x=step_size, step_y=step_size)
                    if placement is not None:
                        s.placed_parts.append((item["name"], placement[2], rot))
                        placed = True
                        break
                        
            if not placed:
                new_s = Sheet(sheet_width, sheet_height, sheet_id=len(sheets) + 1)
                placement = place_part_bottom_left(new_s, rot_poly, clearance=clearance, 
                                                   step_x=step_size, step_y=step_size)
                if placement is not None:
                    new_s.placed_parts.append((item["name"], placement[2], rot))
                sheets.append(new_s)
                
        return sheets, calculate_solution_energy(sheets)

    # Sort initial state by descending area (Decreasing Area Heuristic starting point)
    flat_parts.sort(key=lambda item: item["part"].area, reverse=True)
    current_state = list(flat_parts)
    best_sheets, current_energy = evaluate_state(current_state)
    best_energy = current_energy
    best_state = list(current_state)
    
    temp = initial_temp
    history = []
    
    for iteration in range(max_iterations):
        # Generate neighbor: 3 mutation types
        # 1. Swap two parts
        # 2. Rotate a part
        # 3. Invert sub-sequence (2-opt)
        neighbor_state = [dict(item) for item in current_state]
        move_type = random.random()
        
        if move_type < 0.45 and len(neighbor_state) > 1:
            # Swap
            idx1, idx2 = random.sample(range(len(neighbor_state)), 2)
            neighbor_state[idx1], neighbor_state[idx2] = neighbor_state[idx2], neighbor_state[idx1]
        elif move_type < 0.75:
            # Rotate
            idx = random.randrange(len(neighbor_state))
            target_item = neighbor_state[idx]
            p = target_item["part"]
            p_rots = allowed_rotations if allowed_rotations is not None else get_allowed_rotations(
                p, rotation_mode=rotation_mode, grain_direction=grain_direction
            )
            
            # If adaptive mode and allowed_rotations was not explicitly fixed, choose between coarse jump and fine 5-deg perturbation
            if rotation_mode == "adaptive" and allowed_rotations is None and random.random() < 0.5:
                part_grain = p.metadata.get("grain_direction") or p.metadata.get("grain_constraint") or grain_direction
                if part_grain in ("horizontal", "vertical"):
                    neighbor_state[idx]["rot"] = random.choice(p_rots)
                else:
                    cur_rot = target_item["rot"]
                    delta = random.choice([-10.0, -5.0, 5.0, 10.0])
                    neighbor_state[idx]["rot"] = round((cur_rot + delta) % 360.0, 1)
            else:
                neighbor_state[idx]["rot"] = random.choice(p_rots)
        elif len(neighbor_state) > 2:
            # Sub-sequence inversion
            idx1 = random.randrange(len(neighbor_state) - 1)
            idx2 = random.randint(idx1 + 1, len(neighbor_state))
            neighbor_state[idx1:idx2] = reversed(neighbor_state[idx1:idx2])
            
        candidate_sheets, candidate_energy = evaluate_state(neighbor_state)
        delta_energy = candidate_energy - current_energy
        
        # Metropolis acceptance
        if delta_energy < 0 or (temp > 1e-4 and random.random() < math.exp(-delta_energy / temp)):
            current_state = neighbor_state
            current_energy = candidate_energy
            
            if candidate_energy < best_energy:
                best_energy = candidate_energy
                best_sheets = candidate_sheets
                best_state = neighbor_state
                
        history.append({
            "iteration": iteration + 1,
            "temp": round(temp, 2),
            "current_energy": round(current_energy, 2),
            "best_energy": round(best_energy, 2)
        })
        
        temp *= cooling_rate
        
    elapsed_time = time.time() - start_time
    total_sheet_area = sum(s.area for s in best_sheets)
    total_used_area = sum(s.get_utilized_area() for s in best_sheets)
    overall_utilization = (total_used_area / total_sheet_area * 100.0) if total_sheet_area > 0 else 0.0
    
    total_placed = sum(len(s.placed_parts) for s in best_sheets)
    unplaced_count = len(flat_parts) - total_placed
    
    # Calculate per-sheet linear extents and remnant metrics
    per_sheet_metrics = []
    for s_idx, s in enumerate(best_sheets):
        per_sheet_metrics.append({
            "sheet_id": s_idx + 1,
            "parts_placed": len(s.placed_parts),
            "utilized_area": round(s.get_utilized_area(), 2),
            "utilization_pct": round(s.get_utilization_pct(), 2),
            **s.get_remnant_geometry()
        })
        
    # Total linear length consumed across sheets (coil or discrete strip)
    if best_sheets:
        final_sheet = best_sheets[-1]
        final_max_x = final_sheet.get_max_x()
        total_linear_consumed = (len(best_sheets) - 1) * sheet_width + final_max_x
        total_linear_available = len(best_sheets) * sheet_width
        final_remnant = final_sheet.get_remnant_geometry()
        strip_area = sheet_height * total_linear_consumed if total_linear_consumed > 0 else 0.0
        continuous_strip_util_pct = (total_used_area / strip_area * 100.0) if strip_area > 0 else 0.0
    else:
        total_linear_consumed = 0.0
        total_linear_available = 0.0
        final_remnant = {}
        continuous_strip_util_pct = 0.0
        
    stats = {
        "algorithm": "Simulated Annealing Optimizer",
        "iterations": max_iterations,
        "sheets_used": len(best_sheets),
        "total_parts_nested": total_placed,
        "total_parts_requested": len(flat_parts),
        "unplaced_parts": max(0, unplaced_count),
        "rotation_mode": rotation_mode,
        "grain_direction": grain_direction,
        "allow_part_in_part": allow_part_in_part,
        "parts_nested_in_holes": sum(len(s.part_in_part_assignments) for s in best_sheets),
        "part_in_part_assignments": {name: parent for s in best_sheets for name, parent in s.part_in_part_assignments.items()},
        "utilization_pct": round(overall_utilization, 2),
        "scrap_pct": round(100.0 - overall_utilization, 2),
        "total_sheet_area": round(total_sheet_area, 2),
        "utilized_area": round(total_used_area, 2),
        "runtime_seconds": round(elapsed_time, 3),
        "total_linear_length_consumed": round(total_linear_consumed, 2),
        "total_linear_stock_available": round(total_linear_available, 2),
        "continuous_strip_utilization_pct": round(continuous_strip_util_pct, 2),
        "final_sheet_remnant": final_remnant,
        "per_sheet_metrics": per_sheet_metrics,
        "history": history
    }
    
    return best_sheets, stats
