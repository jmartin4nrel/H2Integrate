from h2integrate.converters.hydrogen.electrolyzer_baseclass import (
    ElectrolyzerCostBaseClass,
    ElectrolyzerPerformanceBaseClass,
)


class DummyElectrolyzerPerformanceModel(ElectrolyzerPerformanceBaseClass):
    def setup(self):
        super().setup()
        self.add_output(
            "oxygen", val=0.0, shape_by_conn=True, copy_shape="electricity", units="kg/s"
        )

    def compute(self, inputs, outputs):
        electricity = inputs["electricity"]

        # Simple model: assume 1 kW electricity produces 0.1 kg/s hydrogen and 0.8 kg/s oxygen
        outputs["hydrogen"] = 0.1 * electricity
        outputs["oxygen"] = 0.8 * electricity


class DummyElectrolyzerCostModel(ElectrolyzerCostBaseClass):
    def compute(self, inputs, outputs):
        outputs["CapEx"] = 1000000.0
