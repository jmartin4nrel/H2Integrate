from greenheart.tools.data_loading_utils import check_create_folder,dump_data_to_pickle,load_dill_pickle
# from greenheart.simulation.greenheart_simulation import GreenHeartSimulationConfig

def save_pre_iron_greenheart_setup(config,wind_cost_results):
    #from setup_greenheart_simulation() if config.save_pre_iron (line 556)
    lat = config.hopp_config["site"]["data"]["lat"]
    lon = config.hopp_config["site"]["data"]["lon"]
    year = config.hopp_config['site']['data']['year']
    site_res_id = "{:.3f}_{:.3f}_{:d}".format(lat,lon,year)
            
    # Write outputs needed for future runs in .pkls
    pkl_fn = site_res_id+".pkl"
    output_names = ["config","wind_cost_results"]
    output_data = [config,wind_cost_results]
    output_data_dict = dict(zip(output_names,output_data))
    
    for output_name,data in output_data_dict.items():
        path = config.pre_iron_fn+'/'+output_name+'/'
        check_create_folder(path)
        output_filepath = path + pkl_fn
        dump_data_to_pickle(data,output_filepath)

def load_pre_iron_greenheart_setup(config):
    lat = config.hopp_config["site"]["data"]["lat"]
    lon = config.hopp_config["site"]["data"]["lon"]
    year = config.hopp_config['site']['data']['year']
    site_res_id = "{:.3f}_{:.3f}_{:d}".format(lat,lon,year)

    # Read in outputs from previously-saved .pkls        
    pkl_fn = site_res_id+".pkl"
    config_fpath = config.pre_iron_fn+'/'+"config"+'/'+pkl_fn
    wind_cost_fpath = config.pre_iron_fn+'/'+"wind_cost_results"+'/'+pkl_fn
    config = load_dill_pickle(config_fpath)
    wind_cost_results = load_dill_pickle(wind_cost_fpath)
    return config,wind_cost_results



def save_pre_iron_greenheart_simulation(config,lcoh,lcoe,electrolyzer_physics_results):
    #from setup_greenheart_simulation() if config.save_pre_iron (line 1071)
    lat = config.hopp_config["site"]["data"]["lat"]
    lon = config.hopp_config["site"]["data"]["lon"]
    year = config.hopp_config['site']['data']['year']
    site_res_id = "{:.3f}_{:.3f}_{:d}".format(lat,lon,year)
            
    # Write outputs needed for future runs in .pkls
    pkl_fn = site_res_id+".pkl"
    output_names = ["lcoe","lcoh","electrolyzer_physics_results"]
    output_data = [lcoe,lcoh,electrolyzer_physics_results]
    output_data_dict = dict(zip(output_names,output_data))
    for output_name,data in output_data_dict.items():
        path = config.pre_iron_fn+'/'+output_name+'/'
        check_create_folder(path)
        output_filepath = path + pkl_fn
        dump_data_to_pickle(data,output_filepath)



def load_pre_iron_greenheart_simulation(config):
    lat = config.hopp_config["site"]["data"]["lat"]
    lon = config.hopp_config["site"]["data"]["lon"]
    year = config.hopp_config['site']['data']['year']
    site_res_id = "{:.3f}_{:.3f}_{:d}".format(lat,lon,year)

    # Read in outputs from previously-saved .pkls        
    pkl_fn = site_res_id+".pkl"
    lcoh_fpath = config.pre_iron_fn+'/'+"lcoh"+'/'+pkl_fn
    lcoe_fpath = config.pre_iron_fn+'/'+"lcoe"+'/'+pkl_fn
    elec_phys_fpath = config.pre_iron_fn+'/'+"electrolyzer_physics_results"+'/'+pkl_fn
    lcoh = load_dill_pickle(lcoh_fpath)
    lcoe = load_dill_pickle(lcoe_fpath)
    electrolyzer_physics_results = load_dill_pickle(elec_phys_fpath)
    return lcoh,lcoe,electrolyzer_physics_results
