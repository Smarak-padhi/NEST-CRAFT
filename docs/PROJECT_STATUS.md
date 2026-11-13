# NEST-CRAFT — Project Status & Handover Ledger

**Current Engineering Stage:** Stage D Completed & Verified (DEF-01 Remediation)  
**Last Audit Date:** 2026-11-13  
**Repository Branch:** `main`

---

## 1. Executive Status Dashboard

| Dimension | Current State | Verifiable Evidence |
| :--- | :---: | :--- |
| **Automated Tests** | **66 / 66 Passing** (100%) | Verified via pytest in clean repository root (4.37s execution). |
| **Geometry Engine** | **DEF-01 Remediated** | Valid MultiPolygons fully preserved. Silent component reduction eliminated. `CADTopologyError` raised on unsanctioned component splitting and hole count alteration. DXF ingestion closed-loop enforced. |
| **Optimization Core** | **BLF & SA Operational** | BLF baseline and Simulated Annealing with Part-in-Part nesting operational across fixed seeds. |
| **Benchmark Status** | **Reconciled & Preserved** | 5-seed Industrial batch orthogonal mean of **1,946.00 mm** verified without regression. |
| **CAD / DXF I/O** | **Structural Validation** | DXF export audited via `ezdxf.audit()` (0 errors, 0 unclosed polylines). Layer separation verified. |
| **UI Dashboard** | **Streamlit MVP Operational** | Interactive multi-sheet CAD viewer, remnant accounting cards, and DXF exporter functional. |
| **Hackathon Readiness** | **READY (VERIFIED)** | Approved for controlled prototype demonstration at Odisha AI Hackathon 2026. |
| **Industrial Pilot** | **CONDITIONAL** | Requires external CAM toolpath post-processing (micro-tabs, lead-ins, kerf compensation). |
| **Autonomous Production** | **NOT READY (DISCLAIMED)** | G-code generation, thermal dissipation modeling, and CNC vision feedback are out of scope. |

---

## 2. Completed Milestones (Stages A through D)

### Stage A: Codebase Audit & Baseline
- Audited 6 reference repositories and established strict security boundaries.
- Set up initial Bottom-Left-Fill (BLF) and Simulated Annealing (SA) baselines.

### Stage B: Core Feature Implementation
- **ENG-04 (Part-in-Part Nesting):** Inward negative buffering ($H.\text{buffer}(-c)$) to identify safe feasible cavities inside parent holes.
- **ENG-05 (Adaptive Rotation):** Coarse $15^\circ$ exploration with $5^\circ$ local refinement and rolling grain constraints.

### Stage C & C.1: Evidence Reconciliation & Rigor
- **Benchmark Reconciliation:** Proved that the 1,946.00 mm vs. 1,939.33 mm deviation was strictly a 5-seed vs. 3-seed arithmetic mean. Both are derived from identical deterministic runs.
- **Adversarial Stress Testing:** Built 9-test adversarial suite for concave cutouts, pinch-off necks, and sub-millimeter clearance checks down to $1\text{ \mu m}$.
- **Evidence Corrections (C.1):** Retracted unsubstantiated claims about adaptive rotation on irregular parts; disclosed that adaptive rotation performed worse on average across both datasets.

### Stage C.2: Independent Verification Gate
- Identified **DEF-01**: `Part.__init__` previously used `max(polygon.geoms, key=lambda g: g.area)`, silently discarding non-maximum components of `MultiPolygon`s and causing up to 50% material loss on bow-tie geometries.

### Stage D: DEF-01 Remediation (Current Master)
- Fully enabled `MultiPolygon` across area calculation, unit normalization, rotation, collision checking, sheet containment, Streamlit visualization, and DXF export.
- Introduced `CADTopologyError` to reject invalid geometry repairs that alter component count or area without explicit authorization.
- Added 8 dedicated regression tests (`test_def01_remediation.py`). Total project tests reached **59 passed**.
- Re-verified non-regression of the 5-seed industrial benchmark ($1,946.00\text{ mm}$ mean).

---

## 3. High-Priority Next Tasks (Roadmap Ahead)

1. **CAM Post-Processor Integration (P1):**
   - Partner with an industrial sheet metal fabrication shop to run exported DXFs through an actual commercial CAM suite (e.g. Trumpf TruTops, Bystronic BySoft, CypCut, or Hypertherm ProNest).
   - Verify automated micro-tab injection to prevent child parts from dropping into table slats.
2. **CAD Ingestion Pre-Check UI (P1):**
   - In the Streamlit UI, provide explicit visual alerts when uploaded DXFs contain self-intersecting polylines, asking the user to authorize or reject repaired topologies.
3. **Continuous Integration (CI) Setup (P2):**
   - Add a GitHub Actions workflow (`.github/workflows/ci.yml`) to automatically run the 59 tests and benchmark checks on every pull request.
4. **Primary Source Customer Validation (P2):**
   - Validate economic assumptions with real fabrication MSMEs, comparing actual shop scrap rates against prototype remnant recovery metrics.
