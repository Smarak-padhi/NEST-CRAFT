# Technical Architecture

## System flow

```text
DXF / ESICUP input
       |
       v
DXF parsing + contour validation
       |
       v
Polygon / MultiPolygon + interior holes
       |
       v
Part and Sheet geometry model
       |
       +------> BLF baseline
       |
       +------> Simulated Annealing
                    |
                    +--> sequence / rotation candidates
                    +--> BLF and part-in-part placement
                    +--> objective evaluation
       |
       v
Placed sheet geometry
       |
       +--> Streamlit visualization
       |
       +--> layered DXF export
                    |
                    v
             downstream CAM required
```

## Modules

- `src/geometry.py`: `Part`, `Sheet`, geometry transforms, allowed rotations, clearance and collision logic.
- `src/baseline.py`: Bottom-Left-Fill and part-in-part placement.
- `src/optimizer.py`: Simulated Annealing search over ordering and rotation candidates.
- `src/dxf_io.py`: ESICUP/DXF ingestion, geometry validation, holes, and DXF export.
- `src/calculator.py`: illustrative fabrication savings and remnant-value calculations.
- `app/app.py`: Streamlit UI.

## Geometry invariants

- Net polygon area accounts for interior holes.
- Every valid disconnected component must remain represented.
- Holes remain attached to the correct containing component.
- Rotation and translation transform all components and holes together.
- Collision and sheet-containment checks consider the complete geometry.
- DXF export preserves geometry and distinguishes outer contours from holes.
- Topology-changing repair must be visible, explicit, and auditable.

## DXF/CAM boundary

The exporter creates CAD geometry and layer labels. It does not determine feed, power, pierce cycles, kerf offsets, lead-ins/outs, micro-tabs, slug handling, controller-specific G-code, or machine safety. A CAM package and machine-specific postprocessor remain necessary.
