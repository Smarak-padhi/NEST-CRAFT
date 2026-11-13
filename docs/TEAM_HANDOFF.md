# NEST-CRAFT — Team Handoff

**Last documented engineering stage: Stage D — DEF-01 remediation**

This is the first document teammates should read. It summarizes the supplied archive. Stage D claims have not been rerun by this publication operation; reproduce them locally.

## What we are building

A 2D irregular sheet-metal nesting prototype that ingests part geometry, arranges parts on stock sheets while respecting clearances and holes, and exports a layered DXF layout for downstream CAD/CAM processing.

## Where we left off

| Stage | Work recorded | Interpretation |
|---|---|---|
| A | Read-only skills/project audit, baseline, engineering plan | Historical audit and baseline |
| B | Approved skills, baseline verification, ENG-04 part-in-part, ENG-05 adaptive rotation | Implemented; adaptive rotation is not the benchmark default |
| C | Benchmark reconciliation, geometry stress tests, DXF structure audit, release review | Evidence and caveats documented |
| C.1 | Corrected benchmark, geometry, CAM, security, release claims | Revised reports supersede overbroad earlier summaries |
| C.2 | Independent verification identified DEF-01 | Prior constructor silently retained only largest MultiPolygon component |
| D | MultiPolygon preservation, topology guardrails, DXF/UI updates, regression tests | Report says 59 tests pass; reproduce locally |

Read the detailed reports in `team_algoryxz/nest_craft/reports/`.

## Implemented (as reported)

- Shapely-based `Part` and `Sheet` geometry.
- Bottom-Left-Fill baseline and Simulated Annealing.
- Orthogonal rotation benchmark mode; adaptive rotation remains experimental.
- Part-in-part nesting using inward-buffered feasible hole regions.
- DXF ingestion and layered DXF export.
- Stage D support for valid MultiPolygon components through geometry, collision/containment, visualization, and DXF export.
- `CADTopologyError` guardrail for invalid geometry repaired by `make_valid`, with explicit metadata authorization for topology-altering repairs.
- DEF-01 regression and adversarial geometry tests.

## Reported validation

Stage D report claims:
- 59 automated tests passed.
- Conservation fixture: 11,700 mm² input net area and 11,700 mm² exported net area; 4 components and 1 hole preserved.
- Industrial orthogonal SA five-seed mean remains 1,946 mm, with 3 sheets in each run.
- DXF structural audit reported zero errors.

These are statements in the supplied report, not results freshly reproduced by the publication process. Run the test and benchmark commands from the README before using them as current verified facts.

## Immediate next steps

1. Reproduce Stage D in a clean environment; record exact output and dependency versions.
2. Review the 5% topology-repair area threshold. A small-area feature can be functionally critical; area percentage alone is not a manufacturing acceptance rule.
3. Adversarially test MultiPolygon collision, clearance, part-in-part, rotation, bounds, visualization, and export.
4. Verify ordinary import/UI paths cannot set `allow_repaired_topology=True` without informed user authorization and an audit record.
5. Import DXFs into a selected commercial CAM package and obtain operator review.
6. Conduct customer trials with permissioned, customer-originated drawings and measure actual outcomes.

## Not done

- No commercial CAM import evidenced.
- No machine-specific postprocessor or G-code generation.
- No physical CNC cutting validation.
- No verified customer savings, pricing willingness, or adoption.
- No autonomous production readiness.

## Controlled demo configuration in Stage C report

17-part batch; 800 × 500 mm stock; 4 mm clearance; 5 mm margin; orthogonal rotations; part-in-part enabled. Run SA, inspect placement and remnant, export DXF, and open it in a CAD viewer. This is a prototype demo, not a production job.
