"""
test_fail_closed_geometry.py
Tests for Stage F Task 1: Fail-closed geometry validation.
Verifies that compute_boundary_deviation() and Part.__init__() fail closed on errors
and never interpret a comparison failure as zero deviation.
"""

import math
import pytest
from unittest.mock import patch
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection, Point, LineString, LinearRing

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
    """Verify compute_boundary_deviation raises if repaired geometry has no 2D components or non-polygonal elements."""
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    gc = GeometryCollection([Point(0, 0), LineString([(0, 0), (5, 5)])])
    with pytest.raises(GeometryComparisonError) as exc_info:
        compute_boundary_deviation(poly, gc, fail_closed=True)
    assert "non-polygonal components" in str(exc_info.value) or "no 2D polygonal components" in str(exc_info.value)

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
        assert sorted(part.validation_record["active_overrides"]) == [
            "allow_feature_loss", "allow_repaired_topology", "allow_unverifiable_geometry"
        ]

def test_compute_boundary_deviation_unsupported_orig_types_rejected():
    """Verify compute_boundary_deviation rejects Point, LineString as original geometry."""
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    point = Point(5, 5)
    line = LineString([(0, 0), (10, 10)])

    with pytest.raises(GeometryComparisonError) as exc_pt:
        compute_boundary_deviation(point, poly, fail_closed=True)
    assert "Unsupported original geometry type 'Point'" in str(exc_pt.value)

    with pytest.raises(GeometryComparisonError) as exc_ln:
        compute_boundary_deviation(line, poly, fail_closed=True)
    assert "Unsupported original geometry type 'LineString'" in str(exc_ln.value)

    assert compute_boundary_deviation(point, poly, fail_closed=False) == float('inf')

def test_compute_boundary_deviation_unsupported_repaired_types_rejected():
    """Verify compute_boundary_deviation rejects Point, LineString as repaired geometry."""
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    point = Point(5, 5)
    line = LineString([(0, 0), (10, 10)])

    with pytest.raises(GeometryComparisonError) as exc_pt:
        compute_boundary_deviation(poly, point, fail_closed=True)
    assert "Unsupported repaired geometry type 'Point'" in str(exc_pt.value)

    with pytest.raises(GeometryComparisonError) as exc_ln:
        compute_boundary_deviation(poly, line, fail_closed=True)
    assert "Unsupported repaired geometry type 'LineString'" in str(exc_ln.value)

    assert compute_boundary_deviation(poly, point, fail_closed=False) == float('inf')

def test_compute_boundary_deviation_polygon_plus_external_linestring_rejected():
    """Verify GeometryCollection with Polygon + LineString raises GeometryComparisonError."""
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    gc = GeometryCollection([poly, LineString([(10, 10), (20, 10)])])
    with pytest.raises(GeometryComparisonError) as exc:
        compute_boundary_deviation(poly, gc, fail_closed=True)
    assert "non-polygonal component of type 'LineString'" in str(exc.value)
    assert compute_boundary_deviation(poly, gc, fail_closed=False) == float('inf')

def test_compute_boundary_deviation_polygon_plus_point_rejected():
    """Verify GeometryCollection with Polygon + Point raises GeometryComparisonError."""
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    gc = GeometryCollection([poly, Point(15, 5)])
    with pytest.raises(GeometryComparisonError) as exc:
        compute_boundary_deviation(poly, gc, fail_closed=True)
    assert "non-polygonal component of type 'Point'" in str(exc.value)
    assert compute_boundary_deviation(poly, gc, fail_closed=False) == float('inf')

def test_compute_boundary_deviation_polygon_plus_empty_linestring_rejected():
    """Verify GeometryCollection with Polygon + empty component raises GeometryComparisonError."""
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    gc = GeometryCollection([poly, LineString()])
    with pytest.raises(GeometryComparisonError) as exc:
        compute_boundary_deviation(poly, gc, fail_closed=True)
    assert "empty component" in str(exc.value) or "non-polygonal" in str(exc.value)
    assert compute_boundary_deviation(poly, gc, fail_closed=False) == float('inf')

def test_compute_boundary_deviation_polygon_plus_unsupported_geometry_rejected():
    """Verify GeometryCollection with LinearRing or unsupported component raises GeometryComparisonError."""
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    ring = LinearRing([(0, 0), (5, 0), (5, 5), (0, 5)])
    gc = GeometryCollection([poly, ring])
    with pytest.raises(GeometryComparisonError) as exc:
        compute_boundary_deviation(poly, gc, fail_closed=True)
    assert "LinearRing" in str(exc.value)
    assert compute_boundary_deviation(poly, gc, fail_closed=False) == float('inf')

def test_compute_boundary_deviation_multiple_polygons_with_non_polygonal_fragment_rejected():
    """Verify MultiPolygon plus non-polygonal fragment in GeometryCollection raises GeometryComparisonError."""
    p1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    p2 = Polygon([(20, 0), (30, 0), (30, 10), (20, 10)])
    gc = GeometryCollection([p1, p2, Point(50, 50)])
    with pytest.raises(GeometryComparisonError) as exc:
        compute_boundary_deviation(MultiPolygon([p1, p2]), gc, fail_closed=True)
    assert "non-polygonal" in str(exc.value)
    assert compute_boundary_deviation(MultiPolygon([p1, p2]), gc, fail_closed=False) == float('inf')

