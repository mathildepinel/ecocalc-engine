import streamlit as st
import pandas as pd
import pydeck as pdk
from src.ingestor import fetch_nyc_data
from src.normalizer import normalize_building_data
from src.engine.penalty import calculate_penalty


# --- Sidebar Parameters ---
st.sidebar.header("Map Parameters")
selected_year = st.sidebar.radio("Select Year", [2024, 2030], horizontal=True)
sample_size = st.sidebar.slider("Sample Size", min_value=100, max_value=2000, value=500, step=100)
fetch_btn = st.sidebar.button("Fetch & Map Data", type="primary")

# --- Main Content ---
st.title(f"🗺️ Citywide Penalty Heatmap ({selected_year} Est.)")
st.markdown("Visualizing buildings with projected Local Law 97 penalties.")

if 'map_data' not in st.session_state:
    st.session_state.map_data = None

if fetch_btn:
    with st.spinner(f"Fetching {sample_size} records from NYC Open Data..."):
        raw_data = fetch_nyc_data(limit=sample_size)
        buildings = normalize_building_data(raw_data)
        
        results = []
        for b in buildings:
            if b.latitude and b.longitude:
                penalty_val = calculate_penalty(b, selected_year)
                if penalty_val > 0:
                        results.append({
                        "building_id": b.building_id,
                        "lat": b.latitude,
                        "lon": b.longitude,
                        "penalty": penalty_val,
                        "address": b.property_type # Using type as proxy for name/address for now
                    })
        
        st.session_state.map_data = pd.DataFrame(results)

if st.session_state.map_data is not None and not st.session_state.map_data.empty:
    df = st.session_state.map_data
    
    st.success(f"Found {len(df)} buildings with penalties out of {sample_size} scanned.")
    
    # PyDeck Scatterplot Layer (Bubbles)
    layer = pdk.Layer(
        "ScatterplotLayer",
        df,
        get_position='[lon, lat]',
        get_color='[255, 75, 75, 160]',
        get_radius='penalty',
        radius_scale=0.05,
        radius_min_pixels=5,
        radius_max_pixels=50,
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=40.7128,
        longitude=-74.0060,
        zoom=11,
        pitch=0
    )

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v9',
        initial_view_state=view_state,
        layers=[layer],
        tooltip={"text": "ID: {building_id}\nType: {address}\nPenalty: ${penalty:,.0f}"}
    ))
    
    st.dataframe(df.sort_values("penalty", ascending=False).head(10), use_container_width=True)
    
elif st.session_state.map_data is not None:
    st.warning("No penalties found in this batch (or missing location data). Try increasing sample size.")
