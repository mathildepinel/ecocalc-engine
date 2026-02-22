# EcoCalc-Engine: A Scalable Decarbonization ROI Logic Layer

> **Note**: I built this to demonstrate how to translate complex regulatory frameworks (like NYC Local Law 97) into a defensible, testable calculation service for decarbonization software.

## The Problem
Real estate owners in NYC face massive fines starting in 2024 under Local Law 97 (LL97) if their buildings exceed carbon emission limits. However, determining the financial viability (ROI) of interventions—like swapping gas boilers for heat pumps—requires navigating complex datasets, regulatory caps, and shifting energy prices.

## The Solution
**EcoCalc-Engine** is a Python-based backend service that helps decision-makers by:
1.  **Ingesting** "messy" real-world benchmarking data (NYC Open Data).
2.  **Normalizing** it into a standardized schema.
3.  **Calculating** precise carbon penalties and electrification ROI.
4.  **Explaining** the math with a "Reasoning Trace" API.

## Architecture

Data Flow:
`NYC Open Data (API)` -> **Ingestor** -> **Normalizer** -> `Building Model` -> **Calculation Engine** -> `FastAPI` -> **JSON Report**

### Key Components
-   **Normalization Layer**: Converts raw utility data into clean Pydantic models.
-   **Carbon Penalty Engine**: Calculates fines based on building type and year (2024 vs. 2030 limits).
-   **ROI Engine**: Models the Net Present Value (NPV) of electrification, accounting for avoided fines.
-   **Explainability Module**: Returns a human-readable log of *why* a number was calculated.

## Quick Start

### Prerequisites
-   Python 3.9+
-   `pip`

### Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/ecocalc-engine.git
    cd ecocalc-engine
    ```
2.  Create a virtual environment:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Usage
Start the API server:
```bash
uvicorn src.main:app --reload
```

**Analyze a Building (by ID):**
Visit `http://127.0.0.1:8000/docs` and use the Swagger UI to try `GET /building/{property_id}`.
*Try ID `2658221` (Example ID).*

**Run Custom Analysis:**
```bash
curl -X POST "http://127.0.0.1:8000/analyze" -H "Content-Type: application/json" -d '{
  "building_id": "demo-1",
  "gross_sq_ft": 50000,
  "annual_gas_usage_therms": 20000,
  "annual_elec_usage_kwh": 500000,
  "property_type": "Office"
}'
```

## Testing
Run the full test suite to verify the "decision-grade" logic:
```bash
pytest
```

## Features
-   **Canoncial Logic**: Rules (LL97 limits) are separated from Code (Calculation Engine) via YAML configuration.
-   **Defensibility**: Unit tests cover edge cases (e.g., negative savings, infinite payback).
-   **Data Integrity**: Pydantic models ensure no "garbage in, garbage out."
