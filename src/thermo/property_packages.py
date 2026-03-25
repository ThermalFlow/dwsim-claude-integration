# -*- coding: utf-8 -*-
"""Property Package mapping and management for DWSIM."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PropertyPackageCategory(Enum):
    """Property package categories."""

    EOS = "Equations of State"
    ACTIVITY = "Activity Coefficient Models"
    STEAM = "Steam/Water"
    SPECIAL = "Special Applications"
    COOLPROP = "CoolProp"


@dataclass
class PropertyPackage:
    """Information about a property package."""

    name: str
    dwsim_name: str
    category: PropertyPackageCategory
    description: str
    recommended_for: list[str]
    limitations: list[str]
    requires_parameters: bool = False


# Complete catalog of DWSIM's 31+ property packages
PROPERTY_PACKAGES: dict[str, PropertyPackage] = {
    # Equations of State
    "peng-robinson": PropertyPackage(
        name="Peng-Robinson",
        dwsim_name="Peng-Robinson (PR)",
        category=PropertyPackageCategory.EOS,
        description="Most widely used cubic EOS in industry. Good for hydrocarbons and gases.",
        recommended_for=["Hydrocarbons", "Natural gas", "Petroleum refining", "Nonpolar systems"],
        limitations=["Polar systems", "Aqueous systems"],
    ),
    "srk": PropertyPackage(
        name="Soave-Redlich-Kwong",
        dwsim_name="Soave-Redlich-Kwong (SRK)",
        category=PropertyPackageCategory.EOS,
        description="Classic cubic EOS. Similar to PR, slightly less accurate for liquids.",
        recommended_for=["Hydrocarbons", "Gases", "Petrochemical industry"],
        limitations=["Polar systems", "High pressure with polar compounds"],
    ),
    "prsv2": PropertyPackage(
        name="PRSV2",
        dwsim_name="Peng-Robinson-Stryjek-Vera 2 (PRSV2)",
        category=PropertyPackageCategory.EOS,
        description="Improved PR variant for polar compounds.",
        recommended_for=["Light polar compounds", "Alcohols", "Amines"],
        limitations=["Requires binary interaction parameters"],
        requires_parameters=True,
    ),
    "pr78": PropertyPackage(
        name="PR78",
        dwsim_name="Peng-Robinson 1978 (PR78)",
        category=PropertyPackageCategory.EOS,
        description="1978 PR revision with improvements for heavy compounds.",
        recommended_for=["Heavy hydrocarbons", "Petroleum"],
        limitations=["Polar systems"],
    ),
    "lee-kesler-plocker": PropertyPackage(
        name="Lee-Kesler-Plocker",
        dwsim_name="Lee-Kesler-Plocker",
        category=PropertyPackageCategory.EOS,
        description="Good for hydrocarbon and gas thermodynamic properties.",
        recommended_for=["Hydrocarbon thermodynamic properties", "LNG"],
        limitations=["Liquid-liquid equilibrium"],
    ),
    "grayson-streed": PropertyPackage(
        name="Grayson-Streed",
        dwsim_name="Grayson-Streed",
        category=PropertyPackageCategory.EOS,
        description="Specific to high-pressure hydrogen-containing systems.",
        recommended_for=["Hydrotreating", "Hydrogenation", "High-pressure H2 systems"],
        limitations=["Systems without H2"],
    ),
    "pc-saft": PropertyPackage(
        name="PC-SAFT",
        dwsim_name="PC-SAFT",
        category=PropertyPackageCategory.EOS,
        description="Advanced EOS based on statistical mechanics. Excellent for polymers.",
        recommended_for=["Polymers", "Associating molecules", "Complex compounds"],
        limitations=["Requires specific parameters"],
        requires_parameters=True,
    ),
    # Activity Coefficient Models
    "nrtl": PropertyPackage(
        name="NRTL",
        dwsim_name="NRTL",
        category=PropertyPackageCategory.ACTIVITY,
        description="Activity coefficient model for polar and non-ideal systems.",
        recommended_for=["Alcohol distillation", "Aqueous systems", "Polar mixtures", "LLE"],
        limitations=["Requires binary interaction parameters"],
        requires_parameters=True,
    ),
    "uniquac": PropertyPackage(
        name="UNIQUAC",
        dwsim_name="UNIQUAC",
        category=PropertyPackageCategory.ACTIVITY,
        description="Quasi-chemical model. Good for molecules of different sizes.",
        recommended_for=["Mixtures with size-asymmetric molecules", "LLE", "VLE"],
        limitations=["Requires binary interaction parameters"],
        requires_parameters=True,
    ),
    "unifac": PropertyPackage(
        name="UNIFAC",
        dwsim_name="UNIFAC",
        category=PropertyPackageCategory.ACTIVITY,
        description="Group contribution method. Does not require experimental data.",
        recommended_for=["Quick estimates", "Missing experimental data", "VLE"],
        limitations=["Less accurate than NRTL/UNIQUAC with fitted parameters"],
    ),
    "unifac-ll": PropertyPackage(
        name="UNIFAC-LL",
        dwsim_name="UNIFAC-LL",
        category=PropertyPackageCategory.ACTIVITY,
        description="UNIFAC optimized for liquid-liquid equilibrium.",
        recommended_for=["Liquid-liquid extraction", "LLE"],
        limitations=["Less accurate for VLE"],
    ),
    "modified-unifac-dortmund": PropertyPackage(
        name="Modified UNIFAC (Dortmund)",
        dwsim_name="Modified UNIFAC (Dortmund)",
        category=PropertyPackageCategory.ACTIVITY,
        description="Improved UNIFAC with updated parameters.",
        recommended_for=["General VLE", "Polar systems", "Estimates"],
        limitations=["Still based on group contributions"],
    ),
    "wilson": PropertyPackage(
        name="Wilson",
        dwsim_name="Wilson",
        category=PropertyPackageCategory.ACTIVITY,
        description="Simple model for completely miscible systems.",
        recommended_for=["VLE of miscible systems", "Distillation"],
        limitations=["Cannot model LLE"],
        requires_parameters=True,
    ),
    "margules": PropertyPackage(
        name="Margules",
        dwsim_name="Margules",
        category=PropertyPackageCategory.ACTIVITY,
        description="Simple empirical model.",
        recommended_for=["Simple systems", "Initial estimates"],
        limitations=["Low accuracy for complex systems"],
        requires_parameters=True,
    ),
    "van-laar": PropertyPackage(
        name="Van Laar",
        dwsim_name="Van Laar",
        category=PropertyPackageCategory.ACTIVITY,
        description="Classic empirical model.",
        recommended_for=["Simple binary systems"],
        limitations=["Does not work well for multicomponent systems"],
        requires_parameters=True,
    ),
    # Steam/Water
    "steam-tables": PropertyPackage(
        name="Steam Tables (IAPWS-IF97)",
        dwsim_name="Steam Tables (IAPWS-IF97)",
        category=PropertyPackageCategory.STEAM,
        description="IAPWS-IF97 steam tables. Industrial standard for water/steam.",
        recommended_for=["Steam cycles", "Boilers", "Turbines", "Pure water"],
        limitations=["Pure water only"],
    ),
    "steam-tables-iapws08": PropertyPackage(
        name="Steam Tables (IAPWS-08)",
        dwsim_name="IAPWS-08 Seawater",
        category=PropertyPackageCategory.STEAM,
        description="Steam tables for seawater.",
        recommended_for=["Desalination", "Processes with seawater"],
        limitations=["Seawater only"],
    ),
    # Special Applications
    "black-oil": PropertyPackage(
        name="Black Oil",
        dwsim_name="Black Oil",
        category=PropertyPackageCategory.SPECIAL,
        description="Simplified model for reservoir simulation.",
        recommended_for=["Oil production", "Reservoir simulation"],
        limitations=["Simplified model"],
    ),
    "sour-water": PropertyPackage(
        name="Sour Water",
        dwsim_name="Sour Water",
        category=PropertyPackageCategory.SPECIAL,
        description="For systems with H2S and NH3 in water.",
        recommended_for=["Sour water treatment", "Refining", "H2S/NH3/CO2 in water"],
        limitations=["System-specific"],
    ),
    "extended-nrtl": PropertyPackage(
        name="Extended NRTL",
        dwsim_name="Extended NRTL (Experiment)",
        category=PropertyPackageCategory.ACTIVITY,
        description="Extended NRTL for electrolytes.",
        recommended_for=["Electrolyte systems", "Ionic solutions"],
        limitations=["Experimental"],
        requires_parameters=True,
    ),
    "raoults-law": PropertyPackage(
        name="Raoult's Law",
        dwsim_name="Raoult's Law",
        category=PropertyPackageCategory.ACTIVITY,
        description="Raoult's Law for ideal solutions.",
        recommended_for=["Ideal solutions", "Quick estimates", "Teaching"],
        limitations=["Ideal systems only"],
    ),
    # CoolProp
    "coolprop": PropertyPackage(
        name="CoolProp",
        dwsim_name="CoolProp",
        category=PropertyPackageCategory.COOLPROP,
        description="CoolProp library interface. High accuracy for pure fluids.",
        recommended_for=["Refrigerants", "Pure fluids", "High accuracy"],
        limitations=["Only compounds supported by CoolProp"],
    ),
}


class PropertyPackageManager:
    """Property package manager."""

    def __init__(self, flowsheet: Any = None):
        """Initialize the manager.

        Args:
            flowsheet: DWSIM Flowsheet object (optional).
        """
        self._flowsheet = flowsheet

    @staticmethod
    def list_all() -> list[str]:
        """Return all available property package keys."""
        return list(PROPERTY_PACKAGES.keys())

    @staticmethod
    def get_info(name: str) -> Optional[PropertyPackage]:
        """Return information about a property package.

        Args:
            name: Property package key.

        Returns:
            PropertyPackage object, or None if not found.
        """
        return PROPERTY_PACKAGES.get(name.lower())

    @staticmethod
    def recommend_for_system(
        compounds: list[str],
        has_water: bool = False,
        has_polar: bool = False,
        has_electrolytes: bool = False,
        high_pressure: bool = False,
    ) -> list[str]:
        """Recommend property packages for a system.

        Args:
            compounds: List of compounds in the system.
            has_water: System contains water.
            has_polar: System contains polar compounds.
            has_electrolytes: System contains electrolytes.
            high_pressure: System at high pressure.

        Returns:
            List of recommended property package keys.
        """
        recommendations = []

        if has_electrolytes:
            recommendations.append("extended-nrtl")
            recommendations.append("sour-water")

        if has_polar or has_water:
            recommendations.append("nrtl")
            recommendations.append("uniquac")
            recommendations.append("unifac")

        if high_pressure and not has_polar:
            recommendations.append("peng-robinson")
            recommendations.append("srk")

        if not has_polar and not has_water:
            recommendations.append("peng-robinson")
            recommendations.append("srk")
            recommendations.append("lee-kesler-plocker")

        # Default fallback
        if not recommendations:
            recommendations = ["peng-robinson", "unifac"]

        return recommendations

    def set_property_package(self, name: str) -> bool:
        """Set the property package on the flowsheet.

        Args:
            name: Property package key (e.g. "peng-robinson").

        Returns:
            True if set successfully.
        """
        if self._flowsheet is None:
            logger.error("No flowsheet set on PropertyPackageManager")
            return False

        pp_info = PROPERTY_PACKAGES.get(name.lower())
        if pp_info is None:
            logger.error(f"Unknown property package: {name}")
            return False

        try:
            self._flowsheet.CreateAndAddPropertyPackage(pp_info.dwsim_name)
            logger.info(f"Set property package: {pp_info.dwsim_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set property package: {e}")
            return False

    @staticmethod
    def get_by_category(category: PropertyPackageCategory) -> list[str]:
        """Return property package keys for a given category.

        Args:
            category: Desired category.

        Returns:
            List of property package keys.
        """
        return [
            name
            for name, pp in PROPERTY_PACKAGES.items()
            if pp.category == category
        ]
