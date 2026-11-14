"""
test_stage_e_integrity.py
Comprehensive regression tests for Stage E:
1. Ingestion of MultiPolygon and multipart geometries in ESICUP TXT and XML without largest-only reduction.
2. Strict CADTopologyError rejection for unauthorized malformed geometry in ESICUP parsers.
3. Accurate preservation of piece IDs, quantities, and areas in ESICUP parsers.
4. Topology validation enhancements in Part.__init__:
   - Hausdorff distance boundary deviation detection (collapsed spikes, pinched slots).
   - Hole count delta tracking.
   - Component count delta tracking.
   - Structured validation_record schema.
5. DXF export verification:
   - Reopenability and structural audit via ezdxf.
   - Polyline closure enforcement.
   - Net area conservation within tolerance.
   - DXFExportValidationError triggering on corrupt, unclosed, or mismatched geometry.
"""

import os
import tempfile
import pytest
import ezdxf
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union

from team_algoryxz.nest_craft.src.geometry import (
    Part,
    Sheet,
    CADTopologyError,
    compute_boundary_deviation,
    count_geometry_holes
)
from team_algoryxz.nest_craft.src.dxf_io import (
    parse_esicup_txt,
    parse_esicup_xml,
    export_nesting_to_dxf,
    validate_exported_dxf,
    DXFExportValidationError
)

# -----------------------------------------------------------------------------
# 1. ESICUP TXT & XML Multipart and Quantity Integrity
# -----------------------------------------------------------------------------

def test_esicup_txt_valid_multipart_preserved():
    """Verify parse_esicup_txt preserves MultiPolygon pieces when authorized."""
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

PIECE 2
QUANTITY
2
NUMBER OF VERTICES
4
VERTICES (X,Y)
0 0
30 0
30 30
0 30
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        parts, meta = parse_esicup_txt(tmp_path, allow_repaired_topology=True)
        assert len(parts) == 2
        p1 = next(p for p in parts if p.part_id == "piece_1")
        assert isinstance(p1.polygon, MultiPolygon)
        assert len(p1.polygon.geoms) == 2
        # Verify areas: (50x50 = 2500) + (50x50 = 2500) = 5000
        assert pytest.approx(p1.polygon.area, rel=1e-3) == 5000.0
        assert p1.quantity == 1

        p2 = next(p for p in parts if p.part_id == "piece_2")
        assert p2.quantity == 2
        assert pytest.approx(p2.polygon.area, rel=1e-3) == 900.0
        assert meta["total_pieces_extracted"] == 2
        assert meta["total_quantity"] == 3
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_esicup_txt_unauthorized_invalid_rejected():
    """Verify parse_esicup_txt raises CADTopologyError on malformed contour when unauthorized."""
    # Self-intersecting bow-tie contour
    content = """PIECE 1
QUANTITY
1
NUMBER OF VERTICES
4
VERTICES (X,Y)
0 0
100 100
0 100
100 0
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with pytest.raises(CADTopologyError) as exc_info:
            parse_esicup_txt(tmp_path, allow_repaired_topology=False)
        assert "validation failed" in str(exc_info.value).lower() or "self-intersecting" in str(exc_info.value).lower()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_esicup_xml_quantity_and_id_preservation():
    """Verify parse_esicup_xml preserves piece IDs, quantities, and geometry."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<nesting_problem xmlns="http://www.esicup.org">
    <polygons>
        <polygon id="poly_A">
            <lines>
                <segment x0="0" y0="0" x1="100" y1="0"/>
                <segment x0="100" y0="0" x1="100" y1="50"/>
                <segment x0="100" y0="50" x1="0" y1="50"/>
                <segment x0="0" y0="50" x1="0" y1="0"/>
            </lines>
        </polygon>
    </polygons>
    <problem>
        <lot>
            <piece id="BRACKET_01" quantity="5">
                <component idPolygon="poly_A"/>
            </piece>
        </lot>
    </problem>
</nesting_problem>
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".xml") as tmp:
        tmp.write(xml_content)
        tmp_path = tmp.name

    try:
        parts, meta = parse_esicup_xml(tmp_path, allow_repaired_topology=False)
        assert len(parts) == 1
        assert parts[0].part_id == "BRACKET_01"
        assert parts[0].quantity == 5
        assert pytest.approx(parts[0].polygon.area, rel=1e-3) == 5000.0
        assert meta["total_quantity"] == 5
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# -----------------------------------------------------------------------------
# 2. Topology Validation & Boundary Deviation Checks
# -----------------------------------------------------------------------------

def test_part_validation_record_schema():
    """Verify Part instances record structured validation_record metadata."""
    poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)], [[(20, 20), (80, 20), (80, 80), (20, 80)]])
    part = Part(poly, part_id="test_part")
    rec = part.validation_record

    assert rec["is_valid_original"] is True
    assert rec["is_valid_repaired"] is True
    assert rec["input_components"] == 1
    assert rec["repaired_components"] == 1
    assert rec["input_holes"] == 1
    assert rec["repaired_holes"] == 1
    assert rec["area_delta_pct"] == 0.0
    assert rec["hausdorff_distance"] == 0.0
    assert rec["feature_loss_detected"] is False

def test_hausdorff_deviation_detection_on_boundary_alteration():
    """Verify compute_boundary_deviation detects collapsed spikes even with near-zero area loss."""
    # Base polygon: 100x100 square with a 100mm needle-thin spike (width 0.001)
    base_poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    needle_spike = Polygon([(100, 50), (200, 50.0005), (100, 50.001)])
    combined = unary_union([base_poly, needle_spike])

    # Truncated polygon where the needle spike is removed
    truncated = base_poly

    dev = compute_boundary_deviation(combined, truncated)
    assert dev >= 99.0 # Detected ~100mm boundary deviation!

