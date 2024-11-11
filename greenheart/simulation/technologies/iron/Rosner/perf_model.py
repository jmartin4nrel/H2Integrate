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
    input_df = pd.read_csv(CD/config.performance_model['inputs_fp'],index_col=[0,1,2])
    coeff_df = pd.read_csv(CD/config.performance_model['coeffs_fp'],index_col=[0,1,2,3])
    
    # PLACEHOLDER OUTPUTS
    return 1,2