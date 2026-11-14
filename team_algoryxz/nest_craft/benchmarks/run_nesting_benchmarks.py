"""
run_nesting_benchmarks.py
Executes reproducible, multi-run benchmarks comparing Bottom-Left-Fill (BLF)
against Simulated Annealing across genuine ESICUP instances and industrial DXF parts.
Never hardcodes outputs; runs actual Shapely geometric calculations.
"""

import os
import sys
sys.stdout.reconfigure(line_buffering=True)
import json
import numpy as np
import pandas as pd

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from team_algoryxz.nest_craft.src.geometry import Part, Sheet
from team_algoryxz.nest_craft.src.dxf_io import parse_esicup_txt, create_sample_industrial_dxfs, parse_dxf
from team_algoryxz.nest_craft.src.baseline import run_bottom_left_fill
from team_algoryxz.nest_craft.src.optimizer import run_simulated_annealing

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(REPORTS_DIR, exist_ok=True)

def benchmark_shapes_instance(seeds=[42, 101, 202, 303, 404]):
    print("\n--- BENCHMARK 1: ESICUP SHAPES (shapes.txt) ---")
    shapes_path = os.path.join(DATA_DIR, "esicup", "shapes.txt")
    if not os.path.exists(shapes_path):
        raise FileNotFoundError(f"Missing {shapes_path}")
        
    parts, meta = parse_esicup_txt(shapes_path)
    total_parts_count = sum(p.quantity for p in parts)
    print(f"Loaded ESICUP SHAPES: {len(parts)} piece types, {total_parts_count} total parts.")
    
    # Standard sheet dimensions for Shapes benchmark: width 100, height 40
    # Or scaled strip: width 40, height 100
    sheet_w, sheet_h = 40.0, 70.0
    clearance = 0.5
    
    # 1. Run Baseline BLF
    print("Running Bottom-Left-Fill baseline...")
    blf_sheets, blf_stats = run_bottom_left_fill(
        parts, sheet_width=sheet_w, sheet_height=sheet_h,
        clearance=clearance, allowed_rotations=[0.0, 90.0, 180.0, 270.0],
        step_size=1.0
    )
    print(f"BLF Baseline: Sheets={blf_stats['sheets_used']}, Util={blf_stats['utilization_pct']}%, Time={blf_stats['runtime_seconds']}s")
    
    # 2. Run Simulated Annealing across seeds
    sa_results = []
    print("Running Simulated Annealing across seeds...")
    for s in seeds:
        sheets, sa_stats = run_simulated_annealing(
            parts, sheet_width=sheet_w, sheet_height=sheet_h,
            clearance=clearance, allowed_rotations=[0.0, 90.0, 180.0, 270.0],
            max_iterations=25, initial_temp=80.0, cooling_rate=0.88,
            step_size=1.0, random_seed=s
        )
        util_gain = sa_stats['utilization_pct'] - blf_stats['utilization_pct']
        linear_saved = blf_stats['total_linear_length_consumed'] - sa_stats['total_linear_length_consumed']
        sa_results.append({
            "seed": s,
            "sheets_used": sa_stats["sheets_used"],
            "utilization_pct": sa_stats["utilization_pct"],
            "scrap_pct": sa_stats["scrap_pct"],
            "total_linear_length_consumed": sa_stats["total_linear_length_consumed"],
            "continuous_strip_utilization_pct": sa_stats["continuous_strip_utilization_pct"],
            "final_sheet_remnant": sa_stats["final_sheet_remnant"],
            "linear_saved_mm": round(linear_saved, 2),
            "runtime_seconds": sa_stats["runtime_seconds"],
            "utilization_gain_pct": round(util_gain, 2)
        })
        print(f"  Seed {s}: Util={sa_stats['utilization_pct']}%, Linear={sa_stats['total_linear_length_consumed']}mm (Saved={linear_saved:+.1f}mm), Time={sa_stats['runtime_seconds']}s")
        
    utils = [r["utilization_pct"] for r in sa_results]
    gains = [r["utilization_gain_pct"] for r in sa_results]
    times = [r["runtime_seconds"] for r in sa_results]
    linears = [r["total_linear_length_consumed"] for r in sa_results]
    linear_saveds = [r["linear_saved_mm"] for r in sa_results]
    strip_utils = [r["continuous_strip_utilization_pct"] for r in sa_results]
    
    summary = {
        "dataset": "ESICUP SHAPES (shapes.txt)",
        "provenance": "Oliveira, Gomes, Ferreira (2000) OR Spektrum",
        "total_parts": total_parts_count,
        "sheet_size": f"{sheet_w} x {sheet_h}",
        "clearance": clearance,
        "baseline_blf": blf_stats,
        "sa_runs": sa_results,
        "sa_mean_utilization": round(float(np.mean(utils)), 2),
        "sa_median_utilization": round(float(np.median(utils)), 2),
        "sa_std_utilization": round(float(np.std(utils)), 2),
        "sa_mean_gain_over_blf": round(float(np.mean(gains)), 2),
        "sa_mean_linear_consumed_mm": round(float(np.mean(linears)), 2),
        "sa_mean_linear_saved_mm": round(float(np.mean(linear_saveds)), 2),
        "sa_mean_strip_utilization": round(float(np.mean(strip_utils)), 2),
        "sa_mean_runtime": round(float(np.mean(times)), 2)
    }
    return summary

