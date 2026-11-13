# NEST-CRAFT — Team Handoff

**Current Engineering Milestone:** Stage D & Post-Publication Audit Completed  
**Verification Status:** 66 / 66 Automated Tests Passing  
**Target Audience:** Teammates, onboarding engineers, and hackathon judges

---

## 1. What We Are Building

NEST-CRAFT is a 2D irregular sheet-metal nesting pre-processor built for regional fabrication job shops. It ingests CAD profile geometries (DXF), models part perimeters and internal cavities using Shapely, optimizes layout packing onto standardized sheet metal plates using Bottom-Left-Fill (BLF) and Simulated Annealing (SA), exploits interior apertures for Part-in-Part nesting, tracks virgin reusable remnant offcut plates, and exports multi-layer AutoCAD R2010 DXF files for downstream CAM toolpath processing.

---

## 2. Engineering Milestones Completed

| Stage | Engineering Objectives | Verifiable Outcome | Current Status |
| :--- | :--- | :--- | :---: |
| **Stage A** | Read-only skills ecosystem audit, security analysis, and initial baseline establishment. | Audited 6 external repos. Enforced strict security boundaries. | **COMPLETED** |
| **Stage B** | Core feature implementation: ENG-04 (Part-in-Part nesting) and ENG-05 (Adaptive rotation). | Implemented inward negative buffering ($H.\text{buffer}(-c)$) for holes. Implemented rotation candidates. | **COMPLETED** |
| **Stage C & C.1** | Benchmark reconciliation, adversarial geometry stress testing, structural DXF validation, and release review. | Reconciled historical 1,946.00 mm vs. 1,939.33 mm linear extent as 5-seed vs. 3-seed means. Passed 10 adversarial suites. | **COMPLETED** |
| **Stage C.2** | Independent verification gate. | Identified defect **DEF-01** (silent component reduction in `Part.__init__` on `MultiPolygon`s). | **COMPLETED** |
| **Stage D** | DEF-01 Geometry Integrity Remediation. | Full `MultiPolygon` support across geometry, bounds, collision, UI, and DXF export. Added `CADTopologyError`. | **COMPLETED** |

Detailed engineering reports are preserved in `team_algoryxz/nest_craft/reports/`.

---

## 3. What Was DEF-01 and How Stage D Fixed It

### The Defect (DEF-01)
In earlier versions, `Part.__init__` in `src/geometry.py` executed:
```python
if isinstance(polygon, MultiPolygon):
    polygon = max(polygon.geoms, key=lambda g: g.area)
```
This silently selected only the single largest polygon component, discarding all remaining components without raising an error or warning. On a self-intersecting bow-tie repaired via `make_valid`, this caused an exact 50% silent material loss ($400\text{ mm}^2$ discarded out of $800\text{ mm}^2$).

### The Remediation (Stage D)
1. **Full `MultiPolygon` Support:**
   - Multi-part components are now preserved in full throughout the entire pipeline.
   - Area equals the exact sum of all components.
   - Bounding box envelops all components as a unified piece.
   - Unit rotation and translation transform all components together around the multi-part centroid.
   - Collision detection buffers and tests all components.
   - DXF export writes every component polygon and interior hole to `CUT_CONTOUR` / `HOLE_CONTOUR`.
   - UI visualization renders all component patches and hole outlines.
2. **Explicit Topology Alteration Guardrails:**
   - Introduced `CADTopologyError(ValueError)`.
   - When an invalid contour is repaired via `make_valid`, the system checks if the repair changed component count (e.g. split into multiple lobes) or materially changed area ($>5\%$).
   - If unsanctioned, it **REJECTS** the input drawing with a clear, actionable exception.
   - If explicitly authorized via `metadata={"allow_repaired_topology": True}`, it preserves **100% of all components** as a `MultiPolygon` with zero material loss.
3. **Regression Testing:**
   - 15 dedicated regression tests in `team_algoryxz/nest_craft/tests/test_def01_remediation.py`.
   - Total project test count reached **66 passed** across 7 test modules.

---

## 4. Verified Benchmark Reference (Reproduce Before Quoting)

