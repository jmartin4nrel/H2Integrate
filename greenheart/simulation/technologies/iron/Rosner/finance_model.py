import ProFAST

def main(config):
    feedstocks = config.feedstocks
    costs = config.costs


    # Set up ProFAST
    pf = ProFAST.ProFAST("blank")

    # apply all params passed through from config
    for param, val in config.financial_assumptions.items():
        pf.set_params(param, val)

    analysis_start = int(list(config.grid_prices.keys())[0]) - config.install_years

    # Fill these in - can have most of them as 0 also
    pf.set_params(
        "commodity",
        {
            "name": "iron",
            "unit": "metric tonnes",
            "initial price": 1000,
            "escalation": config.gen_inflation,
        },
    )
    pf.set_params("capacity", config.plant_capacity_mtpy / 365)  # units/day
    pf.set_params("maintenance", {"value": 0, "escalation": config.gen_inflation})
    pf.set_params("analysis start year", analysis_start)
    pf.set_params("operating life", config.plant_life)
    pf.set_params("installation months", 12 * config.install_years)
    pf.set_params(
        "installation cost",
        {
            "value": costs.installation_cost,
            "depr type": "Straight line",
            "depr period": 4,
            "depreciable": False,
        },
    )
    pf.set_params("non depr assets", costs.land_cost)
    pf.set_params(
        "end of proj sale non depr assets",
        costs.land_cost * (1 + config.gen_inflation) ** config.plant_life,
    )
    pf.set_params("demand rampup", 5.3)
    pf.set_params("long term utilization", config.plant_capacity_factor)
    pf.set_params("credit card fees", 0)
    pf.set_params("sales tax", 0)
    pf.set_params(
        "license and permit", {"value": 00, "escalation": config.gen_inflation}
    )
    pf.set_params("rent", {"value": 0, "escalation": config.gen_inflation})
    pf.set_params("property tax and insurance", 0)
    pf.set_params("admin expense", 0)
    pf.set_params("sell undepreciated cap", True)
    pf.set_params("tax losses monetized", True)
    pf.set_params("general inflation rate", config.gen_inflation)
    pf.set_params("debt type", "Revolving debt")
    pf.set_params("cash onhand", 1)

    # ----------------------------------- Add capital items to ProFAST ----------------
    # apply all params passed through from config
    for param, val in costs.capital_costs.items():
        pf.add_capital_item(
            name= param,
            cost= val,
            depr_type="MACRS",
            depr_period=7,
            refurb=[0], 
        )

    # -------------------------------------- Add fixed costs--------------------------------
    pf.add_fixed_cost(
        name="Annual Operating Labor Cost",
        usage=1,
        unit="$/year",
        cost=costs.labor_cost_annual_operation,
        escalation=config.gen_inflation,
    )
    pf.add_fixed_cost(
        name="Maintenance Labor Cost",
        usage=1,
        unit="$/year",
        cost=costs.labor_cost_maintenance,
        escalation=config.gen_inflation,
    )
    pf.add_fixed_cost(
        name="Administrative & Support Labor Cost",
        usage=1,
        unit="$/year",
        cost=costs.labor_cost_admin_support,
        escalation=config.gen_inflation,
    )
    pf.add_fixed_cost(
        name="Property tax and insurance",
        usage=1,
        unit="$/year",
        cost=costs.property_tax_insurance,
        escalation=0.0,
    )
    # Putting property tax and insurance here to zero out depcreciation/escalation. Could instead put it in set_params if
    # we think that is more accurate

    # ---------------------- Add feedstocks, note the various cost options-------------------
    pf.add_feedstock(
        name="Maintenance Materials",
        usage=1.0,
        unit="Units per metric tonne of iron",
        cost=feedstocks.maintenance_materials_unitcost,
        escalation=config.gen_inflation,
    )
    pf.add_feedstock(
        name="Raw Water Withdrawal",
        usage=feedstocks.raw_water_consumption,
        unit="metric tonnes of water per metric tonne of iron",
        cost=feedstocks.raw_water_unitcost,
        escalation=config.gen_inflation,
    )
    pf.add_feedstock(
        name="Lime",
        usage=feedstocks.lime_consumption,
        unit="metric tonnes of lime per metric tonne of iron",
        cost=feedstocks.lime_unitcost,
        escalation=config.gen_inflation,
    )
    pf.add_feedstock(
        name="Carbon",
        usage=feedstocks.carbon_consumption,
        unit="metric tonnes of carbon per metric tonne of iron",
        cost=feedstocks.carbon_unitcost,
        escalation=config.gen_inflation,
    )
    pf.add_feedstock(
        name="Iron Ore",
        usage=feedstocks.iron_ore_consumption,
        unit="metric tonnes of iron ore per metric tonne of iron",
        cost=feedstocks.iron_ore_pellet_unitcost,
        escalation=config.gen_inflation,
    )
    pf.add_feedstock(
        name="Hydrogen",
        usage=feedstocks.hydrogen_consumption,
        unit="metric tonnes of hydrogen per metric tonne of iron",
        cost=config.lcoh * 1000,
        escalation=config.gen_inflation,
    )
    pf.add_feedstock(
        name="Natural Gas",
        usage=feedstocks.natural_gas_consumption,
        unit="GJ-LHV per metric tonne of iron",
        cost=feedstocks.natural_gas_prices,
        escalation=config.gen_inflation,
    )
    pf.add_feedstock(
        name="Electricity",
        usage=feedstocks.electricity_consumption,
        unit="MWh per metric tonne of iron",
        cost=config.grid_prices,
        escalation=config.gen_inflation,
    )
    pf.add_feedstock(
        name="Slag Disposal",
        usage=feedstocks.slag_production,
        unit="metric tonnes of slag per metric tonne of iron",
        cost=feedstocks.slag_disposal_unitcost,
        escalation=config.gen_inflation,
    )

    pf.add_coproduct(
        name="Oxygen sales",
        usage=feedstocks.excess_oxygen,
        unit="kg O2 per metric tonne of iron",
        cost=feedstocks.oxygen_market_price,
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