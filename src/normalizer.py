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
            val = record[key]
            # Handle "Not Available" or other strings
            if isinstance(val, str):
                if val.lower() in ["not available", "n/a", "nan", ""]:
                    continue
            try:
                return float(val)
            except (ValueError, TypeError):
                continue
    return default

# Maximum plausible site EUI (kBtu/ft²). NYC median office ~80, worst real buildings ~500.
# Records above this threshold are almost certainly estimated/aggregated campus data.
MAX_SITE_EUI_KBTU_FT2 = 5000.0

def normalize_building_data(raw_data: List[Dict[str, Any]]) -> List[Building]:
    """
    Normalizes raw NYC Open Data records into Building objects.
    Records with implausibly high site EUI (> 5,000 kBtu/ft²) are skipped as bad data.
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

            # --- Sanity filter: skip records with implausible site EUI ---
            site_eui_raw = record.get("site_eui_kbtu_ft")
            if site_eui_raw is not None and site_eui_raw != "Not Available":
                try:
                    site_eui = float(site_eui_raw)
                    if site_eui > MAX_SITE_EUI_KBTU_FT2:
                        logger.warning(
                            f"Skipping building {b_id}: site EUI {site_eui:.0f} kBtu/ft² "
                            f"exceeds sanity threshold of {MAX_SITE_EUI_KBTU_FT2:.0f}. "
                            "Likely estimated/aggregated campus data."
                        )
                        continue
                except (ValueError, TypeError):
                    pass  # If we can't parse EUI, proceed normally

            # Extract Energy
            # Note: 2023 data keys are often in kBtu
            
            # 1. Gas (Target: Therms)
            # Try specific kbtu field first, then generic therms
            gas_kbtu = get_value(record, ["natural_gas_use_kbtu"])
            if gas_kbtu > 0:
                gas_therms = gas_kbtu / 100.0 # 1 Therm = 100 kBtu
            else:
                gas_therms = get_value(record, ["natural_gas_use_therms"])

            # 2. Key for Electricity (Target: kWh)
            # Try specific kbtu field first
            elec_kbtu = get_value(record, ["electricity_use_grid_purchase_kbtu", "electricity_use_grid_purchase"])
            if elec_kbtu > 0:
                 # Note: "electricity_use_grid_purchase" in 2023 dataset often seems to be kBtu based on context with other kBtu fields
                 # 1 kWh = 3.41214 kBtu
                 elec_kwh = elec_kbtu / 3.41214
            else:
                 elec_kwh = get_value(record, ["electricity_use_grid_purchase_kwh", "electricity_use_generated_from_onsite_renewable_systems_kwh"])
            
            # Extract Type
            raw_type = record.get("primary_property_type_self_selected", "Office")
            prop_type = map_property_type(raw_type)

            # Extract Geo
            lat = get_value(record, ["latitude"])
            lon = get_value(record, ["longitude"])

            building = Building(
                building_id=b_id,
                gross_sq_ft=sqft,
                annual_gas_usage_therms=gas_therms,
                annual_elec_usage_kwh=elec_kwh,
                property_type=prop_type,
                latitude=lat if lat != 0 else None,
                longitude=lon if lon != 0 else None
            )
            buildings.append(building)
            
        except Exception as e:
            logger.warning(f"Failed to process building {record.get('property_id')}: {e}")
            continue
            
    return buildings
