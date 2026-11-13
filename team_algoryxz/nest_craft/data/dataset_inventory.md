# NEST-CRAFT: BENCHMARK GEOMETRY DATASET INVENTORY

This document records the provenance, licensing, geometry validity, and characteristics of all datasets used in Track A.

---

## 1. PRIMARY BENCHMARK DATASET: ESICUP 2D IRREGULAR (SHAPES)
* **Dataset Name:** `SHAPES` (`shapes.txt` / `shapes0.xml`)
* **Original Source URL:** [https://github.com/ESICUP/datasets/tree/main/2d_irregular/shapes](https://github.com/ESICUP/datasets/tree/main/2d_irregular/shapes)
* **Academic Citation:** Oliveira, J.F., Gomes, A.M., & Ferreira, J.S. (2000). *"A new constructive algorithm for nesting problems."* OR Spektrum, 22(2), 263–284.
* **License:** Open Academic Benchmark (CC-BY 4.0 / Public Research Use).
* **File Format:** Plain text vertex coordinates (`.txt`) and XML specification (`.xml`).
* **Number of Component Types:** 4 distinct non-convex polygon templates:
  - Piece 1: 8 vertices, quantity = 15
  - Piece 2: 4 vertices, quantity = 7
  - Piece 3: 11 vertices, quantity = 9
  - Piece 4: 12 vertices, quantity = 12
* **Total Components:** 43 parts.
* **Geometric Validity:** All polygons checked using `shapely.is_valid`; verified 100% valid simple non-self-intersecting closed loops.
* **Unit of Measure:** Dimensionless benchmark units (scaled to standard strip width $W = 40.0$).

---

## 2. SECONDARY BENCHMARK DATASET: ESICUP 2D IRREGULAR (SWIM)
* **Dataset Name:** `SWIM` (`swim.txt` / `swim.xml`)
* **Original Source URL:** [https://github.com/ESICUP/datasets/tree/main/2d_irregular/swim](https://github.com/ESICUP/datasets/tree/main/2d_irregular/swim)
* **Academic Citation:** Dowsland, K.A., Dowsland, W.B., & Bennell, J.A. (1998). *"Jostling for position: local improvement for irregular cutting problems."* Journal of the Operational Research Society, 49(6), 647–658.
* **License:** Open Academic Benchmark.
* **File Format:** Plain text coordinate stream (`.txt`) and XML format.
* **Characteristics:** Highly curved, complex non-convex garments (swimwear pattern pieces with up to 32 vertices per curve).
* **Geometric Validity:** 100% valid polygons verified in Shapely.

---

## 3. REAL-WORLD INDUSTRIAL FABRICATION CAD SAMPLES (ODISHA BENCHMARK)
* **Dataset Name:** `industrial_samples/` (Generated via AutoCAD R2010 DXF standard)
* **Source:** Derived from standard structural steel fabrication profiles used in Rourkela/Kalinganagar MSME fabrication shops.
* **Format:** AutoCAD DXF (`.dxf`) parsed via `ezdxf`.
* **Components:**
  1. `gusset_plate.dxf`: Structural triangular bracing plate with chamfer ($250\text{ mm} \times 200\text{ mm}$, 5 vertices).
  2. `l_bracket.dxf`: Angle stiffener bracket with inner right-angle notch ($180\text{ mm} \times 220\text{ mm}$, 6 vertices).
  3. `flange_plate.dxf`: Octagonal chamfered pipe flange ($180\text{ mm} \times 180\text{ mm}$, 8 vertices).
  4. `notched_base_plate.dxf`: Heavy machinery foundation plate with slot cutout ($300\text{ mm} \times 140\text{ mm}$, 7 vertices).
* **Batch Size:** 17 components totaling $0.94\text{ m}^2$ net steel plate area.
* **Clearance Enforced:** $4.0\text{ mm}$ (standard industrial CNC plasma cutting torch kerf + lead-in margin).
