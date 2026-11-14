"""
test_esicup_multiloop.py
Comprehensive regression tests for ESICUP multi-loop contour parsing.
Verifies fail-closed validation, hole extraction, disjoint multipart preservation,
and rejection of malformed, unclosed, degenerate, or overlapping sub-loops.
"""

import os
import tempfile
import pytest
from shapely.geometry import Polygon, MultiPolygon

from team_algoryxz.nest_craft.src.dxf_io import parse_esicup_txt
from team_algoryxz.nest_craft.src.geometry import CADTopologyError

def test_esicup_multiple_valid_closed_loops_disjoint_solids():
    """Verify parse_esicup_txt preserves two disjoint closed loops as a MultiPolygon."""
    content = """PIECE 1
QUANTITY
1
NUMBER OF VERTICES
10
VERTICES (X,Y)
0 0
50 0
50 50
0 50
0 0
60 0
110 0
110 50
60 50
60 0
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        parts, meta = parse_esicup_txt(tmp_path, allow_repaired_topology=False)
        assert len(parts) == 1
        p = parts[0]
        assert isinstance(p.polygon, MultiPolygon)
        assert len(p.polygon.geoms) == 2
        # (50*50) + (50*50) = 5000.0
        assert pytest.approx(p.polygon.area, rel=1e-3) == 5000.0
        assert p.quantity == 1
        assert meta["is_valid"] is True
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_esicup_concentric_outer_and_inner_hole():
    """Verify parse_esicup_txt extracts concentric closed sub-loops as outer boundary and interior hole."""
    content = """PIECE 1
QUANTITY
1
NUMBER OF VERTICES
10
VERTICES (X,Y)
0 0
100 0
100 100
0 100
0 0
40 40
60 40
60 60
40 60
40 40
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        parts, meta = parse_esicup_txt(tmp_path, allow_repaired_topology=False)
        assert len(parts) == 1
        p = parts[0]
        assert isinstance(p.polygon, Polygon)
        assert len(p.polygon.interiors) == 1
        # Net area: (100*100) - (20*20) = 10000 - 400 = 9600.0
        assert pytest.approx(p.polygon.area, rel=1e-3) == 9600.0
        assert meta["is_valid"] is True
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_esicup_unclosed_final_loop_rejected():
    """Verify parse_esicup_txt rejects multipart contour with unclosed final sub-loop."""
    content = """PIECE 1
QUANTITY
1
NUMBER OF VERTICES
9
VERTICES (X,Y)
0 0
50 0
50 50
0 50
0 0
60 0
110 0
110 50
60 50
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with pytest.raises(CADTopologyError) as exc_info:
            parse_esicup_txt(tmp_path, allow_repaired_topology=False)
        assert "unclosed final sub-loop" in str(exc_info.value).lower()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_esicup_malformed_first_loop_followed_by_valid_loop_rejected():
    """Verify parse_esicup_txt rejects when first sub-loop is self-intersecting."""
    content = """PIECE 1
QUANTITY
1
NUMBER OF VERTICES
9
VERTICES (X,Y)
0 0
100 100
0 100
100 0
0 0
200 0
250 0
250 50
200 50
200 0
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with pytest.raises(CADTopologyError) as exc_info:
            parse_esicup_txt(tmp_path, allow_repaired_topology=False)
        assert "sub-loop 1" in str(exc_info.value).lower()
        assert "self-intersecting" in str(exc_info.value).lower() or "invalid topology" in str(exc_info.value).lower()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_esicup_valid_first_loop_followed_by_malformed_loop_rejected():
    """Verify parse_esicup_txt rejects when second sub-loop is self-intersecting."""
    content = """PIECE 1
QUANTITY
1
NUMBER OF VERTICES
9
VERTICES (X,Y)
0 0
50 0
50 50
0 50
0 0
200 0
300 100
200 100
300 0
200 0
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with pytest.raises(CADTopologyError) as exc_info:
            parse_esicup_txt(tmp_path, allow_repaired_topology=False)
        assert "sub-loop 2" in str(exc_info.value).lower()
        assert "self-intersecting" in str(exc_info.value).lower() or "invalid topology" in str(exc_info.value).lower()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_esicup_degenerate_loop_insufficient_vertices_rejected():
    """Verify parse_esicup_txt rejects sub-loop with fewer than 3 unique vertices."""
    content = """PIECE 1
