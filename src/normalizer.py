from typing import List, Dict, Any, Optional
from src.models import Building
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def map_property_type(raw_type: str) -> str:
    """
    Maps NYC raw property types to LL97 limits categories.
    """
    raw_type = raw_type.lower()
    if "office" in raw_type or "bank" in raw_type or "financial" in raw_type:
        return "Office"
    elif "multifamily" in raw_type or "residential" in raw_type or "dormitory" in raw_type:
        return "Multifamily"
    elif "hotel" in raw_type:
        return "Hotel"
    elif "retail" in raw_type or "store" in raw_type or "mall" in raw_type or "supermarket" in raw_type:
        return "Store"
    elif "warehouse" in raw_type or "distribution" in raw_type or "manufacturing" in raw_type:
        return "Industrial"
    else:
        # Default fallback or could return "Other" if model supported it
        # For now, mapping to Office as a safe default or raising warning
        # logger.warning(f"Unmapped property type: {raw_type}. Defaulting to Office.")
        return "Office"

def get_value(record: Dict[str, Any], keys: List[str], default: float = 0.0) -> float:
    """Helper to get float value from multiple potential keys."""
    for key in keys:
        if key in record and record[key] is not None:
            try:
                return float(record[key])
            except (ValueError, TypeError):
                continue
    return default

def normalize_building_data(raw_data: List[Dict[str, Any]]) -> List[Building]:
    """
    Normalizes raw NYC Open Data records into Building objects.
    """
    buildings = []
    
    for record in raw_data:
        try:
            # Extract basic info
            b_id = record.get("property_id", "Unknown")
            
            # Extract SQFT
            sqft = get_value(record, ["property_gfa_self_reported", "gross_floor_area_ft"])
            if sqft <= 0:
                continue

            # Extract Energy
            # Note: 2023 data usually has these fields.
            gas_therms = get_value(record, ["natural_gas_use_therms"])
            elec_kwh = get_value(record, ["electricity_use_grid_purchase_kwh", "electricity_use_generated_from_onsite_renewable_systems_kwh"])
            
            # Extract Type
            raw_type = record.get("primary_property_type_self_selected", "Office")
            prop_type = map_property_type(raw_type)

            building = Building(
                building_id=b_id,
                gross_sq_ft=sqft,
                annual_gas_usage_therms=gas_therms,
                annual_elec_usage_kwh=elec_kwh,
                property_type=prop_type
            )
            buildings.append(building)
            
        except Exception as e:
            logger.warning(f"Failed to process building {record.get('property_id')}: {e}")
            continue
            
    return buildings
