# -*- coding: utf-8 -*-
"""Access to compound properties from the DWSIM database."""

import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CriticalProperties:
    """Critical properties of a compound."""

    critical_temperature_K: float
    critical_pressure_Pa: float
    critical_volume_m3_kmol: float
    acentric_factor: float
    critical_compressibility: float


@dataclass
class FormationProperties:
    """Formation properties of a compound."""

    enthalpy_of_formation_kJ_mol: float
    gibbs_energy_of_formation_kJ_mol: float
    entropy_of_formation_kJ_molK: float


@dataclass
class PhysicalProperties:
    """Physical properties of a compound."""

    molecular_weight: float
    normal_boiling_point_K: float
    normal_freezing_point_K: float
    density_kg_m3: Optional[float] = None
    liquid_viscosity_Pa_s: Optional[float] = None
    vapor_viscosity_Pa_s: Optional[float] = None
    liquid_thermal_conductivity_W_mK: Optional[float] = None
    vapor_thermal_conductivity_W_mK: Optional[float] = None


@dataclass
class CompoundInfo:
    """Complete information about a compound."""

    name: str
    cas_number: str
    formula: str
    critical: CriticalProperties
    formation: FormationProperties
    physical: PhysicalProperties
    is_ion: bool = False
    is_salt: bool = False
    is_hydrocarbon: bool = False


