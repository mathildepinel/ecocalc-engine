import streamlit as st
import plotly.graph_objects as go
from src.main import get_building_analysis
from fastapi import HTTPException


# --- Sidebar Parameters ---
st.sidebar.header("Analysis Parameters")
building_id = st.sidebar.text_input("Building ID", value="2658221", help="Enter NYC BBL or Property ID")
run_btn = st.sidebar.button("Run Analysis", type="primary")

# --- Main Content ---
st.title("⚡ Building Decarbonization Analysis")


if building_id:
    try:
        # Fetch Analysis
        with st.spinner(f"Analyzing Building {building_id}..."):
            # Using the direct function call to simulate API response
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
            st.metric("2024 Penalty (Est.)", f"${penalties.get(2024, 0):,.0f}", delta=-penalties.get(2024, 0), delta_color="normal")
        with col4:
            st.metric("2030 Penalty (Est.)", f"${penalties.get(2030, 0):,.0f}", delta=-penalties.get(2030, 0), delta_color="normal")

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
