import numpy as np
import ProFAST  # system financial model
import openmdao.api as om
import numpy_financial as npf


class AdjustedCapexOpexComp(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("tech_config", types=dict)
        self.options.declare("plant_config", types=dict)

    def setup(self):
        tech_config = self.options["tech_config"]
        plant_config = self.options["plant_config"]
        self.discount_years = plant_config["finance_parameters"]["discount_years"]
        self.inflation_rate = plant_config["finance_parameters"]["costing_general_inflation"]
        self.cost_year = plant_config["plant"]["cost_year"]

        for tech in tech_config:
            self.add_input(f"capex_{tech}", val=0.0, units="USD")
            self.add_input(f"opex_{tech}", val=0.0, units="USD/year")
            self.add_output(f"capex_adjusted_{tech}", val=0.0, units="USD")
            self.add_output(f"opex_adjusted_{tech}", val=0.0, units="USD/year")

        self.add_output("total_capex_adjusted", val=0.0, units="USD")
        self.add_output("total_opex_adjusted", val=0.0, units="USD/year")

    def compute(self, inputs, outputs):
        total_capex_adjusted = 0.0
        total_opex_adjusted = 0.0
        for tech in self.options["tech_config"]:
            capex = float(inputs[f"capex_{tech}"][0])
            opex = float(inputs[f"opex_{tech}"][0])
            cost_year = self.discount_years[tech]
            periods = self.cost_year - cost_year
            adjusted_capex = -npf.fv(self.inflation_rate, periods, 0.0, capex)
            adjusted_opex = -npf.fv(self.inflation_rate, periods, 0.0, opex)
            outputs[f"capex_adjusted_{tech}"] = adjusted_capex
            outputs[f"opex_adjusted_{tech}"] = adjusted_opex
            total_capex_adjusted += adjusted_capex
            total_opex_adjusted += adjusted_opex

        outputs["total_capex_adjusted"] = total_capex_adjusted
        outputs["total_opex_adjusted"] = total_opex_adjusted


class ProFastComp(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("tech_config", types=dict)
        self.options.declare("plant_config", types=dict)
        self.options.declare("commodity_type", types=str, default="hydrogen")

    def setup(self):
        tech_config = self.tech_config = self.options["tech_config"]
        plant_config = self.plant_config = self.options["plant_config"]
        self.discount_rate = plant_config["finance_parameters"]["discount_rate"]
        self.inflation_rate = plant_config["finance_parameters"]["costing_general_inflation"]
        self.cost_year = plant_config["plant"]["cost_year"]

        for tech in tech_config:
            self.add_input(f"capex_adjusted_{tech}", val=0.0, units="USD")
            self.add_input(f"opex_adjusted_{tech}", val=0.0, units="USD/year")

        if self.options["commodity_type"] == "hydrogen":
            self.add_output("LCOH", val=0.0, units="USD/kg")

        if self.options["commodity_type"] == "steel":
            self.add_output("LCOS", val=0.0, units="USD/ton")

        if self.options["commodity_type"] == "electricity":
            self.add_output("LCOE", val=0.0, units="USD/kW/h")

        if "electrolyzer" in tech_config:
            self.add_input("total_hydrogen_produced", val=0.0, units="kg/year")
            self.add_input("time_until_replacement", units="h")

    def compute(self, inputs, outputs):
        gen_inflation = self.plant_config["finance_parameters"]["profast_general_inflation"]

        land_cost = 0.0

        pf = ProFAST.ProFAST()
        if self.options["commodity_type"] == "hydrogen":
            pf.set_params(
                "commodity",
                {
                    "name": "Hydrogen",
                    "unit": "kg",
                    "initial price": 100,
                    "escalation": gen_inflation,
                },
            )
            pf.set_params(
                "capacity",
                float(inputs["total_hydrogen_produced"]) / 365.0,
            )  # kg/day
        pf.set_params("maintenance", {"value": 0, "escalation": gen_inflation})
        pf.set_params(
            "analysis start year",
            self.plant_config["plant"]["atb_year"] + 2,  # Add financial analysis start year
        )
        pf.set_params("operating life", self.plant_config["plant"]["plant_life"])
        pf.set_params(
            "installation months",
            self.plant_config["plant"][
                "installation_time"
            ],  # Add installation time to yaml default=0
        )
        pf.set_params(
            "installation cost",
            {
                "value": 0,
                "depr type": "Straight line",
                "depr period": 4,
                "depreciable": False,
            },
        )
        if land_cost > 0:
            pf.set_params("non depr assets", land_cost)
            pf.set_params(
                "end of proj sale non depr assets",
                land_cost * (1 + gen_inflation) ** self.plant_config["plant"]["plant_life"],
            )
        pf.set_params("demand rampup", 0)
        pf.set_params("long term utilization", 1)  # TODO should use utilization
        pf.set_params("credit card fees", 0)
        pf.set_params("sales tax", self.plant_config["finance_parameters"]["sales_tax_rate"])
        pf.set_params("license and permit", {"value": 00, "escalation": gen_inflation})
        pf.set_params("rent", {"value": 0, "escalation": gen_inflation})
        # TODO how to handle property tax and insurance for fully offshore?
        pf.set_params(
            "property tax and insurance",
            self.plant_config["finance_parameters"]["property_tax"]
            + self.plant_config["finance_parameters"]["property_insurance"],
        )
        pf.set_params(
            "admin expense",
            self.plant_config["finance_parameters"]["administrative_expense_percent_of_sales"],
        )
        pf.set_params(
            "total income tax rate",
            self.plant_config["finance_parameters"]["total_income_tax_rate"],
        )
        pf.set_params(
            "capital gains tax rate",
            self.plant_config["finance_parameters"]["capital_gains_tax_rate"],
        )
        pf.set_params("sell undepreciated cap", True)
        pf.set_params("tax losses monetized", True)
        pf.set_params("general inflation rate", gen_inflation)
        pf.set_params(
            "leverage after tax nominal discount rate",
            self.plant_config["finance_parameters"]["discount_rate"],
        )
        if self.plant_config["finance_parameters"]["debt_equity_split"]:
            pf.set_params(
                "debt equity ratio of initial financing",
                (
                    self.plant_config["finance_parameters"]["debt_equity_split"]
                    / (100 - self.plant_config["finance_parameters"]["debt_equity_split"])
                ),
            )  # TODO this may not be put in right
        elif self.plant_config["finance_parameters"]["debt_equity_ratio"]:
            pf.set_params(
                "debt equity ratio of initial financing",
                (self.plant_config["finance_parameters"]["debt_equity_ratio"]),
            )  # TODO this may not be put in right
        pf.set_params("debt type", self.plant_config["finance_parameters"]["debt_type"])
        pf.set_params("loan period if used", self.plant_config["finance_parameters"]["loan_period"])
        pf.set_params(
            "debt interest rate",
            self.plant_config["finance_parameters"]["debt_interest_rate"],
        )
        pf.set_params("cash onhand", self.plant_config["finance_parameters"]["cash_onhand_months"])

        # ----------------------------------- Add capital and fixed items to ProFAST ----------------
        for tech in self.tech_config:
            if "electrolyzer" in tech:
                electrolyzer_refurbishment_schedule = np.zeros(
                    self.plant_config["plant"]["plant_life"]
                )
                refurb_period = round(float(inputs["time_until_replacement"]) / (24 * 365))
                electrolyzer_refurbishment_schedule[
                    refurb_period : self.plant_config["plant"]["plant_life"] : refurb_period
                ] = self.tech_config["electrolyzer"]["model_inputs"]["financial_parameters"][
                    "replacement_cost_percent"
                ]
                electrolyzer_refurbishment_schedule = list(electrolyzer_refurbishment_schedule)

                pf.add_capital_item(
                    name="Electrolysis System",
                    cost=float(inputs[f"capex_adjusted_{tech}"]),
                    depr_type=self.plant_config["finance_parameters"]["depreciation_method"],
                    depr_period=int(
                        self.plant_config["finance_parameters"]["depreciation_period_electrolyzer"]
                    ),
                    refurb=electrolyzer_refurbishment_schedule,
                )
                pf.add_fixed_cost(
                    name="Electrolysis System Fixed O&M Cost",
                    usage=1.0,
                    unit="$/year",
                    cost=float(inputs[f"opex_adjusted_{tech}"]),
                    escalation=gen_inflation,
                )
            else:
                pf.add_capital_item(
                    name=f"{tech} System",
                    cost=float(inputs[f"capex_adjusted_{tech}"]),
                    depr_type=self.plant_config["finance_parameters"]["depreciation_method"],
                    depr_period=self.plant_config["finance_parameters"]["depreciation_period"],
                    refurb=[0],
                )
                pf.add_fixed_cost(
                    name=f"{tech} O&M Cost",
                    usage=1.0,
                    unit="$/year",
                    cost=float(inputs[f"opex_adjusted_{tech}"]),
                    escalation=gen_inflation,
                )

        # # ---------------------- Add feedstocks, note the various cost options-------------------
        # if design_scenario["electrolyzer_location"] == "onshore":
        #     galperkg = 3.785411784
        #     pf.add_feedstock(
        #         name="Water",
        #         usage=sum(
        #             electrolyzer_physics_results["H2_Results"]["Water Hourly Consumption [kg/hr]"]
        #         )
        #         * galperkg
        #         / electrolyzer_physics_results["H2_Results"]["Life: Annual H2 production [kg/year]"],
        #         unit="gal",
        #         cost="US Average",
        #         escalation=gen_inflation,
        #     )
        # else:
        #     pf.add_capital_item(
        #         name="Desal System",
        #         cost=capex_breakdown["desal"],
        #         depr_type=self.plant_config["finance_parameters"]["depreciation_method"],
        #         depr_period=self.plant_config["finance_parameters"]["depreciation_period_electrolyzer"],
        #         refurb=[0],
        #     )
        #     pf.add_fixed_cost(
        #         name="Desal Fixed O&M Cost",
        #         usage=1.0,
        #         unit="$/year",
        #         cost=opex_breakdown["desal"],
        #         escalation=gen_inflation,
        #     )

        # if (
        #     self.plant_config["plant"]["grid_connection"]
        #     or total_accessory_power_grid_kw > 0
        # ):
        #     energy_purchase = sum(total_accessory_power_grid_kw)  # * 365 * 24

        #     if self.plant_config["plant"]["grid_connection"]:
        #         annual_energy_shortfall = np.sum(hopp_results["energy_shortfall_hopp"])
        #         energy_purchase += annual_energy_shortfall

        #     pf.add_fixed_cost(
        #         name="Electricity from grid",
        #         usage=1.0,
        #         unit="$/year",
        #         cost=energy_purchase * self.plant_config["plant"]["ppa_price"],
        #         escalation=gen_inflation,
        #     )

        # ------------------------------------- add incentives -----------------------------------
        """
        Note: units must be given to ProFAST in terms of dollars per unit of the primary commodity being
        produced

        Note: full tech-neutral (wind) tax credits are no longer available if constructions starts after
        Jan. 1 2034 (Jan 1. 2033 for h2 ptc)
        """

        # # catch incentive option and add relevant incentives
        # incentive_dict = self.plant_config["policy_parameters"]

        # # add wind_itc (% of wind capex)
        # electricity_itc_value_percent_wind_capex = incentive_dict["electricity_itc"]
        # electricity_itc_value_dollars = electricity_itc_value_percent_wind_capex * (
        #     capex_breakdown["wind"] + capex_breakdown["electrical_export_system"]
        # )
        # pf.set_params(
        #     "one time cap inct",
        #     {
        #         "value": electricity_itc_value_dollars,
        #         "depr type": self.plant_config["finance_parameters"]["depreciation_method"],
        #         "depr period": self.plant_config["finance_parameters"]["depreciation_period"],
        #         "depreciable": True,
        #     },
        # )

        # # add h2_storage_itc (% of h2 storage capex)
        # itc_value_percent_h2_store_capex = incentive_dict["h2_storage_itc"]
        # electricity_itc_value_dollars_h2_store = (
        #     itc_value_percent_h2_store_capex * (capex_breakdown["h2_storage"])
        # )
        # pf.set_params(
        #     "one time cap inct",
        #     {
        #         "value": electricity_itc_value_dollars_h2_store,
        #         "depr type": self.plant_config["finance_parameters"]["depreciation_method"],
        #         "depr period": self.plant_config["finance_parameters"]["depreciation_period"],
        #         "depreciable": True,
        #     },
        # )

        # # add electricity_ptc ($/kW)
        # # adjust from 1992 dollars to start year
        # electricity_ptc_in_dollars_per_kw = -npf.fv(
        #     self.plant_config["finance_parameters"]["costing_general_inflation"],
        #     self.plant_config["plant"]["atb_year"]
        #     + round(wind_cost_results.installation_time / 12)
        #     - 1992,
        #     0,
        #     incentive_dict["electricity_ptc"],
        # )  # given in 1992 dollars but adjust for inflation
        # kw_per_kg_h2 = (
        #     sum(hopp_results["combined_hybrid_power_production_hopp"])
        #     / electrolyzer_physics_results["H2_Results"]["Life: Annual H2 production [kg/year]"]
        # )
        # electricity_ptc_in_dollars_per_kg_h2 = electricity_ptc_in_dollars_per_kw * kw_per_kg_h2
        # pf.add_incentive(
        #     name="Electricity PTC",
        #     value=electricity_ptc_in_dollars_per_kg_h2,
        #     decay=-gen_inflation,
        #     sunset_years=10,
        #     tax_credit=True,
        # )  # TODO check decay

        # # add h2_ptc ($/kg)
        # h2_ptc_inflation_adjusted = -npf.fv(
        #     self.plant_config["finance_parameters"][
        #         "costing_general_inflation"
        #     ],  # use ATB year (cost inflation 2.5%) costing_general_inflation
        #     self.plant_config["plant"]["atb_year"]
        #     + round(wind_cost_results.installation_time / 12)
        #     - 2022,
        #     0,
        #     incentive_dict["h2_ptc"],
        # )
        # pf.add_incentive(
        #     name="H2 PTC",
        #     value=h2_ptc_inflation_adjusted,
        #     decay=-gen_inflation,  # correct inflation
        #     sunset_years=10,
        #     tax_credit=True,
        # )  # TODO check decay

        # ------------------------------------ solve and post-process -----------------------------

        sol = pf.solve_price()

        # Only hydrogen supported in the very short term
        if self.options["commodity_type"] == "hydrogen":
            lcoh = sol["price"]
            outputs["LCOH"] = lcoh