def test_part_rejection_on_excessive_hausdorff_deviation():
    """Verify Part rejects authorized repair if boundary deviation exceeds tolerance."""
    # A contour that when repaired collapses a critical 100mm boundary feature
    spike_poly = Polygon([(0, 0), (100, 0), (100, 50), (200, 50), (100, 50), (100, 100), (0, 100)])
    assert not spike_poly.is_valid

    # When repaired without generous deviation threshold, CADTopologyError should be raised
    with pytest.raises(CADTopologyError) as exc_info:
        Part(spike_poly, part_id="spike_part", metadata={"allow_repaired_topology": True, "max_boundary_deviation": 10.0})
    assert "feature loss" in str(exc_info.value).lower() or "boundary deviation" in str(exc_info.value).lower()

def test_hole_count_calculation():
    """Verify count_geometry_holes accurately counts across Polygon and MultiPolygon."""
    p1 = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)], [[(10, 10), (20, 10), (20, 20), (10, 20)], [(30, 30), (40, 30), (40, 40), (30, 40)]])
    p2 = Polygon([(200, 0), (300, 0), (300, 100), (200, 100)], [[(210, 10), (220, 10), (220, 20), (210, 20)]])
    mp = MultiPolygon([p1, p2])

    assert count_geometry_holes(p1) == 2
    assert count_geometry_holes(p2) == 1
    assert count_geometry_holes(mp) == 3

# -----------------------------------------------------------------------------
# 3. DXF Export Validation & Integrity Auditing
# -----------------------------------------------------------------------------

def test_export_nesting_dxf_clean_validation():
    """Verify export_nesting_to_dxf succeeds and passes validate_exported_dxf."""
    p1 = Polygon([(0, 0), (120, 0), (120, 80), (0, 80)])
    p2 = Polygon([(0, 0), (150, 0), (150, 60), (0, 60)], [[(20, 20), (50, 20), (50, 40), (20, 40)]])

    sheet = Sheet(width=500, height=300)
    sheet.placed_parts.append(("part_1", p1, 0.0))
    sheet.placed_parts.append(("part_2", p2, 0.0))

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        export_file = tmp.name

    try:
        export_nesting_to_dxf([sheet], export_file, validate=True)
        val_res = validate_exported_dxf(export_file, [sheet], area_tolerance=0.05)

        assert val_res["valid"] is True
        assert val_res["sheet_boundary_count"] == 1
        assert val_res["cut_contour_count"] == 2
        assert val_res["hole_contour_count"] == 1
        assert pytest.approx(val_res["expected_net_area"], rel=1e-4) == (p1.area + p2.area)
        assert val_res["area_delta"] <= 0.05
        assert val_res["audit_errors"] == 0
    finally:
        if os.path.exists(export_file):
            os.unlink(export_file)

def test_validate_exported_dxf_detects_corrupt_file():
    """Verify validate_exported_dxf detects non-existent or corrupted DXF files."""
    with pytest.raises(DXFExportValidationError) as exc:
        validate_exported_dxf("non_existent_file_xyz.dxf", [])
    assert "does not exist" in str(exc.value)

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".dxf") as tmp:
        tmp.write("NOT_A_VALID_DXF_CONTENT")
        tmp_path = tmp.name

    try:
        with pytest.raises(DXFExportValidationError) as exc:
            validate_exported_dxf(tmp_path, [])
        assert "failed reopenability" in str(exc.value).lower()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_validate_exported_dxf_detects_unclosed_contour():
    """Verify validate_exported_dxf detects unclosed cutting polylines."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    # Add open polyline on CUT_CONTOUR
    msp.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=False, dxfattribs={'layer': 'CUT_CONTOUR'})
    msp.add_lwpolyline([(0, 0), (500, 0), (500, 500), (0, 500)], close=True, dxfattribs={'layer': 'SHEET_BOUNDARY'})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        dxf_path = tmp.name
    doc.saveas(dxf_path)

    sheet = Sheet(width=500, height=500)
    sheet.placed_parts.append(("p1", Polygon([(0, 0), (100, 0), (100, 100), (0, 100)]), 0.0))

    try:
        with pytest.raises(DXFExportValidationError) as exc:
            validate_exported_dxf(dxf_path, [sheet])
        assert "not closed" in str(exc.value)
    finally:
        if os.path.exists(dxf_path):
            os.unlink(dxf_path)

def test_validate_exported_dxf_detects_area_mismatch():
    """Verify validate_exported_dxf flags net area divergence."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    # Export contour with 100x100 area (10,000)
    msp.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True, dxfattribs={'layer': 'CUT_CONTOUR'})
    msp.add_lwpolyline([(0, 0), (500, 0), (500, 500), (0, 500)], close=True, dxfattribs={'layer': 'SHEET_BOUNDARY'})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        dxf_path = tmp.name
    doc.saveas(dxf_path)

    # In-memory sheet placed part has 100x200 area (20,000)
    sheet = Sheet(width=500, height=500)
    sheet.placed_parts.append(("p1", Polygon([(0, 0), (100, 0), (100, 200), (0, 200)]), 0.0))

    try:
        with pytest.raises(DXFExportValidationError) as exc:
            validate_exported_dxf(dxf_path, [sheet], area_tolerance=0.05)
        assert "Net area conservation mismatch" in str(exc.value)
    finally:
        if os.path.exists(dxf_path):
            os.unlink(dxf_path)
