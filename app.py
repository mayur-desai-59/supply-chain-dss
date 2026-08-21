import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from optimizer import run_supply_chain_optimization

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive Supply Chain DSS | Indian Wearables",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title Header
st.title("🛡️ Executive Supply Chain Network & Scenario Planning Engine")
st.caption("Strategic Decision Support System (DSS) for Indian Electronics Manufacturing | Tariff Shocks, Disruption Resilience & PLI Trade-offs")

st.markdown("---")

# ---------------------------------------------------------
# SIDEBAR: DATA INPUT, TEMPLATES & POLICY CONTROLS
# ---------------------------------------------------------
st.sidebar.header("📁 1. Data Source & Templates")

# How to format CSVs & Downloadable Templates
with st.sidebar.expander("ℹ️ How to format custom CSVs"):
    st.markdown("""
    **Required Columns per CSV:**
    * **Suppliers:** `supplier_id`, `supplier_name`, `location`, `unit_prod_cost_inr`, `monthly_capacity`, `fixed_contract_cost_inr`, `geo_risk_score`
    * **Lanes:** `supplier_id`, `destination_hub`, `freight_cost_inr`, `bcd_tariff_pct`, `lead_time_days`
    * **Demand:** `destination_hub`, `monthly_demand_units`
    """)
    st.markdown("**Download Baseline Templates:**")
    try:
        st.download_button("📥 Suppliers Template", data=pd.read_csv('suppliers_india.csv').to_csv(index=False), file_name="template_suppliers.csv", mime="text/csv")
        st.download_button("📥 Lanes Template", data=pd.read_csv('lanes_india.csv').to_csv(index=False), file_name="template_lanes.csv", mime="text/csv")
        st.download_button("📥 Demand Template", data=pd.read_csv('demand_india.csv').to_csv(index=False), file_name="template_demand.csv", mime="text/csv")
    except Exception:
        st.caption("Run generate_data.py to enable template downloads locally.")

data_mode = st.sidebar.radio("Select Input Mode:", ["Use Baseline Indian Case Data", "Upload Custom CSV Files"])

if data_mode == "Upload Custom CSV Files":
    sup_file = st.sidebar.file_uploader("Upload Suppliers CSV", type=['csv'])
    lanes_file = st.sidebar.file_uploader("Upload Lanes CSV", type=['csv'])
    dem_file = st.sidebar.file_uploader("Upload Demand CSV", type=['csv'])
    
    if sup_file and lanes_file and dem_file:
        suppliers_df = pd.read_csv(sup_file)
        lanes_df = pd.read_csv(lanes_file)
        demand_df = pd.read_csv(dem_file)
        st.sidebar.success("Custom datasets loaded successfully!")
    else:
        st.sidebar.warning("Upload all 3 CSVs to execute custom analysis. Falling back to baseline Indian case data.")
        suppliers_df = pd.read_csv('suppliers_india.csv')
        lanes_df = pd.read_csv('lanes_india.csv')
        demand_df = pd.read_csv('demand_india.csv')
else:
    suppliers_df = pd.read_csv('suppliers_india.csv')
    lanes_df = pd.read_csv('lanes_india.csv')
    demand_df = pd.read_csv('demand_india.csv')

st.sidebar.markdown("---")
st.sidebar.header("⚠️ 2. Risk & Policy Stress Testing")

# Scenario Planning Controls
tariff_shock = st.sidebar.slider(
    "Basic Customs Duty (BCD) Tariff Hike (+%)", 
    min_value=0, max_value=30, value=0, step=5, 
    help="Simulate an import duty shock on foreign components."
)

disruption_hub = st.sidebar.selectbox(
    "Simulate Regional Disruption / Port Closure", 
    ["None", "Shenzhen_China", "JNPT_Ocean_Hub", "Hai_Phong_Vietnam"],
    help="Shuts down specific sourcing nodes to test supply resilience."
)

max_risk_cap = st.sidebar.slider(
    "Geopolitical Risk Ceiling (1-10)", 
    min_value=1.0, max_value=10.0, value=6.0, step=0.5,
    help="Force re-routing away from high geopolitical risk zones."
)

max_china_share = st.sidebar.slider(
    "Max Sourcing Dependency on China (%)", 
    min_value=0, max_value=100, value=100, step=10,
    help="Set strategic limits on single-country reliance."
) / 100.0

# ---------------------------------------------------------
# DYNAMIC STRESS-TEST ADJUSTMENTS
# ---------------------------------------------------------
lanes_modified = lanes_df.copy()
suppliers_modified = suppliers_df.copy()

if tariff_shock > 0:
    overseas_mask = lanes_modified['bcd_tariff_pct'] > 0
    lanes_modified.loc[overseas_mask, 'bcd_tariff_pct'] += (tariff_shock / 100.0)

