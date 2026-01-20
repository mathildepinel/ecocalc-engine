import yaml
from pathlib import Path
from src.models import Building

# Load Limits
BASE_DIR = Path(__file__).parent.parent.parent
with open(BASE_DIR / "config" / "ll97_limits.yaml", "r") as f:
    LL97_LIMITS = yaml.safe_load(f)

with open(BASE_DIR / "config" / "constants.yaml", "r") as f:
    CONSTANTS = yaml.safe_load(f)

def calculate_emissions(building: Building) -> float:
    """
    Calculates total annual emissions in tCO2e.
    """
    gas_emissions = building.annual_gas_usage_therms * CONSTANTS["EMISSION_FACTOR_GAS_TCO2E_PER_THERM"]
    elec_emissions = building.annual_elec_usage_kwh * CONSTANTS["EMISSION_FACTOR_ELEC_TCO2E_PER_KWH"]
    return gas_emissions + elec_emissions

def calculate_penalty(building: Building, year: int) -> float:
    """
    Calculates estimated LL97 penalty for a given year.
    Returns 0.0 if under the limit.
    """
    # 1. Determine which period limits to use
    if year < 2024:
        return 0.0 # No penalties before 2024
    
    # Simple logic for periods
    period_key = 2024
    if year >= 2030:
        period_key = 2030
        
    limits = LL97_LIMITS.get(period_key, {})
    limit_factor = limits.get(building.property_type)
    
    if limit_factor is None:
        # Assume 0 penalty if unknown type.
        return 0.0

    # 2. Calculate Limit in tCO2e
    # Limit factor is in kgCO2e/sqft. Convert to tCO2e/sqft -> / 1000
    # Total Limit (tCO2e) = sqft * (kg/sqft / 1000)
    annual_limit_tco2e = building.gross_sq_ft * (limit_factor / 1000.0)

    # 3. Calculate Actual Emissions
    actual_emissions_tco2e = calculate_emissions(building)

    # 4. Calculate Penalty
    excess_emissions = max(0.0, actual_emissions_tco2e - annual_limit_tco2e)
    penalty = excess_emissions * CONSTANTS["PENALTY_RATE_PER_TON"]
    
    return round(penalty, 2)
