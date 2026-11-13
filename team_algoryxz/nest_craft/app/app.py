"""
app.py
Streamlit Web MVP for NEST-CRAFT: AI-Assisted 2D Irregular Polygon Nesting.
"""

import os
import sys
import tempfile
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from shapely.geometry import Polygon, MultiPolygon

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from team_algoryxz.nest_craft.src.geometry import Part, Sheet
from team_algoryxz.nest_craft.src.dxf_io import (
    parse_dxf,
    validate_and_parse_dxf,
    create_sample_industrial_dxfs,
    export_nesting_to_dxf
)
from team_algoryxz.nest_craft.src.baseline import run_bottom_left_fill
from team_algoryxz.nest_craft.src.optimizer import run_simulated_annealing
from team_algoryxz.nest_craft.src.calculator import (
    calculate_fabrication_savings,
    calculate_remnant_plate_value
)

st.set_page_config(page_title="NEST-CRAFT — AI Sheet Metal Nesting", page_icon="⚙️", layout="wide")

st.title("⚙️ NEST-CRAFT: AI-Assisted Irregular Polygon Nesting")
st.markdown("**Material Optimization & Scrap Reduction for Structural Steel Fabrication MSMEs**")
st.info("⚠️ **Engineering Note:** Evaluates genuine irregular polygon placement using Shapely exact geometry. Hardware-free MVP.")

# Sidebar: Sheet & Process Parameters
st.sidebar.header("1. Sheet & Cutting Parameters")
sheet_width = st.sidebar.number_input("Sheet Width (mm)", min_value=100.0, max_value=6000.0, value=800.0, step=50.0)
sheet_height = st.sidebar.number_input("Sheet Height (mm)", min_value=100.0, max_value=3000.0, value=500.0, step=50.0)
cutting_clearance = st.sidebar.slider("Torch Clearance / Kerf Offset (mm)", min_value=0.0, max_value=15.0, value=4.0, step=0.5)

st.sidebar.header("2. Optimization Settings")
opt_iterations = st.sidebar.slider("Annealing Iterations", min_value=5, max_value=50, value=20, step=5)

rotation_mode_choice = st.sidebar.selectbox(
    "Rotation Search Strategy",
    options=["Orthogonal (0°, 90°, 180°, 270° — Default)", "Adaptive (15° Coarse + 5° Fine)", "Fixed (0° Only)"],
    index=0
)
rot_mode_map = {
    "Orthogonal (0°, 90°, 180°, 270° — Default)": "orthogonal",
    "Adaptive (15° Coarse + 5° Fine)": "adaptive",
    "Fixed (0° Only)": "none"
}
selected_rot_mode = rot_mode_map[rotation_mode_choice]

grain_choice = st.sidebar.selectbox(
    "Sheet Rolling / Grain Constraint",
    options=["None (Unconstrained)", "Horizontal (0°, 180° only)", "Vertical (90°, 270° only)"],
    index=0
)
grain_map = {
    "None (Unconstrained)": None,
    "Horizontal (0°, 180° only)": "horizontal",
    "Vertical (90°, 270° only)": "vertical"
}
selected_grain = grain_map[grain_choice]

allow_part_in_part = st.sidebar.checkbox(
    "Enable Part-in-Part Nesting (Inside Interior Cutouts)",
    value=True,
    help="Safely nests smaller components inside interior holes of larger parts using inward-buffered feasible regions."
)

# Main Area: Part Upload & Batch Selection
st.subheader("📁 Part Upload & Batch Selection")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_files = st.file_uploader("Upload AutoCAD DXF Files", type=["dxf"], accept_multiple_files=True)
    
with col2:
    use_sample = st.checkbox("Load Sample Industrial Batch (Gussets, Brackets, Flanges, Base Plates)", value=True)

parts_list = []

if uploaded_files:
    total_holes_found = 0
    for up_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            tmp.write(up_file.read())
            tmp_path = tmp.name
        parsed, report = validate_and_parse_dxf(tmp_path)
        parts_list.extend(parsed)
        total_holes_found += report.get("holes_extracted_count", 0)
        
        for w in report.get("warnings", []):
            st.warning(f"[{up_file.name}] {w}")
        for err in report.get("errors", []):
            st.error(f"[{up_file.name}] {err}")
            
        os.unlink(tmp_path)
        
    if parts_list:
        st.success(f"Parsed {len(parts_list)} parts ({total_holes_found} interior cutouts) from uploaded DXFs.")

