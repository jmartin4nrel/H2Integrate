from h2integrate.converters.wind.wind_plant_baseclass import (
    WindCostBaseClass,
    WindPerformanceBaseClass,
)


class DummyPlantPerformance(WindPerformanceBaseClass):
    """
    A simple OpenMDAO component that represents a wind turbine.
    It takes in wind speed and outputs power.
    """

    def compute(self, inputs, outputs):
        tech_config = self.options["tech_config"]
        wind_speed = tech_config["resource"]["wind_speed"]

        # Simple power curve: P = 0.5 * Cp * rho * A * V^3
        Cp = 0.4  # Power coefficient
        rho = 1.225  # Air density in kg/m^3
        A = 10.0  # Swept area in m^2
        outputs["electricity"] = 0.5 * Cp * rho * A * wind_speed**3


class DummyPlantCost(WindCostBaseClass):
    """
    A simple OpenMDAO component that represents the costs of a wind turbine.
    """

    def compute(self, inputs, outputs):
        outputs["CapEx"] = 1000000.0
