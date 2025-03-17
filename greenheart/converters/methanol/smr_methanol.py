from attrs import field, define

from greenheart.core.utilities import (
    BaseConfig,
    merge_shared_cost_inputs,
    merge_shared_performance_inputs,
)
from greenheart.converters.methanol.methanol_baseclass import (
    MethanolPerformanceBaseConfig,
    MethanolPerformanceBaseClass,
    MethanolCostBaseConfig,
    MethanolCostBaseClass,
    MethanolFinanceBaseClass,
)
from greenheart.simulation.technologies.methanol.smr import (
    run_performance_model,
    run_cost_model,
    run_finance_model,
)


@define
class MethanolPerformanceConfig(MethanolPerformanceBaseConfig):
    lng: float = field()
    lng_consumption: float = field()


class MethanolPerformanceModel(MethanolPerformanceBaseClass):
    """
    An OpenMDAO component that wraps the steam methane reforming (SMR) methanol model.
    Takes lng input and outputs methanol generation rates.
    """

    def setup(self):
        super().setup()
        self.config = MethanolPerformanceConfig.from_dict(
            merge_shared_performance_inputs(self.options["tech_config"]["model_inputs"])
        )
        self.add_input("lng", val=self.config.lng, shape_by_conn=False, units="kg/h")
        
    def compute(self, inputs, outputs):
        
        # Run the SMR methanol model using the input lng signal
        methanol_production_kgpy = run_performance_model(
            inputs["lng"],
            self.config.lng_consumption,
        )
        outputs["methanol"] = methanol_production_kgpy


@define
class MethanolCostConfig(MethanolCostBaseConfig):
    lng: float = field()
    lng_cost: float = field()


class MethanolCostModel(MethanolCostBaseClass):
    """
    An OpenMDAO component that computes the cost of an SMR methanol plant.
    """

    def setup(self):
        super().setup()
        self.config = MethanolCostConfig.from_dict(
            merge_shared_cost_inputs(self.options["tech_config"]["model_inputs"])
        )
        self.add_input("lng", val=self.config.lng, shape_by_conn=False, units="kg/h")

    def compute(self, inputs, outputs):
        
        # Call the cost model to compute costs
        costs = run_cost_model(
            inputs["plant_capacity_kgpy"],
            inputs["lng"],
            self.config.lng_cost,
            )
        (capex, opex) = costs

        outputs["CapEx"] = capex * 1.0e-6  # Convert to MUSD
        outputs["OpEx"] = opex * 1.0e-6  # Convert to MUSD


class MethanolFinanceModel(MethanolFinanceBaseClass):
    """
    Placeholder for the financial model of the methanol plant.
    """

    def compute(self, inputs, outputs):
        CAPEX = inputs["CapEX"]
        OPEX = inputs["OpEX"]
        kgpy = inputs["methanol"]
        outputs["LCOM"] = run_finance_model(CAPEX,OPEX,kgpy)
