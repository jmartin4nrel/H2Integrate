import openmdao.api as om


class PipePerformanceModel(om.ExplicitComponent):
    """
    Pass-through pipe with no losses.
    """

    def setup(self):
        self.add_input(
            "hydrogen_input",
            val=0.0,
            shape_by_conn=True,
            copy_shape="hydrogen_output",
            units="kg/s",
        )
        self.add_output(
            "hydrogen_output",
            val=0.0,
            shape_by_conn=True,
            copy_shape="hydrogen_input",
            units="kg/s",
        )

    def compute(self, inputs, outputs):
        outputs["hydrogen_output"] = inputs["hydrogen_input"]
