'''
Direct Reduced Iron (DRI) model developed by Rosner et al.
Energy Environ. Sci., 2023, 16, 4121
doi.org/10.1039/d3ee01077e
'''

import pandas as pd
from pathlib import Path
from hopp.utilities import load_yaml
CD = Path(__file__).parent

def main(config):
    
    # If re-fitting the model, load an inputs dataframe, otherwise, load up the coeffs
    if config.model['refit_coeffs']:
        input_df = pd.read_csv(CD/config.model['inputs_fp'],index_col=[0,1,2])
        raise NotImplementedError('Rosner performance model cannot be re-fit')
    else:
        coeff_df = pd.read_csv(CD/config.model['coeffs_fp'],index_col=[0,1,2,3])   
        tech_coeffs = coeff_df['h2_dri_eaf']
    
    # Calculate the hydrogen or iron capacity
    if 'hydrogen_amount_kgpy' in config.params.keys():
        iron_plant_capacity_mtpy = (config.params['hydrogen_amount_kgpy']
            / 1000
            / tech_coeffs.loc['Hydrogen'].values[0]
            * config.params['input_capacity_factor_estimate']
        )
        hydrogen_amount_kgpy = config.params['hydrogen_amount_kgpy']

    if 'desired_iron_mtpy' in config.params.keys():
        hydrogen_amount_kgpy = (config.params['desired_iron_mtpy ']
            * 1000
            * tech_coeffs.loc['Hydrogen'].values[0]
            / config.params['input_capacity_factor_estimate']
        )
        iron_plant_capacity_mtpy = (config.params['desired_iron_mtpy']
            / config.params['input_capacity_factor_estimate']
        )

    cols = ['Tech','Name','Unit',config.site['name']]
    perf_df = pd.DataFrame([],columns=cols)

    tech = config.technology

    new_line = [tech,'Reduced Iron Capacity','Metric tonnes per year',iron_plant_capacity_mtpy]
    perf_df.loc[len(perf_df)] = new_line

    new_line = [tech,'Hydrogen Used','Kg per year',hydrogen_amount_kgpy]
    perf_df.loc[len(perf_df)] = new_line

    new_line = [tech,'Capacity Factor','-',config.params['input_capacity_factor_estimate']]
    perf_df.loc[len(perf_df)] = new_line

    # feedstock_names = [
    #     'maintenance_materials_unitcost',
    #     'raw_water_consumption',
    #     'lime_consumption',
    #     'carbon_consumption',
    #     'iron_ore_consumption',
    #     'hydrogen_consumption',
    #     'electricity_consumption',
    #     'slag_production',
    #     'excess_oxygen'
    # ]

    # for feedstock in feedstock_names:

    return perf_df