"""
test_benchmark_reproducibility.py
Dedicated regression test that locks the complete historical Stage C benchmark configuration,
validates parameters against the committed reference, records per-seed outputs, and asserts
exact deterministic reproducibility.
"""

import os
import pytest
import numpy as np

from team_algoryxz.nest_craft.src.geometry import Part
from team_algoryxz.nest_craft.src.dxf_io import create_sample_industrial_dxfs, parse_dxf
from team_algoryxz.nest_craft.src.baseline import run_bottom_left_fill
from team_algoryxz.nest_craft.src.optimizer import run_simulated_annealing

# Pinned historical reference configuration from Stage C / benchmark_reconciliation_raw.json
HISTORICAL_CONFIG = {
    "total_parts": 17,
    "part_quantities": {
        "gusset_plate.dxf": 4,
        "l_bracket.dxf": 6,
        "flange_plate.dxf": 4,
        "notched_base_plate.dxf": 3
    },
    "sheet_width": 800.0,
    "sheet_height": 500.0,
    "clearance": 4.0,
    "step_size": 8.0,
    "rotations": [0.0, 90.0, 180.0, 270.0],
    "max_iterations": 20,
    "initial_temp": 100.0,
    "cooling_rate": 0.85,
    "seeds": [42, 101, 202, 303, 404]
}

# Committed historical reference outputs (Stage C Reconciliation)
EXPECTED_OUTPUTS = {
    "blf": {
        "sheets_used": 3,
        "total_linear_length_consumed": 2350.00,
        "utilization_pct": 46.67,
        "remnant_width": 50.00,
        "estimated_geometric_remnant": False
    },
    "sa_per_seed": {
        42: {
            "sheets_used": 3,
            "total_linear_length_consumed": 1966.0,
            "remnant_width": 434.0,
            "estimated_geometric_remnant": True
        },
        101: {
            "sheets_used": 3,
            "total_linear_length_consumed": 2110.0,
            "remnant_width": 290.0,
            "estimated_geometric_remnant": True
        },
        202: {
            "sheets_used": 3,
            "total_linear_length_consumed": 1742.0,
            "remnant_width": 658.0,
            "estimated_geometric_remnant": True
        },
        303: {
            "sheets_used": 3,
            "total_linear_length_consumed": 1986.0,
            "remnant_width": 414.0,
            "estimated_geometric_remnant": True
        },
        404: {
            "sheets_used": 3,
            "total_linear_length_consumed": 1926.0,
            "remnant_width": 474.0,
            "estimated_geometric_remnant": True
        }
    },
    "sa_5_seed_mean_linear": 1946.00,
    "sa_linear_saved_mean": 404.00,
    "sa_linear_compaction_pct": 17.19
}

@pytest.fixture(scope="module")
def loaded_industrial_batch():
    """Loads and returns the standard 17-part industrial benchmark batch."""
    sample_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data", "industrial_samples")
    )
    dxf_files = create_sample_industrial_dxfs(sample_dir)
    assert len(dxf_files) == 4, f"Expected 4 sample DXF files, found {len(dxf_files)}"

    parts = []
    for f in dxf_files:
        base = os.path.basename(f)
        parsed = parse_dxf(f)
        qty = HISTORICAL_CONFIG["part_quantities"].get(base, 0)
        assert qty > 0, f"Unrecognized sample file '{base}'"
        for p in parsed:
            p.quantity = qty
            parts.append(p)

    total_qty = sum(p.quantity for p in parts)
    assert total_qty == HISTORICAL_CONFIG["total_parts"], (
        f"Expected {HISTORICAL_CONFIG['total_parts']} parts, got {total_qty}"
    )
    return parts

def test_benchmark_configuration_integrity():
    """Verify that configuration constants strictly match the historical reference."""
    assert HISTORICAL_CONFIG["sheet_width"] == 800.0
    assert HISTORICAL_CONFIG["sheet_height"] == 500.0
    assert HISTORICAL_CONFIG["clearance"] == 4.0
    assert HISTORICAL_CONFIG["step_size"] == 8.0
    assert HISTORICAL_CONFIG["max_iterations"] == 20
    assert HISTORICAL_CONFIG["initial_temp"] == 100.0
    assert HISTORICAL_CONFIG["cooling_rate"] == 0.85
    assert HISTORICAL_CONFIG["seeds"] == [42, 101, 202, 303, 404]

