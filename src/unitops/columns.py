# -*- coding: utf-8 -*-
"""Distillation and Absorption Columns."""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from .base import UnitOperationBase

logger = logging.getLogger(__name__)


@dataclass
class ColumnStageSpec:
    """Specification for a single column stage."""

    stage: int
    pressure_Pa: Optional[float] = None
    efficiency: float = 1.0
    duty_kW: float = 0.0


class DistillationColumn(UnitOperationBase):
    """Rigorous distillation column."""

    DWSIM_TYPE = "DistillationColumn"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)
        self._n_stages: int = 10
        self._feed_stages: list[int] = []

    def set_number_of_stages(self, n: int) -> bool:
        """Set the number of theoretical stages.

        Args:
            n: Number of stages (including condenser and reboiler).
        """
        self._n_stages = n
        return self.set_property("NumberOfStages", n)

    def set_feed_stage(self, stage: int) -> bool:
        """Set the feed stage number.

        Args:
            stage: Stage number (1 = top).
        """
        self._feed_stages.append(stage)
        # Exact configuration depends on how the feed stream is connected
        return True

    def set_condenser_type(self, total: bool = True) -> bool:
        """Set the condenser type.

        Args:
            total: True for total condenser, False for partial.
        """
        cond_type = 0 if total else 1
        return self.set_property("CondenserType", cond_type)

    def set_condenser_pressure(self, pressure_Pa: float) -> bool:
        """Set the condenser pressure in Pa."""
        return self.set_property("CondenserPressure", pressure_Pa)

    def set_reboiler_pressure(self, pressure_Pa: float) -> bool:
        """Set the reboiler pressure in Pa."""
        return self.set_property("ReboilerPressure", pressure_Pa)

    def set_reflux_ratio(self, ratio: float) -> bool:
        """Set the reflux ratio (L/D)."""
        return self.set_property("RefluxRatio", ratio)

    def set_distillate_rate(self, rate_mol_s: float) -> bool:
        """Set the distillate molar flow rate in mol/s."""
        return self.set_property("DistillateFlowRate", rate_mol_s)

    def set_bottoms_rate(self, rate_mol_s: float) -> bool:
        """Set the bottoms molar flow rate in mol/s."""
        return self.set_property("BottomsFlowRate", rate_mol_s)

    def set_condenser_duty(self, duty_kW: float) -> bool:
        """Set the condenser duty in kW."""
        return self.set_property("CondenserDuty", duty_kW)

    def set_reboiler_duty(self, duty_kW: float) -> bool:
        """Set the reboiler duty in kW."""
        return self.set_property("ReboilerDuty", duty_kW)

    def set_max_iterations(self, n: int) -> bool:
        """Set the maximum number of solver iterations."""
        return self.set_property("MaxIterations", n)

    def set_convergence_tolerance(self, tol: float) -> bool:
        """Set the convergence tolerance."""
        return self.set_property("Tolerance", tol)

    def get_results(self) -> dict:
        """Return column results after calculation."""
        if self._obj is None:
            return {}

        return {
            "condenser_duty_kW": getattr(self._obj, "CondenserDuty", 0),
            "reboiler_duty_kW": getattr(self._obj, "ReboilerDuty", 0),
            "reflux_ratio": getattr(self._obj, "ActualRefluxRatio", 0),
            "number_of_stages": self._n_stages,
            "converged": self.is_calculated,
            "iterations": getattr(self._obj, "ic", 0),
        }

    def get_stage_profiles(self) -> dict:
        """Return temperature, pressure, and flow profiles per stage."""
        if self._obj is None:
            return {}

        profiles = {
            "temperature_K": [],
            "pressure_Pa": [],
            "vapor_flow_mol_s": [],
            "liquid_flow_mol_s": [],
        }

        try:
            for i in range(self._n_stages):
                stage = self._obj.Stages[i]
                profiles["temperature_K"].append(stage.T)
                profiles["pressure_Pa"].append(stage.P)
                profiles["vapor_flow_mol_s"].append(stage.V)
                profiles["liquid_flow_mol_s"].append(stage.L)
        except Exception as e:
            logger.warning(f"Could not extract stage profiles: {e}")

        return profiles


