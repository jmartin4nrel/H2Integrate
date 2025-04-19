import importlib
import numpy as np

from attrs import field, define

from h2integrate.core.utilities import (
    BaseConfig,
    merge_shared_cost_inputs,
    merge_shared_finance_inputs,
    merge_shared_performance_inputs,
)
from h2integrate.converters.methanol.methanol_baseclass import (
    MethanolCostBaseClass,
    MethanolFinanceBaseClass,
    MethanolPerformanceBaseClass,
)


@define
class MethanolPerformanceConfig(BaseConfig):
    conversion_tech: str = field()
    plant_capacity_kgpy: float = field()
    capacity_factor: float = field()


class MethanolPlantPerformanceModel(MethanolPerformanceBaseClass):
    """
    An OpenMDAO component that wraps various methanol performance models.
    Takes in conversion technology and plant capacity from config and computes the plant's flows.

    An OpenMDAO component for modeling the performance of a methanol plant.
    Computes annual methanol and co-product production, feedstock consumption, and emissions
    based on plant capacity and capacity factor.

    Inputs:
        - plant_capacity_kgpy: methanol production capacity in kg/year
        - capacity_factor: fractional factor of full production capacity that is realized
        - XXX_produce_ratio: ratio of XXX produced to kg methanol produced
        - XXX_consume_ratio: ratio of XXX consumed to kg methanol produced
        - XXX_emit_ratio: ratio of XXX emitted to kg methanol produced
    Outputs:
        - XXX_production: XXX production
        - XXX_consumption: XXX consumption
        - XXX_emission: XXX emission
    """

    def setup(self):
        super().setup()
        self.config = MethanolPerformanceConfig.from_dict(
            merge_shared_performance_inputs(self.options["tech_config"]["model_inputs"])
        )

        # Define any non-zero default values
        self.values = {
            "plant_capacity_kgpy": 100000000.0,
            "capacity_factor": 0.85,
        }

        tech = self.config.conversion_tech

        if tech == "smr":
            # Already declared in baseclass
            self.values["co2e_emit_ratio"] = 1.13442,
            self.values["h2o_consume_ratio"] = 2.669877132,
            self.values["h2_consume_ratio"] = 0.0,
            self.values["co2_consume_ratio"] = 0.0,
            self.values["elec_consume_ratio"] = 0.1,
            # tech-specific
            self.values["meoh_syn_cat_consume_ratio"] = 0.00000036322492251,
            self.values["meoh_atr_cat_consume_ratio"] = 0.0000013078433938,
            self.values["lng_consume_ratio"] = 1.61561859,
            self.values["elec_produce_ratio"] = 0.338415339,

        # Declare inputs and outputs - combination of values from config and model
        config_values = self.config.as_dict()
        # Config values overwrite any defaults from baseclass
        if config_values:
            for key, value in config_values.items():
                self.values[key] = value

        self.add_input("plant_capacity_kgpy", units="kg/year", val=self.values.get("plant_capacity_kgpy", 0.0))
        self.add_input("capacity_factor", units="unitless", val=self.values.get("capacity_factor", 0.0))
        self.add_input("co2e_emit_ratio", units="kg/kg", val=self.values.get("co2e_emit_ratio", 0.0))
        self.add_input("h2o_consume_ratio", units="kg/kg", val=self.values.get("h2o_consume_ratio", 0.0))
        self.add_input("h2_consume_ratio", units="kg/kg", val=self.values.get("h2_consume_ratio", 0.0))
        self.add_input("co2_consume_ratio", units="kg/kg", val=self.values.get("co2_consume_ratio", 0.0))
        self.add_input("elec_consume_ratio", units="kW*h/kg", val=self.values.get("elec_consume_ratio", 0.0))

        self.add_output("methanol_production", units="kg/h", shape=(8760,))
        self.add_output("co2e_emissions", units="kg/h", shape=(8760,))
        self.add_output("h2o_consumption", units="kg/h", shape=(8760,))
        self.add_output("h2_consumption", units="kg/h", shape=(8760,))
        self.add_output("co2_consumption", units="kg/h", shape=(8760,))
        self.add_output("elec_consumption", units="kW*h/h", shape=(8760,))

        # Add in tech-specific variables and values
        if tech == "smr":
            self.add_input("meoh_syn_cat_consume_ratio", units="ft**3/kg", val=self.values.get("meoh_syn_cat_consume_ratio", 0.0))
            self.add_input("meoh_atr_cat_consume_ratio", units="ft**3/kg", val=self.values.get("meoh_atr_cat_consume_ratio", 0.0))
            self.add_input("lng_consume_ratio", units="kg/kg", val=self.values.get("lng_consume_ratio", 0.0))
            self.add_input("elec_produce_ratio", units="kW*h/kg", val=self.values.get("elec_produce_ratio", 0.0))

            self.add_output("meoh_syn_cat_consumption", units="ft**3/yr")
            self.add_output("meoh_atr_cat_consumption", units="ft**3/yr")
            self.add_output("lng_consumption", shape=8760, units="kg/h")
            self.add_output("elec_production", shape=8760, units="kW*h/h")

    def compute(self, inputs, outputs):
        if self.config.conversion_tech == "smr":
            # Calculate methanol production #TODO get shape from output shape
            meoh_kgph = inputs["plant_capacity_kgpy"] * inputs["capacity_factor"] / 8760 * np.ones(shape=(8760,))

            # Parse outputs
            outputs["methanol_production"] = meoh_kgph
            outputs["co2_consumption"] = meoh_kgph * inputs["co2_consume_ratio"]
            outputs["h2o_consumption"] = meoh_kgph * inputs["h2o_consume_ratio"]
            outputs["h2_consumption"] = meoh_kgph * inputs["h2_consume_ratio"]
            outputs["co2e_emissions"] = meoh_kgph * inputs["co2e_emit_ratio"]
            outputs["elec_consumption"] = meoh_kgph * inputs["elec_consume_ratio"]
            outputs["meoh_atr_cat_consumption"] = np.sum(meoh_kgph) * inputs["meoh_atr_cat_consume_ratio"]
            outputs["meoh_syn_cat_consumption"] = np.sum(meoh_kgph) * inputs["meoh_syn_cat_consume_ratio"]
            outputs["lng_consumption"] = meoh_kgph * inputs["lng_consume_ratio"]
            outputs["elec_production"] = meoh_kgph * inputs["elec_produce_ratio"]


