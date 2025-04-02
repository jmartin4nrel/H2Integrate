from attrs import field, define

from h2integrate.core.utilities import (
    BaseConfig,
    merge_shared_cost_inputs,
    merge_shared_performance_inputs,
)
from h2integrate.converters.methanol.methanol_baseclass import (
    MethanolPerformanceBaseClass,
    MethanolCostBaseClass,
    MethanolFinanceBaseClass,
)
from h2integrate.simulation.technologies.methanol.smr import (
    SMR_methanol,
    SMR_methanol_cost,
    SMR_methanol_finance,
)


@define
class MethanolPerformanceConfig(BaseConfig):
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
        self.methanol = SMR_methanol()
        self.add_input("lng", val=self.config.lng, shape_by_conn=False, units="kg/year")
        self.add_input(
            "lng_consumption",
            val=self.config.lng_consumption,
            shape_by_conn=False,
            units="kg/year"
        )

    def compute(self, inputs, outputs):
        
        # Run the SMR methanol model using the input lng signal
        methanol_production_kgpy = self.methanol.run_performance_model(
            inputs["lng"],
            inputs["lng_consumption"],
        )
        outputs["methanol"] = methanol_production_kgpy


@define
class MethanolCostConfig(BaseConfig):
    plant_capacity_kgpy: float = field()
    capex_factor: float = field()
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
        self.cost_model = SMR_methanol_cost(self.config.plant_capacity_kgpy)
        self.add_input(
            "plant_capacity_kgpy",
            val=self.config.plant_capacity_kgpy,
            shape_by_conn=False,
            units="kg/year"
        )
        self.add_input(
            "capex_factor",
            val=self.config.capex_factor,
            shape_by_conn=False,
            units="USD/kg/year"
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


class MethanolFinanceModel(MethanolFinanceBaseClass):
    """
    An OpenMDAO component that computes the financials of an SMR methanol plant.
    """

    def setup(self):
        super().setup()
        self.finance_model = SMR_methanol_finance(0,0)
        
    def compute(self, inputs, outputs):
        CAPEX = inputs["CapEx"]
        OPEX = inputs["OpEx"]
        kgpy = inputs["methanol"]
        finance_model = self.finance_model
        outputs["LCOM"] = finance_model.run_finance_model(CAPEX,OPEX,kgpy)