elif use_sample:
    sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "industrial_samples"))
    dxf_files = create_sample_industrial_dxfs(sample_dir)
    quantities = {"gusset_plate.dxf": 4, "l_bracket.dxf": 6, "flange_plate.dxf": 4, "notched_base_plate.dxf": 3}
    for f in dxf_files:
        base = os.path.basename(f)
        parsed = parse_dxf(f)
        for p in parsed:
            p.quantity = quantities.get(base, 2)
            parts_list.append(p)
    st.info(f"Loaded Standard Industrial Sample Batch: {sum(p.quantity for p in parts_list)} parts across 4 components.")

if not parts_list:
    st.warning("Please upload DXF files or check the sample batch to continue.")
    st.stop()

# Parts Summary Table
total_quantity = sum(p.quantity for p in parts_list)
total_net_area = sum(p.area * p.quantity for p in parts_list) / 1e6 # m^2

st.write(f"**Total Components in Batch:** {total_quantity} | **Total Net Steel Area:** {total_net_area:.3f} m²")

# Run Nesting Comparison
if st.button("🚀 Run Nesting Optimization (BLF Baseline vs. Simulated Annealing)", type="primary"):
    with st.spinner("Executing Bottom-Left-Fill Baseline..."):
        blf_sheets, blf_stats = run_bottom_left_fill(
            parts_list, sheet_width=sheet_width, sheet_height=sheet_height,
            clearance=cutting_clearance, rotation_mode=selected_rot_mode,
            grain_direction=selected_grain, step_size=8.0,
            allow_part_in_part=allow_part_in_part
        )
        
    with st.spinner(f"Running Simulated Annealing Optimizer ({opt_iterations} iterations)..."):
        sa_sheets, sa_stats = run_simulated_annealing(
            parts_list, sheet_width=sheet_width, sheet_height=sheet_height,
            clearance=cutting_clearance, rotation_mode=selected_rot_mode,
            grain_direction=selected_grain,
            max_iterations=opt_iterations, initial_temp=100.0, cooling_rate=0.88,
            step_size=8.0, random_seed=42,
            allow_part_in_part=allow_part_in_part
        )
        
    st.session_state["blf_sheets"] = blf_sheets
    st.session_state["blf_stats"] = blf_stats
    st.session_state["sa_sheets"] = sa_sheets
    st.session_state["sa_stats"] = sa_stats