class CompoundDatabase:
    """DWSIM compound database interface."""

    def __init__(self, automation: Any = None):
        """Initialize the compound database.

        Args:
            automation: DWSIMAutomation instance (optional). When provided,
                        the full DWSIM compound list is available.
        """
        self._automation = automation
        self._cache: dict[str, CompoundInfo] = {}
        self._compound_list: Optional[list[str]] = None

    def search(self, query: str) -> list[str]:
        """Search compounds by name or formula.

        Args:
            query: Search term (case-insensitive substring match).

        Returns:
            List of matching compound names.
        """
        query_lower = query.lower()
        all_compounds = self.list_all()

        return [
            name
            for name in all_compounds
            if query_lower in name.lower()
        ]

    def list_all(self) -> list[str]:
        """Return all available compound names.

        Returns:
            List of compound names. Falls back to a common compound list
            if DWSIM is not connected.
        """
        if self._compound_list is not None:
            return self._compound_list

        if self._automation is None:
            return self._get_common_compounds()

        try:
            self._compound_list = self._automation.get_available_compounds()
            return self._compound_list
        except Exception as e:
            logger.warning(f"Could not load compound list: {e}")
            return self._get_common_compounds()

    def get_info(self, name: str) -> Optional[CompoundInfo]:
        """Return complete information about a compound.

        Args:
            name: Compound name.

        Returns:
            CompoundInfo object, or None if not found.
        """
        if name in self._cache:
            return self._cache[name]

        if self._automation is None:
            return self._get_builtin_compound_info(name)

        try:
            info = self._load_from_dwsim(name)
            if info:
                self._cache[name] = info
            return info
        except Exception as e:
            logger.error(f"Failed to get compound info for '{name}': {e}")
            return self._get_builtin_compound_info(name)

    def get_critical_properties(self, name: str) -> Optional[CriticalProperties]:
        """Return critical properties for a compound.

        Args:
            name: Compound name.

        Returns:
            CriticalProperties object, or None if not found.
        """
        info = self.get_info(name)
        return info.critical if info else None

    def get_formation_properties(self, name: str) -> Optional[FormationProperties]:
        """Return formation properties for a compound.

        Args:
            name: Compound name.

        Returns:
            FormationProperties object, or None if not found.
        """
        info = self.get_info(name)
        return info.formation if info else None

    def _load_from_dwsim(self, name: str) -> Optional[CompoundInfo]:
        """Load compound info from DWSIM (placeholder for DWSIM API call)."""
        return None

    def _get_builtin_compound_info(self, name: str) -> Optional[CompoundInfo]:
        """Return built-in data for common compounds."""
        builtin_data = {
            "Water": CompoundInfo(
                name="Water",
                cas_number="7732-18-5",
                formula="H2O",
                critical=CriticalProperties(
                    critical_temperature_K=647.14,
                    critical_pressure_Pa=22064000,
                    critical_volume_m3_kmol=0.0559,
                    acentric_factor=0.344,
                    critical_compressibility=0.229,
                ),
                formation=FormationProperties(
                    enthalpy_of_formation_kJ_mol=-285.83,
                    gibbs_energy_of_formation_kJ_mol=-237.14,
                    entropy_of_formation_kJ_molK=0.06991,
                ),
                physical=PhysicalProperties(
                    molecular_weight=18.015,
                    normal_boiling_point_K=373.15,
                    normal_freezing_point_K=273.15,
                    density_kg_m3=997,
                ),
            ),
            "Ethanol": CompoundInfo(
                name="Ethanol",
                cas_number="64-17-5",
                formula="C2H5OH",
                critical=CriticalProperties(
                    critical_temperature_K=513.92,
                    critical_pressure_Pa=6148000,
                    critical_volume_m3_kmol=0.167,
                    acentric_factor=0.644,
                    critical_compressibility=0.240,
                ),
                formation=FormationProperties(
                    enthalpy_of_formation_kJ_mol=-277.69,
                    gibbs_energy_of_formation_kJ_mol=-174.78,
                    entropy_of_formation_kJ_molK=0.1607,
                ),
                physical=PhysicalProperties(
                    molecular_weight=46.069,
                    normal_boiling_point_K=351.44,
                    normal_freezing_point_K=159.05,
                    density_kg_m3=789,
                ),
            ),
            "Methane": CompoundInfo(
                name="Methane",
                cas_number="74-82-8",
                formula="CH4",
                critical=CriticalProperties(
                    critical_temperature_K=190.56,
                    critical_pressure_Pa=4599000,
                    critical_volume_m3_kmol=0.0986,
                    acentric_factor=0.011,
                    critical_compressibility=0.286,
                ),
                formation=FormationProperties(
                    enthalpy_of_formation_kJ_mol=-74.52,
                    gibbs_energy_of_formation_kJ_mol=-50.49,
                    entropy_of_formation_kJ_molK=0.1862,
                ),
                physical=PhysicalProperties(
                    molecular_weight=16.043,
                    normal_boiling_point_K=111.66,
                    normal_freezing_point_K=90.69,
                ),
                is_hydrocarbon=True,
            ),
            "Nitrogen": CompoundInfo(
                name="Nitrogen",
                cas_number="7727-37-9",
                formula="N2",
                critical=CriticalProperties(
                    critical_temperature_K=126.19,
                    critical_pressure_Pa=3390000,
                    critical_volume_m3_kmol=0.0895,
                    acentric_factor=0.039,
                    critical_compressibility=0.289,
                ),
                formation=FormationProperties(
                    enthalpy_of_formation_kJ_mol=0.0,
                    gibbs_energy_of_formation_kJ_mol=0.0,
                    entropy_of_formation_kJ_molK=0.1915,
                ),
                physical=PhysicalProperties(
                    molecular_weight=28.014,
                    normal_boiling_point_K=77.35,
                    normal_freezing_point_K=63.15,
                ),
            ),
            "Oxygen": CompoundInfo(
                name="Oxygen",
                cas_number="7782-44-7",
                formula="O2",
                critical=CriticalProperties(
                    critical_temperature_K=154.58,
                    critical_pressure_Pa=5043000,
                    critical_volume_m3_kmol=0.0734,
                    acentric_factor=0.022,
                    critical_compressibility=0.288,
                ),
                formation=FormationProperties(
                    enthalpy_of_formation_kJ_mol=0.0,
                    gibbs_energy_of_formation_kJ_mol=0.0,
                    entropy_of_formation_kJ_molK=0.2050,
                ),
                physical=PhysicalProperties(
                    molecular_weight=31.999,
                    normal_boiling_point_K=90.19,
                    normal_freezing_point_K=54.36,
                ),
            ),
            "Carbon dioxide": CompoundInfo(
                name="Carbon dioxide",
                cas_number="124-38-9",
                formula="CO2",
                critical=CriticalProperties(
                    critical_temperature_K=304.13,
                    critical_pressure_Pa=7375000,
                    critical_volume_m3_kmol=0.0940,
                    acentric_factor=0.225,
                    critical_compressibility=0.274,
                ),
                formation=FormationProperties(
                    enthalpy_of_formation_kJ_mol=-393.51,
                    gibbs_energy_of_formation_kJ_mol=-394.36,
                    entropy_of_formation_kJ_molK=0.2136,
                ),
                physical=PhysicalProperties(
                    molecular_weight=44.010,
                    normal_boiling_point_K=194.65,
                    normal_freezing_point_K=216.55,
                ),
            ),
        }

        return builtin_data.get(name)

    def _get_common_compounds(self) -> list[str]:
        """Return a list of common compound names (offline fallback)."""
        return [
            "Water",
            "Ethanol",
            "Methanol",
            "Methane",
            "Ethane",
            "Propane",
            "n-Butane",
            "n-Pentane",
            "n-Hexane",
            "n-Heptane",
            "n-Octane",
            "Benzene",
            "Toluene",
            "Nitrogen",
            "Oxygen",
            "Carbon dioxide",
            "Hydrogen",
            "Ammonia",
            "Hydrogen sulfide",
            "Acetone",
            "Acetic acid",
        ]
