import openmdao.api as om
from attrs import field, define

from greenheart.core.utilities import (
    BaseConfig,
    merge_shared_cost_inputs,
    merge_shared_performance_inputs,
)
from greenheart.simulation.technologies.methanol.smr import (
    run_performance_model,
    run_cost_model,
    run_finance_model
)


@define
class MethanolFeedstocksBase(BaseConfig):
    """
    Represents the costs and consumption rates of various feedstocks and resources
    used in methanol production.

    Attributes:
        electricity_consumption (float): MWh electricity used per kg methanol.
        hydrogen_consumption (float): kg hydrogen used per kg methanol.
        electricity_cost (float): Cost per MWh of electricity.
        hydrogen_cost (float): Cost per kg of hydrogen.
    """

    electricity_consumption: float = field()
    hydrogen_consumption: float = field()
    electricity_cost: float = field()
    hydrogen_cost: float = field()


@define
class MethanolPerformanceBaseConfig(BaseConfig):
    plant_capacity_kgpy: float = field()


class MethanolPerformanceBaseClass(om.ExplicitComponent):
    """
    An OpenMDAO component for modeling the performance of an ammonia plant.
    Computes annual ammonia production based on plant capacity and capacity factor.
    """

    def initialize(self):
        self.options.declare("plant_config", types=dict)
        self.options.declare("tech_config", types=dict)

    def setup(self):
        
        self.add_input(
            "electricity", val=0.0, shape_by_conn=False, units="kW"
        )
        self.add_input(
            "hydrogen", val=0.0, shape_by_conn=False, units="kg/h"
            )
        self.add_output(
            "methanol", val=0.0, shape_by_conn=False, units="kg/h"
        )

    def compute(self, inputs, outputs):
        """
        Computation for the OM component.

        For a template class this is not implement and raises an error.
        """

        raise NotImplementedError("This method should be implemented in a subclass.")


@define
class MethanolCostBaseConfig(BaseConfig):
    """
    Configuration inputs for the ammonia cost model, including plant capacity and
    feedstock details.

    Attributes:
        plant_capacity_kgpy (float): Annual production capacity of the plant in kg.
        plant_capacity_factor (float): The ratio of actual production to maximum
            possible production over a year.
        feedstocks (dict): A dictionary that is passed to the `Feedstocks` class detailing the
            costs and consumption rates of resources used in production.
    """

    plant_capacity_kgpy: float = field()


class MethanolCostBaseClass(om.ExplicitComponent):
    """
    An OpenMDAO component for calculating the costs associated with ammonia production.
    Includes CapEx, OpEx, and byproduct credits.
    """

    def initialize(self):
        self.options.declare("plant_config", types=dict)
        self.options.declare("tech_config", types=dict)

    def setup(self):
        # Inputs for cost model configuration
        self.add_input(
            "plant_capacity_kgpy", val=0.0, units="kg/year", desc="Annual plant capacity"
        )
        self.add_output(
            "CapEx", val=0.0, units="USD", desc="Total capital expenditures"
            )
        self.add_output(
            "OpEx", val=0.0, units="USD/year", desc="Total fixed operating costs"
            )

    def compute(self, inputs, outputs):
        """
        Computation for the OM component.

        For a template class this is not implement and raises an error.
        """

        raise NotImplementedError("This method should be implemented in a subclass.")


class MethanolFinanceBaseClass(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("plant_config", types=dict)
        self.options.declare("tech_config", types=dict)

    def setup(self):
        self.add_input("CapEx", val=0.0, units="USD")
        self.add_input("OpEx", val=0.0, units="USD/year")
        self.add_input("methanol", val=0.0, unit="kgpy")
        self.add_output("LCOM", val=0.0, units="USD", desc="Net present value")

    def compute(self, inputs, outputs):
        """
        Computation for the OM component.

        For a template class this is not implement and raises an error.
        """

        raise NotImplementedError("This method should be implemented in a subclass.")