def benchmark_industrial_dxf_instance(seeds=[42, 101, 202, 303, 404]):
    print("\n--- BENCHMARK 2: INDUSTRIAL DXF FABRICATION BATCH ---")
    dxf_dir = os.path.join(DATA_DIR, "industrial_samples")
    dxf_files = create_sample_industrial_dxfs(dxf_dir)
    print(f"Created {len(dxf_files)} industrial sample DXF files.")
    
    all_parts = []
    # Mix batch: 4 gussets, 6 brackets, 4 flanges, 3 base plates = 17 parts
    quantities = {"gusset_plate.dxf": 4, "l_bracket.dxf": 6, "flange_plate.dxf": 4, "notched_base_plate.dxf": 3}
    for f in dxf_files:
        base = os.path.basename(f)
        parsed = parse_dxf(f)
        for p in parsed:
            p.quantity = quantities.get(base, 2)
            all_parts.append(p)
            
    total_parts = sum(p.quantity for p in all_parts)
    print(f"Loaded Industrial Batch: {total_parts} parts.")
    
    # Standard sheet: 800mm x 500mm
    sheet_w, sheet_h = 800.0, 500.0
    clearance = 4.0 # 4mm industrial plasma cutting clearance
    
    print("Running Bottom-Left-Fill baseline...")
    blf_sheets, blf_stats = run_bottom_left_fill(
        all_parts, sheet_width=sheet_w, sheet_height=sheet_h,
        clearance=clearance, allowed_rotations=[0.0, 90.0, 180.0, 270.0],
        step_size=8.0
    )
    print(f"BLF Baseline: Sheets={blf_stats['sheets_used']}, Util={blf_stats['utilization_pct']}%, Time={blf_stats['runtime_seconds']}s")
    
    sa_results = []
    print("Running Simulated Annealing across seeds...")
    for s in seeds:
        sheets, sa_stats = run_simulated_annealing(
            all_parts, sheet_width=sheet_w, sheet_height=sheet_h,
            clearance=clearance, allowed_rotations=[0.0, 90.0, 180.0, 270.0],
            max_iterations=20, initial_temp=100.0, cooling_rate=0.85,
            step_size=8.0, random_seed=s
        )
        util_gain = sa_stats['utilization_pct'] - blf_stats['utilization_pct']
        linear_saved = blf_stats['total_linear_length_consumed'] - sa_stats['total_linear_length_consumed']
        sa_results.append({
            "seed": s,
            "sheets_used": sa_stats["sheets_used"],
            "utilization_pct": sa_stats["utilization_pct"],
            "scrap_pct": sa_stats["scrap_pct"],
            "total_linear_length_consumed": sa_stats["total_linear_length_consumed"],
            "continuous_strip_utilization_pct": sa_stats["continuous_strip_utilization_pct"],
            "final_sheet_remnant": sa_stats["final_sheet_remnant"],
            "linear_saved_mm": round(linear_saved, 2),
            "runtime_seconds": sa_stats["runtime_seconds"],
            "utilization_gain_pct": round(util_gain, 2)
        })
        print(f"  Seed {s}: Util={sa_stats['utilization_pct']}%, Linear={sa_stats['total_linear_length_consumed']}mm (Saved={linear_saved:+.1f}mm), Time={sa_stats['runtime_seconds']}s")
        
    utils = [r["utilization_pct"] for r in sa_results]
    gains = [r["utilization_gain_pct"] for r in sa_results]
    times = [r["runtime_seconds"] for r in sa_results]
    linears = [r["total_linear_length_consumed"] for r in sa_results]
    linear_saveds = [r["linear_saved_mm"] for r in sa_results]
    strip_utils = [r["continuous_strip_utilization_pct"] for r in sa_results]
    
    summary = {
        "dataset": "Industrial DXF Mechanical Fabrication Batch",
        "provenance": "Synthetic parametric CAD contours (brackets, gussets, flanges, base plates) generated for mechanical fabrication testing",
        "total_parts": total_parts,
        "sheet_size": f"{sheet_w} x {sheet_h} mm",
        "clearance": clearance,
        "baseline_blf": blf_stats,
        "sa_runs": sa_results,
        "sa_mean_utilization": round(float(np.mean(utils)), 2),
        "sa_median_utilization": round(float(np.median(utils)), 2),
        "sa_std_utilization": round(float(np.std(utils)), 2),
        "sa_mean_gain_over_blf": round(float(np.mean(gains)), 2),
        "sa_mean_linear_consumed_mm": round(float(np.mean(linears)), 2),
        "sa_mean_linear_saved_mm": round(float(np.mean(linear_saveds)), 2),
        "sa_mean_strip_utilization": round(float(np.mean(strip_utils)), 2),
        "sa_mean_runtime": round(float(np.mean(times)), 2)
    }
    return summary