if disruption_hub != "None":
    if "China" in disruption_hub:
        suppliers_modified.loc[suppliers_modified['location'].str.contains('China'), 'monthly_capacity'] = 0
    elif "Vietnam" in disruption_hub:
        suppliers_modified.loc[suppliers_modified['location'].str.contains('Vietnam'), 'monthly_capacity'] = 0

# ---------------------------------------------------------
# RUN OPTIMIZATION (BASELINE VS. STRESSED SCENARIO)
# ---------------------------------------------------------
base_status, base_cost, base_res = run_supply_chain_optimization(suppliers_df, lanes_df, demand_df, max_risk_cap=10.0, max_china_share=1.0)
stress_status, stress_cost, stress_res = run_supply_chain_optimization(suppliers_modified, lanes_modified, demand_df, max_risk_cap=max_risk_cap, max_china_share=max_china_share)

if stress_status != 'Optimal':
    st.error("❌ CRITICAL NETWORK FAILURE: The applied disruption parameters or risk constraints make it mathematically impossible to satisfy total regional demand. Please ease the constraints or re-activate key supply hubs.")
else:
    # ---------------------------------------------------------
    # EXECUTIVE KPI DASHBOARD
    # ---------------------------------------------------------
    cost_delta = stress_cost - base_cost
    pct_delta = (cost_delta / base_cost) * 100 if base_cost else 0
    
    base_avg_lt = (base_res['Units Shipped'] * base_res['Lead Time (Days)']).sum() / base_res['Units Shipped'].sum()
    stress_avg_lt = (stress_res['Units Shipped'] * stress_res['Lead Time (Days)']).sum() / stress_res['Units Shipped'].sum()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Stressed Network Spend", f"₹{stress_cost:,.2f}", delta=f"{pct_delta:+.2f}% vs Baseline", delta_color="inverse")
    kpi2.metric("Financial Delta (Impact)", f"₹{cost_delta:,.2f}", delta="Cost Variance", delta_color="off")
    kpi3.metric("Avg Lead Time", f"{stress_avg_lt:.1f} Days", delta=f"{stress_avg_lt - base_avg_lt:+.1f} Days", delta_color="inverse")
    kpi4.metric("Geo Risk Profile Score", f"{(stress_res['Units Shipped'] * stress_res['Geo Risk Score']).sum() / stress_res['Units Shipped'].sum():.2f} / 10")

    st.markdown("---")

    # ---------------------------------------------------------
    # ANALYTICS DASHBOARD TABS
    # ---------------------------------------------------------
    tab1, tab2, tab3 = st.tabs(["📊 Executive Trade-off Analysis", "🚚 Sourcing Strategy & Allocation", "📑 Data Management & Export"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Cost Structure Impact Breakdown (₹)")
            comp_df = pd.DataFrame({
                'Scenario': ['Baseline', 'Stressed Scenario'],
                'Base Production': [base_res['Base Cost (₹)'].sum(), stress_res['Base Cost (₹)'].sum()],
                'Freight Costs': [base_res['Freight (₹)'].sum(), stress_res['Freight (₹)'].sum()],
                'Customs Tariff (BCD)': [base_res['Tariff BCD (₹)'].sum(), stress_res['Tariff BCD (₹)'].sum()]
            })
            fig_comp = px.bar(
                comp_df, 
                x='Scenario', 
                y=['Base Production', 'Freight Costs', 'Customs Tariff (BCD)'], 
                title="Financial Driver Comparison", 
                barmode='stack'
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        with c2:
            st.subheader("Geopolitical Volume Allocation")
            fig_pie = px.pie(
                stress_res, 
                names='Location', 
                values='Units Shipped', 
                hole=0.4, 
                title="Active Sourcing Volume Share"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.subheader("Optimal Routing Schedule per Demand Hub")
        fig_routes = px.bar(
            stress_res, 
            x='Destination Hub', 
            y='Units Shipped', 
            color='Supplier Name', 
            title="Volume Allocation per Hub (Units)",
            text_auto=True
        )
        st.plotly_chart(fig_routes, use_container_width=True)

    with tab3:
        st.subheader("Data Inspector & Allocation Export")
        display_cols = [
            'Supplier Name', 'Location', 'Destination Hub', 'Mode', 
            'Units Shipped', 'Base Cost (₹)', 'Freight (₹)', 'Tariff BCD (₹)', 
            'Landed Cost/Unit (₹)', 'Total Spend (₹)', 'Lead Time (Days)'
        ]
        st.dataframe(stress_res[display_cols].sort_values(by='Units Shipped', ascending=False), use_container_width=True)
        
        # Download Executable CSV Plan
        csv_data = stress_res[display_cols].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Executive Sourcing Plan (CSV)",
            data=csv_data,
            file_name="executive_sourcing_plan.csv",
            mime="text/csv"
        )