@define
class MethanolCostConfig(BaseConfig):
    conversion_tech: str = field()
    plant_capacity_kgpy: float = field()


class MethanolPlantCostModel(MethanolCostBaseClass):
    """
    An OpenMDAO component for modeling the cost of a methanol plant.
    Includes CapEx, OpEx (fixed and variable), feedstock costs, and co-product credits.

    Uses NETL power plant quality guidelines quantity of "total overnight cost" (TOC) for CapEx
    NETL-PUB-22580 doi.org/10.2172/1567736
    Splits OpEx into Fixed and Variable (variable scales with capacity factor, fixed does not)

    Inputs:
        toc_kg_y: total overnight cost (TOC) slope - multiply by plant_capacity_kgpy to get CapEx
        foc_kg_y^2: fixed operating cost slope - multiply by plant_capacity_kgpy to get Fixed_OpEx
        voc_kg: variable operating cost - multiple by methanol_production to get Variable_OpEx
        plant_capacity_kgpy: shared input, see MethanolPerformanceBaseClass
        methanol_production: promoted output from MethanolPerformanceBaseClass
    Outputs:
        CapEx: all methanol plant capital expenses in the form of total overnight cost (TOC)
        OpEx: all methanol plant operating expenses (fixed and variable)
        Fixed_OpEx: all methanol plant fixed operating expenses (do NOT vary with production rate)
        Variable_OpEx: all methanol plant variable operating expenses (vary with production rate)
    """

    def setup(self):
        super().setup()
        self.config = MethanolCostConfig.from_dict(
            merge_shared_cost_inputs(self.options["tech_config"]["model_inputs"])
        )
        tech = self.config.conversion_tech

        # Define any non-zero default values
        self.values = {
            "plant_capacity_kgpy": 100000000.0,
        }

        if tech == "smr":
            self.values = {
                # Already declared in baseclass
                "toc_kg_y": 0.782749307,
                "foc_kg_y^2": 0.020675078,
                "voc_kg": 0.012271827,
                # tech-specific
                "meoh_syn_cat_price": 615.274273,
                "meoh_atr_cat_price": 747.9768786,
                "lng_price": 4.0,
                "elec_sales_price": 0.027498168,
            }

        # Declare inputs and outputs - combination of values from config and model
        config_values = self.config.as_dict()
        # Config values overwrite any defaults from baseclass
        if config_values:
            for key, value in config_values.items():
                self.values[key] = value

        self.add_input("toc_kg_y", units="USD/kg/year", val=self.values.get("toc_kg_y", 0.0))
        self.add_input("foc_kg_y^2", units="USD/kg/year**2", val=self.values.get("foc_kg_y^2", 0.0))
        self.add_input("voc_kg", units="USD/kg", val=self.values.get("voc_kg", 0.0))
        self.add_input("plant_capacity_kgpy", units="kg/year", val=self.values.get("plant_capacity_kgpy", 0.0))
        self.add_input("electricity_price", units="USD/kW/h", val=self.values.get("electricity_price", 0.0))
        self.add_input("hydrogen_price", units="USD/kg", val=self.values.get("hydrogen_price", 0.0))
        self.add_input("electricity_consumption", shape=8760, units="kW*h/h", val=self.values.get("electricity_consumption", 0.0))
        self.add_input("hydrogen_consumption", shape=8760, units="kg/h", val=self.values.get("hydrogen_consumption", 0.0))
        self.add_input("methanol_production", shape=8760, units="kg/h", val=self.values.get("methanol_production", 0.0))

        self.add_output("CapEx", units="USD")
        self.add_output("OpEx", units="USD/year")
        self.add_output("Fixed_OpEx", units="USD/year")
        self.add_output("Variable_OpEx", units="USD/year")

        # Add in tech-specific variables and values
        if tech == "smr":
            self.add_input("meoh_syn_cat_consumption", units="ft**3/yr", val=self.values.get("meoh_syn_cat_consumption", 0.0))
            self.add_input("meoh_atr_cat_consumption", units="ft**3/yr", val=self.values.get("meoh_atr_cat_consumption", 0.0))
            self.add_input("lng_consumption", shape=8760, units="kg/h", val=self.values.get("lng_consumption", 0.0))
            self.add_input("elec_production", shape=8760, units="kW*h/h", val=self.values.get("elec_production", 0.0))
            self.add_input("meoh_syn_cat_price", units="USD/ft**3", val=self.values.get("meoh_syn_cat_price", 0.0))
            self.add_input("meoh_atr_cat_price", units="USD/ft**3", val=self.values.get("meoh_atr_cat_price", 0.0))
            self.add_input("lng_price", units="USD/MBtu", val=self.values.get("lng_price", 0.))  # TODO: get OpenMDAO to recognize 'MMBtu'
            self.add_input("elec_sales_price", units="USD/kW/h", val=self.values.get("elec_sales_price", 0.0))

            self.add_output("meoh_syn_cat_cost", units="USD/year")
            self.add_output("meoh_atr_cat_cost", units="USD/year")
            self.add_output("lng_cost", units="USD/year")
            self.add_output("elec_revenue", units="USD/year")

    def compute(self, inputs, outputs):
        if self.config.conversion_tech == "smr":
            MMBTU_per_GJ = 1.055
            LHV = 0.0201  # GJ/kg

            toc_usd = inputs["plant_capacity_kgpy"] * inputs["toc_kg_y"]
            foc_usd_y = inputs["plant_capacity_kgpy"] * inputs["foc_kg_y^2"]
            voc_usd_y = np.sum(inputs["methanol_production"]) * inputs["voc_kg"]

            outputs["CapEx"] = toc_usd
            outputs["OpEx"] = foc_usd_y + voc_usd_y
            outputs["Fixed_OpEx"] = foc_usd_y
            outputs["Variable_OpEx"] = voc_usd_y
            outputs["meoh_syn_cat_cost"] = inputs["meoh_syn_cat_consumption"] * inputs["meoh_syn_cat_price"]
            outputs["meoh_atr_cat_cost"] = inputs["meoh_atr_cat_consumption"] * inputs["meoh_atr_cat_price"]
            outputs["lng_cost"] = np.sum(inputs["lng_consumption"]) * MMBTU_per_GJ * LHV * inputs["lng_price"]
            outputs["elec_revenue"] = np.sum(inputs["elec_production"]) * inputs["elec_sales_price"]


