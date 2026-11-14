# NEST-CRAFT — Real-World DXF Drawing Intake & Validation Protocol

**Document Purpose:** Standard Operating Procedure (SOP) for acquiring, documenting, sanitizing, testing, and archiving genuine production DXF drawings from sheet metal fabricators and CNC cutting shops.  
**Version:** Stage G Engineering Release  
**Status:** ACTIVE GOVERNANCE PROTOCOL  

---

## 1. Objectives & Scope

This protocol establishes a rigorous, legally compliant, and technically reproducible process for evaluating real-world customer CAD drawings within NEST-CRAFT. It governs every drawing from initial fabricator consent to CAM verification, ensuring that:
1. All drawings have verifiable commercial provenance and written permission.
2. Proprietary customer geometry is redacted or anonymized where required.
3. Cryptographic integrity (SHA-256) is recorded prior to any CAD modification.
4. Fail-closed ingestion diagnostics and nesting outcomes are reproducibly documented.
5. Ingestion limitations are transparently acknowledged without unverified claims.

---

## 2. 10-Step Intake & Verification Lifecycle

```
┌─────────────────────────┐
│ 1. Fabricator Consent   │ ── Written evaluation permission & NDA/IP agreement
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 2. Provenance Logging   │ ── Record shop type, machine type, cutting process, CAD software
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 3. Cryptographic Hash   │ ── Compute SHA-256 on pristine original DXF file
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 4. IP Redaction/Clean   │ ── Strip title blocks, customer logos, company metadata if needed
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 5. Unit & Stock Audit   │ ── Confirm units (mm vs inches), raw sheet size, thickness, kerf
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 6. Ingestion Diagnosis  │ ── Run validate_and_parse_dxf(file, allow_repaired_topology=False)
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 7. Nesting Benchmark    │ ── Run BLF and Simulated Annealing (record runtime, plates, extent)
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 8. Multi-Layer DXF Out  │ ── Export nested layout DXF (R2010 AC1024, structured layers)
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 9. External CAM Import  │ ── Operator loads exported DXF in workshop CAM (lead-ins, toolpath)
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 10. Audit Archival      │ ── Record results in REAL_WORLD_DXF_TEST_MATRIX.md & secure store
└─────────────────────────┘
```

---

## 3. Detailed Protocol Specifications

### Step 1: Fabricator Permission & IP Authorization
- Obtain written or documented email authorization from the workshop owner, production manager, or CAD engineer permitting use of the DXF files for evaluation and benchmarking.
- Confirm whether the drawings may be published in an open-source evaluation repository or must remain private/confidential.
- If proprietary: obtain authorization to sanitize/anonymize geometry.

### Step 2: Provenance Documentation
For each received file, record:
- **Shop / Fabricator:** Anonymous identifier or authorized company name.
- **Cutting Process:** Fiber Laser / CO2 Laser / High-Definition Plasma / Waterjet / Oxy-Fuel.
- **Source CAD Tool:** AutoCAD, SolidWorks, Autodesk Inventor, Tekla, DraftSight, LibreCAD, etc.
- **Production Context:** Structural bracket, HVAC ducting, heavy equipment gusset, architectural panel, etc.

### Step 3: Cryptographic Integrity (Original Pristine Hash)
- Place the original unmodified drawing into a secure intake vault: `data/real_world_intake/pristine/`.
- Compute and record the SHA-256 hash immediately:
  ```powershell
  Get-FileHash -Algorithm SHA256 <file.dxf>
  ```
- The pristine copy is **never edited or overwritten**.

### Step 4: Redaction & Working Copy Creation
- If the DXF contains proprietary customer title blocks, order numbers, designer names, or client logos:
  - Copy to `data/real_world_intake/working/<sanitized_name>.dxf`.
  - Remove non-cutting layers (`DEFPOINTS`, `TITLE_BLOCK`, `BORDER`, text annotations) using CAD software or `ezdxf`.
  - Ensure cutting contours remain mathematically unchanged.
  - Compute and log the SHA-256 hash of the sanitized working copy.

### Step 5: Unit & Stock Geometry Verification
- Inspect the `$INSUNITS` header in the DXF:
  - `4` = Millimeters (Default accepted)
  - `1` = Inches (Flag for 25.4x conversion)
  - `0` = Unitless (Must request explicit unit confirmation from fabricator)
- Record fabricator stock plate dimensions (e.g., $2500 \times 1250\text{ mm}$, $3000 \times 1500\text{ mm}$, $800 \times 500\text{ mm}$), plate thickness, material grade, and torch clearance.

### Step 6: Automated Fail-Closed Ingestion & Diagnostics
- Run `validate_and_parse_dxf(working_copy_path, allow_repaired_topology=False)`.
- Record:
  - Total entity count and distribution (`LWPOLYLINE`, `POLYLINE`, `LINE`, `ARC`, `SPLINE`, etc.).
  - Unclosed segment count and dangling nodes.
  - Extracted solid parts and interior cutouts (holes).
  - Warnings for unsupported 3D entities or non-cutting annotations.
  - Ingestion status: `PASS` (valid closed planar profiles) or `REJECTED` (open loop, self-intersection, corrupt entity).
- **Rule:** Never silently repair topology without explicit operator authorization.

### Step 7: Nesting Execution & Metric Capture
- Execute baseline Bottom-Left-Fill (`run_bottom_left_fill`).
- Execute Simulated Annealing with orthogonal rotation (`run_simulated_annealing`).
- Record:
  - Discrete sheet count consumed (must be whole integers).
  - Total linear extent ($X_{\max}$ on final plate).
  - Execution runtime (seconds).
  - Reusable remnant geometry ($> 100\text{ mm}$ width).

### Step 8: Production DXF Layout Export
- Export multi-sheet or single-sheet layout via `export_nesting_to_dxf()`.
- Validate exported DXF using `validate_exported_dxf()`.
- Confirm structured layer assignments: `SHEET_BOUNDARY`, `CUT_CONTOUR`, `HOLE_CONTOUR`, `PART_IN_PART_CHILD`.

### Step 9: Commercial CAM Import & Post-Processing
- Provide exported DXF to fabricator CAM programmer.
- Execute import SOP according to [`CAM_INTEROPERABILITY_TEST_PROTOCOL.md`](./CAM_INTEROPERABILITY_TEST_PROTOCOL.md).
- Record lead-in behavior, micro-tab feasibility, cutting sequence, and collision check results.

### Step 10: Matrix Publication & Archival
- Enter complete case audit record into [`REAL_WORLD_DXF_TEST_MATRIX.md`](./REAL_WORLD_DXF_TEST_MATRIX.md).
- Preserve all working files, logs, and CAM audit records in version-controlled project storage.
