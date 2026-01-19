import sys
import json
from src.main import get_building_analysis
from fastapi import HTTPException

def run_demo(building_id: str):
    print(f"--- Running Analysis for Building ID: {building_id} ---")
    try:
        # Call the logic directly
        result = get_building_analysis(building_id)
        
        # Parse result to dict if it's a Pydantic model (FastAPI returns models)
        if hasattr(result, "model_dump"):
            data = result.model_dump()
        else:
            data = dict(result)

        print("\n[SUCCESS]")
        print(json.dumps(data, indent=2))
        
        print("\n--- Explainability Trace ---")
        for step in data.get("explainability", []):
            print(f"> {step}")

    except HTTPException as e:
        print(f"\n[ERROR] API Error {e.status_code}: {e.detail}")
    except Exception as e:
        print(f"\n[ERROR] Unexpected Error: {e}")

if __name__ == "__main__":
    # Default ID if none provided
    # 2658221 is a valid ID from the dataset (Empire State Building or similar large building often in these datasets)
    # Actually, let's use a random valid ID or the one from the test? 
    # In test_api.py we mocked it. In real life we need a valid ID.
    # I'll default to one, but allow arg.
    
    target_id = sys.argv[1] if len(sys.argv) > 1 else "2658221"
    run_demo(target_id)
