from greenheart.transporters.pipe import PipePerformanceModel
from greenheart.transporters.cable import CablePerformanceModel
from greenheart.converters.steel.steel import SteelPerformanceModel, SteelCostAndFinancialModel
from greenheart.converters.wind.wind_plant import WindPlantCostModel, WindPlantPerformanceModel
from greenheart.transporters.power_combiner import CombinerPerformanceModel
from greenheart.converters.hopp.hopp_wrapper import HOPPComponent
from greenheart.converters.solar.solar_pysam import PYSAMSolarPlantPerformanceModel
from greenheart.storage.hydrogen.eco_storage import H2Storage
from greenheart.storage.hydrogen.tank_baseclass import (
    HydrogenTankCostModel,
    HydrogenTankPerformanceModel,
)
from greenheart.converters.wind.wind_plant_pysam import PYSAMWindPlantPerformanceModel
from greenheart.converters.wind.dummy_wind_turbine import DummyPlantCost, DummyPlantPerformance
from greenheart.converters.ammonia.ammonia_baseclass import (
    AmmoniaCostModel,
    AmmoniaPerformanceModel,
)
from greenheart.converters.desalination.desalination import (
    ReverseOsmosisCostModel,
    ReverseOsmosisPerformanceModel,
)
from greenheart.converters.hydrogen.pem_electrolyzer import (
    ElectrolyzerCostModel,
    ElectrolyzerFinanceModel,
    ElectrolyzerPerformanceModel,
)
from greenheart.converters.hydrogen.dummy_electrolyzer import (
    DummyElectrolyzerCostModel,
    DummyElectrolyzerPerformanceModel,
)
from greenheart.converters.hydrogen.eco_tools_pem_electrolyzer import (
    ECOElectrolyzerCostModel,
    ECOElectrolyzerPerformanceModel,
)
from greenheart.converters.methanol.smr_methanol import (
    MethanolPerformanceModel,
    MethanolCostModel,
    MethanolFinanceModel,
)


supported_models = {
    # Converters
    "dummy_wind_turbine_performance": DummyPlantPerformance,
    "dummy_wind_turbine_cost": DummyPlantCost,
    "dummy_electrolyzer_performance": DummyElectrolyzerPerformanceModel,
    "dummy_electrolyzer_cost": DummyElectrolyzerCostModel,
    "wind_plant_performance": WindPlantPerformanceModel,
    "wind_plant_cost": WindPlantCostModel,
    "pysam_wind_plant_performance": PYSAMWindPlantPerformanceModel,
    "pysam_solar_plant_performance": PYSAMSolarPlantPerformanceModel,
    "pem_electrolyzer_performance": ElectrolyzerPerformanceModel,
    "pem_electrolyzer_cost": ElectrolyzerCostModel,
    "pem_electrolyzer_financial": ElectrolyzerFinanceModel,
    "eco_pem_electrolyzer_performance": ECOElectrolyzerPerformanceModel,
    "eco_pem_electrolyzer_cost": ECOElectrolyzerCostModel,
    "h2_storage": H2Storage,
    "hopp": HOPPComponent,
    "reverse_osmosis_desalination_performance": ReverseOsmosisPerformanceModel,
    "reverse_osmosis_desalination_cost": ReverseOsmosisCostModel,
    "ammonia_performance": AmmoniaPerformanceModel,
    "ammonia_cost": AmmoniaCostModel,
    "steel_performance": SteelPerformanceModel,
    "steel_cost": SteelCostAndFinancialModel,
    # Transport
    "cable": CablePerformanceModel,
    "pipe": PipePerformanceModel,
    "combiner_performance": CombinerPerformanceModel,
    # Storage
    "hydrogen_tank_performance": HydrogenTankPerformanceModel,
    "hydrogen_tank_cost": HydrogenTankCostModel,
    "smr_methanol_performance": MethanolPerformanceModel,
    "smr_methanol_cost": MethanolCostModel,
    "smr_methanol_financial": MethanolFinanceModel,
}
