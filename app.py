import streamlit as st
import pandas as pd
import plotly.express as px
from optimizer import run_supply_chain_optimization

st.set_page_config(page_title="Executive Supply Chain DSS | Indian Wearables", layout="wide")

st.title("🛡️ Executive Supply Chain Network & Scenario Planning Engine")
st.caption("Strategic Decision Support System (DSS) for Indian Electronics Manufacturing | PLI Incentives, Tariff Shocks & Localization Trade-offs")
st.markdown("---")

# --- SIDEBAR ---
st.sidebar.header("📁 1. Data Source & Templates")

with st.sidebar.expander("ℹ️ How to format custom CSVs"):
    st.markdown("""
    **Required Columns:**
    * **Suppliers:** `supplier_id`, `supplier_name`, `location`, `supplier_type`, `unit_prod_cost_inr`, `monthly_capacity`, `fixed_contract_cost_inr`, `geo_risk_score`
    * **Lanes:** `supplier_id`, `destination_hub`, `freight_cost_inr`, `bcd_tariff_pct`, `lead_time_days`
    * **Demand:** `destination_hub`, `monthly_demand_units`
    """)

data_mode = st.sidebar.radio("Select Input Mode:", ["Use Baseline Indian Case Data", "Upload Custom CSV Files"])

if data_mode == "Upload Custom CSV Files":
    sup_file = st.sidebar.file_uploader("Upload Suppliers CSV", type=['csv'])
    lanes_file = st.sidebar.file_uploader("Upload Lanes CSV", type=['csv'])
    dem_file = st.sidebar.file_uploader("Upload Demand CSV", type=['csv'])
    
    if sup_file and lanes_file and dem_file:
        suppliers_df = pd.read_csv(sup_file)
        lanes_df = pd.read_csv(lanes_file)
        demand_df = pd.read_csv(dem_file)
    else:
        suppliers_df = pd.read_csv('suppliers_india.csv')
        lanes_df = pd.read_csv('lanes_india.csv')
        demand_df = pd.read_csv('demand_india.csv')
else:
    suppliers_df = pd.read_csv('suppliers_india.csv')
    lanes_df = pd.read_csv('lanes_india.csv')
    demand_df = pd.read_csv('demand_india.csv')

st.sidebar.markdown("---")
st.sidebar.header("🇮🇳 2. PLI & Trade Policy Controls")

pli_rate = st.sidebar.slider("Government PLI Cashback Benefit (% on Domestic Prod)", 0.0, 6.0, 4.0, step=0.5, help="Simulate 2% to 6% Production Linked Incentives for local manufacturing.")
tariff_shock = st.sidebar.slider("Basic Customs Duty (BCD) Import Tariff Hike (+%)", 0, 30, 0, step=5)
disruption_hub = st.sidebar.selectbox("Simulate Regional Disruption / Port Closure", ["None", "Shenzhen_China", "Hai_Phong_Vietnam"])
max_risk_cap = st.sidebar.slider("Geopolitical Risk Ceiling (1-10)", 1.0, 10.0, 6.0, step=0.5)
max_china_share = st.sidebar.slider("Max Sourcing Dependency on China (%)", 0, 100, 100, step=10) / 100.0

# --- DYNAMIC ADJUSTMENTS ---
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

# --- RUN OPTIMIZATION ---
base_status, base_cost, base_res = run_supply_chain_optimization(suppliers_df, lanes_df, demand_df, max_risk_cap=10.0, max_china_share=1.0, pli_incentive_pct=0.0)
stress_status, stress_cost, stress_res = run_supply_chain_optimization(suppliers_modified, lanes_modified, demand_df, max_risk_cap=max_risk_cap, max_china_share=max_china_share, pli_incentive_pct=pli_rate)

if stress_status != 'Optimal':
    st.error("❌ CRITICAL NETWORK FAILURE: Applied disruption parameters or risk constraints make it impossible to meet demand.")