@define
class MethanolFinanceConfig(BaseConfig):
    conversion_tech: str = field()
    plant_capacity_kgpy: float = field()
    discount_rate: float = field()
    tasc_toc_multiplier: float = field()


class MethanolPlantFinanceModel(MethanolFinanceBaseClass):
    """
    An OpenMDAO component for modeling the financing of a methanol plant.
    Includes CapEx, OpEx (fixed and variable), feedstock costs, and co-product credits.

    Uses NETL power plant quality guidelines' total as-spent cost (TASC) multiplier for capex
    Capex expenses are annualized using a fixed charge rate also taken from NETL guidelines
    NETL-PUB-22580 doi.org/10.2172/1567736

    Inputs:
        CapEx: promoted output from MethanolCostBaseClass
        OpEx: promoted output from MethanolCostBaseClass
        Fixed_OpEx: promoted output from MethanolCostBaseClass
        Variable_OpEx: promoted output from MethanolCostBaseClass
        tasc_toc_multiplier: calculates TASC (total as-spent cost) from CapEx
        fixed_charge_rate: calculates annualized CapEx finance payments from TASC
        methanol_production: promoted output from MethanolPerformanceBaseClass
    Outputs:
        LCOM: levelized cost of methanol
        LCOM_meoh: portion of the LCOM from the methanol plant itself (no feedstocks)
        LCOM_meoh_capex: portion of the LCOM_meoh from capital expenses
        LCOM_meoh_fopex: portion of the LCOM_meoh from fixed operating expenses
        LCOM_meoh_vopex: portion of the LCOM_meoh from variable operating expenses
    """

    def setup(self):
        super().setup()
        self.config = MethanolFinanceConfig.from_dict(
            merge_shared_finance_inputs(self.options["tech_config"]["model_inputs"])
        )
        tech = self.config.conversion_tech

        # Sources in NETL-PUB-22580: Exhibit 3-5 and Exhibit 3-7
        self.values = {
            "fixed_charge_rate": 0.0707,
            "tasc_toc_multiplier": 1.093,
        }

        # Declare inputs and outputs - combination of values from config and model
        config_values = self.config.as_dict()
        # Config values overwrite any defaults from baseclass
        if config_values:
            for key, value in config_values.items():
                self.values[key] = value

        self.add_input("CapEx", units="USD", val=self.values.get("CapEx", 0.0))
        self.add_input("OpEx", units="USD/year", val=self.values.get("OpEx", 0.0))
        self.add_input("Fixed_OpEx", units="USD/year", val=self.values.get("Fixed_OpEx", 0.0))
        self.add_input("Variable_OpEx", units="USD/year", val=self.values.get("Variable_OpEx", 0.0))
        self.add_input("tasc_toc_multiplier", units=None, val=self.values.get("tasc_toc_multiplier", 0.0))
        self.add_input("fixed_charge_rate", units=None, val=self.values.get("fixed_charge_rate", 0.0))
        self.add_input("methanol_production", shape=8760, units="kg/h", val=self.values.get("methanol_production", 0.0))

        self.add_output("LCOM", units="USD/kg")
        self.add_output("LCOM_meoh", units="USD/kg")
        self.add_output("LCOM_meoh_capex", units="USD/kg")
        self.add_output("LCOM_meoh_fopex", units="USD/kg")
        self.add_output("LCOM_meoh_vopex", units="USD/kg")

        if tech == "smr":
            self.add_input("meoh_syn_cat_cost", units="USD/year", val=self.values.get("meoh_syn_cat_cost", 0.0))
            self.add_input("meoh_atr_cat_cost", units="USD/year", val=self.values.get("meoh_atr_cat_cost", 0.0))
            self.add_input("lng_cost", units="USD/year", val=self.values.get("lng_cost", 0.0))
            self.add_input("elec_revenue", units="USD/year", val=self.values.get("elec_revenue", 0.0))
            self.add_output("LCOM_meoh_atr_cat", units="USD/kg")
            self.add_output("LCOM_meoh_syn_cat", units="USD/kg")
            self.add_output("LCOM_ng", units="USD/kg")
            self.add_output("LCOM_elec", units="USD/kg")
        

    def compute(self, inputs, outputs):
        kgph = inputs["methanol_production"]

        lcom_capex = inputs["CapEx"] * inputs["fixed_charge_rate"] * inputs["tasc_toc_multiplier"] / np.sum(kgph)
        lcom_fopex = inputs["Fixed_OpEx"] / np.sum(kgph)
        lcom_vopex = inputs["Variable_OpEx"] / np.sum(kgph)
        outputs["LCOM_meoh_capex"] = lcom_capex
        outputs["LCOM_meoh_fopex"] = lcom_fopex

        meoh_syn_cat_cost = inputs["meoh_syn_cat_cost"]
        meoh_atr_cat_cost = inputs["meoh_atr_cat_cost"]
        lcom_meoh_syn_cat = meoh_syn_cat_cost / np.sum(kgph)
        lcom_meoh_atr_cat = meoh_atr_cat_cost / np.sum(kgph)
        outputs["LCOM_meoh_syn_cat"] = lcom_meoh_syn_cat
        outputs["LCOM_meoh_atr_cat"] = lcom_meoh_atr_cat

        # Correct LCOM_meoh_vopex which initially included catalyst
        lcom_vopex -= lcom_meoh_syn_cat + lcom_meoh_atr_cat
        outputs["LCOM_meoh_vopex"] = lcom_vopex

        ng_cost = inputs["lng_cost"]
        lcom_ng = ng_cost / np.sum(kgph)
        outputs["LCOM_ng"] = lcom_ng

        elec_rev = inputs["elec_revenue"]
        lcom_elec = -elec_rev / np.sum(kgph)
        outputs["LCOM_elec"] = lcom_elec

        lcom_meoh = lcom_capex + lcom_fopex + lcom_vopex + lcom_meoh_syn_cat + lcom_meoh_atr_cat
        outputs["LCOM_meoh"] = lcom_meoh

        lcom = lcom_meoh + lcom_ng + lcom_elec
        outputs["LCOM"] = lcom
