# -*- coding: utf-8 -*-
"""Mixers and Splitters - Mixer, Splitter, Recycle."""

import logging
from typing import Any

from .base import UnitOperationBase

logger = logging.getLogger(__name__)


class Mixer(UnitOperationBase):
    """Stream mixer."""

    DWSIM_TYPE = "Mixer"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_pressure_calculation(self, use_minimum: bool = True) -> bool:
        """Set the outlet pressure calculation method.

        Args:
            use_minimum: True to use the minimum of all inlet pressures,
                         False to use the average.
        """
        mode = 0 if use_minimum else 1
        return self.set_property("PressureCalculation", mode)

    def set_outlet_pressure(self, pressure_Pa: float) -> bool:
        """Set a fixed outlet pressure in Pa."""
        self.set_property("PressureCalculation", 2)  # User specified
        return self.set_property("OutletPressure", pressure_Pa)

    def get_results(self) -> dict:
        """Return mixer results after calculation."""
        if self._obj is None:
            return {}

        return {
            "outlet_temperature_K": getattr(self._obj, "OutletTemperature", 0),
            "outlet_pressure_Pa": getattr(self._obj, "OutletPressure", 0),
            "outlet_flow_mol_s": getattr(self._obj, "OutletMolarFlow", 0),
            "number_of_inlets": len(self._inlet_streams),
        }


class Splitter(UnitOperationBase):
    """Stream splitter."""

    DWSIM_TYPE = "Splitter"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)
        self._split_ratios: list[float] = []

    def set_split_ratios(self, ratios: list[float]) -> bool:
        """Set split fractions for each outlet stream.

        Args:
            ratios: List of fractions (must sum to 1.0).
        """
        if abs(sum(ratios) - 1.0) > 0.001:
            logger.warning("Split ratios should sum to 1.0")

        self._split_ratios = ratios

        if self._obj is None:
            return False

        try:
            for i, ratio in enumerate(ratios):
                self._obj.OutletMolarFlowFractions[i] = ratio
            return True
        except Exception as e:
            logger.error(f"Failed to set split ratios: {e}")
            return False

    def set_number_of_outlets(self, n: int) -> bool:
        """Set the number of outlet streams."""
        return self.set_property("NumberOfOutputStreams", n)

    def set_operation_mode(self, stream_ratio: bool = True) -> bool:
        """Set the operation mode.

        Args:
            stream_ratio: True for stream ratio mode, False to specify outlet flows.
        """
        mode = 0 if stream_ratio else 1
        return self.set_property("OperationMode", mode)

    def get_results(self) -> dict:
        """Return splitter results after calculation."""
        if self._obj is None:
            return {}

        return {
            "split_ratios": self._split_ratios.copy(),
            "number_of_outlets": len(self._outlet_streams),
            "inlet_flow_mol_s": getattr(self._obj, "InletMolarFlow", 0),
        }


class Recycle(UnitOperationBase):
    """Recycle convergence block for recycle loops."""

    DWSIM_TYPE = "Recycle"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_convergence_tolerance(
        self,
        temperature_K: float = 0.1,
        pressure_Pa: float = 100,
        flow_mol_s: float = 0.0001,
    ) -> bool:
        """Set convergence tolerances for temperature, pressure, and flow."""
        success = True
        success = success and self.set_property("TemperatureTolerance", temperature_K)
        success = success and self.set_property("PressureTolerance", pressure_Pa)
        success = success and self.set_property("MolarFlowTolerance", flow_mol_s)
        return success

    def set_acceleration_factor(self, factor: float) -> bool:
        """Set the Wegstein acceleration factor."""
        return self.set_property("AccelerationFactor", factor)

    def set_max_iterations(self, n: int) -> bool:
        """Set the maximum number of iterations."""
        return self.set_property("MaximumIterations", n)

    def get_results(self) -> dict:
        """Return recycle block results after calculation."""
        if self._obj is None:
            return {}

        return {
            "converged": self.is_calculated,
            "iterations": getattr(self._obj, "IterationCount", 0),
            "temperature_error_K": getattr(self._obj, "TemperatureError", 0),
            "pressure_error_Pa": getattr(self._obj, "PressureError", 0),
            "flow_error_mol_s": getattr(self._obj, "MolarFlowError", 0),
        }
