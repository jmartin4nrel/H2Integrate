import numpy as np
import openmdao.api as om


class FeedstockComponent(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("feedstocks_config", types=dict)

    def setup(self):
        self.feedstock_data = {}
        for feedstock_name, feedstock_data in self.options["feedstocks_config"].items():
            self.feedstock_data[feedstock_name] = feedstock_data
            self.add_output(feedstock_name, shape=(8760,), units=feedstock_data["capacity_units"])
            self.add_output(f"{feedstock_name}_CapEx", val=0.0, units="USD")
            self.add_output(f"{feedstock_name}_OpEx", val=0.0, units="USD/yr")

        # Add total CapEx and OpEx outputs
        self.add_output("CapEx", val=0.0, units="USD")
        self.add_output("OpEx", val=0.0, units="USD/yr")

    def compute(self, inputs, outputs):
        total_capex = 0.0
        total_opex = 0.0

        for feedstock_name, feedstock_data in self.feedstock_data.items():
            rated_capacity = feedstock_data["rated_capacity"]
            price = feedstock_data["price"]

            # Generate feedstock array operating at full capacity for the full year
            outputs[feedstock_name] = np.full(8760, rated_capacity)

            # Calculate capex (given as $0)
            capex = 0.0
            outputs[f"{feedstock_name}_CapEx"] = capex
            total_capex += capex

            # Calculate opex based on the cost of feedstock and total feedstock used
            total_feedstock_used = rated_capacity * 8760
            opex = total_feedstock_used * price
            outputs[f"{feedstock_name}_OpEx"] = opex
            total_opex += opex

        # Set total CapEx and OpEx
        outputs["CapEx"] = total_capex
        outputs["OpEx"] = total_opex
