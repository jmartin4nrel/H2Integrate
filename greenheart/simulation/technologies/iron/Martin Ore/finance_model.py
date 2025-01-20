import os
import numpy as np
import pandas as pd
import ProFAST
from greenheart.tools.inflation.inflate import inflate_cpi
from greenheart.simulation.technologies.iron.load_top_down_coeffs import load_top_down_coeffs

def main(config):

    # Pull in costs from config
    costs = config.costs
    cost_names = costs.costs_df.loc[:,'Name'].values
    cost_types = costs.costs_df.loc[:,'Type'].values
    cost_units = costs.costs_df.loc[:,'Unit'].values

    # Set up ProFAST
    pf = ProFAST.ProFAST("blank")

    # Get mine/ore costs into data frame/series with cost names as index
    cost_df = costs.costs_df.set_index('Name')
    cost_ds = cost_df.loc[:,config.iron_config['ore_type']]

    # Apply all params passed through from config
    for param, val in config.financial_assumptions.items():
        pf.set_params(param, val)
    analysis_start = int(list(config.grid_prices.keys())[0]) - config.install_years
    pf.set_params("analysis start year", analysis_start)
    pf.set_params("operating life", config.plant_life)
    pf.set_params("installation months", 12 * config.install_years)
    pf.set_params("general inflation rate", config.gen_inflation)
    
    # Set the commodity produced as processed iron ore
    pf.set_params(
        "commodity",
        {
            "name": "processed iron ore",
            "unit": "wet metric tonnes",
            "initial price": 80,
            "escalation": config.gen_inflation,
        },
    )
    
    # Set plant production capacity
    ore_produced_wltpy = cost_ds.loc['Ore pellets produced'] # wltpy = wet long tons per year
    ore_produced_wmtpy = ore_produced_wltpy*1.016047 # wmtpy = wet metric tones per year
    pf.set_params("capacity", ore_produced_wmtpy / 365)  # units/day
    
    # Set default parameters
    pf.set_params("sell undepreciated cap", True)
    pf.set_params("tax losses monetized", True)
    pf.set_params("debt type", "Revolving debt")
    
    # Set unused parameters to zeros and ones
    pf.set_params("maintenance", {"value": 0, "escalation": config.gen_inflation})
    pf.set_params("non depr assets",0)
    pf.set_params("end of proj sale non depr assets", 0)
    pf.set_params("demand rampup", 0)
    pf.set_params("long term utilization", 1)
    pf.set_params("credit card fees", 0)
    pf.set_params("sales tax", 0)
    pf.set_params("license and permit", {"value": 00, "escalation": config.gen_inflation})
    pf.set_params("rent", {"value": 0, "escalation": config.gen_inflation})
    pf.set_params("property tax and insurance", 0)
    pf.set_params("admin expense", 0)
    pf.set_params("cash onhand", 1)

    '''
    Add the costs - find the indices ("idxs") of the costs in the cost dataframe
    and loop through each index ("idx") to add the name, unit, and value to ProFAST 
    '''

    # Add capital items
    capital_idxs = np.where(cost_types=='capital')[0]
    for idx in capital_idxs:
        name = cost_names[idx]
        unit = cost_units[idx] # Units for capital costs should be "<YYYY> $""
        source_year = int(unit[:4])
        cost_year = config.cost_year
        source_year_cost = cost_ds.iloc[idx]
        cost = inflate_cpi(source_year_cost, source_year, cost_year)

        pf.add_capital_item(
                name= name,
                cost= cost,
                depr_type="MACRS",
                depr_period=7,
                refurb=[0], 
            )

    # Add fixed opex costs 
    fixed_idxs = np.where(cost_types=='fixed opex')[0]
    installation_cost = 0
    for idx in fixed_idxs:
        name = cost_names[idx]
        unit = cost_units[idx] # Units for fixed opex costs should be "<YYYY> $ per year"
        source_year = int(unit[:4])
        cost_year = config.cost_year
        source_year_cost = cost_ds.iloc[idx]
        cost = inflate_cpi(source_year_cost, source_year, cost_year)
        pf.add_fixed_cost(
            name=name,
            usage=1,
            unit="$/year",
            cost=cost,
            escalation=config.gen_inflation,
        )
        installation_cost += cost

    # Installation costs = 6 months fixed opex cost
    installation_cost = installation_cost * 6 / 12
    pf.set_params(
        "installation cost",
        {
            "value": installation_cost,
            "depr type": "Straight line",
            "depr period": 4,
            "depreciable": False,
        },
    )
    
    '''
    In the Martin model, the ProFAST 'feedstocks' cost class covers both the Martin model's
    'variable opex' costs, which are defined solely by the model for the specific technology,
    and the Martin model's 'variable opex td' costs, which are UNIVERSAL, 'top-down' costs where
    the price of the feedstock (e.g. natural gas) changes in tandem across multiple modules.
    '''

    # Add variable opex costs (defined in model)
    var_idxs = np.where(cost_types=='variable opex')[0]
    installation_cost = 0
    for idx in var_idxs:
        name = cost_names[idx]
        unit = cost_units[idx] # Should be "<YYYY> $ per <unit plant output>"
        source_year = int(unit[:4])
        cost_year = config.cost_year
        source_year_cost = cost_ds.iloc[idx]
        cost = inflate_cpi(source_year_cost, source_year, cost_year)
        pf.add_feedstock(
            name=name,
            usage=1.0,
            unit=unit,
            cost=cost,
            escalation=config.gen_inflation,
        )


    # Add variable opex costs (look up price from 'top-down' inputs)
    var_td_idxs = np.where(cost_types=='variable opex td')[0]
    var_td_names = cost_names[var_td_idxs]
    var_td_input_costs = load_top_down_coeffs(var_td_names, config.cost_year)
    var_td_years = var_td_input_costs['years']
    year_start_idx = np.where(var_td_years==analysis_start)[0][0]
    analysis_end = min(max(var_td_years),analysis_start+config.plant_life)
    year_end_idx = np.where(var_td_years==analysis_end)[0][0]
    year_idxs = range(year_start_idx,year_end_idx)
    installation_cost = 0
    for idx in var_td_idxs:
        name = cost_names[idx]
        unit1 = cost_units[idx] # Should be "<unit top-down input> per <unit plant output>"
        var_td_usage = cost_ds.iloc[idx]
        
        var_td_dict = var_td_input_costs[name]
        unit2 = var_td_dict['unit'] # Should be "<YYYY> $ per <unit top-down input"
        var_td_price = var_td_dict['values']
        var_td_price = np.mean(var_td_price[year_idxs])

        cost = var_td_usage*var_td_price

        pf.add_feedstock(
            name=name,
            usage=1.0,
            unit=unit1+' / '+unit2,
            cost=cost,
            escalation=config.gen_inflation,
        )

    # ------------------------------ Set up outputs ---------------------------

    sol = pf.solve_price()
    summary = pf.get_summary_vals()
    price_breakdown = pf.get_cost_breakdown()

    if config.save_plots or config.show_plots:
        savepaths = [
            config.output_dir + "figures/capex/",
            config.output_dir + "figures/annual_cash_flow/",
            config.output_dir + "figures/lcos_breakdown/",
            config.output_dir + "data/",
        ]
        for savepath in savepaths:
            if not os.path.exists(savepath):
                os.makedirs(savepath)

        pf.plot_capital_expenses(
            fileout=savepaths[0] + "iron_capital_expense_%i.pdf" % (config.design_scenario_id),
            show_plot=config.show_plots,
        )
        pf.plot_cashflow(
            fileout=savepaths[1] + "iron_cash_flow_%i.png"
            % (config.design_scenario_id),
            show_plot=config.show_plots,
        )

        pd.DataFrame.from_dict(data=pf.cash_flow_out).to_csv(
            savepaths[3] + "iron_cash_flow_%i.csv" % (config.design_scenario_id)
        )

        pf.plot_costs(
            savepaths[2] + "lcos_%i" % (config.design_scenario_id),
            show_plot=config.show_plots,
        )

    return sol, summary, price_breakdown