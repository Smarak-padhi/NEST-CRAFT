"""
calculator.py
Financial savings and ROI calculator for NEST-CRAFT.
Evaluates scrap reduction and bottom-line profit for fabrication MSMEs.
"""

from typing import Dict, Any

def calculate_fabrication_savings(annual_tonnes: float = 120.0,
                                  steel_price_per_kg: float = 65.0,
                                  scrap_sale_per_kg: float = 32.0,
                                  baseline_utilization_pct: float = 65.0,
                                  optimized_utilization_pct: float = 78.0,
                                  software_monthly_fee_inr: float = 3500.0) -> Dict[str, Any]:
    """
    Computes transparent financial savings from nesting optimization.
    
    Formula:
    - Net material cost lost per kg of scrap = Steel Purchase Price - Scrap Resale Price
    - Baseline Scrap (tonnes) = Annual Tonnes * (100 - Baseline Util) / 100
    - Optimized Scrap (tonnes) = Annual Tonnes * (100 - Optimized Util) / 100
    - Scrap Saved (tonnes) = Baseline Scrap - Optimized Scrap
    - Gross Cash Savings = Scrap Saved (kg) * Net Cost Lost per kg
    """
    # Validation
    baseline_utilization_pct = max(10.0, min(95.0, baseline_utilization_pct))
    optimized_utilization_pct = max(baseline_utilization_pct, min(98.0, optimized_utilization_pct))
    
    net_scrap_loss_per_kg = max(0.0, steel_price_per_kg - scrap_sale_per_kg)
    
    baseline_scrap_tonnes = annual_tonnes * ((100.0 - baseline_utilization_pct) / 100.0)
    optimized_scrap_tonnes = annual_tonnes * ((100.0 - optimized_utilization_pct) / 100.0)
    scrap_saved_tonnes = baseline_scrap_tonnes - optimized_scrap_tonnes
    
    gross_annual_savings_inr = (scrap_saved_tonnes * 1000.0) * net_scrap_loss_per_kg
    annual_software_cost_inr = software_monthly_fee_inr * 12.0
    net_annual_profit_inr = gross_annual_savings_inr - annual_software_cost_inr
    
    roi_multiple = (gross_annual_savings_inr / annual_software_cost_inr) if annual_software_cost_inr > 0 else 0.0
    payback_days = (annual_software_cost_inr / gross_annual_savings_inr * 365.0) if gross_annual_savings_inr > 0 else 999.0
    
    return {
        "inputs": {
            "annual_steel_consumption_tonnes": annual_tonnes,
            "steel_purchase_price_per_kg_inr": steel_price_per_kg,
            "scrap_resale_price_per_kg_inr": scrap_sale_per_kg,
            "baseline_utilization_pct": baseline_utilization_pct,
            "optimized_utilization_pct": optimized_utilization_pct,
            "software_monthly_fee_inr": software_monthly_fee_inr,
            "status": "ASSUMPTIONS (Editable by workshop owner)"
        },
        "results": {
            "net_scrap_loss_per_kg_inr": round(net_scrap_loss_per_kg, 2),
            "baseline_scrap_tonnes_per_year": round(baseline_scrap_tonnes, 2),
            "optimized_scrap_tonnes_per_year": round(optimized_scrap_tonnes, 2),
            "annual_scrap_reduced_tonnes": round(scrap_saved_tonnes, 2),
            "gross_annual_savings_inr": round(gross_annual_savings_inr, 2),
            "annual_software_subscription_cost_inr": round(annual_software_cost_inr, 2),
            "net_annual_profit_inr": round(net_annual_profit_inr, 2),
            "roi_multiple": round(roi_multiple, 1),
            "payback_period_days": round(payback_days, 1)
        },
        "disclaimer": "Savings figures represent direct material yield improvements. Tool wear, electricity, and gas costs excluded."
    }

def calculate_remnant_plate_value(width_mm: float,
                                  height_mm: float,
                                  thickness_mm: float = 10.0,
                                  material_density_kg_m3: float = 7850.0,
                                  raw_plate_price_per_kg: float = 65.0,
                                  scrap_sale_price_per_kg: float = 32.0) -> Dict[str, Any]:
    """
    Computes the tangible economic inventory value of an intact prime remnant offcut.
    
    In structural steel fabrication:
    - If a remnant width is too narrow (< 100mm), it cannot be re-clamped on a CNC cutting table
      and is discarded into the scrap bin, recovering only scrap resale price.
    - If a remnant plate is wide (e.g. >= 100mm, like 434mm x 500mm), it constitutes prime virgin
      plate inventory that can be directly reused for subsequent cutting orders.
    - Net Value Preserved = (Plate Weight in kg) * (Raw Purchase Price - Scrap Resale Price).
    """
    is_prime = width_mm >= 100.0 and height_mm >= 100.0
    area_m2 = (width_mm / 1000.0) * (height_mm / 1000.0)
    volume_m3 = area_m2 * (thickness_mm / 1000.0)
    weight_kg = volume_m3 * material_density_kg_m3
    
    raw_material_value_inr = weight_kg * raw_plate_price_per_kg
    scrap_recovery_value_inr = weight_kg * scrap_sale_price_per_kg
    net_value_saved_inr = (raw_material_value_inr - scrap_recovery_value_inr) if is_prime else 0.0
    
    return {
        "dimensions_mm": f"{width_mm:.1f} x {height_mm:.1f} x {thickness_mm:.1f} mm",
        "plate_area_m2": round(area_m2, 4),
        "plate_weight_kg": round(weight_kg, 2),
        "is_prime_reusable_remnant": is_prime,
        "raw_plate_inventory_value_inr": round(raw_material_value_inr, 2),
        "scrap_recovery_value_inr": round(scrap_recovery_value_inr, 2),
        "net_value_saved_vs_scrap_inr": round(net_value_saved_inr, 2),
        "commercial_note": (
            "Prime plate saved for inventory reuse" if is_prime else 
            "Offcut strip too narrow for standard CNC re-fixturing; sold as scrap"
        )
    }

