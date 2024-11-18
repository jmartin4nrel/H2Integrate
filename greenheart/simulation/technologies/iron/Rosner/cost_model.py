'''
Direct Reduced Iron (DRI) model developed by Rosner et al.
Energy Environ. Sci., 2023, 16, 4121
doi.org/10.1039/d3ee01077e
'''

import pandas as pd
from pathlib import Path
from hopp.utilities import load_yaml
CD = Path(__file__).parent

# Get model locations loaded up to refer to
model_locs_fp = CD / '../model_locations.yaml'
model_locs = load_yaml(model_locs_fp)

# Load CPI and CEPCI
cpi_df = pd.read_csv(CD/"../inflation/cpi.csv",index_col=0)
cepci_df = pd.read_csv(CD/"../inflation/cepci.csv",index_col=0)

def main(config):

    # Import 'top-down' costs
    top_down_df = pd.read_csv(CD/'../top_down_coeffs.csv',index_col=[0,1,2,3])
    top_down_year = top_down_df[str(config.operational_year)]

    technology = config.technology
    # If re-fitting the model, load an inputs dataframe, otherwise, load up the coeffs
    if config.cost_model['refit_coeffs']:
        input_df = pd.read_csv(CD/config.cost_model['inputs_fp'],index_col=[0,1,2])
        raise NotImplementedError('Rosner cost model cannot be re-fit')
    else:
        coeff_df = pd.read_csv(CD/config.cost_model['coeffs_fp'],index_col=[0,1,2,3])
        tech_coeffs = coeff_df[[technology]].reset_index()
        perf_coeff_df = pd.read_csv(CD/'perf_coeffs.csv',index_col=[0,1,2,3]) #TODO: decouple performance and cost models
        perf_coeffs = perf_coeff_df[technology]

    # Import Peters opex model
    if config.cost_model['refit_coeffs']:
        input_df = pd.read_csv(CD/'../Peters'/model_locs['cost']['Peters']['inputs'],index_col=[0,1,2])
    else:
        coeff_df = pd.read_csv(CD/'../Peters'/model_locs['cost']['Peters']['coeffs'],index_col=[0,1,2,3])
        Peters_coeffs = coeff_df['A']

    model_year_CEPCI = 596.2 # Where is this value from? 
    equation_year_CEPCI = 708.8 # Where is this value from? 

    # --------------- capital items ----------------

    capital_costs = {}

    # Add unique capital items based on the "Name" column for technology
    for item_name in tech_coeffs[tech_coeffs["Type"] == "capital"]["Name"].unique():
        # Filter for this item and get the lin and exp coefficients
        item_data = tech_coeffs[(tech_coeffs["Name"] == item_name) & (tech_coeffs["Type"] == "capital")]
        lin_coeff = item_data[item_data["Coeff"] == "lin"][technology].values[0]
        exp_coeff = item_data[item_data["Coeff"] == "exp"][technology].values[0]
        
        # Calculate the capital cost for the item
        capital_costs[item_name] = (
            model_year_CEPCI
            / equation_year_CEPCI
            * lin_coeff
            * config.plant_capacity_mtpy**exp_coeff
        )

    total_plant_cost = sum(capital_costs.values())

    # -------------------------------Fixed O&M Costs------------------------------

    # Peters model - employee-hours/day/process step * # of process steps
    labor_cost_annual_operation = ( 365
        * (tech_coeffs.loc[tech_coeffs["Name"] == "% Skilled Labor", technology].values[0]/100 * top_down_year.loc["Skilled Labor Cost"].values[0]
        + tech_coeffs.loc[tech_coeffs["Name"] == "% Unskilled Labor", technology].values[0]/100 * top_down_year.loc["Unskilled Labor Cost"].values[0])
        * tech_coeffs.loc[tech_coeffs["Name"] == "Processing Steps", technology].values[0]
        * Peters_coeffs.loc["Annual Operating Labor Cost",:,'lin'].values[0]
        * (config.plant_capacity_mtpy / 365 * 1000) ** Peters_coeffs.loc["Annual Operating Labor Cost",:,'exp'].values[0]
    ) * 63325349.24631249 / 63322395.97940371
    labor_cost_maintenance = tech_coeffs.loc[tech_coeffs["Name"] == "Maintenance Labor Cost", technology].values[0]  * total_plant_cost
    labor_cost_admin_support = tech_coeffs.loc[tech_coeffs["Name"] == "Administrative & Support Labor Cost", technology].values[0] * (
        labor_cost_annual_operation + labor_cost_maintenance
    )

    property_tax_insurance = tech_coeffs.loc[tech_coeffs["Name"] == "Property Tax & Insurance", technology].values[0] * total_plant_cost

    total_fixed_operating_cost = (
        labor_cost_annual_operation
        + labor_cost_maintenance
        + labor_cost_admin_support
        + property_tax_insurance
    )

    # ---------------------- Owner's (Installation) Costs --------------------------
    labor_cost_fivemonth = (
        5
        / 12
        * (
            labor_cost_annual_operation
            + labor_cost_maintenance
            + labor_cost_admin_support
        )
    )

    maintenance_materials_onemonth = (
        tech_coeffs.loc[tech_coeffs["Name"] == "Maintenance Materials", technology].values[0]
        * config.plant_capacity_mtpy / 12
    )
    non_fuel_consumables_onemonth = (
        config.plant_capacity_mtpy
        * (
            perf_coeffs.loc['Raw Water Withdrawal'].values[0] * top_down_year.loc['Raw Water'].values[0]
            + perf_coeffs.loc['Lime'].values[0] * top_down_year.loc['Lime'].values[0]
            + perf_coeffs.loc['Carbon (Coke)'].values[0] * top_down_year.loc['Carbon'].values[0]
            + perf_coeffs.loc['Iron Ore'].values[0] * top_down_year.loc['Iron Ore Pellets'].values[0]
        )
        / 12
    )

    waste_disposal_onemonth = (
        config.plant_capacity_mtpy
        * perf_coeffs.loc['Slag'].values[0]
        * top_down_year.loc["Slag Disposal"].values[0]
        / 12
    )

    monthly_energy_cost = (
        config.plant_capacity_mtpy
        * (
            perf_coeffs.loc["Hydrogen"].values[0] * config.lcoh * 1000
            + perf_coeffs.loc["Natural Gas"].values[0] * top_down_year.loc["Natural Gas"].values[0]
            + perf_coeffs.loc["Electricity"].values[0] * top_down_year.loc["Electricity"].values[0]
        )
        / 12
    )
    preproduction_cost = tech_coeffs.loc[tech_coeffs["Name"] == "Preproduction", technology].values[0] * total_plant_cost

    fuel_consumables_60day_supply_cost = non_fuel_consumables_onemonth * 12 / 365 * 60

    spare_parts_cost = tech_coeffs.loc[tech_coeffs["Name"] == "Spare Parts", technology].values[0] * total_plant_cost
    land_cost = tech_coeffs.loc[tech_coeffs["Name"] == "Land", technology].values[0] * config.plant_capacity_mtpy
    misc_owners_costs = tech_coeffs.loc[tech_coeffs["Name"] == "Other Owners's Costs", technology].values[0] * total_plant_cost

    installation_cost = (
        labor_cost_fivemonth
        + preproduction_cost
        + fuel_consumables_60day_supply_cost
        + spare_parts_cost
        + misc_owners_costs
    )

    return capital_costs,total_plant_cost,labor_cost_annual_operation,labor_cost_maintenance,\
        labor_cost_admin_support,property_tax_insurance,total_fixed_operating_cost,\
        labor_cost_fivemonth,maintenance_materials_onemonth,non_fuel_consumables_onemonth,\
        waste_disposal_onemonth,monthly_energy_cost,spare_parts_cost,land_cost,\
        misc_owners_costs,installation_cost