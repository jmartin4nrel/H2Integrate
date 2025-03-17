from __future__ import annotations


def run_performance_model(lng: float, lng_meoh_ratio: float) -> float:
    """
    Calculates the annual methanol production in kilograms based on the lng input and the
    lng:methanol ratio

    Args:
        lng (float): The LNG supply to the plant in kg/y.
        lng_meoh_ratio (float): The mass ratio of LNG in to methanol out.

    Returns:
        float: The calculated annual ammonia production in kilograms per year.
    """
    methanol_production_kgpy = lng / lng_meoh_ratio

    return methanol_production_kgpy


def run_cost_model(plant_capacity_kgpy: float, lng: float, lng_cost: float):
    """
    Calculates the various costs associated with methanol production, including
    capital expenditures (CapEx), operating expenditures (OpEx), and credits from
    byproducts, based on the provided configuration settings.

    Args:
        plant_capacity_kgpy (float): The maximum output capacity of methanol in kg/yr.
        lng (float): The LNG supply to the plant in kg/y.
        lng_cost (float): The cost of LNG in USD/kg.

    Returns:
        capex (float): The capital expenses of methanol production in USD.
        opex (float): Operating expenses of methanol production in USD.
    """
    capex = plant_capacity_kgpy*1e3
    opex = lng*lng_cost

    return capex, opex


def run_finance_model(capex: float, opex: float, kgpy: float):
    """
    Simple financial model of an SMR methanol plant.

    Args:
        capex (float): capex in MUSD
        opex (float): opex in MUSD/yr
        kgpy (float): methanol production in kg/yr
        
    Returns:
        lcom (float): Levelized cost of methanol in USD/kg
    """
    lcom = (capex*.07+opex)/1e6/kgpy

    return lcom