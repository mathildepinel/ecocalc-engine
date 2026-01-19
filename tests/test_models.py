import pytest
from pydantic import ValidationError
from src.models import Building

def test_valid_building():
    """Test creating a valid building instance."""
    building = Building(
        building_id="123",
        gross_sq_ft=10000.0,
        annual_gas_usage_therms=5000.0,
        annual_elec_usage_kwh=20000.0,
        property_type="Office"
    )
    assert building.building_id == "123"
    assert building.gross_sq_ft == 10000.0
    assert building.property_type == "Office"

def test_invalid_sq_ft():
    """Test that negative square footage raises an error."""
    with pytest.raises(ValidationError):
        Building(
            building_id="123",
            gross_sq_ft=-100.0,
            annual_gas_usage_therms=5000.0,
            annual_elec_usage_kwh=20000.0,
            property_type="Office"
        )

def test_invalid_property_type():
    """Test that an invalid property type raises an error."""
    with pytest.raises(ValidationError):
        Building(
            building_id="123",
            gross_sq_ft=10000.0,
            annual_gas_usage_therms=5000.0,
            annual_elec_usage_kwh=20000.0,
            property_type="InvalidType"
        )
