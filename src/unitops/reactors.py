# -*- coding: utf-8 -*-
"""Reactors - CSTR, PFR, Gibbs, Equilibrium."""

import logging
from typing import Any, Optional

from .base import UnitOperationBase

logger = logging.getLogger(__name__)


class CSTR(UnitOperationBase):
    """Continuous Stirred Tank Reactor (CSTR)."""

    DWSIM_TYPE = "RCT_CSTR"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)
        self._reactions: list[str] = []

    def set_volume(self, volume_m3: float) -> bool:
        """Set the reactor volume in m³."""
        return self.set_property("Volume", volume_m3)

    def set_operating_mode(self, isothermal: bool = True) -> bool:
        """Set the operating mode.

        Args:
            isothermal: True for isothermal, False for adiabatic.
        """
        mode = 0 if isothermal else 1
        return self.set_property("ReactorOperationMode", mode)

    def set_outlet_temperature(self, temperature_K: float) -> bool:
        """Set the outlet temperature in K (isothermal mode)."""
        return self.set_property("OutletTemperature", temperature_K)

    def add_reaction_set(self, reaction_set_name: str) -> bool:
        """Attach a reaction set to this reactor.

        Args:
            reaction_set_name: Name of the reaction set defined in the flowsheet.
        """
        if self._obj is None:
            return False

        try:
            self._obj.ReactionSetID = reaction_set_name
            self._reactions.append(reaction_set_name)
            logger.info(f"Added reaction set '{reaction_set_name}' to {self._name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add reaction set: {e}")
            return False

    def get_results(self) -> dict:
        """Return CSTR results after calculation."""
        if self._obj is None:
            return {}

        return {
            "duty_kW": getattr(self._obj, "DeltaQ", 0),
            "outlet_temperature_K": getattr(self._obj, "OutletTemperature", 0),
            "conversion": getattr(self._obj, "Conversions", {}),
            "residence_time_s": getattr(self._obj, "ResidenceTime", 0),
        }


class PFR(UnitOperationBase):
    """Plug Flow Reactor (PFR)."""

    DWSIM_TYPE = "RCT_PFR"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_volume(self, volume_m3: float) -> bool:
        """Set the reactor volume in m³."""
        return self.set_property("Volume", volume_m3)

    def set_length(self, length_m: float) -> bool:
        """Set the tube length in m."""
        return self.set_property("Length", length_m)

    def set_diameter(self, diameter_m: float) -> bool:
        """Set the tube internal diameter in m."""
        return self.set_property("Diameter", diameter_m)

    def set_segments(self, n_segments: int) -> bool:
        """Set the number of integration segments."""
        return self.set_property("NumberOfTubes", n_segments)

    def set_operating_mode(self, isothermal: bool = True) -> bool:
        """Set the operating mode.

        Args:
            isothermal: True for isothermal, False for adiabatic.
        """
        mode = 0 if isothermal else 1
        return self.set_property("ReactorOperationMode", mode)

    def add_reaction_set(self, reaction_set_name: str) -> bool:
        """Attach a reaction set to this reactor."""
        if self._obj is None:
            return False

        try:
            self._obj.ReactionSetID = reaction_set_name
            return True
        except Exception as e:
            logger.error(f"Failed to add reaction set: {e}")
            return False

    def get_results(self) -> dict:
        """Return PFR results after calculation."""
        if self._obj is None:
            return {}

        return {
            "duty_kW": getattr(self._obj, "DeltaQ", 0),
            "outlet_temperature_K": getattr(self._obj, "OutletTemperature", 0),
            "conversion": getattr(self._obj, "Conversions", {}),
            "pressure_drop_Pa": getattr(self._obj, "DeltaP", 0),
            "residence_time_s": getattr(self._obj, "ResidenceTime", 0),
        }


class GibbsReactor(UnitOperationBase):
    """Gibbs reactor (free energy minimization)."""

    DWSIM_TYPE = "RCT_Gibbs"

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
        return self.set_property("OutletTemperature", temperature_K)

    def set_outlet_pressure(self, pressure_Pa: float) -> bool:
        """Set the outlet pressure in Pa."""
        return self.set_property("OutletPressure", pressure_Pa)

    def set_pressure_drop(self, delta_P_Pa: float) -> bool:
        """Set the pressure drop in Pa."""
        return self.set_property("DeltaP", delta_P_Pa)

    def set_calculation_mode(self, isothermal: bool = False) -> bool:
        """Set the calculation mode.

        Args:
            isothermal: True for isothermal, False for adiabatic.
        """
        mode = 0 if isothermal else 1
        return self.set_property("ReactorOperationMode", mode)

    def get_results(self) -> dict:
        """Return Gibbs reactor results after calculation."""
        if self._obj is None:
            return {}

        return {
            "duty_kW": getattr(self._obj, "DeltaQ", 0),
            "outlet_temperature_K": getattr(self._obj, "OutletTemperature", 0),
            "equilibrium_composition": {},  # Extract from outlet stream
        }


class EquilibriumReactor(UnitOperationBase):
    """Equilibrium reactor (based on equilibrium constants)."""

    DWSIM_TYPE = "RCT_Equilibrium"

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
        return self.set_property("OutletTemperature", temperature_K)

    def set_pressure_drop(self, delta_P_Pa: float) -> bool:
        """Set the pressure drop in Pa."""
        return self.set_property("DeltaP", delta_P_Pa)

    def add_reaction_set(self, reaction_set_name: str) -> bool:
        """Attach an equilibrium reaction set to this reactor."""
        if self._obj is None:
            return False

        try:
            self._obj.ReactionSetID = reaction_set_name
            return True
        except Exception as e:
            logger.error(f"Failed to add reaction set: {e}")
            return False

    def get_results(self) -> dict:
        """Return equilibrium reactor results after calculation."""
        if self._obj is None:
            return {}

        return {
            "duty_kW": getattr(self._obj, "DeltaQ", 0),
            "outlet_temperature_K": getattr(self._obj, "OutletTemperature", 0),
            "equilibrium_constants": getattr(self._obj, "Keq", {}),
        }
