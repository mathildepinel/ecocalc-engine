import streamlit as st
from app_pages import single_building_analysis, city_wide_heatmap

# # Layout Configuration
# st.set_page_config(
#     page_title="EcoCalc Engine Dashboard",
#     page_icon="⚡",
#     layout="wide"
# )

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

single_building = st.Page(
    "app_pages/single_building_analysis.py",
    title="Single Building Analysis"
)

city_wide = st.Page(
    "app_pages/city_wide_heatmap.py",
    title="Citywide Penalty Heatmap"
)

# Navigation Logic
pg = st.navigation({
    "Navigation": [single_building, city_wide]
})

pg.run()
