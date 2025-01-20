'''
Direct Reduced Iron (DRI) model developed by Rosner et al.
Energy Environ. Sci., 2023, 16, 4121
doi.org/10.1039/d3ee01077e
'''

import pandas as pd
import numpy as np
from pathlib import Path
from hopp.utilities import load_yaml
from greenheart.tools.inflation.inflate import inflate_cpi, inflate_cepci
from greenheart.simulation.technologies.iron.load_top_down_coeffs import load_top_down_coeffs

CD = Path(__file__).parent

# Get model locations loaded up to refer to
model_locs_fp = CD / '../model_locations.yaml'
model_locs = load_yaml(model_locs_fp)

def main(config):

    # Import 'top-down' costs
    top_down_coeffs = load_top_down_coeffs()

    model_year = 2022 # Rosner paper: All economic data in 2022 $
    technology = config.technology

    start_year = config.params['operational_year']
    end_year = start_year+config.params['plant_life']
    end_year = min(end_year,top_down_coeffs['years'][-1])
    td_start_idx = np.where(top_down_coeffs['years']==start_year)[0][0]
    td_end_idx = np.where(top_down_coeffs['years']==end_year)[0][0]

    # model_year_CEPCI = 596.2 # Where is this value from? 
    # equation_year_CEPCI = 708.8
    # Rosner paper in 2022 $, not sure where these value came from but close to 2020/2022 CEPCI values

    # Get plant performances into data frame/series with performance names as index
    perf_df = config.performance.performances_df.set_index('Name')
    perf_ds = perf_df.loc[:,config.site['name']]

    plant_capacity_mtpy = perf_ds['Reduced Iron Capacity'] # In metric tonnes per year
    lcoh = config.params['lcoh']
    
    # Set up dataframe to store costs
    cols = ['Tech','Name','Type','Unit',config.site['name']]
    costs_df = pd.DataFrame([],columns=cols)

    # --------------- capital items ----------------
    capital_costs = {}
    # If re-fitting the model, load an inputs dataframe, otherwise, load up the coeffs
    if config.model['refit_coeffs']:
        input_df = pd.read_csv(CD/config.model['inputs_fp'])
        tech_df = input_df[input_df['Tech'].str.contains(technology, case=False, na=False)]

        remove_rows = ["Capacity Factor", "Pig Iron", "Liquid Steel"]
        pattern = '|'.join(remove_rows)
        tech_df = tech_df[~tech_df['Name'].str.contains(pattern, case=False, na=False)]

        keys = tech_df.iloc[:, 1]  # Extract name
        values = tech_df.iloc[:, 4:19]  # Extract values for cost re-fitting

        # Create dictionary with keys for name and arrays of values
        array_dict = {
            key: np.array(row) for key, row in zip(keys, values.itertuples(index=False, name=None))
        }

        x = np.log(array_dict["Steel Slab"])
        del array_dict["Steel Slab"]
        # Dictionary to store the fitted parameters
        params_dict = {}
        for key in array_dict:
            y = np.log(array_dict[key])
            # Fit the curve
            coeffs = np.polyfit(x,y,1)

            # Extract coefficients
            a = np.exp(coeffs[1])
            b = coeffs[0]

            # Ensure all values are real
            a = 0 if np.isnan(a) else a
            b = 0 if np.isnan(b) else b
            
            # Store the parameters in the dictionary
            params_dict[key] = {"lin": a, "exp": b}

        # Add unique capital items based on the "Name" column for technology
        for key,values in params_dict.items():
            # Filter for this item and get the lin and exp coefficients
            lin_coeff = values['lin']
            exp_coeff = values['exp']
            
            # Calculate the capital cost for the item
            capital_costs[key] = lin_coeff * plant_capacity_mtpy**exp_coeff

        # Read in cost coeffs for non-capital costs
        coeff_df = pd.read_csv(CD/config.model['coeffs_fp'],index_col=[0,1,2,3])
        tech_coeffs = coeff_df[[technology]].reset_index()
        perf_coeff_df = pd.read_csv(CD/'perf_coeffs.csv',index_col=[0,1,2,3]) #TODO: decouple performance and cost models
        perf_coeffs = perf_coeff_df[technology]

    else:
        coeff_df = pd.read_csv(CD/config.model['coeffs_fp'],index_col=[0,1,2,3])
        tech_coeffs = coeff_df[[technology]].reset_index()
        perf_coeff_df = pd.read_csv(CD/'perf_coeffs.csv',index_col=[0,1,2,3]) #TODO: decouple performance and cost models
        perf_coeffs = perf_coeff_df[technology]

        # Add unique capital items based on the "Name" column for technology
        for item_name in tech_coeffs[tech_coeffs["Type"] == "capital"]["Name"].unique():
            # Filter for this item and get the lin and exp coefficients
            item_data = tech_coeffs[(tech_coeffs["Name"] == item_name) & (tech_coeffs["Type"] == "capital")]
            lin_coeff = item_data[item_data["Coeff"] == "lin"][technology].values[0]
            exp_coeff = item_data[item_data["Coeff"] == "exp"][technology].values[0]
            
            # Calculate the capital cost for the item
            capital_costs[item_name] = lin_coeff * plant_capacity_mtpy**exp_coeff

    total_plant_cost = sum(capital_costs.values())

    for cost_name, cost in capital_costs.items():
        new_cost = [technology,cost_name,'capital',str(model_year)+" $",cost]
        costs_df.loc[len(costs_df)] = new_cost

    # -------------------------------Fixed O&M Costs------------------------------

    # Import Peters opex model
    if config.model['refit_coeffs']:
        input_df = pd.read_csv(CD/'../Peters'/model_locs['cost']['Peters']['inputs'])
        keys = input_df.iloc[:, 0]  # Extract name
        values = input_df.iloc[:, 3:16]  # Extract values for cost re-fitting

        # Create dictionary with keys for name and arrays of values
        array_dict = {
            key: np.array(row) for key, row in zip(keys, values.itertuples(index=False, name=None))
        }

        x = np.log(array_dict["Plant Size"])
        y = np.log(array_dict["Operating Labor"])

        # Fit the curve
        coeffs = np.polyfit(x,y,1)

        # Extract coefficients
        Peters_coeffs_lin = np.exp(coeffs[1])
        Peters_coeffs_exp = coeffs[0]

    else:
        coeff_df = pd.read_csv(CD/'../Peters'/model_locs['cost']['Peters']['coeffs'],index_col=[0,1,2,3])
        Peters_coeffs = coeff_df['A']
        Peters_coeffs_lin = Peters_coeffs.loc["Annual Operating Labor Cost",:,'lin'].values[0]
        Peters_coeffs_exp = Peters_coeffs.loc["Annual Operating Labor Cost",:,'exp'].values[0]


    # Peters model - employee-hours/day/process step * # of process steps
    fixed_costs = {}
    
    cost = (365
        * (tech_coeffs.loc[tech_coeffs["Name"] == "% Skilled Labor", technology].values[0]/100 * 
            np.mean(top_down_coeffs["Skilled Labor Cost"]['values'][td_start_idx:td_end_idx])
        + tech_coeffs.loc[tech_coeffs["Name"] == "% Unskilled Labor", technology].values[0]/100 * 
            np.mean(top_down_coeffs["Unskilled Labor Cost"]['values'][td_start_idx:td_end_idx]))
        * tech_coeffs.loc[tech_coeffs["Name"] == "Processing Steps", technology].values[0]
        * Peters_coeffs_lin
        * (plant_capacity_mtpy / 365 * 1000) ** Peters_coeffs_exp
    )
    labor_cost_annual_operation = cost
    fixed_costs['labor_cost_annual_operation'] = cost 

    cost = tech_coeffs.loc[tech_coeffs["Name"] == "Maintenance Labor Cost", technology].values[0]  * total_plant_cost
    labor_cost_maintenance = cost
    fixed_costs['labor_cost_annual_operation'] = cost

    cost = tech_coeffs.loc[tech_coeffs["Name"] == "Administrative & Support Labor Cost", technology].values[0] * (
        labor_cost_annual_operation + labor_cost_maintenance
    )
    labor_cost_admin_support = cost
    fixed_costs['labor_cost_admin_support'] = cost

    cost = tech_coeffs.loc[tech_coeffs["Name"] == "Property Tax & Insurance", technology].values[0] * total_plant_cost
    property_tax_insurance = cost
    fixed_costs['property_tax_insurance'] = cost

    total_fixed_operating_cost = (
        labor_cost_annual_operation
        + labor_cost_maintenance
        + labor_cost_admin_support
        + property_tax_insurance
    )

    for cost_name, cost in fixed_costs.items():
        new_cost = [technology,cost_name,'fixed opex',str(model_year)+" $ per year",cost]
        costs_df.loc[len(costs_df)] = new_cost

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
        * plant_capacity_mtpy / 12
    )
    non_fuel_consumables_onemonth = (
        plant_capacity_mtpy
        * (
            perf_coeffs.loc['Raw Water Withdrawal'].values[0] * top_down_coeffs["Raw Water"]['values'][td_start_idx]
            + perf_coeffs.loc['Lime'].values[0] * top_down_coeffs["Lime"]['values'][td_start_idx]
            + perf_coeffs.loc['Carbon (Coke)'].values[0] * top_down_coeffs["Carbon"]['values'][td_start_idx]
            + perf_coeffs.loc['Iron Ore'].values[0] * top_down_coeffs["Iron Ore Pellets"]['values'][td_start_idx]
            + perf_coeffs.loc['Reformer Catalyst'].values[0] * top_down_coeffs["Reformer Catalyst"]['values'][td_start_idx]
        )
        / 12
    )

    waste_disposal_onemonth = (
        plant_capacity_mtpy
        * perf_coeffs.loc['Slag'].values[0]
        * top_down_coeffs["Slag Disposal"]['values'][td_start_idx]
        / 12
    )

    monthly_energy_cost = (
        plant_capacity_mtpy
        * (
            perf_coeffs.loc["Hydrogen"].values[0] * lcoh * 1000
            + perf_coeffs.loc["Natural Gas"].values[0] * top_down_coeffs["Natural Gas"]['values'][td_start_idx]
            + perf_coeffs.loc["Electricity"].values[0] * top_down_coeffs["Electricity"]['values'][td_start_idx]
        )
        / 12
    )
    preproduction_cost = tech_coeffs.loc[tech_coeffs["Name"] == "Preproduction", technology].values[0] * total_plant_cost

    fuel_consumables_60day_supply_cost = non_fuel_consumables_onemonth * 12 / 365 * 60

    spare_parts_cost = tech_coeffs.loc[tech_coeffs["Name"] == "Spare Parts", technology].values[0] * total_plant_cost
    land_cost = tech_coeffs.loc[tech_coeffs["Name"] == "Land", technology].values[0] * plant_capacity_mtpy
    misc_owners_costs = tech_coeffs.loc[tech_coeffs["Name"] == "Other Owners's Costs", technology].values[0] * total_plant_cost

    installation_cost = (
        labor_cost_fivemonth
        + preproduction_cost
        + fuel_consumables_60day_supply_cost
        + spare_parts_cost
        + misc_owners_costs
    )

    new_cost = [technology,"Land cost",'other',str(model_year)+" $ per year",land_cost]
    costs_df.loc[len(costs_df)] = new_cost

    new_cost = [technology,"Installation cost",'other',str(model_year)+" $ per year",installation_cost]
    costs_df.loc[len(costs_df)] = new_cost

    return costs_df