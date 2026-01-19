import yaml
import numpy_financial as npf
from pathlib import Path
from src.models import Building
from src.engine.penalty import calculate_penalty, calculate_emissions

BASE_DIR = Path(__file__).parent.parent.parent
with open(BASE_DIR / "config" / "constants.yaml", "r") as f:
    AUTH_CONSTANTS = yaml.safe_load(f)

def calculate_roi(building: Building) -> dict:
    """
    Calculates ROI for full electrification retrofit (Gas Boiler -> Heat Pump).
    """
    # --- 1. Baseline Financials ---
    current_gas_cost = building.annual_gas_usage_therms * AUTH_CONSTANTS["GAS_COST_PER_THERM"]
    current_elec_cost = building.annual_elec_usage_kwh * AUTH_CONSTANTS["ELEC_COST_PER_KWH"]
    
    # Average annual penalty over next 15 years (Simplified)
    # Using 2024 rate for first 6 years, 2030 for remaining 9.
    penalty_2024 = calculate_penalty(building, 2024)
    penalty_2030 = calculate_penalty(building, 2030)
    avg_annual_penalty = ((penalty_2024 * 6) + (penalty_2030 * 9)) / 15
    
    baseline_opex = current_gas_cost + current_elec_cost + avg_annual_penalty

    # --- 2. Intervention: Electrification ---
    # Convert Gas Heating Load to Electric Heating Load
    # Heat Output needed (therm) = Input Gas (therm) * Boiler Eff
    heating_load_therms = building.annual_gas_usage_therms * AUTH_CONSTANTS["GAS_BOILER_EFFICIENCY"]
    # Convert to kWh: 1 therm = 29.3071 kWh
    heating_load_kwh_thermal = heating_load_therms * 29.3071
    
    # Elec Input needed = Output / COP
    new_heating_elec_kwh = heating_load_kwh_thermal / AUTH_CONSTANTS["HEAT_PUMP_COP"]
    
    # New Usage Profiles
    new_gas_usage = 0.0
    new_elec_usage = building.annual_elec_usage_kwh + new_heating_elec_kwh
    
    # Create "Post-Retrofit" Building Object for penalty calc
    retrofit_building = Building(
        building_id=f"{building.building_id}_retrofit",
        gross_sq_ft=building.gross_sq_ft,
        annual_gas_usage_therms=new_gas_usage,
        annual_elec_usage_kwh=new_elec_usage,
        property_type=building.property_type
    )

    # --- 3. New Financials ---
    new_gas_cost = 0.0
    new_elec_cost = new_elec_usage * AUTH_CONSTANTS["ELEC_COST_PER_KWH"]
    
    # New Penalties
    new_penalty_2024 = calculate_penalty(retrofit_building, 2024)
    new_penalty_2030 = calculate_penalty(retrofit_building, 2030)
    new_avg_penalty = ((new_penalty_2024 * 6) + (new_penalty_2030 * 9)) / 15
    
    new_opex = new_gas_cost + new_elec_cost + new_avg_penalty
    
    # --- 4. ROI Metrics ---
    annual_savings = baseline_opex - new_opex
    
    # Investment Cost
    investment_cost = building.gross_sq_ft * AUTH_CONSTANTS["RETROFIT_COST_PER_SQFT"]
    
    simple_payback = investment_cost / annual_savings if annual_savings > 0 else -1.0
    
    # NPV (15 years)
    # Cash flows: Year 0 = -Investment, Year 1-15 = Savings
    cash_flows = [-investment_cost] + [annual_savings] * 15
    npv = npf.npv(AUTH_CONSTANTS["DISCOUNT_RATE"], cash_flows)
    
    return {
        "baseline_opex": round(baseline_opex, 2),
        "new_opex": round(new_opex, 2),
        "annual_savings": round(annual_savings, 2),
        "investment_cost": round(investment_cost, 2),
        "simple_payback_years": round(simple_payback, 1),
        "npv": round(npv, 2),
        "baseline_penalty_avg": round(avg_annual_penalty, 2),
        "new_penalty_avg": round(new_avg_penalty, 2)
    }
