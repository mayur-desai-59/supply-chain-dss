import pandas as pd

def create_indian_supply_chain_data():
    # 1. SUPPLIERS DATASET
    suppliers_data = [
        {
            'supplier_id': 'SUP-CHN-01',
            'supplier_name': 'Shenzhen Micro-Tech Ltd',
            'location': 'Shenzhen, China',
            'supplier_type': 'Overseas LCC',
            'unit_prod_cost_inr': 1850.00,
            'monthly_capacity': 80000,
            'fixed_contract_cost_inr': 500000,
            'defect_ppm': 450,
            'otif_rate': 0.91,
            'geo_risk_score': 7.2
        },
        {
            'supplier_id': 'SUP-VNM-01',
            'supplier_name': 'Hai Phong Assembly Corp',
            'location': 'Hai Phong, Vietnam',
            'supplier_type': 'ASEAN Nearshore',
            'unit_prod_cost_inr': 2100.00,
            'monthly_capacity': 50000,
            'fixed_contract_cost_inr': 350000,
            'defect_ppm': 280,
            'otif_rate': 0.94,
            'geo_risk_score': 4.1
        },
        {
            'supplier_id': 'SUP-IND-TN',
            'supplier_name': 'Sriperumbudur SMT Hub',
            'location': 'Tamil Nadu, India',
            'supplier_type': 'Domestic PLI',
            'unit_prod_cost_inr': 2350.00,
            'monthly_capacity': 45000,
            'fixed_contract_cost_inr': 200000,
            'defect_ppm': 150,
            'otif_rate': 0.98,
            'geo_risk_score': 1.2
        },
        {
            'supplier_id': 'SUP-IND-UP',
            'supplier_name': 'Noida Electronics Park',
            'location': 'Uttar Pradesh, India',
            'supplier_type': 'Domestic PLI',
            'unit_prod_cost_inr': 2400.00,
            'monthly_capacity': 35000,
            'fixed_contract_cost_inr': 150000,
            'defect_ppm': 120,
            'otif_rate': 0.97,
            'geo_risk_score': 1.1
        }
    ]

    # 2. LANES & TARIFFS DATASET
    lanes_data = [
        {'supplier_id': 'SUP-CHN-01', 'destination_hub': 'Bhiwandi_West', 'transport_mode': 'Ocean Freight (JNPT)', 'freight_cost_inr': 180.0, 'bcd_tariff_pct': 0.22, 'lead_time_days': 24},
        {'supplier_id': 'SUP-CHN-01', 'destination_hub': 'Hoskote_South', 'transport_mode': 'Ocean Freight (Chennai)', 'freight_cost_inr': 165.0, 'bcd_tariff_pct': 0.22, 'lead_time_days': 21},
        {'supplier_id': 'SUP-CHN-01', 'destination_hub': 'Farrukhnagar_North', 'transport_mode': 'Ocean + Rail (Mundra to NCR)', 'freight_cost_inr': 220.0, 'bcd_tariff_pct': 0.22, 'lead_time_days': 28},
        
        {'supplier_id': 'SUP-VNM-01', 'destination_hub': 'Bhiwandi_West', 'transport_mode': 'Ocean Freight (JNPT)', 'freight_cost_inr': 150.0, 'bcd_tariff_pct': 0.10, 'lead_time_days': 18},
        {'supplier_id': 'SUP-VNM-01', 'destination_hub': 'Hoskote_South', 'transport_mode': 'Ocean Freight (Chennai)', 'freight_cost_inr': 125.0, 'bcd_tariff_pct': 0.10, 'lead_time_days': 14},
        {'supplier_id': 'SUP-VNM-01', 'destination_hub': 'Farrukhnagar_North', 'transport_mode': 'Ocean + Rail', 'freight_cost_inr': 190.0, 'bcd_tariff_pct': 0.10, 'lead_time_days': 22},

        {'supplier_id': 'SUP-IND-TN', 'destination_hub': 'Bhiwandi_West', 'transport_mode': 'Road Express', 'freight_cost_inr': 85.0, 'bcd_tariff_pct': 0.00, 'lead_time_days': 4},
        {'supplier_id': 'SUP-IND-TN', 'destination_hub': 'Hoskote_South', 'transport_mode': 'Road Express', 'freight_cost_inr': 35.0, 'bcd_tariff_pct': 0.00, 'lead_time_days': 1},
        {'supplier_id': 'SUP-IND-TN', 'destination_hub': 'Farrukhnagar_North', 'transport_mode': 'Road Express', 'freight_cost_inr': 110.0, 'bcd_tariff_pct': 0.00, 'lead_time_days': 5},

        {'supplier_id': 'SUP-IND-UP', 'destination_hub': 'Bhiwandi_West', 'transport_mode': 'Road Express', 'freight_cost_inr': 90.0, 'bcd_tariff_pct': 0.00, 'lead_time_days': 4},
        {'supplier_id': 'SUP-IND-UP', 'destination_hub': 'Hoskote_South', 'transport_mode': 'Road Express', 'freight_cost_inr': 115.0, 'bcd_tariff_pct': 0.00, 'lead_time_days': 5},
        {'supplier_id': 'SUP-IND-UP', 'destination_hub': 'Farrukhnagar_North', 'transport_mode': 'Road Express', 'freight_cost_inr': 25.0, 'bcd_tariff_pct': 0.00, 'lead_time_days': 1}
    ]

    # 3. DEMAND FORECAST DATASET
    demand_data = [
        {'destination_hub': 'Bhiwandi_West', 'monthly_demand_units': 45000, 'region': 'West India'},
        {'destination_hub': 'Hoskote_South', 'monthly_demand_units': 40000, 'region': 'South India'},
        {'destination_hub': 'Farrukhnagar_North', 'monthly_demand_units': 35000, 'region': 'North India'}
    ]

    pd.DataFrame(suppliers_data).to_csv('suppliers_india.csv', index=False)
    pd.DataFrame(lanes_data).to_csv('lanes_india.csv', index=False)
    pd.DataFrame(demand_data).to_csv('demand_india.csv', index=False)

    print("SUCCESS: Indian baseline supply chain CSVs created!")

if __name__ == "__main__":
    create_indian_supply_chain_data()