import openmdao.api as om


class CablePerformanceModel(om.ExplicitComponent):
    """
    Pass-through cable with no losses.
    """

    def setup(self):
        self.add_input(
            "electricity_input",
            val=0.0,
            shape_by_conn=True,
            copy_shape="electricity_output",
            units="kW",
        )
        self.add_output(
            "electricity_output",
            val=0.0,
            shape_by_conn=True,
            copy_shape="electricity_input",
            units="kW",
        )

    def compute(self, inputs, outputs):
        outputs["electricity_output"] = inputs["electricity_input"]
