# NEST-CRAFT — Fabricator Demonstration Package & Feedback Template

**For:** Sheet Metal Fabrication MSMEs & CNC Cutting Machine Operators  
**Engine:** NEST-CRAFT (Team Algoryxz · Odisha AI Hackathon 2026)  
**Prototype Version:** Stage F Engineering Release  
**Notice:** This document serves as an evaluation guide and survey instrument for external fabricators. **No fabricated customer claims or unverified endorsements are included.**

---

## 1. What NEST-CRAFT Does & Does Not Do

### What It Does:
1. **Automated 2D Profile Packing:** Ingests planar AutoCAD DXF vector drawings of parts (gussets, brackets, flanges, base plates) and packs them efficiently across standard raw sheet metal plates.
2. **Linear Cutting Extent Compaction:** Heuristically groups components along the X-axis using Simulated Annealing, reducing total linear cutting span by up to **$17.19\%$** compared to standard Bottom-Left-Fill (BLF).
3. **Prime Remnant Offcut Preservation:** Rather than spreading parts sparsely across the entire final sheet, it compacts parts to the left side, preserving an intact, rectangular **virgin remnant plate** ($> 100\text{ mm}$ width) on the right for future production jobs.
4. **Part-in-Part Cavity Nesting:** Identifies large interior apertures in components (e.g. flange center cutouts) and nests smaller parts inside them using inward kerf buffering.
5. **Multi-Layer DXF Export:** Generates clean AutoCAD R2010 DXF layouts with structured layers (`SHEET_BOUNDARY`, `CUT_CONTOUR`, `HOLE_CONTOUR`, `PART_IN_PART_CHILD`).

### What It DOES NOT Do:
1. **NO CNC G-Code Generation:** NEST-CRAFT does **NOT** generate machine-specific G-code (`G00`, `G01`, `M03`, `M05`, `G02/G03`).
2. **NO Machine-Specific Toolpathing:** It does not assign pierce dwell cycles, torch height control (THC) voltages, cutting gas pressures, or feed rates.
3. **NO Micro-Tab / Joint Generation:** Micro-tabs (to prevent small parts from tipping or falling into table slats) must be applied in CAM software.
4. **NO Kerf Offset Application:** While parts are nested with user-specified clearance spacing (e.g. $4.0\text{ mm}$), the actual CNC torch kerf diameter compensation (cutter radius compensation `G41/G42`) must be handled by your machine controller or CAM software.

---

## 2. Supported Input Formats & CAD Ingestion Rules

| Feature | Supported? | Operating Notes |
| :--- | :---: | :--- |
| **AutoCAD DXF Versions** | ✅ Yes | R12, R2000, R2004, R2007, R2010, R2013, R2018 formats supported via ezdxf. |
| **Supported 2D Entities** | ✅ Yes | `LWPOLYLINE`, `POLYLINE`, `LINE`, `ARC`, `CIRCLE`, `SPLINE`, `ELLIPSE`. |
| **Concentric Interior Holes** | ✅ Yes | Automatically extracted and placed on `HOLE_CONTOUR` layer. |
| **Open Contours / Gaps** | ❌ Rejected | Segments with gaps $> 0.001\text{ mm}$ are rejected to prevent torch blowouts. |
| **Self-Intersecting Lines** | ⚠️ Guarded | Rejected by default (`CADTopologyError`). Requires explicit operator repair toggle. |
| **3D CAD Entities** | ⚠️ Ignored | `3DFACE`, `MESH`, `SOLID3D` entities are flagged and ignored. Profiles must be 2D. |
| **DWG Native Files** | ❌ No | Must be exported/saved as `.dxf` in AutoCAD, SolidWorks, or LibreCAD before uploading. |

---

## 3. Example Nesting Comparison (17-Part Industrial Batch)

* **Stock Size:** $800\text{ mm} \times 500\text{ mm}$
* **Torch Clearance:** $4.0\text{ mm}$
* **Parts Batch:** 4 gussets, 6 brackets, 4 flanges, 3 base plates

