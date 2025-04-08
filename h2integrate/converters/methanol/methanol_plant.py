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
    conversion_model: str = field()
    lng: float = field()
    lng_consumption: float = field()


class MethanolPlantPerformanceModel(MethanolPerformanceBaseClass):
    """
    An OpenMDAO component that wraps various methanol models.
    Takes lng input and outputs methanol generation rates.
    """

    def setup(self):
        super().setup()
        self.config = MethanolPerformanceConfig.from_dict(
            merge_shared_performance_inputs(self.options["tech_config"]["model_inputs"])
        )

        # Import performance model for specified tech and model
        tech = self.config.conversion_tech
        import_path = "h2integrate.simulation.technologies.methanol." + tech
        Performance = importlib.import_module(import_path).Performance
        self.methanol = Performance()

        # Declare inputs and outputs - combination of values from config and model
        values = self.config.as_dict()
        dec_table = self.methanol.perf_dec_table
        self.declare_from_table(dec_table, values)

    def compute(self, inputs, outputs):
        # Run the SMR methanol model using the input lng signal
        methanol_production_kgph = self.methanol.run_performance_model(
            inputs["lng"],
            inputs["lng_consumption"],
        )
        outputs["methanol_production"] = np.ones(8760) * methanol_production_kgph


@define
class MethanolCostConfig(BaseConfig):
    conversion_tech: str = field()
    conversion_model: str = field()
    plant_capacity_kgpy: float = field()
    capex_factor: float = field()
    lng: float = field()
    lng_cost: float = field()


class MethanolPlantCostModel(MethanolCostBaseClass):
    """
    An OpenMDAO component that computes the cost of an SMR methanol plant.
    """

    def setup(self):
        super().setup()
        self.config = MethanolCostConfig.from_dict(
            merge_shared_cost_inputs(self.options["tech_config"]["model_inputs"])
        )
        # Import cost model for specified tech and model
        tech = self.config.conversion_tech
        import_path = "h2integrate.simulation.technologies.methanol." + tech
        Cost = importlib.import_module(import_path).Cost
        self.cost_model = Cost()

        self.add_input(
            "plant_capacity_kgpy",
            val=self.config.plant_capacity_kgpy,
            shape_by_conn=False,
            units="kg/year",
        )
        self.add_input(
            "capex_factor", val=self.config.capex_factor, shape_by_conn=False, units="USD/kg/year"
        )
        self.add_input("lng", val=self.config.lng, shape_by_conn=False, units="kg/year")
        self.add_input("lng_cost", val=self.config.lng_cost, shape_by_conn=False, units="USD/kg")

    def compute(self, inputs, outputs):
        # Call the cost model to compute costs
        cost_model = self.cost_model
        costs = cost_model.run_cost_model(
            inputs["plant_capacity_kgpy"],
            inputs["capex_factor"],
            inputs["lng"],
            inputs["lng_cost"],
        )
        (capex, opex) = costs

        outputs["CapEx"] = capex
        outputs["OpEx"] = opex


@define
class MethanolFinanceConfig(BaseConfig):
    conversion_tech: str = field()
    conversion_model: str = field()
    discount_rate: float = field()


class MethanolPlantFinanceModel(MethanolFinanceBaseClass):
    """
    An OpenMDAO component that computes the financials of an SMR methanol plant.
    """

    def setup(self):
        super().setup()
        self.config = MethanolFinanceConfig.from_dict(
            merge_shared_finance_inputs(self.options["tech_config"]["model_inputs"])
        )
        # Import finance model for specified tech and model
        tech = self.config.conversion_tech
        import_path = "h2integrate.simulation.technologies.methanol." + tech
        Finance = importlib.import_module(import_path).Finance
        self.finance_model = Finance()

    def compute(self, inputs, outputs):
        CAPEX = inputs["CapEx"]
        OPEX = inputs["OpEx"]
        kgph = inputs["methanol_production"]
        finance_model = self.finance_model
        outputs["LCOM"] = finance_model.run_finance_model(CAPEX, OPEX, kgph)
