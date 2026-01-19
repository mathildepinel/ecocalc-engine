import pytest
from src.models import Building
from src.engine.penalty import calculate_penalty, calculate_emissions
from src.engine.roi import calculate_roi

# Mock Building: High Emissions (Old Boiler)
# 50,000 sqft Office
# Gas: 50,000 therms (High!)
# Elec: 500,000 kWh
@pytest.fixture
def dirty_building():
    return Building(
        building_id="dirty_1",
        gross_sq_ft=50000.0,
        annual_gas_usage_therms=50000.0,
        annual_elec_usage_kwh=500000.0,
        property_type="Office"
    )

@pytest.fixture
def clean_building():
    return Building(
        building_id="clean_1",
        gross_sq_ft=50000.0,
        annual_gas_usage_therms=5000.0, # Low gas
        annual_elec_usage_kwh=500000.0,
        property_type="Office"
    )

def test_calculate_emissions(dirty_building):
    # Gas: 50000 * 0.005311 = 265.55
    # Elec: 500000 * 0.000288962 = 144.481
    # Total: ~410.03
    emissions = calculate_emissions(dirty_building)
    assert emissions > 400
    assert emissions < 420

def test_calculate_penalty_2024(dirty_building):
    # Limit 2024 Office: 8.46 kg/sqft = 0.00846 t/sqft
    # Limit Total: 50000 * 0.00846 = 423 tCO2e
    # Emissions: ~410 tCO2e
    # Should be 0 penalty (Under limit)
    penalty = calculate_penalty(dirty_building, 2024)
    assert penalty == 0.0

def test_calculate_penalty_2030(dirty_building):
    # Limit 2030 Office: 4.53 kg/sqft = 0.00453 t/sqft
    # Limit Total: 50000 * 0.00453 = 226.5 tCO2e
    # Emissions: ~410 tCO2e
    # Excess: 410 - 226.5 = 183.5
    # Penalty: 183.5 * 268 = ~49,178
    penalty = calculate_penalty(dirty_building, 2030)
    assert penalty > 40000

def test_calculate_roi(dirty_building):
    roi = calculate_roi(dirty_building)
    
    # Expect positive savings because we avoid massive 2030 penalties
    # and gas is expensive.
    assert roi["annual_savings"] > 0
    assert roi["simple_payback_years"] > 0
    # NPV might be negative if retrofit cost is huge, but check it returns a number
    assert isinstance(roi["npv"], float)
