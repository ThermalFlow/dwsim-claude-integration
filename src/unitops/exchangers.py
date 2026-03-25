# -*- coding: utf-8 -*-
"""Heat Exchangers - HeatExchanger, Heater, Cooler."""

import logging
from enum import Enum
from typing import Any

from .base import UnitOperationBase

logger = logging.getLogger(__name__)


class HeatExchangerMode(Enum):
    """Calculation modes for a heat exchanger."""

    SPECIFY_UA = 0
    SPECIFY_OUTLET_TEMPS = 1
    SPECIFY_AREA = 2
    SPECIFY_COLD_OUTLET = 3
    SPECIFY_HOT_OUTLET = 4
    SPECIFY_DUTY = 5


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
            "duty_kW": getattr(self._obj, "Q", 0),
            "hot_inlet_temp_K": getattr(self._obj, "HotSideInletTemperature", 0),
            "hot_outlet_temp_K": getattr(self._obj, "HotSideOutletTemperature", 0),
            "cold_inlet_temp_K": getattr(self._obj, "ColdSideInletTemperature", 0),
            "cold_outlet_temp_K": getattr(self._obj, "ColdSideOutletTemperature", 0),
            "lmtd_K": getattr(self._obj, "LMTD", 0),
            "ua_W_K": getattr(self._obj, "OverallUA", 0),
            "effectiveness": getattr(self._obj, "ThermalEfficiency", 0),
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
        """Set the outlet temperature in K."""
        self.set_property("CalcMode", 0)  # Mode: outlet temperature
        return self.set_property("OutletTemperature", temperature_K)

    def set_duty(self, duty_kW: float) -> bool:
        """Set the heater duty in kW."""
        self.set_property("CalcMode", 1)  # Mode: duty
        return self.set_property("DeltaQ", duty_kW)

    def set_vapor_fraction(self, vf: float) -> bool:
        """Set the outlet vapor fraction.

        Args:
            vf: Vapor fraction (0-1).
        """
        self.set_property("CalcMode", 2)  # Mode: vapor fraction
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
            "duty_kW": getattr(self._obj, "DeltaQ", 0),
            "inlet_temperature_K": getattr(self._obj, "InletTemperature", 0),
            "outlet_temperature_K": getattr(self._obj, "OutletTemperature", 0),
            "pressure_drop_Pa": getattr(self._obj, "DeltaP", 0),
            "outlet_vapor_fraction": getattr(self._obj, "Vfrac", 0),
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
        """Set the outlet temperature in K."""
        self.set_property("CalcMode", 0)
        return self.set_property("OutletTemperature", temperature_K)

    def set_duty(self, duty_kW: float) -> bool:
        """Set the cooler duty in kW (positive value; stored as negative internally)."""
        self.set_property("CalcMode", 1)
        return self.set_property("DeltaQ", -abs(duty_kW))

    def set_vapor_fraction(self, vf: float) -> bool:
        """Set the outlet vapor fraction."""
        self.set_property("CalcMode", 2)
        return self.set_property("Vfrac", vf)

    def set_pressure_drop(self, delta_P_Pa: float) -> bool:
        """Set the pressure drop in Pa."""
        return self.set_property("DeltaP", delta_P_Pa)

    def get_results(self) -> dict:
        """Return cooler results after calculation."""
        if self._obj is None:
            return {}

        return {
            "duty_kW": getattr(self._obj, "DeltaQ", 0),
            "inlet_temperature_K": getattr(self._obj, "InletTemperature", 0),
            "outlet_temperature_K": getattr(self._obj, "OutletTemperature", 0),
            "pressure_drop_Pa": getattr(self._obj, "DeltaP", 0),
            "outlet_vapor_fraction": getattr(self._obj, "Vfrac", 0),
        }
