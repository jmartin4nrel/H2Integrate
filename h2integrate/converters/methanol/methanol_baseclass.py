import numpy as np
import pandas as pd
import openmdao.api as om


class MethanolBaseClass(om.ExplicitComponent):
    """
    An OpenMDAO component for modeling a methanol plant.
    A base class used to further define Performance, Cost, and Finacnce components.
    """

    dec_table_inputs: list
    dec_table: pd.DataFrame
    values: dict

    def declare_from_table(self, add_dec_table_inputs=None, add_values=None):
        """
        Declare inputs/outputs from a table, either initialized with zeros or with values from dict
            - dec_table_inputs (list of lists): formatted table of inputs/outputs to declare
                                                see examples below for formatting
            - values (dict): optional dict of values to initialze inputs/outputs with
        """

        # Convert dec_table to dataframe for easy references
        dec_table = pd.DataFrame(self.dec_table_inputs[1:], columns=self.dec_table_inputs[0])
        if add_dec_table_inputs:
            add_dec_table = pd.DataFrame(add_dec_table_inputs[1:], columns=add_dec_table_inputs[0])
            dec_table = pd.concat([dec_table, add_dec_table])
        self.dec_table = dec_table

        # Combine any additional values from those already defined
        values = self.values
        if add_values:
            for key, value in add_values.items():
                values[key] = value
            self.values = values

        # Add each row of the dec_table as an input or output
        for dec in self.dec_table.itertuples():
            # If a value was given for the given input/output name, initialize with that value
            if dec.name in list(values.keys()):
                value = self.values[dec.name]
            # Otherwise initialize as zero(s)
            else:
                if dec.len == 1:
                    value = 0.0
                else:
                    value = np.zeros(int(dec.len))

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
        # Make table of all inputs and outputs to declare
        self.dec_table_inputs = [
            ["type", "len", "conn", "unit", "name"],
            ["in", 1, False, "kg/year", "plant_capacity_kgpy"],
            ["in", 1, False, None, "capacity_factor"],
            ["in", 1, False, "kg/kg", "co2e_emit_ratio"],
            ["in", 1, False, "kg/kg", "h2o_consume_ratio"],
            ["in", 1, False, "kg/kg", "h2_consume_ratio"],
            ["in", 1, False, "kg/kg", "co2_consume_ratio"],
            ["in", 1, False, "kW*h/kg", "elec_consume_ratio"],
            ["out", 8760, False, "kg/h", "methanol_production"],
            ["out", 8760, False, "kg/h", "co2e_emissions"],
            ["out", 8760, False, "kg/h", "h2o_consumption"],
            ["out", 8760, False, "kg/h", "h2_consumption"],
            ["out", 8760, False, "kg/h", "co2_consumption"],
            ["out", 8760, False, "kW*h/h", "elec_consumption"],
        ]
        # Define any non-zero default values
        self.values = {
            "plant_capacity_kgpy": 100000000.0,
            "capacity_factor": 0.85,
        }

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
        # Make table of all inputs and outputs to declare
        self.dec_table_inputs = [
            ["type", "len", "conn", "unit", "name"],
            ["in", 1, False, "USD/kg/year", "toc_kg_y"],  # total overnight capex slope
            ["in", 1, False, "USD/kg/year**2", "foc_kg_y^2"],  # fixed operating cost slope
            ["in", 1, False, "USD/kg", "voc_kg"],  # variable operating cost
            ["in", 1, False, "kg/year", "plant_capacity_kgpy"],
            ["in", 8760, False, "kg/h", "methanol_production"],
            ["out", 1, False, "USD", "CapEx"],
            ["out", 1, False, "USD/year", "OpEx"],
            ["out", 1, False, "USD/year", "Fixed_OpEx"],
            ["out", 1, False, "USD/year", "Variable_OpEx"],
        ]
        # Define any non-zero default values
        self.values = {
            "plant_capacity_kgpy": 100000000.0,
        }

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
        # Make table of all inputs and outputs to declare
        self.dec_table_inputs = [
            ["type", "len", "conn", "unit", "name"],
            ["in", 1, False, "USD", "CapEx"],
            ["in", 1, False, "USD/year", "OpEx"],
            ["in", 1, False, "USD/year", "Fixed_OpEx"],
            ["in", 1, False, "USD/year", "Variable_OpEx"],
            ["in", 1, False, None, "discount_rate"],
            ["in", 1, False, None, "tasc_toc_multiplier"],
            ["in", 8760, False, "kg/h", "methanol_production"],
            ["out", 1, False, "USD/kg", "LCOM"],  # Levelized cost of methanol (LCOM) - total system
            ["out", 1, False, "USD/kg", "LCOM_meoh"],  # LCOM - just methanol plant component
            ["out", 1, False, "USD/kg", "LCOM_meoh_capex"],  # just methanol plant capex
            ["out", 1, False, "USD/kg", "LCOM_meoh_fopex"],  # just methanol plant fixed opex
            ["out", 1, False, "USD/kg", "LCOM_meoh_vopex"],  # just methanol plant variable opex
        ]
        self.values = {
            "discount_rate": 0.0707,
            "tasc_toc_multiplier": 1.093,
        }

    def compute(self, inputs, outputs):
        """
        Computation for the OM component.

        For a template class this is not implement and raises an error.
        """

        raise NotImplementedError("This method should be implemented in a subclass.")
