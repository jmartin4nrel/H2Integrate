import numpy as np
import pandas as pd
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
        dec_table = [
            ["type", "len", "conn", "unit", "name"],
            ["in", 1, False, "kg/year", "plant_capacity"],
            ["in", 1, False, None, "capacity_factor"],
            ["in", 8760, False, "kW", "electricity"],
            ["in", 8760, False, "kg/h", "hydrogen"],
            ["in", 8760, False, "kg/h", "carbon_dioxide"],
            ["out", 8760, False, "kg/h", "methanol_production"],
            ["out", 1, False, "kg/year", "co2e_emissions"],
            ["out", 1, False, "kg/year", "h2o_consumption"],
        ]
        declarations = pd.DataFrame(dec_table[1:], columns=dec_table[0])

        for dec in declarations.itertuples():
            if dec.len == 1:
                value = 0.0
            else:
                value = np.zeros(dec.len)

            if dec.type == "in":
                self.add_input(dec.name, val=value, shape_by_conn=dec.conn, units=dec.unit)
            elif dec.type == "out":
                self.add_output(dec.name, val=value, shape_by_conn=dec.conn, units=dec.unit)

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
        self.add_output("CapEx", val=0.0, units="USD", desc="Total capital expenditures")
        self.add_output("OpEx", val=0.0, units="USD/year", desc="Total fixed operating costs")

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
        self.add_input("methanol_production", val=np.zeros(8760), units="kg/h")
        self.add_output("LCOM", val=0.0, units="USD/kg", desc="Levelized cost of methanol")

    def compute(self, inputs, outputs):
        """
        Computation for the OM component.

        For a template class this is not implement and raises an error.
        """

        raise NotImplementedError("This method should be implemented in a subclass.")
