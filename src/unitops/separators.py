# -*- coding: utf-8 -*-
"""Separators - FlashSeparator, ComponentSeparator, Filter."""

import logging
from typing import Any

from .base import UnitOperationBase

logger = logging.getLogger(__name__)


class FlashSeparator(UnitOperationBase):
    """Flash vessel separator (vapor-liquid)."""

    DWSIM_TYPE = "Vessel"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_pressure(self, pressure_Pa: float) -> bool:
        """Set the operating pressure in Pa."""
        return self.set_property("FlashPressure", pressure_Pa)

    def set_temperature(self, temperature_K: float) -> bool:
        """Set the operating temperature in K."""
        return self.set_property("FlashTemperature", temperature_K)

    def set_pressure_drop(self, delta_P_Pa: float) -> bool:
        """Set the pressure drop in Pa."""
        return self.set_property("DeltaP", delta_P_Pa)

    def set_flash_type(self, adiabatic: bool = True) -> bool:
        """Set the flash calculation type.

        Args:
            adiabatic: True for adiabatic flash, False for isothermal.
        """
        flash_type = 0 if adiabatic else 1
        return self.set_property("FlashType", flash_type)

    def get_results(self) -> dict:
        """Return flash separator results after calculation."""
        if self._obj is None:
            return {}

        return {
            "vapor_fraction": getattr(self._obj, "VaporFraction", 0),
            "temperature_K": getattr(self._obj, "FlashTemperature", 0),
            "pressure_Pa": getattr(self._obj, "FlashPressure", 0),
            "duty_kW": getattr(self._obj, "DeltaQ", 0),
        }


class ComponentSeparator(UnitOperationBase):
    """Ideal component separator."""

    DWSIM_TYPE = "ComponentSeparator"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)
        self._split_fractions: dict[str, float] = {}

    def set_split_fraction(self, compound: str, fraction: float) -> bool:
        """Set the split fraction for a specific component.

        Args:
            compound: Component name.
            fraction: Fraction directed to outlet 1 (0-1).
        """
        if self._obj is None:
            return False

        try:
            self._split_fractions[compound] = fraction
            self._obj.SplitFactors[compound] = fraction
            logger.info(f"Set split fraction for {compound}: {fraction}")
            return True
        except Exception as e:
            logger.error(f"Failed to set split fraction: {e}")
            return False

    def set_split_fractions(self, fractions: dict[str, float]) -> bool:
        """Set split fractions for multiple components at once."""
        success = True
        for compound, fraction in fractions.items():
            if not self.set_split_fraction(compound, fraction):
                success = False
        return success

    def set_energy_stream(self, connected: bool = False) -> bool:
        """Specify whether an energy stream is connected."""
        return self.set_property("EnergyStreamConnected", connected)

    def get_results(self) -> dict:
        """Return component separator results after calculation."""
        if self._obj is None:
            return {}

        return {
            "split_fractions": self._split_fractions.copy(),
            "calculated": self.is_calculated,
        }


class Filter(UnitOperationBase):
    """Solid-liquid filter."""

    DWSIM_TYPE = "Filter"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_pressure_drop(self, delta_P_Pa: float) -> bool:
        """Set the pressure drop in Pa."""
        return self.set_property("DeltaP", delta_P_Pa)

    def set_solids_recovery(self, recovery: float) -> bool:
        """Set the solids recovery fraction (0-1)."""
        return self.set_property("SolidsRecovery", recovery)

    def get_results(self) -> dict:
        """Return filter results after calculation."""
        if self._obj is None:
            return {}

        return {
            "pressure_drop_Pa": getattr(self._obj, "DeltaP", 0),
            "solids_recovery": getattr(self._obj, "SolidsRecovery", 0),
        }
