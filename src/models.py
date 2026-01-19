from pydantic import BaseModel, Field, field_validator
from typing import Optional

class Building(BaseModel):
    """
    Represents a building with energy usage data.
    """
    building_id: str = Field(..., description="Unique identifier for the building")
    gross_sq_ft: float = Field(..., gt=0, description="Gross square footage of the building")
    annual_gas_usage_therms: float = Field(..., ge=0, description="Annual gas usage in therms")
    annual_elec_usage_kwh: float = Field(..., ge=0, description="Annual electricity usage in kWh")
    property_type: str = Field(..., description="Type of property (e.g., Office, Multifamily)")

    @field_validator('property_type')
    @classmethod
    def validate_property_type(cls, v: str) -> str:
        allowed_types = ["Office", "Multifamily", "Hotel", "Store", "Industrial"]
        if v not in allowed_types:
            raise ValueError(f"Property type must be one of {allowed_types}")
        return v
