# Roadmap

Recommended next work; these tasks are not represented as completed.

## P0 — Reproduce and lock current state

- [ ] Fresh environment install.
- [ ] Reproduce the reported 59-test result and record exact output.
- [ ] Re-run five-seed industrial orthogonal benchmark.
- [ ] Compare raw outputs with archived Stage C results.
- [ ] Record Python, Shapely, ezdxf, Streamlit, NumPy, and pytest versions.
- [ ] Add continuous integration.

**Acceptance:** clean checkout reproduces tests and benchmark outputs within documented tolerances.

## P1 — Adversarial geometry audit

- [ ] Test disconnected components far apart and near stock edges.
- [ ] Test component collisions against other parts and each other.
- [ ] Test holes on each component, multiple holes, and multipart cutouts.
- [ ] Test buffering and clearance around narrow necks, slivers, and touching boundaries.
- [ ] Test rotations/translations preserve component/hole counts and net area.
- [ ] Test DXF round-trip geometry with independent area/topology comparisons.
- [ ] Verify topology authorization cannot be enabled silently through normal UI/import.
- [ ] Reconsider 5% area threshold; use topology and feature-level checks, not area alone.

**Acceptance:** supported geometries have explicit invariants and regression tests; unsupported geometries fail visibly.

## P1 — DXF/CAM interoperability

- [ ] Select one target CAM product/version with a fabrication partner.
- [ ] Import sample DXFs and record layer/entity interpretation.
- [ ] Verify cut order, kerf offset, pierce, lead-in/out, tabs, and slug handling.
- [ ] Obtain experienced operator review.
- [ ] Only then plan a supervised machine trial with machine-specific safety controls.

**Acceptance:** documented CAM import and operator sign-off; not universal CNC compatibility.

## P2 — Product validation

- [ ] Interview fabrication MSMEs about current nesting workflow.
- [ ] Obtain permission to test representative customer drawings.
- [ ] Compare against each shop's actual workflow, not only BLF.
- [ ] Measure sheet count, scrap, remnant usability, setup time, rework, and operator intervention.
- [ ] Validate pricing and procurement requirements.

**Acceptance:** documented customer trials and measured outcomes.

## P2 — Engineering quality

- [ ] Add structured import diagnostics and typed interfaces.
- [ ] Make benchmark configuration/results machine-readable and reproducible.
- [ ] Add CI and dependency lockfile.
- [ ] Add dataset provenance/license notes.
- [ ] Add application-level validation and export warnings.
