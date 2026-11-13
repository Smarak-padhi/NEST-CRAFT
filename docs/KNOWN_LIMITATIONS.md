# Known Limitations and Non-Claims

## Manufacturing and CAM

- DXF is CAD geometry, not G-code.
- No commercial CAM import is evidenced in the supplied reports.
- No physical CNC cutting test is evidenced.
- No machine-specific postprocessor, feed/power settings, pierce cycles, lead-ins/outs, kerf compensation, micro-tabs, slug handling, or controller validation is included.
- Layer names are semantic hints; downstream CAM must implement and verify cut sequencing.

## Geometry

- Stage D reports MultiPolygon support and topology-repair guardrails. Reproduce tests and adversarially inspect all consumers.
- The reported 5% area-change threshold is not a manufacturing acceptance standard. A small feature may be functionally critical despite a small total area change.
- Explicit topology-repair authorization must be visible and recorded. Do not set authorization implicitly.
- Automated area conservation on one fixture does not prove every geometry class is safe.
- Test touching components, overlaps, tiny slivers, nested holes, invalid rings, splines, bulges, and precision rounding.

## Optimization and metrics

- Simulated Annealing is heuristic, not proof of global optimality.
- Orthogonal rotation performed better than adaptive rotation on reported five-seed means. Keep adaptive mode experimental unless new multi-seed evidence changes the result.
- Linear extent, discrete sheet count, utilization, remnant area, and runtime are separate metrics.
- Remnant area is not automatically reusable or monetizable.

## Commercial validation

- Sample DXFs do not establish customer-originated production drawings.
- No verified customer savings, willingness to pay, adoption, or market size is established.
- Financial calculator outputs depend on editable assumptions; they are not measured ROI.

## Security and dependencies

- Historical static skill scans do not establish zero risk.
- Review licensing and dependency updates before external distribution.
- Do not commit secrets, proprietary customer drawings, or credentials.