else:
    cost_delta = stress_cost - base_cost
    pct_delta = (cost_delta / base_cost) * 100
    
    base_avg_lt = (base_res['Units Shipped'] * base_res['Lead Time (Days)']).sum() / base_res['Units Shipped'].sum()
    stress_avg_lt = (stress_res['Units Shipped'] * stress_res['Lead Time (Days)']).sum() / stress_res['Units Shipped'].sum()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Stressed Network Spend", f"₹{stress_cost:,.2f}", delta=f"{pct_delta:+.2f}% vs Baseline", delta_color="inverse")
    kpi2.metric("Financial Delta", f"₹{cost_delta:,.2f}", delta="Cost Variance", delta_color="off")
    kpi3.metric("Avg Lead Time", f"{stress_avg_lt:.1f} Days", delta=f"{stress_avg_lt - base_avg_lt:+.1f} Days", delta_color="inverse")
    kpi4.metric("Risk Profile Score", f"{(stress_res['Units Shipped'] * stress_res['Geo Risk Score']).sum() / stress_res['Units Shipped'].sum():.2f} / 10")

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Executive Trade-off Analysis", "🇮🇳 PLI vs. Localization Simulator", "🚚 Sourcing Strategy & Routing", "📑 Data Export"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Cost Structure Drivers Comparison (₹)")
            comp_df = pd.DataFrame({
                'Scenario': ['Baseline', 'Stressed Scenario'],
                'Base Production': [base_res['Base Cost (₹)'].sum(), stress_res['Base Cost (₹)'].sum()],
                'Freight Costs': [base_res['Freight (₹)'].sum(), stress_res['Freight (₹)'].sum()],
                'Customs Tariff (BCD)': [base_res['Tariff BCD (₹)'].sum(), stress_res['Tariff BCD (₹)'].sum()]
            })
            st.plotly_chart(px.bar(comp_df, x='Scenario', y=['Base Production', 'Freight Costs', 'Customs Tariff (BCD)'], barmode='stack'), use_container_width=True)

        with c2:
            st.subheader("Geopolitical Volume Allocation")
            st.plotly_chart(px.pie(stress_res, names='Location', values='Units Shipped', hole=0.4), use_container_width=True)

    with tab2:
        st.subheader("🇮🇳 Government PLI Scheme vs. Domestic Localization Trade-off")
        st.write("Evaluates how PLI cashback incentives offset higher domestic base manufacturing costs and encourage shifting away from imports.")

        # Calculate Domestic vs Import Sourcing Share
        domestic_share = stress_res[stress_res['Supplier Type'].str.contains('Domestic', case=False)]['Units Shipped'].sum() / stress_res['Units Shipped'].sum() * 100
        pli_savings_total = (stress_res['Units Shipped'] * stress_res['PLI Rebate (₹)']).sum()

        col_p1, col_p2, col_p3 = st.columns(3)
        col_p1.metric("Domestic Sourcing Share (%)", f"{domestic_share:.1f}%")
        col_p2.metric("Total PLI Incentive Cashback Realized", f"₹{pli_savings_total:,.2f}")
        col_p3.metric("Import Dependency Rate", f"{100 - domestic_share:.1f}%")

        st.markdown("---")
        st.subheader("Cost Breakdown with PLI Cashback Impact")
        fig_pli = px.bar(
            stress_res, 
            x='Supplier Name', 
            y=['Base Cost (₹)', 'PLI Rebate (₹)', 'Tariff BCD (₹)', 'Freight (₹)'],
            title="Unit Cost Composition (Net of PLI Rebate)",
            barmode='group'
        )
        st.plotly_chart(fig_pli, use_container_width=True)

    with tab3:
        st.subheader("Optimal Routing Schedule per Demand Hub")
        st.plotly_chart(px.bar(stress_res, x='Destination Hub', y='Units Shipped', color='Supplier Name', text_auto=True), use_container_width=True)

    with tab4:
        st.subheader("Data Inspector & Export")
        st.dataframe(stress_res, use_container_width=True)
        st.download_button("📥 Download Executive Plan (CSV)", data=stress_res.to_csv(index=False).encode('utf-8'), file_name="executive_sourcing_plan.csv", mime="text/csv")