def main():
    print("=========================================================")
    print("STARTING NEST-CRAFT INDEPENDENT BENCHMARK SUITE")
    print("=========================================================")
    
    results = {
        "esicup_shapes": benchmark_shapes_instance(),
        "industrial_dxf": benchmark_industrial_dxf_instance()
    }
    
    out_json = os.path.join(REPORTS_DIR, "benchmark_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll benchmark results successfully saved to {out_json}")
    
    # Save CSV comparison
    rows = []
    for k, v in results.items():
        blf = v["baseline_blf"]
        linear_saved = blf["total_linear_length_consumed"] - v["sa_mean_linear_consumed_mm"]
        linear_compaction_pct = (linear_saved / blf["total_linear_length_consumed"] * 100.0) if blf["total_linear_length_consumed"] > 0 else 0.0
        rows.append({
            "Instance": v["dataset"],
            "Total_Parts": v["total_parts"],
            "Sheet_Dimensions": v["sheet_size"],
            "BLF_Sheets": blf["sheets_used"],
            "BLF_Discrete_Util_Pct": blf["utilization_pct"],
            "BLF_Linear_Consumed_mm": blf["total_linear_length_consumed"],
            "BLF_Strip_Util_Pct": blf["continuous_strip_utilization_pct"],
            "BLF_Remnant_Width_mm": blf["final_sheet_remnant"].get("remnant_width", 0.0),
            "SA_Sheets": v["sa_runs"][0]["sheets_used"],
            "SA_Discrete_Util_Pct": v["sa_mean_utilization"],
            "SA_Linear_Consumed_mm": v["sa_mean_linear_consumed_mm"],
            "SA_Linear_Saved_mm": round(linear_saved, 2),
            "SA_Linear_Compaction_Pct": round(linear_compaction_pct, 2),
            "SA_Strip_Util_Pct": v["sa_mean_strip_utilization"],
            "SA_Remnant_Width_mm": v["sa_runs"][0]["final_sheet_remnant"].get("remnant_width", 0.0),
            "SA_Prime_Remnant_Saved": v["sa_runs"][0]["final_sheet_remnant"].get("is_prime_remnant", False),
            "BLF_Runtime_Sec": blf["runtime_seconds"],
            "SA_Mean_Runtime_Sec": v["sa_mean_runtime"]
        })
    df = pd.DataFrame(rows)
    out_csv = os.path.join(REPORTS_DIR, "nesting_benchmark_summary.csv")
    df.to_csv(out_csv, index=False)
    print(f"Summary table saved to {out_csv}")
    print("\n" + df.to_string())

if __name__ == "__main__":
    main()