| Evaluation Metric | Bottom-Left-Fill (Baseline) | NEST-CRAFT (Simulated Annealing) | Shop Floor Impact |
| :--- | :---: | :---: | :--- |
| **Plates Purchased** | 3 plates | 3 plates | Same stock purchase requirement. |
| **Linear Cutting Span** | 2,350.00 mm | **1,946.00 mm** | **$-404.0\text{ mm}$ linear compaction ($-17.19\%$)**. |
| **Sheet 3 Usable Remnant** | $50\text{ mm} \times 500\text{ mm}$ strip | **$434\text{ mm} \times 500\text{ mm}$ plate** | **$217,000\text{ mm}^2$ prime plate recovered for next job**. |
| **Offcut Classification** | Unusable skeleton scrap | **Prime reusable plate** | Saved from scrap resale bin. |

---

## 4. How to Inspect & Export in the Web Interface

1. **CAD Diagnostics:** Review the per-file diagnostics table in Step 4. Ensure all drawings show `✅ Valid` status with 0 errors.
2. **Remnant Intelligence:** In Step 7, inspect the green-hatched region on Sheet 3 to verify the width and square footage of the intact offcut plate.
3. **Export DXF:** Click **"Download Nesting DXF Layout"** in Step 8.
4. **CAM Import:** Load the downloaded `.dxf` into your workshop CAM software (ProNest, CypCut, FastCAM, SheetCAM). Assign lead-ins, micro-tabs, and post-process to G-code.

---

## 5. Structured Fabricator Feedback Form

*Please complete this evaluation after reviewing the software demonstration or importing a sample DXF.*

### Section A: General Information
* **Shop / Enterprise Name:** __________________________________________________
* **Location (City / State):** __________________________________________________
* **Primary Cutting Process:** `[ ] Fiber Laser` `[ ] Plasma` `[ ] Oxy-Fuel` `[ ] Waterjet`
* **Current CAM Software Used:** `[ ] CypCut` `[ ] ProNest` `[ ] FastCAM` `[ ] SheetCAM` `[ ] Other: _______`
* **Typical Monthly Sheet Metal Consumption:** `[ ] < 10 Tonnes` `[ ] 10–50 Tonnes` `[ ] > 50 Tonnes`

### Section B: Technical Evaluation (Rate 1 to 5: 1 = Poor, 5 = Excellent)

1. **Drawing Ingestion & Compatibility:**  
   *Did the DXF parser correctly recognize your parts, contours, and internal holes?*  
   `Score: [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]`  
   *Comments / Issues Encountered:* _____________________________________________

2. **Nesting Density & Layout Quality:**  
   *How does the part packing compare to your operator's manual nesting or current CAM nesting?*  
   `Score: [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]`  
   *Comments:* _________________________________________________________________

3. **Prime Remnant Preservation Value:**  
   *Is the rectangular virgin offcut plate on the final sheet large enough to be scheduled for another job?*  
   `Score: [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]`  
   *Comments on Remnant Dimensions:* ___________________________________________

4. **Web Interface Usability & Speed:**  
   *Was the 9-step progression clear, fast, and easy for machine operators to understand?*  
   `Score: [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]`  
   *Comments:* _________________________________________________________________

5. **CAM Export Handoff:**  
   *Did the exported DXF open cleanly in your CAM tool without scaling errors or missing lines?*  
   `Score: [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]  [ N/A - Not Tested in CAM ]`  
   *Details of Import Warnings / Errors:* ________________________________________

### Section C: Qualitative Feedback

* **What critical feature is missing that you need before using this in daily production?**  
  _____________________________________________________________________________  
  _____________________________________________________________________________

* **Would your shop consider using NEST-CRAFT as a pre-nesting material estimator or layout engine?**  
  `[ ] Yes, immediately`  
  `[ ] Yes, after adding direct CAM post-processing`  
  `[ ] Unlikely (explain reason below)`  
  *Reason:* ___________________________________________________________________

* **Sign-off / Evaluator Signature:** ______________________ **Date:** _______________
