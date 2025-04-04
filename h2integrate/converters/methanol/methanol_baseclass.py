import numpy as np
import pandas as pd
import openmdao.api as om


class MethanolBaseClass(om.ExplicitComponent):
    """
    An OpenMDAO component for modeling a methanol plant.
    A base class used to further define Performance, Cost, and Finacnce components.
    """

    def declare_from_table(self, dec_table, values={}):
        """
        Declare inputs/outputs from a table, either initialized with zeros or with values from dict
            - dec_table (list of lists or Path): formatted table of inputs/outputs to declare
                if list of lists, see examples below for formatting
            - values (dict): optional dict of values to initialze inputs/outputs with
        """

        # Convert dec_table to dataframe for easy references
        declarations = pd.DataFrame(dec_table[1:], columns=dec_table[0])

        # Add each row of the dec_table as an input or output
        for dec in declarations.itertuples():
            # If a value was given for the given input/output name, initialize with that value
            if dec.name in list(values.keys()):
                value = values[dec.name]
            # Otherwise initialize as zero(s)
            else:
                if dec.len == 1:
                    value = 0.0
                else:
                    value = np.zeros(dec.len)

            # Add inputs/outputs to OpenMDAO component
            if dec.type == "in":
                self.add_input(dec.name, val=value, shape_by_conn=dec.conn, units=dec.unit)
            elif dec.type == "out":
                self.add_output(dec.name, val=value, shape_by_conn=dec.conn, units=dec.unit)


class MethanolPerformanceBaseClass(MethanolBaseClass):
    """
    An OpenMDAO component for modeling the performance of a methanol plant.
    Computes annual methanol production based on plant capacity and capacity factor.
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
        self.declare_from_table(dec_table)

    def compute(self, inputs, outputs):
        """
        Computation for the OM component.

        For a template class this is not implemented and raises an error.
        """

        raise NotImplementedError("This method should be implemented in a subclass.")


class MethanolCostBaseClass(MethanolBaseClass):
    """
    An OpenMDAO component for calculating the costs associated with ammonia production.
    Includes CapEx, OpEx, and byproduct credits.
    """

    def initialize(self):
        self.options.declare("plant_config", types=dict)
        self.options.declare("tech_config", types=dict)

    def setup(self):
        # Inputs for cost model configuration
        dec_table = [
            ["type", "len", "conn", "unit", "name"],
            ["out", 1, False, "USD", "CapEx"],
            ["out", 1, False, "USD/year", "OpEx"],
        ]
        self.declare_from_table(dec_table)

    def compute(self, inputs, outputs):
        """
        Computation for the OM component.

        For a template class this is not implement and raises an error.
        """

        raise NotImplementedError("This method should be implemented in a subclass.")


class MethanolFinanceBaseClass(MethanolBaseClass):
    def initialize(self):
        self.options.declare("plant_config", types=dict)
        self.options.declare("tech_config", types=dict)

    def setup(self):
        dec_table = [
            ["type", "len", "conn", "unit", "name"],
            ["in", 1, False, "USD", "CapEx"],
            ["in", 1, False, "USD/year", "OpEx"],
            ["in", 8760, False, "kg/h", "methanol_production"],
            ["out", 1, False, "USD/kg", "LCOM"],  # Levelized cost of methanol
        ]
        self.declare_from_table(dec_table)

    def compute(self, inputs, outputs):
        """
        Computation for the OM component.

        For a template class this is not implement and raises an error.
        """

        raise NotImplementedError("This method should be implemented in a subclass.")
