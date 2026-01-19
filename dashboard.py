import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.graph_objects as go
from src.main import get_building_analysis
from src.ingestor import fetch_nyc_data
from src.normalizer import normalize_building_data
from src.engine.penalty import calculate_penalty
from fastapi import HTTPException

# Layout Configuration
st.set_page_config(
    page_title="EcoCalc Engine Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for "Premium" feel
st.markdown("""
    <style>
    .metric-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #4F5056;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ EcoCalc Engine: Decarbonization ROI")

# Sidebar for Navigation
with st.sidebar:
    st.header("EcoCalc Engine")
    page = st.radio("Navigation", ["Single Building Analysis", "Citywide Penalty Heatmap"])

    st.divider()

    if page == "Single Building Analysis":
        st.header("Analysis Parameters")
        building_id = st.text_input("Building ID", value="2658221", help="Enter NYC BBL or Property ID")
        run_btn = st.button("Run Analysis", type="primary")
    else:
        st.header("Map Parameters")
        sample_size = st.slider("Sample Size", min_value=100, max_value=2000, value=500, step=100)
        fetch_btn = st.button("Fetch & Map Data", type="primary")

# --- Page 1: Single Building Analysis ---
if page == "Single Building Analysis":
    st.title("⚡ Building Decarbonization Analysis")
    if building_id:
        try:
            # Fetch Analysis
            with st.spinner(f"Analyzing Building {building_id}..."):
                # Using the direct function call to simulate API response
                # In a real deployed app, this would be requests.get(API_URL)
                result = get_building_analysis(building_id)
                
                # Convert to dict if needed
                if hasattr(result, "model_dump"):
                    data = result.model_dump()
                else:
                    data = dict(result)

            # --- Dashboard Layout ---
            
            # 1. Header Metrics
            st.subheader(f"Building {data['building_id']}")
            
            # Extract easy access variables
            roi = data['roi_analysis']
            penalties = data['penalties']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Annual Savings", f"${roi['annual_savings']:,.0f}")
            with col2:
                st.metric("Simple Payback", f"{roi['simple_payback_years']} Years")
            with col3:
                st.metric("2024 Penalty (Est.)", f"${penalties.get(2024, 0):,.0f}", delta=-penalties.get(2024, 0), delta_color="inverse")
            with col4:
                st.metric("2030 Penalty (Est.)", f"${penalties.get(2030, 0):,.0f}", delta=-penalties.get(2030, 0), delta_color="inverse")

            st.divider()

            # 2. Visualization Row
            col_charts, col_details = st.columns([2, 1])

            with col_charts:
                st.markdown("### Penalty Trajectory")
                
                # Penalty Chart
                years = list(penalties.keys())
                amounts = list(penalties.values())
                
                fig = go.Figure(data=[
                    go.Bar(name='LL97 Penalty', x=years, y=amounts, marker_color='#ff4b4b')
                ])
                fig.update_layout(
                    title="Projected LL97 Fines (Annual)",
                    xaxis_title="Year",
                    yaxis_title="Penalty ($)",
                    template="plotly_dark",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_details:
                st.markdown("### Investment Stats")
                st.write(f"**Total Investment:** ${roi['investment_cost']:,.2f}")
                # st.write(f"**Annual Energy Savings:** {roi['energy_savings_mmbtu']:,.0f} MMBtu") # Not returned by API yet
                # Placeholder for more detailed stats if available in the future
                
                st.info("ROI calculation assumes full electrification of heating systems based on current utility rates.")

            # 3. Explainability Trace
            st.markdown("### 🔎 Engine Explainability Trace")
            trace_text = "\n".join([f"• {step}" for step in data['explainability']])
            st.text_area("Live Analysis Log", value=trace_text, height=200)

        except HTTPException as e:
            st.error(f"API Error: {e.detail}")
        except Exception as e:
            st.error(f"Unexpected Error: {e}")
    else:
        st.info("Please enter a Building ID to start.")

# --- Page 2: Citywide Heatmap ---
elif page == "Citywide Penalty Heatmap":
    st.title("🗺️ Citywide Penalty Heatmap (2024 Est.)")
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
                    p_2024 = calculate_penalty(b, 2024)
                    if p_2024 > 0:
                         results.append({
                            "building_id": b.building_id,
                            "lat": b.latitude,
                            "lon": b.longitude,
                            "penalty": p_2024,
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
