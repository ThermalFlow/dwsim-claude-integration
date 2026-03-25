# -*- coding: utf-8 -*-
"""Pressure Equipment - Pump, Compressor, Expander, Valve."""

import logging
from enum import Enum
from typing import Any

from .base import UnitOperationBase

logger = logging.getLogger(__name__)


class PumpCalculationMode(Enum):
    """Calculation modes for a pump."""

    OUTLET_PRESSURE = 0
    DELTA_P = 1
    POWER = 2
    CURVES = 3


class Pump(UnitOperationBase):
    """Centrifugal pump."""

    DWSIM_TYPE = "Pump"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_calculation_mode(self, mode: PumpCalculationMode) -> bool:
        """Set the calculation mode."""
        return self.set_property("CalcMode", mode.value)

    def set_outlet_pressure(self, pressure_Pa: float) -> bool:
        """Set the outlet pressure in Pa."""
        self.set_calculation_mode(PumpCalculationMode.OUTLET_PRESSURE)
        return self.set_property("OutletPressure", pressure_Pa)

    def set_pressure_increase(self, delta_P_Pa: float) -> bool:
        """Set the pressure increase in Pa."""
        self.set_calculation_mode(PumpCalculationMode.DELTA_P)
        return self.set_property("DeltaP", delta_P_Pa)

    def set_power(self, power_kW: float) -> bool:
        """Set the shaft power consumption in kW."""
        self.set_calculation_mode(PumpCalculationMode.POWER)
        return self.set_property("DeltaQ", power_kW)

    def set_efficiency(self, efficiency: float) -> bool:
        """Set the pump efficiency (0-1).

        Note: DWSIM stores this attribute as 'Eficiencia' (Portuguese) internally.
        """
        return self.set_property("Eficiencia", efficiency)

    def get_results(self) -> dict:
        """Return pump results after calculation."""
        if self._obj is None:
            return {}

        return {
            "power_kW": getattr(self._obj, "DeltaQ", 0),
            "inlet_pressure_Pa": getattr(self._obj, "InletPressure", 0),
            "outlet_pressure_Pa": getattr(self._obj, "OutletPressure", 0),
            "delta_P_Pa": getattr(self._obj, "DeltaP", 0),
            "efficiency": getattr(self._obj, "Eficiencia", 0),
            "npsh_available_m": getattr(self._obj, "NPSHa", 0),
        }


class CompressorCalculationMode(Enum):
    """Calculation modes for a compressor."""

    OUTLET_PRESSURE = 0
    DELTA_P = 1
    POWER = 2
    POLYTROPIC_HEAD = 3


class Compressor(UnitOperationBase):
    """Gas compressor."""

    DWSIM_TYPE = "Compressor"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_calculation_mode(self, mode: CompressorCalculationMode) -> bool:
        """Set the calculation mode."""
        return self.set_property("CalcMode", mode.value)

    def set_outlet_pressure(self, pressure_Pa: float) -> bool:
        """Set the outlet pressure in Pa."""
        self.set_calculation_mode(CompressorCalculationMode.OUTLET_PRESSURE)
        return self.set_property("POut", pressure_Pa)

    def set_pressure_ratio(self, ratio: float) -> bool:
        """Set the compression ratio."""
        return self.set_property("PressureRatio", ratio)

    def set_power(self, power_kW: float) -> bool:
        """Set the shaft power consumption in kW."""
        self.set_calculation_mode(CompressorCalculationMode.POWER)
        return self.set_property("DeltaQ", power_kW)

    def set_adiabatic_efficiency(self, efficiency: float) -> bool:
        """Set the adiabatic (isentropic) efficiency (0-1)."""
        return self.set_property("AdiabaticEfficiency", efficiency)

    def set_polytropic_efficiency(self, efficiency: float) -> bool:
        """Set the polytropic efficiency (0-1)."""
        return self.set_property("PolytropicEfficiency", efficiency)

    def get_results(self) -> dict:
        """Return compressor results after calculation."""
        if self._obj is None:
            return {}

        return {
            "power_kW": getattr(self._obj, "DeltaQ", 0),
            "inlet_pressure_Pa": getattr(self._obj, "PIn", 0),
            "outlet_pressure_Pa": getattr(self._obj, "POut", 0),
            "pressure_ratio": getattr(self._obj, "PressureRatio", 0),
            "inlet_temperature_K": getattr(self._obj, "TIn", 0),
            "outlet_temperature_K": getattr(self._obj, "TOut", 0),
            "adiabatic_efficiency": getattr(self._obj, "AdiabaticEfficiency", 0),
            "polytropic_efficiency": getattr(self._obj, "PolytropicEfficiency", 0),
            "adiabatic_head_m": getattr(self._obj, "AdiabaticHead", 0),
            "polytropic_head_m": getattr(self._obj, "PolytropicHead", 0),
        }


class Expander(UnitOperationBase):
    """Expander / turbine."""

    DWSIM_TYPE = "Expander"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_outlet_pressure(self, pressure_Pa: float) -> bool:
        """Set the outlet pressure in Pa."""
        self.set_property("CalcMode", 0)
        return self.set_property("POut", pressure_Pa)

    def set_power_generated(self, power_kW: float) -> bool:
        """Set the shaft power generated in kW."""
        self.set_property("CalcMode", 2)
        return self.set_property("DeltaQ", power_kW)

    def set_adiabatic_efficiency(self, efficiency: float) -> bool:
        """Set the adiabatic efficiency (0-1)."""
        return self.set_property("AdiabaticEfficiency", efficiency)

    def get_results(self) -> dict:
        """Return expander results after calculation."""
        if self._obj is None:
            return {}

        return {
            "power_generated_kW": getattr(self._obj, "DeltaQ", 0),
            "inlet_pressure_Pa": getattr(self._obj, "PIn", 0),
            "outlet_pressure_Pa": getattr(self._obj, "POut", 0),
            "inlet_temperature_K": getattr(self._obj, "TIn", 0),
            "outlet_temperature_K": getattr(self._obj, "TOut", 0),
            "adiabatic_efficiency": getattr(self._obj, "AdiabaticEfficiency", 0),
        }


class Valve(UnitOperationBase):
    """Control valve."""

    DWSIM_TYPE = "Valve"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_outlet_pressure(self, pressure_Pa: float) -> bool:
        """Set the outlet pressure in Pa."""
        self.set_property("CalcMode", 0)
        return self.set_property("OutletPressure", pressure_Pa)

    def set_pressure_drop(self, delta_P_Pa: float) -> bool:
        """Set the pressure drop in Pa."""
        self.set_property("CalcMode", 1)
        return self.set_property("DeltaP", delta_P_Pa)

    def set_opening(self, opening: float) -> bool:
        """Set the valve opening percentage (0-100)."""
        return self.set_property("OpeningPct", opening)

    def set_cv(self, cv: float) -> bool:
        """Set the valve flow coefficient (Cv)."""
        return self.set_property("Cv", cv)

    def get_results(self) -> dict:
        """Return valve results after calculation."""
        if self._obj is None:
            return {}

        return {
            "inlet_pressure_Pa": getattr(self._obj, "InletPressure", 0),
            "outlet_pressure_Pa": getattr(self._obj, "OutletPressure", 0),
            "delta_P_Pa": getattr(self._obj, "DeltaP", 0),
            "inlet_temperature_K": getattr(self._obj, "InletTemperature", 0),
            "outlet_temperature_K": getattr(self._obj, "OutletTemperature", 0),
            "opening_pct": getattr(self._obj, "OpeningPct", 0),
        }
