import requests
import json

def inspect():
    url = "https://data.cityofnewyork.us/resource/5zyy-y8am.json"
    params = {"$limit": 1}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            print("Keys found:", list(data[0].keys()))
            print("Sample record:", json.dumps(data[0], indent=2))
        else:
            print("No data returned.")
    except Exception as e:
        print(f"Error: {e}")
        print(response.text)

if __name__ == "__main__":
    inspect()