QUANTITY
1
NUMBER OF VERTICES
3
VERTICES (X,Y)
0 0
10 0
0 0
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with pytest.raises(CADTopologyError) as exc_info:
            parse_esicup_txt(tmp_path, allow_repaired_topology=False)
        assert "degenerate" in str(exc_info.value).lower()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_esicup_zero_area_collinear_loop_rejected():
    """Verify parse_esicup_txt rejects sub-loop with collinear vertices and zero area."""
    content = """PIECE 1
QUANTITY
1
NUMBER OF VERTICES
4
VERTICES (X,Y)
0 0
10 0
20 0
0 0
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with pytest.raises(CADTopologyError) as exc_info:
            parse_esicup_txt(tmp_path, allow_repaired_topology=False)
        assert "zero or sub-threshold area" in str(exc_info.value).lower()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_esicup_overlapping_loops_rejected():
    """Verify parse_esicup_txt rejects partially overlapping/crossing sub-loops."""
    content = """PIECE 1
QUANTITY
1
NUMBER OF VERTICES
10
VERTICES (X,Y)
0 0
50 0
50 50
0 50
0 0
25 25
75 25
75 75
25 75
25 25
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with pytest.raises(CADTopologyError) as exc_info:
            parse_esicup_txt(tmp_path, allow_repaired_topology=False)
        assert "intersect or partially overlap" in str(exc_info.value).lower()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_esicup_duplicate_loops_rejected():
    """Verify parse_esicup_txt rejects duplicate sub-loops."""
    content = """PIECE 1
QUANTITY
1
NUMBER OF VERTICES
10
VERTICES (X,Y)
0 0
50 0
50 50
0 50
0 0
0 0
50 0
50 50
0 50
0 0
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with pytest.raises(CADTopologyError) as exc_info:
            parse_esicup_txt(tmp_path, allow_repaired_topology=False)
        assert "duplicate" in str(exc_info.value).lower()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_esicup_fewer_than_three_total_vertices_rejected():
    """Verify parse_esicup_txt rejects pieces with fewer than 3 total coordinates."""
    content = """PIECE 1
QUANTITY
1
NUMBER OF VERTICES
2
VERTICES (X,Y)
0 0
10 10
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with pytest.raises(CADTopologyError) as exc_info:
            parse_esicup_txt(tmp_path, allow_repaired_topology=False)
        assert "fewer than 3 vertices" in str(exc_info.value).lower()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_esicup_multipart_quantity_and_area_preservation():
    """Verify multiple pieces preserve respective quantities and areas."""
    content = """PIECE 1
QUANTITY
3
NUMBER OF VERTICES
10
VERTICES (X,Y)
0 0
50 0
50 50
0 50
0 0
60 0
110 0
110 50
60 50
60 0

PIECE 2
QUANTITY
5
NUMBER OF VERTICES
4
VERTICES (X,Y)
0 0
40 0
40 40
0 40
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        parts, meta = parse_esicup_txt(tmp_path, allow_repaired_topology=False)
        assert len(parts) == 2
        p1 = next(p for p in parts if p.part_id == "piece_1")
        assert p1.quantity == 3
        assert isinstance(p1.polygon, MultiPolygon)
        assert pytest.approx(p1.polygon.area, rel=1e-3) == 5000.0

        p2 = next(p for p in parts if p.part_id == "piece_2")
        assert p2.quantity == 5
        assert isinstance(p2.polygon, Polygon)
        assert pytest.approx(p2.polygon.area, rel=1e-3) == 1600.0

        assert meta["total_pieces_extracted"] == 2
        assert meta["total_quantity"] == 8
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