class AbsorptionColumn(UnitOperationBase):
    """Absorption column."""

    DWSIM_TYPE = "AbsorptionColumn"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_number_of_stages(self, n: int) -> bool:
        """Set the number of stages."""
        return self.set_property("NumberOfStages", n)

    def set_operating_pressure(self, pressure_Pa: float) -> bool:
        """Set the operating pressure in Pa."""
        return self.set_property("OperatingPressure", pressure_Pa)

    def set_temperature_profile(self, temperatures_K: list[float]) -> bool:
        """Set the temperature profile across stages.

        Args:
            temperatures_K: List of temperatures (K) for each stage.
        """
        if self._obj is None:
            return False

        try:
            for i, temp in enumerate(temperatures_K):
                self._obj.Stages[i].T = temp
            return True
        except Exception as e:
            logger.error(f"Failed to set temperature profile: {e}")
            return False

    def get_results(self) -> dict:
        """Return absorption column results after calculation."""
        if self._obj is None:
            return {}

        return {
            "number_of_stages": getattr(self._obj, "NumberOfStages", 0),
            "converged": self.is_calculated,
        }


class ShortcutColumn(UnitOperationBase):
    """Shortcut distillation column (Fenske-Underwood-Gilliland)."""

    DWSIM_TYPE = "ShortcutColumn"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        super().__init__(flowsheet, name, x, y)

    def set_light_key(self, compound: str, recovery: float) -> bool:
        """Set the light key component and its recovery fraction.

        Args:
            compound: Light key component name.
            recovery: Recovery fraction in the distillate (0-1).
        """
        if self._obj is None:
            return False

        try:
            self._obj.LightKey = compound
            self._obj.LightKeyRecovery = recovery
            return True
        except Exception as e:
            logger.error(f"Failed to set light key: {e}")
            return False

    def set_heavy_key(self, compound: str, recovery: float) -> bool:
        """Set the heavy key component and its recovery fraction.

        Args:
            compound: Heavy key component name.
            recovery: Recovery fraction in the bottoms (0-1).
        """
        if self._obj is None:
            return False

        try:
            self._obj.HeavyKey = compound
            self._obj.HeavyKeyRecovery = recovery
            return True
        except Exception as e:
            logger.error(f"Failed to set heavy key: {e}")
            return False

    def set_condenser_pressure(self, pressure_Pa: float) -> bool:
        """Set the condenser pressure in Pa."""
        return self.set_property("CondenserPressure", pressure_Pa)

    def set_reboiler_pressure(self, pressure_Pa: float) -> bool:
        """Set the reboiler pressure in Pa."""
        return self.set_property("ReboilerPressure", pressure_Pa)

    def set_reflux_ratio(self, ratio: float) -> bool:
        """Set the reflux ratio (or multiple of minimum)."""
        return self.set_property("RefluxRatio", ratio)

    def set_reflux_ratio_multiple(self, multiple: float) -> bool:
        """Set the reflux ratio as a multiple of the minimum (e.g. 1.2 = 1.2*Rmin)."""
        return self.set_property("RefluxRatioMult", multiple)

    def get_results(self) -> dict:
        """Return shortcut column results after calculation."""
        if self._obj is None:
            return {}

        return {
            "minimum_stages": getattr(self._obj, "Nmin", 0),
            "actual_stages": getattr(self._obj, "N", 0),
            "minimum_reflux_ratio": getattr(self._obj, "Rmin", 0),
            "actual_reflux_ratio": getattr(self._obj, "R", 0),
            "feed_stage": getattr(self._obj, "Nfeed", 0),
            "condenser_duty_kW": getattr(self._obj, "Qc", 0),
            "reboiler_duty_kW": getattr(self._obj, "Qr", 0),
        }
