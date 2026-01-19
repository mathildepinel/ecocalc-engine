from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from src.models import Building
from src.ingestor import fetch_nyc_data
from src.normalizer import normalize_building_data
from src.engine.roi import calculate_roi
from src.engine.penalty import calculate_penalty
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EcoCalc Engine API",
    description="API for calculating decarbonization ROI and LL97 penalties for NYC buildings.",
    version="1.0.0"
)

class AnalysisResult(BaseModel):
    building_id: str
    roi_analysis: Dict[str, float]
    penalties: Dict[int, float]
    explainability: List[str]

@app.get("/")
def read_root():
    return {"message": "Welcome to EcoCalc Engine API. Use /docs for documentation."}

@app.post("/analyze", response_model=AnalysisResult)
def analyze_building(building: Building):
    """
    Analyzes a building object provided in the request body.
    Returns ROI analysis, penalties, and an explainability trace.
    """
    try:
        # 1. Calculate ROI
        roi_result = calculate_roi(building)
        
        # 2. Calculate Penalties explicitly for reporting
        penalty_2024 = calculate_penalty(building, 2024)
        penalty_2030 = calculate_penalty(building, 2030)
        
        # 3. Generate Explainability Trace
        trace = []
        trace.append(f"Analyzed Building {building.building_id} ({building.property_type}).")
        trace.append(f"Gross SQFT: {building.gross_sq_ft:,.0f}. Annual Gas: {building.annual_gas_usage_therms:,.0f} therms.")
        
        if penalty_2024 > 0:
            trace.append(f"ALERT: Est. 2024 Penalty is ${penalty_2024:,.2f}/year.")
        else:
            trace.append("Pass: Building is under 2024 LL97 emissions limits.")
            
        if penalty_2030 > 0:
            trace.append(f"WARNING: Est. 2030 Penalty increases to ${penalty_2030:,.2f}/year.")
            
        if roi_result['annual_savings'] > 0:
            trace.append(f"OPPORTUNITY: Electrification could save ${roi_result['annual_savings']:,.2f}/year with {roi_result['simple_payback_years']} year payback.")
        else:
            trace.append("Note: Electrification may not have immediate positive ROI based on current assumptions.")

        return AnalysisResult(
            building_id=building.building_id,
            roi_analysis=roi_result,
            penalties={2024: penalty_2024, 2030: penalty_2030},
            explainability=trace
        )
        
    except Exception as e:
        logger.error(f"Error analyzing building: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/building/{property_id}", response_model=AnalysisResult)
def get_building_analysis(property_id: str):
    """
    Fetches data for a specific building ID from NYC Open Data and analyzes it.
    Note: In a real app, this would be cached or optimized. Currently scans dataset.
    """
    try:
        # 1. Fetch Data (Inefficient linear scan for demo - ideally filter API side via ingestor params)
        # We will attempt to fetch with a filter if ingestor supported it, but our ingestor is simple.
        # Let's fetch a chunk and look for it, or just fail if not found in top N.
        # Ideally, update ingestor to accept a property_id filter.
        # For now, let's just fetch a small batch and see if we get lucky, or better yet,
        # update the logic to fetch *specifically* this ID.
        
        # HACK: Using a specialized fetch logic here or updating ingestor.
        # Let's rely on a new function we'll monkey-patch or add to ingestor? 
        # Actually, let's just use the ingestor as is but maybe we should've added filtering.
        # Let's try to filter using the generic fetch but requesting a specific ID via SODA if possible.
        # Socrata supports ?property_id=...
        
        url = "https://data.cityofnewyork.us/resource/5zyy-y8am.json"
        
        resp = requests.get(url, params={"property_id": property_id, "$limit": 1})
        resp.raise_for_status()
        data = resp.json()
        
        if not data:
            raise HTTPException(status_code=404, detail=f"Building {property_id} not found in NYC Open Data (2023).")
            
        # 2. Normalize
        buildings = normalize_building_data(data)
        if not buildings:
             raise HTTPException(status_code=400, detail="Could not normalize building data (missing GFA or Energy data).")
             
        # 3. Analyze
        return analyze_building(buildings[0])

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching/analyzing building {property_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
