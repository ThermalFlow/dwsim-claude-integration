# -*- coding: utf-8 -*-
"""Pressure Equipment - Pump, Compressor, Expander, Valve."""

import logging
from enum import Enum
from typing import Any

from .base import UnitOperationBase

logger = logging.getLogger(__name__)


class PumpCalculationMode(Enum):
    """Calculation modes for a pump.

    DWSIM enum mapping (confirmed from testing):
      0 = Delta_P         – specify pressure rise (ΔP)
      1 = OutletPressure  – specify absolute outlet pressure
      2 = EnergyStream    – power driven by connected energy stream
      3 = Curves          – use pump performance curves
      4 = Power           – specify shaft power directly
    """

    DELTA_P         = 0
    OUTLET_PRESSURE = 1
    ENERGY_STREAM   = 2
    CURVES          = 3
    POWER           = 4


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
        return self._set_calc_mode(mode.value)

    def set_outlet_pressure(self, pressure_Pa: float) -> bool:
        """Set the outlet pressure in Pa (CalcMode = OUTLET_PRESSURE = 1)."""
        self._set_calc_mode(PumpCalculationMode.OUTLET_PRESSURE.value)
        return self.set_property("OutletPressure", pressure_Pa)

    def set_pressure_increase(self, delta_P_Pa: float) -> bool:
        """Set the pressure increase in Pa (CalcMode = DELTA_P = 0)."""
        self._set_calc_mode(PumpCalculationMode.DELTA_P.value)
        return self.set_property("DeltaP", delta_P_Pa)

    def set_power(self, power_kW: float) -> bool:
        """Set the shaft power consumption in kW (CalcMode = POWER = 4)."""
        self._set_calc_mode(PumpCalculationMode.POWER.value)
        return self.set_property("DeltaQ", power_kW)

    def set_efficiency(self, efficiency: float) -> bool:
        """Set the pump efficiency as a fraction (0–1).

        Note: DWSIM stores this attribute as 'Eficiencia' (Portuguese)
        in percent (0–100), so the value is multiplied by 100 before storing.
        """
        return self.set_property("Eficiencia", efficiency * 100.0)

    def get_results(self) -> dict:
        """Return pump results after calculation."""
        if self._obj is None:
            return {}

        return {
            "power_kW": self._read("DeltaQ"),
            "inlet_pressure_Pa": self._read("InletPressure"),
            "outlet_pressure_Pa": self._read("OutletPressure"),
            "delta_P_Pa": self._read("DeltaP"),
            "efficiency": self._read("Eficiencia"),
            "npsh_available_m": self._read("NPSHa"),
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
        return self._set_calc_mode(mode.value)

    def set_outlet_pressure(self, pressure_Pa: float) -> bool:
        """Set the outlet pressure in Pa."""
        self._set_calc_mode(CompressorCalculationMode.OUTLET_PRESSURE.value)
        return self.set_property("POut", pressure_Pa)

    def set_pressure_ratio(self, ratio: float) -> bool:
        """Set the compression ratio."""
        return self.set_property("PressureRatio", ratio)

    def set_power(self, power_kW: float) -> bool:
        """Set the shaft power consumption in kW."""
        self._set_calc_mode(CompressorCalculationMode.POWER.value)
        return self.set_property("DeltaQ", power_kW)

    def set_adiabatic_efficiency(self, efficiency: float) -> bool:
        """Set the adiabatic (isentropic) efficiency as a fraction (0–1).

        DWSIM stores this in percent (0–100) internally.
        """
        return self.set_property("AdiabaticEfficiency", efficiency * 100.0)

    def set_polytropic_efficiency(self, efficiency: float) -> bool:
        """Set the polytropic efficiency as a fraction (0–1).

        DWSIM stores this in percent (0–100) internally.
        """
        return self.set_property("PolytropicEfficiency", efficiency * 100.0)

    def get_results(self) -> dict:
        """Return compressor results after calculation."""
        if self._obj is None:
            return {}

        return {
            "power_kW": self._read("DeltaQ"),
            "inlet_pressure_Pa": self._read("PIn"),
            "outlet_pressure_Pa": self._read("POut"),
            "pressure_ratio": self._read("PressureRatio"),
            "inlet_temperature_K": self._read("TIn"),
            "outlet_temperature_K": self._read("TOut"),
            "adiabatic_efficiency": self._read("AdiabaticEfficiency"),
            "polytropic_efficiency": self._read("PolytropicEfficiency"),
            "adiabatic_head_m": self._read("AdiabaticHead"),
            "polytropic_head_m": self._read("PolytropicHead"),
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
        """Set the adiabatic efficiency as a fraction (0–1).

        DWSIM stores this in percent (0–100) internally.
        """
        return self.set_property("AdiabaticEfficiency", efficiency * 100.0)

    def get_results(self) -> dict:
        """Return expander results after calculation."""
        if self._obj is None:
            return {}

        return {
            "power_generated_kW": self._read("DeltaQ"),
            "inlet_pressure_Pa": self._read("PIn"),
            "outlet_pressure_Pa": self._read("POut"),
            "inlet_temperature_K": self._read("TIn"),
            "outlet_temperature_K": self._read("TOut"),
            "adiabatic_efficiency": self._read("AdiabaticEfficiency"),
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
            "inlet_pressure_Pa": self._read("InletPressure"),
            "outlet_pressure_Pa": self._read("OutletPressure"),
            "delta_P_Pa": self._read("DeltaP"),
            "inlet_temperature_K": self._read("InletTemperature"),
            "outlet_temperature_K": self._read("OutletTemperature"),
            "opening_pct": self._read("OpeningPct"),
        }
