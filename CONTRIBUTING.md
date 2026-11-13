# Contributing

1. Read `docs/TEAM_HANDOFF.md` and `docs/KNOWN_LIMITATIONS.md`.
2. Run the existing tests and record the baseline before changing code.
3. Keep datasets, seeds, stock dimensions, clearance, iterations, and metrics unchanged unless the task is benchmark methodology.

## Validation

```bash
python -m pytest team_algoryxz/nest_craft/tests -q
```

For geometry changes, also run the industrial five-seed benchmark and inspect exported DXF geometry. Record commands, environment versions, raw output, and modified files in a report under `team_algoryxz/nest_craft/reports/`.

## Engineering rules

- Never silently discard geometry. Preserve valid components and holes or reject unsupported input explicitly.
- Never silently authorize topology repair.
- Test positive and negative cases: multipart geometry, holes, invalid contours, exact clearance, and near-clearance violations.
- Passing unit tests does not establish CAM compatibility or physical cutting safety.
- Separate discrete sheet count, utilization, linear extent, remnant area, and runtime.
- Never describe DXF as G-code or production-ready machine instructions.
- Do not claim customer savings or demand without customer evidence.

## PR checklist

- [ ] Scope is limited and explained.
- [ ] Tests added and full suite passes.
- [ ] Benchmark non-regression checked for geometry/optimizer changes.
- [ ] DXF behavior checked when CAD paths change.
- [ ] Report includes environment, command, raw results, and limitations.
- [ ] Documentation updated.
- [ ] No secrets, local paths, virtual environments, caches, or customer-confidential files.
