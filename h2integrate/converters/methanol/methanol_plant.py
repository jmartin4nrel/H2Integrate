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
    """

    def setup(self):
        super().setup()
        self.config = MethanolPerformanceConfig.from_dict(
            merge_shared_performance_inputs(self.options["tech_config"]["model_inputs"])
        )

        tech = self.config.conversion_tech

        if tech == "smr":
            self.values = {
                # Already declared in baseclass
                "co2e_emit_ratio": 1.13442,
                "h2o_consume_ratio": 2.669877132,
                "h2_consume_ratio": 0.0,
                "co2_consume_ratio": 0.0,
                "elec_consume_ratio": 0.1,
                # tech-specific
                "meoh_syn_cat_consume_ratio": 0.00000036322492251,
                "meoh_atr_cat_consume_ratio": 0.0000013078433938,
                "lng_consume_ratio": 1.61561859,
                "elec_produce_ratio": 0.338415339,
            }
        # Add in tech-specific variables and values
        if tech == "smr":
            tech_dec_table_inputs = [
                ["type", "len", "conn", "unit", "name"],
                ["in", 1, False, "ft**3/kg", "meoh_syn_cat_consume_ratio"],
                ["in", 1, False, "ft**3/kg", "meoh_atr_cat_consume_ratio"],
                ["in", 1, False, "kg/kg", "lng_consume_ratio"],
                ["in", 1, False, "kW*h/kg", "elec_produce_ratio"],
                ["out", 1, False, "ft**3/yr", "meoh_syn_cat_consumption"],
                ["out", 1, False, "ft**3/yr", "meoh_atr_cat_consumption"],
                ["out", 8760, False, "kg/h", "lng_consumption"],
                ["out", 8760, False, "kW*h/h", "elec_production"],
            ]
        
        # Declare inputs and outputs - combination of values from config and model
        config_values = self.config.as_dict()
        # Config values overwrite any defaults from baseclass
        if config_values:
            for key, value in config_values.items():
                self.values[key] = value

        self.declare_from_table(tech_dec_table_inputs, self.values)

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
    An OpenMDAO component that wraps various methanol cost models.
    Takes in conversion technology and plant capacity from config and computes the plant's costs.
    """

    def setup(self):
        super().setup()
        self.config = MethanolCostConfig.from_dict(
            merge_shared_cost_inputs(self.options["tech_config"]["model_inputs"])
        )
        tech = self.config.conversion_tech

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
        # Add in tech-specific variables and values
        if tech == "smr":
            tech_dec_table_inputs = [
                ["type", "len", "conn", "unit", "name"],
                ["in", 1, False, "ft**3/yr", "meoh_syn_cat_consumption"],
                ["in", 1, False, "ft**3/yr", "meoh_atr_cat_consumption"],
                ["in", 8760, False, "kg/h", "lng_consumption"],
                ["in", 8760, False, "kW*h/h", "elec_production"],
                ["in", 1, False, "USD/ft**3", "meoh_syn_cat_price"],
                ["in", 1, False, "USD/ft**3", "meoh_atr_cat_price"],
                ["in", 1, False, "USD/MBtu", "lng_price"],  # TODO: get OpenMDAO to recognize 'MMBtu'
                ["in", 1, False, "USD/kW/h", "elec_sales_price"],
                ["out", 1, False, "USD/year", "meoh_syn_cat_cost"],
                ["out", 1, False, "USD/year", "meoh_atr_cat_cost"],
                ["out", 1, False, "USD/year", "lng_cost"],
                ["out", 1, False, "USD/year", "elec_revenue"],
            ]
        
        # Declare inputs and outputs - combination of values from config and model
        config_values = self.config.as_dict()
        # Config values overwrite any defaults from baseclass
        if config_values:
            for key, value in config_values.items():
                self.values[key] = value

        self.declare_from_table(tech_dec_table_inputs, self.values)

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
    An OpenMDAO component that wraps various methanol finance models.
    Takes in conversion technology, plant capacity, and financial constants from config and
    computes the plant's finances.
    """

    def setup(self):
        super().setup()
        self.config = MethanolFinanceConfig.from_dict(
            merge_shared_finance_inputs(self.options["tech_config"]["model_inputs"])
        )
        tech = self.config.conversion_tech

        if tech == "smr":
            tech_dec_table_inputs = [
                ["type", "len", "conn", "unit", "name"],
                ["in", 1, False, "USD/year", "meoh_syn_cat_cost"],
                ["in", 1, False, "USD/year", "meoh_atr_cat_cost"],
                ["in", 1, False, "USD/year", "lng_cost"],
                ["in", 1, False, "USD/year", "elec_revenue"],
                ["out", 1, False, "USD/kg", "LCOM_meoh_atr_cat"],
                ["out", 1, False, "USD/kg", "LCOM_meoh_syn_cat"],
                ["out", 1, False, "USD/kg", "LCOM_ng"],
                ["out", 1, False, "USD/kg", "LCOM_elec"],
            ]
        
        # Declare inputs and outputs - combination of values from config and model
        config_values = self.config.as_dict()
        # Config values overwrite any defaults from baseclass
        if config_values:
            for key, value in config_values.items():
                self.values[key] = value

        self.declare_from_table(tech_dec_table_inputs, self.values)

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