# Display Results if run
if "blf_stats" in st.session_state and "sa_stats" in st.session_state:
    blf_stats = st.session_state["blf_stats"]
    sa_stats = st.session_state["sa_stats"]
    blf_sheets = st.session_state["blf_sheets"]
    sa_sheets = st.session_state["sa_sheets"]
    
    st.markdown("---")
    st.subheader("📊 Empirical Performance Comparison")
    
    # 1. Discrete Multi-Sheet Metric Tier
    st.markdown("##### 1. Discrete Plate Metrics (Multi-Sheet Procurement)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BLF Sheets Used", f"{blf_stats['sheets_used']}")
    m2.metric("Optimized Sheets Used", f"{sa_stats['sheets_used']}", 
              delta=f"{blf_stats['sheets_used'] - sa_stats['sheets_used']} sheets saved" if blf_stats['sheets_used'] > sa_stats['sheets_used'] else "Same sheet tier")
    m3.metric("BLF Discrete Utilization", f"{blf_stats['utilization_pct']}%")
    m4.metric("Optimized Discrete Utilization", f"{sa_stats['utilization_pct']}%", 
              delta=f"{sa_stats['utilization_pct'] - blf_stats['utilization_pct']:+.2f}%")
              
    # 2. Linear Compaction & Remnant Preservation Tier (The Physical Breakthrough)
    st.markdown("##### 2. Linear Compaction & Prime Remnant Preservation")
    blf_lin = blf_stats.get('total_linear_length_consumed', 0.0)
    sa_lin = sa_stats.get('total_linear_length_consumed', 0.0)
    lin_saved = blf_lin - sa_lin
    lin_pct = (lin_saved / blf_lin * 100.0) if blf_lin > 0 else 0.0
    
    sa_rem = sa_stats.get('final_sheet_remnant', {})
    blf_rem = blf_stats.get('final_sheet_remnant', {})
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("BLF Linear Span", f"{blf_lin:.1f} mm")
    c2.metric("SA Linear Span", f"{sa_lin:.1f} mm", delta=f"-{lin_saved:.1f} mm ({lin_pct:.1f}% saved)" if lin_saved > 0 else "0 mm")
    c3.metric("Sheet 3 Remnant (BLF)", f"{blf_rem.get('remnant_width', 0):.0f} x {sheet_height:.0f} mm", delta="Unusable scrap strip" if not blf_rem.get('is_prime_remnant', False) else "Prime plate")
    c4.metric("Sheet 3 Remnant (SA)", f"{sa_rem.get('remnant_width', 0):.0f} x {sheet_height:.0f} mm", delta=f"{sa_rem.get('remnant_pct', 0):.1f}% preserved plate" if sa_rem.get('is_prime_remnant', False) else "Scrap")

    # 3. Advanced Geometry & Placement Diagnostics
    st.markdown("##### 3. Advanced Geometry & Placement Diagnostics")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Parts Nested in Cutouts", f"{sa_stats.get('parts_nested_in_holes', 0)} parts")
    d2.metric("Rotation Strategy", f"{sa_stats.get('rotation_mode', 'orthogonal').title()}")
    d3.metric("Rolling Grain Constraint", f"{str(sa_stats.get('grain_direction', 'None')).title()}")
    d4.metric("Algorithm Run Time", f"{sa_stats.get('runtime_seconds', 0.0):.2f} s")

    st.caption("ℹ️ **Industrial Reality:** In discrete plate purchases, raw steel invoices require buying integer sheets. Simulated Annealing creates economic value by compacting nested parts to leave a large, intact **prime remnant plate** on Sheet 3 for subsequent jobs rather than wasting it as scrap.")
              
    # Visual Layout Plots
    st.subheader("📐 Nested Sheet Layouts")
    
    def plot_sheets(sheets, title):
        fig, axes = plt.subplots(len(sheets), 1, figsize=(8, 3.5 * len(sheets)))
        if len(sheets) == 1:
            axes = [axes]
        cmap = plt.get_cmap('tab10')
        
        for idx, (ax, s) in enumerate(zip(axes, sheets)):
            rem = s.get_remnant_geometry()
            ax.set_title(f"{title} — Sheet {idx+1} ({s.width:.0f}x{s.height:.0f}mm) | Util: {s.get_utilization_pct():.1f}% | Remnant: {rem['remnant_width']:.0f}mm ({rem['remnant_pct']:.1f}%)", fontsize=9)
            ax.set_xlim(-20, s.width + 20)
            ax.set_ylim(-20, s.height + 20)
            ax.set_aspect('equal')
            ax.grid(True, linestyle='--', alpha=0.3)
            # Draw sheet box
            ax.plot([0, s.width, s.width, 0, 0], [0, 0, s.height, s.height, 0], 'r--', lw=1.5, label="Sheet Boundary")
            
            # Draw remnant offcut zone
            if rem["remnant_width"] > 0:
                ax.axvspan(rem["max_x_span"], s.width, ymin=0, ymax=1, color='green', alpha=0.12, hatch='//', label="Preserved Remnant" if idx == len(sheets)-1 else "")
            
            # Draw parts (supporting both Polygon and MultiPolygon)
            for p_idx, (p_id, poly, rot) in enumerate(s.placed_parts):
                sub_polys = poly.geoms if isinstance(poly, MultiPolygon) else [poly]
                is_child = hasattr(s, 'part_in_part_assignments') and p_id in s.part_in_part_assignments
                color = '#00E5FF' if is_child else cmap(p_idx % 10)
                
                for sub_poly in sub_polys:
                    ext = np.array(sub_poly.exterior.coords)
                    patch = MplPolygon(ext, closed=True, facecolor=color, edgecolor='black', alpha=0.85 if is_child else 0.75, lw=1.5 if is_child else 1.0)
                    ax.add_patch(patch)
                    
                    # Render interior holes in white with dashed red outline
                    for interior in sub_poly.interiors:
                        hole_coords = np.array(interior.coords)
                        hole_patch = MplPolygon(hole_coords, closed=True, facecolor='white', edgecolor='red', lw=1.2, linestyle='--')
                        ax.add_patch(hole_patch)
                    
                cx, cy = poly.centroid.x, poly.centroid.y
                has_holes = any(len(sub.interiors) > 0 for sub in sub_polys)
                label = f"{p_id}\n(in hole)" if is_child else str(p_id)
                ax.text(cx, cy, label, fontsize=6.0 if is_child else 6.5, ha='center', va='center', color='black' if (has_holes or is_child) else 'white', weight='bold')
                
        plt.tight_layout()
        return fig

    v_col1, v_col2 = st.columns(2)
    with v_col1:
        st.write("**Bottom-Left-Fill (Baseline)**")
        fig_blf = plot_sheets(blf_sheets, "Baseline BLF")
        st.pyplot(fig_blf)
        
    with v_col2:
        st.write("**Simulated Annealing (Optimized)**")
        fig_sa = plot_sheets(sa_sheets, "Simulated Annealing")
        st.pyplot(fig_sa)
        
    # Export Layout Button
    st.markdown("---")
    st.subheader("💾 Export Machine Layout")
    export_path = os.path.join(tempfile.gettempdir(), "nested_layout.dxf")
    export_nesting_to_dxf(sa_sheets, export_path)
    with open(export_path, "rb") as f:
        st.download_button(
            label="📥 Download CNC Cutting DXF Layout",
            data=f.read(),
            file_name="nest_craft_cut_sheet.dxf",
            mime="application/dxf"
        )
    st.caption("⚠️ **Safety Notice:** Output DXF provides geometry placement. Machine-specific lead-ins, kerf calibration, and controller G-code verification required before cutting.")

