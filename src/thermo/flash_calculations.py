# -*- coding: utf-8 -*-
"""Flash Calculations and Thermodynamic Equilibrium."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FlashType(Enum):
    """Flash calculation types."""

    PT = "PT"   # Pressure-Temperature
    PH = "PH"   # Pressure-Enthalpy
    PS = "PS"   # Pressure-Entropy
    PV = "PV"   # Pressure-Vapor Fraction
    TV = "TV"   # Temperature-Vapor Fraction
    TH = "TH"   # Temperature-Enthalpy


@dataclass
class FlashResult:
    """Result of a flash calculation."""

    success: bool
    temperature_K: float
    pressure_Pa: float
    vapor_fraction: float
    liquid_fraction: float
    enthalpy_kJ_kg: float
    entropy_kJ_kgK: float
    vapor_composition: dict[str, float]
    liquid_composition: dict[str, float]
    liquid2_composition: Optional[dict[str, float]] = None
    error_message: Optional[str] = None


@dataclass
class BubblePointResult:
    """Result of a bubble point calculation."""

    success: bool
    temperature_K: Optional[float] = None
    pressure_Pa: Optional[float] = None
    vapor_composition: Optional[dict[str, float]] = None
    error_message: Optional[str] = None


@dataclass
class DewPointResult:
    """Result of a dew point calculation."""

    success: bool
    temperature_K: Optional[float] = None
    pressure_Pa: Optional[float] = None
    liquid_composition: Optional[dict[str, float]] = None
    error_message: Optional[str] = None


class FlashCalculator:
    """Flash and phase equilibrium calculator."""

    def __init__(self, flowsheet: Any, automation: Any = None):
        """Initialize the calculator.

        Args:
            flowsheet: DWSIM Flowsheet object.
            automation: Automation3 instance (required to trigger flowsheet
                        recalculation via CalculateFlowsheet4). If omitted,
                        the flash methods will set conditions but cannot
                        trigger the solver automatically.
        """
        self._flowsheet = flowsheet
        self._automation = automation

    def pt_flash(
        self,
        stream: Any,
        temperature_K: float,
        pressure_Pa: float,
    ) -> FlashResult:
        """Run a PT flash (Pressure-Temperature specification).

        Sets T and P on the stream via SetPropertyValue, then triggers
        CalculateFlowsheet4 if the automation object is available.

        Args:
            stream: MaterialStream simulation object.
            temperature_K: Temperature in Kelvin.
            pressure_Pa: Pressure in Pascal.

        Returns:
            FlashResult with calculation results.
        """
        try:
            stream.SetPropertyValue("PROP_MS_0", float(temperature_K))
            stream.SetPropertyValue("PROP_MS_1", float(pressure_Pa))

            if self._automation is not None:
                self._automation.CalculateFlowsheet4(self._flowsheet)

            return self._extract_flash_results(stream)

        except Exception as e:
            logger.error(f"PT Flash failed: {e}")
            return FlashResult(
                success=False,
                temperature_K=temperature_K,
                pressure_Pa=pressure_Pa,
                vapor_fraction=0,
                liquid_fraction=0,
                enthalpy_kJ_kg=0,
                entropy_kJ_kgK=0,
                vapor_composition={},
                liquid_composition={},
                error_message=str(e),
            )

    def ph_flash(
        self,
        stream: Any,
        pressure_Pa: float,
        enthalpy_kJ_kg: float,
    ) -> FlashResult:
        """Run a PH flash (Pressure-Enthalpy specification).

        Args:
            stream: MaterialStream simulation object.
            pressure_Pa: Pressure in Pascal.
            enthalpy_kJ_kg: Enthalpy in kJ/kg.

        Returns:
            FlashResult with calculation results.
        """
        try:
            stream.SetPropertyValue("PROP_MS_1", float(pressure_Pa))
            stream.SetPropertyValue("PROP_MS_7", float(enthalpy_kJ_kg))

            if self._automation is not None:
                self._automation.CalculateFlowsheet4(self._flowsheet)

            return self._extract_flash_results(stream)

        except Exception as e:
            logger.error(f"PH Flash failed: {e}")
            return FlashResult(
                success=False,
                temperature_K=0,
                pressure_Pa=pressure_Pa,
                vapor_fraction=0,
                liquid_fraction=0,
                enthalpy_kJ_kg=enthalpy_kJ_kg,
                entropy_kJ_kgK=0,
                vapor_composition={},
                liquid_composition={},
                error_message=str(e),
            )

    def ps_flash(
        self,
        stream: Any,
        pressure_Pa: float,
        entropy_kJ_kgK: float,
    ) -> FlashResult:
        """Run a PS flash (Pressure-Entropy specification).

        Args:
            stream: MaterialStream simulation object.
            pressure_Pa: Pressure in Pascal.
            entropy_kJ_kgK: Entropy in kJ/kg.K.

        Returns:
            FlashResult with calculation results.
        """
        try:
            stream.SetPropertyValue("PROP_MS_1", float(pressure_Pa))
            stream.SetPropertyValue("PROP_MS_8", float(entropy_kJ_kgK))

            if self._automation is not None:
                self._automation.CalculateFlowsheet4(self._flowsheet)

            return self._extract_flash_results(stream)

        except Exception as e:
            logger.error(f"PS Flash failed: {e}")
            return FlashResult(
                success=False,
                temperature_K=0,
                pressure_Pa=pressure_Pa,
                vapor_fraction=0,
                liquid_fraction=0,
                enthalpy_kJ_kg=0,
                entropy_kJ_kgK=entropy_kJ_kgK,
                vapor_composition={},
                liquid_composition={},
                error_message=str(e),
            )

    def pv_flash(
        self,
        stream: Any,
        pressure_Pa: float,
        vapor_fraction: float,
    ) -> FlashResult:
        """Run a PV flash (Pressure-Vapor Fraction specification).

        Args:
            stream: MaterialStream simulation object.
            pressure_Pa: Pressure in Pascal.
            vapor_fraction: Molar vapor fraction (0-1).

        Returns:
            FlashResult with calculation results.
        """
        try:
            stream.SetPropertyValue("PROP_MS_1", float(pressure_Pa))
            stream.SetPropertyValue("PROP_MS_27", float(vapor_fraction))

            if self._automation is not None:
                self._automation.CalculateFlowsheet4(self._flowsheet)

            return self._extract_flash_results(stream)

        except Exception as e:
            logger.error(f"PV Flash failed: {e}")
            return FlashResult(
                success=False,
                temperature_K=0,
                pressure_Pa=pressure_Pa,
                vapor_fraction=vapor_fraction,
                liquid_fraction=1 - vapor_fraction,
                enthalpy_kJ_kg=0,
                entropy_kJ_kgK=0,
                vapor_composition={},
                liquid_composition={},
                error_message=str(e),
            )

    def bubble_point_pressure(
        self,
        stream: Any,
        temperature_K: float,
    ) -> BubblePointResult:
        """Calculate bubble point pressure.

        Args:
            stream: MaterialStream simulation object.
            temperature_K: Temperature in Kelvin.

        Returns:
            BubblePointResult object.
        """
        try:
            stream.SetPropertyValue("PROP_MS_0", float(temperature_K))
            stream.SetPropertyValue("PROP_MS_27", 0.0)  # specify bubble point (VF=0)

            if self._automation is not None:
                self._automation.CalculateFlowsheet4(self._flowsheet)

            result_p = float(stream.GetPropertyValue("PROP_MS_1"))
            return BubblePointResult(
                success=True,
                temperature_K=temperature_K,
                pressure_Pa=result_p,
                vapor_composition=self._get_phase_composition(stream, 2),
            )

        except Exception as e:
            logger.error(f"Bubble point calculation failed: {e}")
            return BubblePointResult(
                success=False,
                error_message=str(e),
            )

    def bubble_point_temperature(
        self,
        stream: Any,
        pressure_Pa: float,
    ) -> BubblePointResult:
        """Calculate bubble point temperature.

        Args:
            stream: MaterialStream simulation object.
            pressure_Pa: Pressure in Pascal.

        Returns:
            BubblePointResult object.
        """
        try:
            stream.SetPropertyValue("PROP_MS_1", float(pressure_Pa))
            stream.SetPropertyValue("PROP_MS_27", 0.0)  # specify bubble point (VF=0)

            if self._automation is not None:
                self._automation.CalculateFlowsheet4(self._flowsheet)

            result_t = float(stream.GetPropertyValue("PROP_MS_0"))
            return BubblePointResult(
                success=True,
                temperature_K=result_t,
                pressure_Pa=pressure_Pa,
                vapor_composition=self._get_phase_composition(stream, 2),
            )

        except Exception as e:
            logger.error(f"Bubble point calculation failed: {e}")
            return BubblePointResult(
                success=False,
                error_message=str(e),
            )

    def dew_point_pressure(
        self,
        stream: Any,
        temperature_K: float,
    ) -> DewPointResult:
        """Calculate dew point pressure.

        Args:
            stream: MaterialStream simulation object.
            temperature_K: Temperature in Kelvin.

        Returns:
            DewPointResult object.
        """
        try:
            stream.SetPropertyValue("PROP_MS_0", float(temperature_K))
            stream.SetPropertyValue("PROP_MS_27", 1.0)  # specify dew point (VF=1)

            if self._automation is not None:
                self._automation.CalculateFlowsheet4(self._flowsheet)

            result_p = float(stream.GetPropertyValue("PROP_MS_1"))
            return DewPointResult(
                success=True,
                temperature_K=temperature_K,
                pressure_Pa=result_p,
                liquid_composition=self._get_phase_composition(stream, 3),
            )

        except Exception as e:
            logger.error(f"Dew point calculation failed: {e}")
            return DewPointResult(
                success=False,
                error_message=str(e),
            )

    def dew_point_temperature(
        self,
        stream: Any,
        pressure_Pa: float,
    ) -> DewPointResult:
        """Calculate dew point temperature.

        Args:
            stream: MaterialStream simulation object.
            pressure_Pa: Pressure in Pascal.

        Returns:
            DewPointResult object.
        """
        try:
            stream.SetPropertyValue("PROP_MS_1", float(pressure_Pa))
            stream.SetPropertyValue("PROP_MS_27", 1.0)  # specify dew point (VF=1)

            if self._automation is not None:
                self._automation.CalculateFlowsheet4(self._flowsheet)

            result_t = float(stream.GetPropertyValue("PROP_MS_0"))
            return DewPointResult(
                success=True,
                temperature_K=result_t,
                pressure_Pa=pressure_Pa,
                liquid_composition=self._get_phase_composition(stream, 3),
            )

        except Exception as e:
            logger.error(f"Dew point calculation failed: {e}")
            return DewPointResult(
                success=False,
                error_message=str(e),
            )

    def _extract_flash_results(self, stream: Any) -> FlashResult:
        """Extract flash results from a calculated stream.

        Uses PROP_MS_* property codes for scalar values and .NET reflection
        for phase composition access.
        """
        try:
            vapor_comp = self._get_phase_composition(stream, 2)
            liquid_comp = self._get_phase_composition(stream, 3)

            # Check for second liquid phase
            liquid2_comp = None
            try:
                phases_prop = stream.GetType().GetProperty("Phases")
                if phases_prop is not None:
                    phases = phases_prop.GetValue(stream, None)
                    if len(phases) > 4:
                        liquid2_comp = self._get_phase_composition(stream, 4)
            except Exception:
                pass

            return FlashResult(
                success=True,
                temperature_K=float(stream.GetPropertyValue("PROP_MS_0")),
                pressure_Pa=float(stream.GetPropertyValue("PROP_MS_1")),
                vapor_fraction=float(stream.GetPropertyValue("PROP_MS_27")),
                liquid_fraction=1.0 - float(stream.GetPropertyValue("PROP_MS_27")),
                enthalpy_kJ_kg=float(stream.GetPropertyValue("PROP_MS_7")),
                entropy_kJ_kgK=float(stream.GetPropertyValue("PROP_MS_8")),
                vapor_composition=vapor_comp,
                liquid_composition=liquid_comp,
                liquid2_composition=liquid2_comp,
            )
        except Exception as e:
            logger.error(f"Failed to extract flash results: {e}")
            return FlashResult(
                success=False,
                temperature_K=0,
                pressure_Pa=0,
                vapor_fraction=0,
                liquid_fraction=0,
                enthalpy_kJ_kg=0,
                entropy_kJ_kgK=0,
                vapor_composition={},
                liquid_composition={},
                error_message=str(e),
            )

    def _get_phase_composition(self, stream: Any, phase_index: int) -> dict[str, float]:
        """Extract mole fractions for a phase via .NET reflection.

        Args:
            stream: MaterialStream simulation object.
            phase_index: Phase index (0=overall, 2=vapor, 3=liquid, 4=liquid2).

        Returns:
            Dictionary of {compound_name: mole_fraction}.
        """
        composition = {}
        try:
            phases_prop = stream.GetType().GetProperty("Phases")
            if phases_prop is None:
                return composition
            phases = phases_prop.GetValue(stream, None)
            phase = phases[phase_index]
            for comp_name, comp in phase.Compounds.items():
                try:
                    composition[str(comp_name)] = float(comp.MoleFraction)
                except Exception:
                    composition[str(comp_name)] = 0.0
        except Exception:
            pass
        return composition
