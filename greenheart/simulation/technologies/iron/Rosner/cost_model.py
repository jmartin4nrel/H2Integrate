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

def main(config):

    input_df = pd.read_csv(CD/config.cost_model['inputs_fp'])
    coeff_df = pd.read_csv(CD/config.cost_model['coeffs_fp'])

    # Import Peters opex model
    input_df = pd.read_csv(CD/model_locs['cost']['Peters']['inputs'])
    coeff_df = pd.read_csv(CD/model_locs['cost']['Peters']['inputs'])

    # PLACEHOLDER OUTPUTS
    return 1,2,3,4,5,6,7,8,9,10,1,2,3,4,5,6,7,8,9,10,1,2,3,4