# Savings Calculator Section
st.markdown("---")
st.subheader("💰 MSME Financial Savings Calculator")
st.markdown("*Customizable ROI model for fabrication shop owners.*")

calc_col1, calc_col2, calc_col3 = st.columns(3)
with calc_col1:
    tonnes_in = st.number_input("Annual Steel Consumption (Tonnes)", value=120.0, step=10.0)
    steel_price_in = st.number_input("Raw Steel Purchase Cost (₹/kg)", value=65.0, step=2.0)
with calc_col2:
    scrap_price_in = st.number_input("Scrap Resale Value (₹/kg)", value=32.0, step=1.0)
    sub_fee_in = st.number_input("NEST-CRAFT Monthly SaaS Fee (₹)", value=3500.0, step=500.0)
with calc_col3:
    base_util_in = st.number_input("Current Shop Utilization (%)", value=65.0, min_value=30.0, max_value=90.0, step=1.0)
    opt_util_in = st.number_input("Optimized Utilization (%)", value=78.0, min_value=30.0, max_value=98.0, step=1.0)

savings_res = calculate_fabrication_savings(
    annual_tonnes=tonnes_in,
    steel_price_per_kg=steel_price_in,
    scrap_sale_per_kg=scrap_price_in,
    baseline_utilization_pct=base_util_in,
    optimized_utilization_pct=opt_util_in,
    software_monthly_fee_inr=sub_fee_in
)

res = savings_res["results"]
r1, r2, r3, r4 = st.columns(4)
r1.metric("Annual Scrap Reduced", f"{res['annual_scrap_reduced_tonnes']} Tonnes")
r2.metric("Gross Material Savings", f"₹{res['gross_annual_savings_inr']:,.0f}")
r3.metric("Net Annual Profit", f"₹{res['net_annual_profit_inr']:,.0f}")
r4.metric("Customer ROI Multiple", f"{res['roi_multiple']}x", delta=f"{res['payback_period_days']} days payback")
st.caption(f"**Model Status:** {savings_res['inputs']['status']} | {savings_res['disclaimer']}")
