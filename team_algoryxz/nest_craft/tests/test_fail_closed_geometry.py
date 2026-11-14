"""
test_fail_closed_geometry.py
Tests for Stage F Task 1: Fail-closed geometry validation.
Verifies that compute_boundary_deviation() and Part.__init__() fail closed on errors
and never interpret a comparison failure as zero deviation.
"""

import math
import pytest
from unittest.mock import patch
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection, Point, LineString

from team_algoryxz.nest_craft.src.geometry import (
    Part,
    compute_boundary_deviation,
    CADTopologyError,
    GeometryComparisonError
)

def test_compute_boundary_deviation_none_geometry_fails_closed():
    """Verify compute_boundary_deviation raises GeometryComparisonError on None input."""
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    with pytest.raises(GeometryComparisonError) as exc_info:
        compute_boundary_deviation(None, poly, fail_closed=True)
    assert "input geometry is None" in str(exc_info.value)

    with pytest.raises(GeometryComparisonError) as exc_info:
        compute_boundary_deviation(poly, None, fail_closed=True)
    assert "input geometry is None" in str(exc_info.value)

    # When fail_closed=False, returns float('inf'), never 0.0
    assert compute_boundary_deviation(None, poly, fail_closed=False) == float('inf')

def test_compute_boundary_deviation_empty_geometry_fails_closed():
    """Verify compute_boundary_deviation raises on empty geometry."""
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    empty_poly = Polygon()
    with pytest.raises(GeometryComparisonError) as exc_info:
        compute_boundary_deviation(empty_poly, poly, fail_closed=True)
    assert "empty" in str(exc_info.value)

    assert compute_boundary_deviation(empty_poly, poly, fail_closed=False) == float('inf')

def test_compute_boundary_deviation_non_polygonal_collection_fails_closed():
    """Verify compute_boundary_deviation raises if repaired geometry has no 2D components."""
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    gc = GeometryCollection([Point(0, 0), LineString([(0, 0), (5, 5)])])
    with pytest.raises(GeometryComparisonError) as exc_info:
        compute_boundary_deviation(poly, gc, fail_closed=True)
    assert "no 2D polygonal components" in str(exc_info.value)

    assert compute_boundary_deviation(poly, gc, fail_closed=False) == float('inf')

def test_compute_boundary_deviation_geos_exception_fails_closed():
    """Verify any internal GEOS or Hausdorff exception raises GeometryComparisonError, never returns 0.0."""
    poly1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    poly2 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])

    with patch.object(LineString, "hausdorff_distance", side_effect=RuntimeError("GEOS internal error")):
        with pytest.raises(GeometryComparisonError) as exc_info:
            compute_boundary_deviation(poly1, poly2, fail_closed=True)
        assert "Boundary deviation comparison failed" in str(exc_info.value)
        assert "GEOS internal error" in str(exc_info.value)

        # Non-raising mode must return float('inf'), never 0.0
        val = compute_boundary_deviation(poly1, poly2, fail_closed=False)
        assert math.isinf(val)
        assert val > 0

def test_compute_boundary_deviation_nan_fails_closed():
    """Verify NaN Hausdorff distance is rejected as GeometryComparisonError."""
    poly1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    poly2 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])

    with patch.object(LineString, "hausdorff_distance", return_value=float('nan')):
        with pytest.raises(GeometryComparisonError) as exc_info:
            compute_boundary_deviation(poly1, poly2, fail_closed=True)
        assert "non-finite value" in str(exc_info.value)

        assert compute_boundary_deviation(poly1, poly2, fail_closed=False) == float('inf')

def test_part_init_unauthorized_repair_fails_closed_on_comparison_error():
    """Verify Part rejects self-intersecting contour when comparison fails (unauthorized path)."""
    # Self-intersecting bow-tie contour
    bowtie = Polygon([(0, 0), (100, 100), (0, 100), (100, 0)])
    assert not bowtie.is_valid

    with patch("team_algoryxz.nest_craft.src.geometry.compute_boundary_deviation", side_effect=GeometryComparisonError("Corrupt boundary")):
        with pytest.raises(CADTopologyError) as exc_info:
            Part(bowtie, part_id="p_fail_unauthorized", metadata={"allow_repaired_topology": False})
        assert "Boundary deviation comparison failed" in str(exc_info.value) or "validation failed" in str(exc_info.value).lower()

def test_part_init_authorized_repair_fails_closed_on_comparison_error():
    """Verify Part does NOT accidentally authorize damaged geometry when comparison fails."""
    bowtie = Polygon([(0, 0), (100, 100), (0, 100), (100, 0)])
    assert not bowtie.is_valid

    # Even with allow_repaired_topology=True, comparison failure must FAIL CLOSED
    with patch("team_algoryxz.nest_craft.src.geometry.compute_boundary_deviation", side_effect=GeometryComparisonError("Corrupt boundary")):
        with pytest.raises(GeometryComparisonError) as exc_info:
            Part(bowtie, part_id="p_fail_authorized", metadata={"allow_repaired_topology": True})
        assert "Cannot verify feature preservation; failing closed" in str(exc_info.value)

def test_part_init_unverifiable_requires_both_explicit_flags():
    """Verify unverifiable geometry requires both allow_unverifiable_geometry AND allow_feature_loss."""
    bowtie = Polygon([(0, 0), (100, 100), (0, 100), (100, 0)])
    assert not bowtie.is_valid

    with patch("team_algoryxz.nest_craft.src.geometry.compute_boundary_deviation", side_effect=GeometryComparisonError("Corrupt boundary")):
        # Only allow_unverifiable_geometry -> still fails on feature_loss_detected
        with pytest.raises(CADTopologyError) as exc_info:
            Part(bowtie, part_id="p_fail_partial", metadata={
                "allow_repaired_topology": True,
                "allow_unverifiable_geometry": True,
                "allow_feature_loss": False
            })
        assert "Critical feature loss or boundary deviation detected" in str(exc_info.value)

        # Both flags explicitly provided -> part accepted with recorded inf deviation
        part = Part(bowtie, part_id="p_explicit_authorized", metadata={
            "allow_repaired_topology": True,
            "allow_unverifiable_geometry": True,
            "allow_feature_loss": True
        })
        assert math.isinf(part.validation_record["hausdorff_distance"])
        assert part.validation_record["feature_loss_detected"] is True
        assert part.validation_record["topology_altered"] is True
