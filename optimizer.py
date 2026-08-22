import pandas as pd
import pulp

def run_supply_chain_optimization(suppliers_df, lanes_df, demand_df, max_risk_cap=10.0, max_china_share=1.0, pli_incentive_pct=0.0):
    """
    Solves the Supply Chain Network Optimization using Mixed-Integer Linear Programming (MILP).
    Includes PLI Incentive Cashback for Domestic Suppliers.
    """
    # 1. Merge datasets to form complete supply routes
    routes = lanes_df.merge(suppliers_df, on='supplier_id').merge(demand_df, on='destination_hub')
    
    # Apply PLI Incentive (Cashback on unit prod cost for domestic suppliers)
    is_domestic = routes['supplier_type'].str.contains('Domestic', case=False, na=False)
    routes['pli_rebate_inr'] = 0.0
    routes.loc[is_domestic, 'pli_rebate_inr'] = routes.loc[is_domestic, 'unit_prod_cost_inr'] * (pli_incentive_pct / 100.0)

    # Calculate Net Total Landed Cost per unit in INR
    routes['tariff_cost_inr'] = routes['unit_prod_cost_inr'] * routes['bcd_tariff_pct']
    routes['total_landed_cost_inr'] = (routes['unit_prod_cost_inr'] - routes['pli_rebate_inr']) + routes['freight_cost_inr'] + routes['tariff_cost_inr']

    # 2. Define PuLP Optimization Model
    model = pulp.LpProblem("Indian_Supply_Chain_Optimization", pulp.LpMinimize)

    # Decision Variables
    route_keys = [(r['supplier_id'], r['destination_hub']) for _, r in routes.iterrows()]
    ship_vars = pulp.LpVariable.dicts("Ship_Units", route_keys, lowBound=0, cat='Continuous')

    suppliers = suppliers_df['supplier_id'].unique()
    supplier_active = pulp.LpVariable.dicts("Supplier_Active", suppliers, cat='Binary')

    # 3. Objective Function
    total_landed_cost_expr = pulp.lpSum([
        ship_vars[(r['supplier_id'], r['destination_hub'])] * r['total_landed_cost_inr']
        for _, r in routes.iterrows()
    ])
    
    fixed_contract_cost_expr = pulp.lpSum([
        supplier_active[s] * suppliers_df.loc[suppliers_df['supplier_id'] == s, 'fixed_contract_cost_inr'].values[0]
        for s in suppliers
    ])

    model += total_landed_cost_expr + fixed_contract_cost_expr

    # 4. Constraints
    for _, d in demand_df.iterrows():
        hub = d['destination_hub']
        req_demand = d['monthly_demand_units']
        model += pulp.lpSum([ship_vars[(s, hub)] for s in suppliers if (s, hub) in route_keys]) == req_demand

    for _, s in suppliers_df.iterrows():
        sup_id = s['supplier_id']
        capacity = s['monthly_capacity']
        supplied_total = pulp.lpSum([ship_vars[(sup_id, h)] for h in demand_df['destination_hub'] if (sup_id, h) in route_keys])
        model += supplied_total <= capacity * supplier_active[sup_id]

    total_demand = demand_df['monthly_demand_units'].sum()
    weighted_risk_expr = pulp.lpSum([
        ship_vars[(r['supplier_id'], r['destination_hub'])] * r['geo_risk_score']
        for _, r in routes.iterrows()
    ])
    model += (weighted_risk_expr / total_demand) <= max_risk_cap

    china_suppliers = suppliers_df[suppliers_df['location'].str.contains('China')]['supplier_id'].tolist()
    if china_suppliers:
        china_supply = pulp.lpSum([
            ship_vars[(s, h)] for s in china_suppliers for h in demand_df['destination_hub'] if (s, h) in route_keys
        ])
        model += china_supply <= total_demand * max_china_share

    # 5. Solve
    model.solve(pulp.PULP_CBC_CMD(msg=False))

    # 6. Process Results
    results = []
    for _, r in routes.iterrows():
        s_id = r['supplier_id']
        h_id = r['destination_hub']
        qty = ship_vars[(s_id, h_id)].varValue
        if qty and qty > 0:
            results.append({
                'Supplier ID': s_id,
                'Supplier Name': r['supplier_name'],
                'Location': r['location'],
                'Supplier Type': r['supplier_type'],
                'Destination Hub': h_id,
                'Mode': r['transport_mode'],
                'Units Shipped': qty,
                'Base Cost (₹)': r['unit_prod_cost_inr'],
                'PLI Rebate (₹)': r['pli_rebate_inr'],
                'Freight (₹)': r['freight_cost_inr'],
                'Tariff BCD (₹)': r['tariff_cost_inr'],
                'Landed Cost/Unit (₹)': r['total_landed_cost_inr'],
                'Total Spend (₹)': qty * r['total_landed_cost_inr'],
                'Lead Time (Days)': r['lead_time_days'],
                'Geo Risk Score': r['geo_risk_score']
            })

    results_df = pd.DataFrame(results)
    total_cost = pulp.value(model.objective)
    status = pulp.LpStatus[model.status]

    return status, total_cost, results_df
