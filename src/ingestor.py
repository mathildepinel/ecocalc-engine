import requests
import pandas as pd
from typing import List, Dict, Any

def fetch_nyc_data(limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetches LL84 benchmarking data from NYC Open Data.
    Dataset ID: 5zyy-y8am (2023 data)
    """
    url = "https://data.cityofnewyork.us/resource/5zyy-y8am.json"
    params = {
        "$limit": limit,
        "$order": "property_id",
        "$where": "property_gfa_self_reported IS NOT NULL" # Filter out empty GFA
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

if __name__ == "__main__":
    # Test run
    data = fetch_nyc_data(limit=5)
    print(f"Fetched {len(data)} records")
    if data:
        print(data[0].keys())
