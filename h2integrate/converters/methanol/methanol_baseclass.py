import openmdao.api as om


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
            "hydrogen", val=0.0, shape_by_conn=False, units="kg/year"
            )
        self.add_output(
            "methanol", val=0.0, shape_by_conn=False, units="kg/year"
        )

    def compute(self, inputs, outputs):
        """
        Computation for the OM component.

        For a template class this is not implement and raises an error.
        """

        raise NotImplementedError("This method should be implemented in a subclass.")


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
        self.add_input("methanol", val=0.0, units="kg/year")
        self.add_output("LCOM", val=0.0, units="USD/kg", desc="Levelized cost of methanol")

    def compute(self, inputs, outputs):
        """
        Computation for the OM component.

        For a template class this is not implement and raises an error.
        """

        raise NotImplementedError("This method should be implemented in a subclass.")
