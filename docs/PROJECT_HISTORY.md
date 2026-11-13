# Project History and Decision Log

## Selection

NEST-CRAFT was selected as the strongest hackathon candidate based on prototype maturity and demonstrability. This did not establish commercial viability or customer demand.

## Stage A — Audit and baseline

The Stage A work audited candidate agent skills and project architecture, established a baseline, and proposed ENG-04 (part-in-part nesting) and ENG-05 (rotation refinement). Unsafe autonomous prompt/tool-hooking patterns were rejected. The early headline utilization improvement of 64.2% to 78.4% was later found not to be reproducible as stated; do not reuse it.

## Stage B — Engineering implementation

The Stage B report records skill security review, approved skill installation, baseline replication, ENG-04 part-in-part feasible-region logic, ENG-05 adaptive rotation candidate generation, and critic-driven fixes for collision and grain-direction edge cases. Later five-seed benchmarks did not support adaptive rotation as the default.

## Stage C — Evidence reconciliation

Stage C separated linear extent, discrete sheet count, area utilization, remnant area, and runtime. It documented structural DXF validation and clarified that DXF is not G-code. It also separated hackathon demo readiness from industrial pilot and production release.

## Stage C.1 — Corrections

The changelog records corrections to benchmark comparisons, exact clearance tests, `make_valid` topology behavior, CAM boundaries, and security wording. Dated `.bak.md` reports are historical pre-correction snapshots; read the non-backup reports as revised versions.

## Stage C.2 — DEF-01 discovered

The Stage C.2 report describes a constructor that reduced a `MultiPolygon` to its largest component. A bow-tie repaired into two 400 mm² lobes lost one lobe; a valid two-component MultiPolygon was also reduced. This was formalized as DEF-01.

## Stage D — DEF-01 remediation

The Stage D report states that valid multipart geometries are retained; transformations, collision/containment, UI visualization, and DXF export were updated; topology-altering repairs are rejected unless explicitly authorized; conservation tests were added; 59 tests passed; and the industrial orthogonal five-seed mean remained 1,946 mm.

Treat Stage D as an implementation report until a clean checkout reproduces its tests and benchmark.

## Decisions carried forward

1. Orthogonal rotation is the current benchmark default.
2. Never silently drop geometry or holes.
3. Explicitly reject unsupported or topology-altered CAD input.
4. Keep physical sheet count distinct from linear extent.
5. DXF is an intermediate CAD artifact, not machine-ready instructions.
6. No customer ROI/adoption claim without primary customer evidence.
