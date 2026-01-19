import pytest
import requests
from unittest.mock import patch, MagicMock
from src.ingestor import fetch_nyc_data
from src.normalizer import normalize_building_data
from src.models import Building

# --- Ingestor Tests ---
@patch("src.ingestor.requests.get")
def test_fetch_nyc_data_success(mock_get):
    """Test successful data fetch."""
    mock_response = MagicMock()
    mock_response.json.return_value = [{"property_id": "123", "some_field": "value"}]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = fetch_nyc_data(limit=10)
    assert len(data) == 1
    assert data[0]["property_id"] == "123"
    mock_get.assert_called_once()

@patch("src.ingestor.requests.get")
def test_fetch_nyc_data_failure(mock_get):
    """Test data fetch failure handled gracefully."""
    mock_get.side_effect = requests.RequestException("API Error")
    data = fetch_nyc_data()
    assert data == []

# --- Normalizer Tests ---
def test_normalize_valid_data():
    """Test normalization of valid raw data."""
    raw_data = [{
        "property_id": "1001",
        "property_gfa_self_reported": "50000",
        "natural_gas_use_therms": "1000",
        "electricity_use_grid_purchase_kwh": "20000",
        "primary_property_type_self_selected": "Multifamily Housing"
    }]
    
    buildings = normalize_building_data(raw_data)
    assert len(buildings) == 1
    b = buildings[0]
    assert b.building_id == "1001"
    assert b.gross_sq_ft == 50000.0
    assert b.annual_gas_usage_therms == 1000.0
    assert b.annual_elec_usage_kwh == 20000.0
    assert b.property_type == "Multifamily"

def test_normalize_missing_sqft():
    """Test that records with missing/zero SQFT are skipped."""
    raw_data = [{
        "property_id": "1002",
        "property_gfa_self_reported": "0",  # Invalid
        "primary_property_type_self_selected": "Office"
    }]
    buildings = normalize_building_data(raw_data)
    assert len(buildings) == 0

def test_normalize_mapping():
    """Test property type mapping logic."""
    raw_data = [
        {"property_id": "1", "property_gfa_self_reported": "100", "primary_property_type_self_selected": "Supermarket/Grocery Store"},
        {"property_id": "2", "property_gfa_self_reported": "100", "primary_property_type_self_selected": "Distribution Center"},
    ]
    buildings = normalize_building_data(raw_data)
    assert buildings[0].property_type == "Store"
    assert buildings[1].property_type == "Industrial"