Do not alter algorithms or benchmark methodology merely to improve numbers. The verified reference results across 5 seeds on the Industrial 17-part batch ($800 \times 500\text{ mm}$ stock, $4.0\text{ mm}$ clearance) are:

| Seed | BLF Baseline (Linear) | SA Orthogonal (Linear) | Discrete Sheets | Final Sheet Remnant |
| :---: | :---: | :---: | :---: | :---: |
| **42** | 2,350.00 mm | 1,966.00 mm | 3 | $434 \times 500\text{ mm}$ (Prime) |
| **101** | 2,350.00 mm | 2,110.00 mm | 3 | $290 \times 500\text{ mm}$ (Prime) |
| **202** | 2,350.00 mm | 1,742.00 mm | 3 | $658 \times 500\text{ mm}$ (Prime) |
| **303** | 2,350.00 mm | 1,986.00 mm | 3 | $414 \times 500\text{ mm}$ (Prime) |
| **404** | 2,350.00 mm | 1,926.00 mm | 3 | $474 \times 500\text{ mm}$ (Prime) |
| **5-Seed Mean** | **2,350.00 mm** | **1,946.00 mm** | **3.00** | **$227,000.00\text{ mm}^2$** |

### Benchmark Key Findings:
- **Linear Extent Compaction:** -17.19% reduction in linear shearing advance versus BLF.
- **Stock Plate Requirement:** Exactly 3 discrete stock plates consumed in 100% of orthogonal runs.
- **Adaptive Rotation Disclosure:** On this rectilinear stock, non-orthogonal adaptive rotation ($15^\circ$ increments) expanded part bounding envelopes, averaging **2,509.34 mm** (+28.95% penalty) and requiring 4 sheets in 3 out of 5 runs. **Orthogonal rotation remains the mandatory benchmark default.**

---

## 5. What Has Actually Been Tested vs. Unverified Claims

### Tested & Verified:
- Programmatic 2D CAD vector generation and structural compliance via `ezdxf.audit()` (0 errors, 0 unclosed polylines).
- Geometric collision detection down to $1\text{ \mu m}$ clearance tolerance.
- 100% bitwise deterministic reproducibility across 10 consecutive optimization runs.
- End-to-end geometry conservation ($11,700\text{ mm}^2$ input $\longleftrightarrow$ $11,700\text{ mm}^2$ DXF export).

### Unverified Claims (Strictly Disclaimed):
- **NO Commercial CAM Import Test:** No commercial software (Trumpf TruTops, CypCut, BySoft, ProNest) was executed during this audit.
- **NO CNC Machine Cutting Trials:** No physical CNC laser or plasma cutting table was run. Real-world phenomena such as laser slat tipping, slug drop-through, thermal buckling, and pierce blowholes remain unvalidated on physical hardware.
- **NO G-Code Generation:** NEST-CRAFT outputs standard CAD DXF geometry, NOT CNC machine code (`G01`, `G02`, `M-codes`).
- **NO Validated Financial Savings:** Linear compaction on an unfinished sheet does not reduce discrete sheet procurement costs.

---

## 6. What the Next Developer Should Do

1. **Read the Documentation:**
   - [Developer Onboarding Guide](DEVELOPER_ONBOARDING.md)
   - [Current Project Status](PROJECT_STATUS.md)
   - [Technical Architecture](TECHNICAL_ARCHITECTURE.md)
   - [Known Limitations](KNOWN_LIMITATIONS.md)
2. **Reproduce the Baseline:**
   - Clone repo, create `.venv`, install `requirements.txt`.
   - Run `$env:PYTHONPATH="."; pytest team_algoryxz/nest_craft/tests` $\longrightarrow$ confirm 59 passed.
   - Run `python team_algoryxz/nest_craft/benchmarks/run_nesting_benchmarks.py` $\longrightarrow$ confirm 1,946.00 mm mean.
3. **High-Priority Work Items (See [ROADMAP.md](ROADMAP.md)):**
   - Connect with a fabrication partner to test DXF import in commercial CAM software (e.g. CypCut).
   - Add micro-tab generation in CAM post-processing rules.
   - Add a pre-check modal in the Streamlit UI for invalid/self-intersecting CAD uploads.