def test_compute_boundary_deviation_geometry_collection_only_non_polygonal_rejected():
    """Verify GeometryCollection containing only non-polygonal components raises GeometryComparisonError."""
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    gc = GeometryCollection([Point(0, 0), LineString([(0, 0), (5, 5)])])
    with pytest.raises(GeometryComparisonError) as exc:
        compute_boundary_deviation(poly, gc, fail_closed=True)
    assert "non-polygonal" in str(exc.value) or "no 2D polygonal components" in str(exc.value)
    assert compute_boundary_deviation(poly, gc, fail_closed=False) == float('inf')

def test_part_init_make_valid_polygonal_and_non_polygonal_fragments_rejected():
    """Verify Part.__init__ rejects repair output containing non-polygonal fragments unless fully authorized."""
    # Self-intersecting contour with needle spike that make_valid turns into (Polygon + LineString)
    spike_poly = Polygon([(0, 0), (100, 0), (100, 50), (200, 50), (100, 50), (100, 100), (0, 100)])
    assert not spike_poly.is_valid

    # Unauthorized: raises GeometryComparisonError / CADTopologyError
    with pytest.raises(CADTopologyError):
        Part(spike_poly, part_id="spike_unauth")

    # Only allow_repaired_topology: fails closed on comparison error
    with pytest.raises(GeometryComparisonError):
        Part(spike_poly, part_id="spike_partial1", metadata={"allow_repaired_topology": True})

    # allow_repaired_topology + allow_unverifiable_geometry: fails closed on feature loss detected
    with pytest.raises(CADTopologyError) as exc_feat:
        Part(spike_poly, part_id="spike_partial2", metadata={
            "allow_repaired_topology": True,
            "allow_unverifiable_geometry": True
        })
    assert "Critical feature loss" in str(exc_feat.value) or "feature loss" in str(exc_feat.value).lower()

    # All three overrides active: accepted, but deviation remains inf, feature_loss_detected remains True
    p = Part(spike_poly, part_id="spike_auth", metadata={
        "allow_repaired_topology": True,
        "allow_unverifiable_geometry": True,
        "allow_feature_loss": True
    })
    assert math.isinf(p.validation_record["hausdorff_distance"])
    assert p.validation_record["feature_loss_detected"] is True
    assert p.validation_record["topology_altered"] is True
    assert sorted(p.validation_record["active_overrides"]) == [
        "allow_feature_loss", "allow_repaired_topology", "allow_unverifiable_geometry"
    ]

def test_part_init_tiny_polygon_component_rejected():
    """Verify Part.__init__ rejects repaired sub-threshold components unless allow_feature_loss=True."""
    p_large = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    p_tiny = Polygon([(200, 200), (200.0001, 200), (200.0001, 200.0001), (200, 200.0001)])
    mp = MultiPolygon([p_large, p_tiny])
    bowtie = Polygon([(0, 0), (100, 100), (0, 100), (100, 0)])

    with patch("team_algoryxz.nest_craft.src.geometry.make_valid", return_value=mp):
        with pytest.raises(CADTopologyError) as exc:
            Part(bowtie, part_id="tiny_comp", metadata={"allow_repaired_topology": True})
        assert "sub-threshold" in str(exc.value) or "feature loss" in str(exc.value).lower()

        # Authorized with allow_feature_loss
        p = Part(bowtie, part_id="tiny_comp_auth", metadata={
            "allow_repaired_topology": True,
            "allow_feature_loss": True
        })
        assert p.polygon.area >= 10000.0

def test_compute_boundary_deviation_valid_polygon_and_multipolygon_behavior():
    """Verify compute_boundary_deviation returns accurate metrics for valid Polygons and MultiPolygons."""
    p1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    p2 = Polygon([(0, 0), (10, 0), (10, 12), (0, 12)])
    mp1 = MultiPolygon([p1, Polygon([(20, 20), (30, 20), (30, 30), (20, 30)])])
    mp2 = MultiPolygon([p2, Polygon([(20, 20), (30, 20), (30, 30), (20, 30)])])
    gc_pure = GeometryCollection([p1, p2])

    # Polygon to Polygon
    assert compute_boundary_deviation(p1, p1) == 0.0
    assert compute_boundary_deviation(p1, p2) == 2.0

    # Polygon to MultiPolygon
    dist_p_mp = compute_boundary_deviation(p1, mp1)
    assert isinstance(dist_p_mp, float) and dist_p_mp >= 0.0

    # MultiPolygon to MultiPolygon
    assert compute_boundary_deviation(mp1, mp1) == 0.0
    dist_mp = compute_boundary_deviation(mp1, mp2)
    assert isinstance(dist_mp, float) and dist_mp > 0.0

    # Polygon to pure polygonal GeometryCollection
    dist_gc = compute_boundary_deviation(p1, gc_pure)
    assert isinstance(dist_gc, float) and dist_gc == 2.0

def test_part_validation_record_active_overrides_tracking():
    """Verify Part.validation_record accurately tracks active unsafe overrides."""
    valid_poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    part_default = Part(valid_poly, part_id="default")
    assert part_default.validation_record["active_overrides"] == []

    part_with_override = Part(
        valid_poly,
        part_id="with_override",
        metadata={"allow_repaired_topology": True}
    )
    assert part_with_override.validation_record["active_overrides"] == ["allow_repaired_topology"]

