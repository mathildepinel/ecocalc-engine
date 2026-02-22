import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
from src.ingestor import fetch_nyc_data
from src.normalizer import normalize_building_data
from src.engine.penalty import calculate_penalty


# --- Sidebar Parameters ---
st.sidebar.header("Map Parameters")
selected_year = st.sidebar.radio("Select Year", [2024, 2030], horizontal=True)
sample_size = st.sidebar.slider("Sample Size", min_value=100, max_value=10000, value=500, step=100)
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
                        "property_type": b.property_type,
                    })

        st.session_state.map_data = pd.DataFrame(results)

if st.session_state.map_data is not None and not st.session_state.map_data.empty:
    df = st.session_state.map_data.copy()

    st.success(f"Found {len(df)} buildings with penalties out of {sample_size} scanned.")

    # --- Discrete color buckets by penalty bracket ---
    # White < $10k | Yellow < $100k | Orange < $1M | Red < $10M | Deep Red >= $10M
    def penalty_color(p):
        if p < 10_000:
            return [255, 255, 255, 200]   # White
        elif p < 100_000:
            return [255, 220, 0,   220]   # Yellow
        elif p < 1_000_000:
            return [255, 120, 0,   220]   # Orange
        elif p < 10_000_000:
            return [220, 0,   0,   230]   # Red
        else:
            return [120, 0,   0,   240]   # Deep Red

    colors = df["penalty"].apply(penalty_color)
    df["r"] = colors.apply(lambda c: c[0])
    df["g"] = colors.apply(lambda c: c[1])
    df["b"] = colors.apply(lambda c: c[2])
    df["a"] = colors.apply(lambda c: c[3])

    # Pre-format penalty as string for tooltip (pydeck doesn't support Python format specs)
    df["penalty_display"] = df["penalty"].apply(lambda x: f"${x:,.0f}")

    layer = pdk.Layer(
        "ScatterplotLayer",
        df,
        get_position="[lon, lat]",
        get_color="[r, g, b, a]",
        get_radius=60,           # Fixed radius in meters (uniform bubbles)
        radius_min_pixels=4,
        radius_max_pixels=14,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=40.7128,
        longitude=-74.0060,
        zoom=11,
        pitch=0,
    )

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v9",
        initial_view_state=view_state,
        layers=[layer],
        tooltip={"text": "Building ID: {building_id}\nType: {property_type}\nPenalty: {penalty_display}"},
    ))

    st.dataframe(
        df[["building_id", "property_type", "penalty"]]
        .sort_values("penalty", ascending=False)
        .rename(columns={"building_id": "Building ID", "property_type": "Type", "penalty": "Penalty ($)"})
        .style.format({"Penalty ($)": "${:,.0f}"}),
        use_container_width=True,
    )

elif st.session_state.map_data is not None:
    st.warning("No penalties found in this batch (or missing location data). Try increasing sample size.")
