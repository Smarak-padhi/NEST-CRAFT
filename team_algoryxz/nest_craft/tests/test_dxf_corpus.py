"""
test_dxf_corpus.py
Automated tests for the real-world DXF edge-case test corpus.
Validates ingestion behavior across all 16 representative CAD edge cases:
closed polylines, open contours, bulged arcs, circles, splines, disconnected components,
nested holes, narrow slots, small cutouts, self-intersections, unsupported 3D, duplicate
contours, overlapping contours, large coordinates, and DXF version variations.
"""

import os
import pytest

from team_algoryxz.nest_craft.src.dxf_io import validate_and_parse_dxf

CORPUS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "dxf_test_corpus")
)

def test_corpus_case01_closed_polyline():
    p = os.path.join(CORPUS_DIR, "case01_closed_poly.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 1
    assert rep["holes_extracted_count"] == 0
    assert pytest.approx(parts[0].area, abs=1.0) == 14700.0

def test_corpus_case02_open_contour_rejected():
    p = os.path.join(CORPUS_DIR, "case02_open_contour.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is False
    assert len(parts) == 0
    assert rep["unclosed_segments_count"] == 4
    assert any("open line/arc segment" in w for w in rep["warnings"])
    assert any("No valid closed 2D cutting contours" in e for e in rep["errors"])

def test_corpus_case03_bulged_arcs():
    p = os.path.join(CORPUS_DIR, "case03_bulged_arcs.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 1
    assert pytest.approx(parts[0].area, abs=5.0) == 13912.64

def test_corpus_case04_circles_and_holes():
    p = os.path.join(CORPUS_DIR, "case04_circles_holes.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 1
    assert rep["holes_extracted_count"] == 2
    # 200x150 = 30000 - 2 * pi * 15^2 ≈ 28586.3
    assert pytest.approx(parts[0].area, abs=10.0) == 28594.97

def test_corpus_case05_splines():
    p = os.path.join(CORPUS_DIR, "case05_splines.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 1
    assert parts[0].area > 10000.0

def test_corpus_case06_disconnected_components():
    p = os.path.join(CORPUS_DIR, "case06_disconnected_components.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 2
    assert pytest.approx(sum(pt.area for pt in parts), abs=1.0) == 9600.0

def test_corpus_case07_nested_holes_concentric():
    p = os.path.join(CORPUS_DIR, "case07_nested_holes.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 2
    assert rep["holes_extracted_count"] == 2
    # Outer plate with hole: 300x300 - 200x200 = 50000
    # Island with hole: 140x140 - 60x60 = 16000
    # Total net area = 66000
    assert pytest.approx(sum(pt.area for pt in parts), abs=1.0) == 66000.0

def test_corpus_case08_narrow_slots():
    p = os.path.join(CORPUS_DIR, "case08_narrow_slots.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 1
    assert rep["holes_extracted_count"] == 1
    # 200x100 = 20000 - 60 * 0.8 = 19952
    assert pytest.approx(parts[0].area, abs=1.0) == 19952.0

def test_corpus_case09_small_cutouts():
    p = os.path.join(CORPUS_DIR, "case09_small_cutouts.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 1
    assert rep["holes_extracted_count"] == 3
    assert pytest.approx(parts[0].area, abs=2.0) == 9994.83

def test_corpus_case10_self_intersecting_gate():
    p = os.path.join(CORPUS_DIR, "case10_self_intersecting.dxf")
    # Unauthorized path: rejected
    parts_unauth, rep_unauth = validate_and_parse_dxf(p, allow_repaired_topology=False)
    assert rep_unauth["is_valid"] is False
    assert len(parts_unauth) == 0
    assert any("self-intersections" in e for e in rep_unauth["errors"])

    # Authorized path: repaired into 2 components
    parts_auth, rep_auth = validate_and_parse_dxf(p, allow_repaired_topology=True)
    assert rep_auth["is_valid"] is True
    assert len(parts_auth) == 2
    assert pytest.approx(sum(pt.area for pt in parts_auth), abs=1.0) == 5000.0

def test_corpus_case11_unsupported_3d():
    p = os.path.join(CORPUS_DIR, "case11_unsupported_3d.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 1
    assert any("3DFACE" in w for w in rep["warnings"])

def test_corpus_case12_duplicate_contours():
    p = os.path.join(CORPUS_DIR, "case12_duplicate_contours.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 2

def test_corpus_case13_overlapping_contours():
    p = os.path.join(CORPUS_DIR, "case13_overlapping_contours.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 2

def test_corpus_case14_large_coordinates_normalized():
    p = os.path.join(CORPUS_DIR, "case14_large_coordinates.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 1
    assert pytest.approx(parts[0].area, abs=1.0) == 8400.0
    # Normalized base polygon bounds must start at (0, 0)
    assert parts[0].base_polygon.bounds[0] == 0.0
    assert parts[0].base_polygon.bounds[1] == 0.0

def test_corpus_case15_dxf_version_r12():
    p = os.path.join(CORPUS_DIR, "case15_dxf_version_r12.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 1
    assert pytest.approx(parts[0].area, abs=1.0) == 12600.0

def test_corpus_case16_dxf_version_r2018():
    p = os.path.join(CORPUS_DIR, "case16_dxf_version_r2018.dxf")
    parts, rep = validate_and_parse_dxf(p)
    assert rep["is_valid"] is True
    assert len(parts) == 1
    assert pytest.approx(parts[0].area, abs=1.0) == 14400.0
