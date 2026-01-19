from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app
from src.models import Building

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_analyze_building():
    # Payload matching Building model
    payload = {
        "building_id": "test_1",
        "gross_sq_ft": 50000.0,
        "annual_gas_usage_therms": 50000.0,
        "annual_elec_usage_kwh": 500000.0,
        "property_type": "Office"
    }
    
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["building_id"] == "test_1"
    assert "roi_analysis" in data
    assert "penalties" in data
    assert "explainability" in data
    assert len(data["explainability"]) > 0

@patch("src.main.requests.get")
def test_get_building_analysis_found(mock_get):
    # Mock NYC Open Data response
    mock_response = MagicMock()
    mock_response.json.return_value = [{
        "property_id": "12345",
        "property_gfa_self_reported": "10000",
        "natural_gas_use_therms": "5000",
        "electricity_use_grid_purchase_kwh": "20000",
        "primary_property_type_self_selected": "Office"
    }]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    response = client.get("/building/12345")
    assert response.status_code == 200
    data = response.json()
    assert data["building_id"] == "12345"
    assert data["roi_analysis"]["annual_savings"] != 0

@patch("src.main.requests.get")
def test_get_building_analysis_not_found(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    response = client.get("/building/99999")
    assert response.status_code == 404
