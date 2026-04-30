# -*- coding: utf-8 -*-
"""Heat Exchangers - HeatExchanger, Heater, Cooler."""

import logging
from enum import Enum
from typing import Any

from .base import UnitOperationBase

logger = logging.getLogger(__name__)


class HeatExchangerMode(Enum):
    """Calculation modes for a HeatExchanger (CalculationMode property).

    DWSIM enum mapping (confirmed from DWSIM source):
      0 = CalcTempHotOut  – specify cold-side outlet T, calculate hot-side outlet T
      1 = CalcTempColdOut – specify hot-side outlet T, calculate cold-side outlet T
      2 = CalcBothTemp    – specify UA; calculate both outlet temperatures
      3 = CalcBothTemp_UA – specify area + U; calculate both outlet temperatures
      4 = CalcArea        – specify duty or UA; calculate required area
      5 = (duty mode)     – specify duty directly
    """

    CALC_HOT_OUTLET  = 0  # specify cold outlet T → calc hot outlet T
    CALC_COLD_OUTLET = 1  # specify hot outlet T  → calc cold outlet T
    CALC_BOTH_TEMPS  = 2  # specify UA            → calc both outlet temps
    CALC_BOTH_UA     = 3  # specify area + U      → calc both outlet temps
    CALC_AREA        = 4  # specify duty/UA       → calc required area
    SPECIFY_DUTY     = 5  # specify duty directly


class HeatExchanger(UnitOperationBase):
    """Shell-and-tube heat exchanger."""

    DWSIM_TYPE = "HeatExchanger"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_calculation_mode(self, mode: HeatExchangerMode) -> bool:
        """Set the calculation mode.

        Args:
            mode: Desired calculation mode.
        """
        return self.set_property("CalculationMode", mode.value)

    def set_hot_side_outlet_temperature(self, temperature_K: float) -> bool:
        """Set the hot side outlet temperature in K."""
        return self.set_property("HotSideOutletTemperature", temperature_K)

    def set_cold_side_outlet_temperature(self, temperature_K: float) -> bool:
        """Set the cold side outlet temperature in K."""
        return self.set_property("ColdSideOutletTemperature", temperature_K)

    def set_duty(self, duty_kW: float) -> bool:
        """Set the exchanger duty in kW."""
        return self.set_property("Q", duty_kW)

    def set_ua(self, ua_W_K: float) -> bool:
        """Set the overall UA (overall heat transfer coefficient times area) in W/K."""
        return self.set_property("OverallUA", ua_W_K)

    def set_area(self, area_m2: float) -> bool:
        """Set the heat transfer area in m²."""
        return self.set_property("Area", area_m2)

    def set_pressure_drop_hot(self, delta_P_Pa: float) -> bool:
        """Set the hot side pressure drop in Pa."""
        return self.set_property("HotSidePressureDrop", delta_P_Pa)

    def set_pressure_drop_cold(self, delta_P_Pa: float) -> bool:
        """Set the cold side pressure drop in Pa."""
        return self.set_property("ColdSidePressureDrop", delta_P_Pa)

    def set_flow_direction(self, countercurrent: bool = True) -> bool:
        """Set the flow direction.

        Args:
            countercurrent: True for counter-current, False for co-current.
        """
        direction = 0 if countercurrent else 1
        return self.set_property("FlowDir", direction)

    def get_results(self) -> dict:
        """Return heat exchanger results after calculation."""
        if self._obj is None:
            return {}

        return {
            "duty_kW": self._read("Q"),
            "hot_inlet_temp_K": self._read("HotSideInletTemperature"),
            "hot_outlet_temp_K": self._read("HotSideOutletTemperature"),
            "cold_inlet_temp_K": self._read("ColdSideInletTemperature"),
            "cold_outlet_temp_K": self._read("ColdSideOutletTemperature"),
            "lmtd_K": self._read("LMTD"),
            "ua_W_K": self._read("OverallUA"),
            "effectiveness": self._read("ThermalEfficiency"),
        }


class Heater(UnitOperationBase):
    """Heater (heat source)."""

    DWSIM_TYPE = "Heater"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_outlet_temperature(self, temperature_K: float) -> bool:
        """Set the outlet temperature in K (CalcMode = OutletTemperature = 1)."""
        self._set_calc_mode(1)
        return self.set_property("OutletTemperature", temperature_K)

    def set_duty(self, duty_kW: float) -> bool:
        """Set the heater duty in kW (CalcMode = HeatAdded = 0)."""
        self._set_calc_mode(0)
        return self.set_property("DeltaQ", duty_kW)

    def set_vapor_fraction(self, vf: float) -> bool:
        """Set the outlet vapor fraction (CalcMode = OutletVaporFraction = 3).

        Args:
            vf: Vapor fraction (0-1).
        """
        self._set_calc_mode(3)
        return self.set_property("Vfrac", vf)

    def set_pressure_drop(self, delta_P_Pa: float) -> bool:
        """Set the pressure drop in Pa."""
        return self.set_property("DeltaP", delta_P_Pa)

    def set_efficiency(self, efficiency: float) -> bool:
        """Set the heater efficiency (0-1).

        Note: DWSIM stores this attribute as 'Eficiencia' (Portuguese) internally.
        """
        return self.set_property("Eficiencia", efficiency)

    def get_results(self) -> dict:
        """Return heater results after calculation."""
        if self._obj is None:
            return {}

        return {
            "duty_kW": self._read("DeltaQ"),
            "inlet_temperature_K": self._read("InletTemperature"),
            "outlet_temperature_K": self._read("OutletTemperature"),
            "pressure_drop_Pa": self._read("DeltaP"),
            "outlet_vapor_fraction": self._read("Vfrac"),
        }


class Cooler(UnitOperationBase):
    """Cooler (heat sink)."""

    DWSIM_TYPE = "Cooler"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_outlet_temperature(self, temperature_K: float) -> bool:
        """Set the outlet temperature in K (CalcMode = OutletTemperature = 1)."""
        self._set_calc_mode(1)
        return self.set_property("OutletTemperature", temperature_K)

    def set_duty(self, duty_kW: float) -> bool:
        """Set the cooler duty in kW — positive value; stored negative internally
        (CalcMode = HeatRemoved = 0)."""
        self._set_calc_mode(0)
        return self.set_property("DeltaQ", -abs(duty_kW))

    def set_vapor_fraction(self, vf: float) -> bool:
        """Set the outlet vapor fraction (CalcMode = OutletVaporFraction = 2)."""
        self._set_calc_mode(2)
        return self.set_property("Vfrac", vf)

    def set_pressure_drop(self, delta_P_Pa: float) -> bool:
        """Set the pressure drop in Pa."""
        return self.set_property("DeltaP", delta_P_Pa)

    def get_results(self) -> dict:
        """Return cooler results after calculation."""
        if self._obj is None:
            return {}

        return {
            "duty_kW": self._read("DeltaQ"),
            "inlet_temperature_K": self._read("InletTemperature"),
            "outlet_temperature_K": self._read("OutletTemperature"),
            "pressure_drop_Pa": self._read("DeltaP"),
            "outlet_vapor_fraction": self._read("Vfrac"),
        }