def test_blf_baseline_reproducibility(loaded_industrial_batch):
    """Verify that BLF baseline exactly reproduces historical linear extent and sheet count."""
    sheets, stats = run_bottom_left_fill(
        loaded_industrial_batch,
        sheet_width=HISTORICAL_CONFIG["sheet_width"],
        sheet_height=HISTORICAL_CONFIG["sheet_height"],
        clearance=HISTORICAL_CONFIG["clearance"],
        allowed_rotations=HISTORICAL_CONFIG["rotations"],
        step_size=HISTORICAL_CONFIG["step_size"]
    )

    exp = EXPECTED_OUTPUTS["blf"]
    assert stats["sheets_used"] == exp["sheets_used"]
    assert stats["total_linear_length_consumed"] == exp["total_linear_length_consumed"]
    assert pytest.approx(stats["utilization_pct"], abs=0.01) == exp["utilization_pct"]

    rem = stats["final_sheet_remnant"]
    assert rem["remnant_width"] == exp["remnant_width"]
    assert rem["estimated_geometric_remnant"] == exp["estimated_geometric_remnant"]

@pytest.mark.parametrize("seed", HISTORICAL_CONFIG["seeds"])
def test_sa_per_seed_reproducibility(loaded_industrial_batch, seed):
    """Verify that each individual SA seed reproduces the exact historical output."""
    sheets, stats = run_simulated_annealing(
        loaded_industrial_batch,
        sheet_width=HISTORICAL_CONFIG["sheet_width"],
        sheet_height=HISTORICAL_CONFIG["sheet_height"],
        clearance=HISTORICAL_CONFIG["clearance"],
        allowed_rotations=HISTORICAL_CONFIG["rotations"],
        max_iterations=HISTORICAL_CONFIG["max_iterations"],
        initial_temp=HISTORICAL_CONFIG["initial_temp"],
        cooling_rate=HISTORICAL_CONFIG["cooling_rate"],
        step_size=HISTORICAL_CONFIG["step_size"],
        random_seed=seed
    )

    exp = EXPECTED_OUTPUTS["sa_per_seed"][seed]
    assert stats["sheets_used"] == exp["sheets_used"], f"Seed {seed} sheets used mismatch"
    assert stats["total_linear_length_consumed"] == exp["total_linear_length_consumed"], (
        f"Seed {seed} linear consumed: {stats['total_linear_length_consumed']} != expected {exp['total_linear_length_consumed']}"
    )

    rem = stats["final_sheet_remnant"]
    assert rem["remnant_width"] == exp["remnant_width"], f"Seed {seed} remnant width mismatch"
    assert rem["estimated_geometric_remnant"] == exp["estimated_geometric_remnant"]

def test_sa_five_seed_mean_reproducibility(loaded_industrial_batch):
    """Verify that the 5-seed mean linear extent reproduces 1,946.00 mm and 17.19% compaction."""
    linears = []
    for s in HISTORICAL_CONFIG["seeds"]:
        _, stats = run_simulated_annealing(
            loaded_industrial_batch,
            sheet_width=HISTORICAL_CONFIG["sheet_width"],
            sheet_height=HISTORICAL_CONFIG["sheet_height"],
            clearance=HISTORICAL_CONFIG["clearance"],
            allowed_rotations=HISTORICAL_CONFIG["rotations"],
            max_iterations=HISTORICAL_CONFIG["max_iterations"],
            initial_temp=HISTORICAL_CONFIG["initial_temp"],
            cooling_rate=HISTORICAL_CONFIG["cooling_rate"],
            step_size=HISTORICAL_CONFIG["step_size"],
            random_seed=s
        )
        linears.append(stats["total_linear_length_consumed"])

    mean_lin = round(float(np.mean(linears)), 2)
    assert mean_lin == EXPECTED_OUTPUTS["sa_5_seed_mean_linear"], (
        f"5-seed mean linear extent {mean_lin} != {EXPECTED_OUTPUTS['sa_5_seed_mean_linear']}"
    )

    saved_mean = EXPECTED_OUTPUTS["blf"]["total_linear_length_consumed"] - mean_lin
    assert saved_mean == EXPECTED_OUTPUTS["sa_linear_saved_mean"]

    compaction_pct = round(saved_mean / EXPECTED_OUTPUTS["blf"]["total_linear_length_consumed"] * 100.0, 2)
    assert compaction_pct == EXPECTED_OUTPUTS["sa_linear_compaction_pct"]
