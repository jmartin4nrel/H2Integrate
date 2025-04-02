from __future__ import annotations

import numpy as np


class SMR_methanol:
    """
    Create an instance of a Steam Methane Reforming plant.
    """

    def __init__(
        self,
    ):
        pass

    def run_performance_model(self, lng: float, lng_consumption: float) -> float:
        """
        Calculates the annual methanol production in kilograms based on the lng input and the
        lng:methanol ratio

        Args:
            lng (float): The LNG supply to the plant in kg/y.
            lng_meoh_ratio (float): The mass ratio of LNG in to methanol out.

        Returns:
            float: The calculated annual ammonia production in kilograms per hour.
        """
        methanol_production_kgph = lng / lng_consumption / 8760

        return methanol_production_kgph


class SMR_methanol_cost:
    """
    Create an instance of a Steam Methane Reforming plant cost model.
    """

    def __init__(
        self,
        plant_capacity_kgpy,
    ):
        self.plant_capacity_kgpy = plant_capacity_kgpy

    def run_cost_model(
        self, plant_capacity_kgpy: float, capex_factor: float, lng: float, lng_cost: float
    ):
        """
        Calculates the various costs associated with methanol production, including
        capital expenditures (CapEx), operating expenditures (OpEx), and credits from
        byproducts, based on the provided configuration settings.

        Args:
            plant_capacity_kgpy (float): The maximum output capacity of methanol in kg/yr.
            capex_factor (float): The linear scaling of capex to plant capacity.
            lng (float): The LNG supply to the plant in kg/yr.
            lng_cost (float): The cost of LNG in USD/kg.

        Returns:
            capex (float): The capital expenses of methanol production in USD.
            opex (float): Operating expenses of methanol production in USD/yr.
        """
        capex = plant_capacity_kgpy * capex_factor
        opex = lng * lng_cost

        return capex, opex


class SMR_methanol_finance:
    """
    Create an instance of a Steam Methane Reforming plant cost model.
    """

    def __init__(
        self,
        capex,
        opex,
    ):
        self.capex = capex
        self.opex = opex

    def run_finance_model(self, capex: float, opex: float, kgph: float):
        """
        Simple financial model of an SMR methanol plant.

        Args:
            capex (float): capex in USD
            opex (float): opex in USD/yr
            kgph (array): methanol production in kg/hr

        Returns:
            lcom (float): Levelized cost of methanol in USD/kg
        """
        lcom = (capex * 0.07 + opex) / np.sum(kgph)

        return lcom
