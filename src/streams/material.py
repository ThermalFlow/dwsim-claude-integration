# -*- coding: utf-8 -*-
"""Material Stream - DWSIM material streams."""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MaterialStream:
    """Represents a material stream in DWSIM."""

    DWSIM_TYPE = "MaterialStream"

    # PROP_MS_* property codes for SetPropertyValue / GetPropertyValue
    _PROP_T = "PROP_MS_0"    # Temperature (K)
    _PROP_P = "PROP_MS_1"    # Pressure (Pa)
    _PROP_F = "PROP_MS_2"    # Molar flow (mol/s)
    _PROP_M = "PROP_MS_3"    # Mass flow (kg/s)
    _PROP_V = "PROP_MS_4"    # Volumetric flow (m3/s)
    _PROP_H = "PROP_MS_7"    # Enthalpy (kJ/kg)
    _PROP_S = "PROP_MS_8"    # Entropy (kJ/kg.K)
    _PROP_VF = "PROP_MS_27"  # Vapor fraction

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        """Initialize the material stream.

        Args:
            flowsheet: DWSIM Flowsheet object.
            name: Stream name/tag.
            x: X position in the diagram.
            y: Y position in the diagram.
        """
        self._flowsheet = flowsheet
        self._name = name
        self._x = x
        self._y = y
        self._obj: Optional[Any] = None

    @property
    def name(self) -> str:
        """Return stream name/tag."""
        return self._name

    @property
    def dwsim_object(self) -> Optional[Any]:
        """Return the underlying DWSIM simulation object."""
        return self._obj

    def create(self) -> bool:
        """Create the stream in the flowsheet.

        Uses the ObjectType enum (not a string) as required by DWSIM's
        AddObject API, then resolves the returned GraphicObject reference
        to the actual ISimulationObject.
        """
        try:
            # ObjectType is a .NET enum; import lazily after DLLs are loaded
            from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType
            obj_type_enum = getattr(ObjectType, self.DWSIM_TYPE)
            ref = self._flowsheet.AddObject(obj_type_enum, self._x, self._y, self._name)
            # AddObject returns a GraphicObject; resolve to the simulation object
            self._obj = self._flowsheet.SimulationObjects[ref.Name]
            logger.info(f"Created MaterialStream '{self._name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to create stream '{self._name}': {e}")
            return False

    def set_conditions(
        self,
        temperature_K: float,
        pressure_Pa: float,
        molar_flow_mol_s: float,
        composition: dict[str, float],
    ) -> bool:
        """Set all stream conditions in one call.

        This is the recommended way to configure a stream before calculation.
        Sets T, P, molar flow, and mole fraction composition.

        Args:
            temperature_K: Temperature in Kelvin.
            pressure_Pa: Pressure in Pascal.
            molar_flow_mol_s: Total molar flow in mol/s.
            composition: Mole fractions {compound_name: fraction}.
                         Fractions must sum to 1.0.

        Returns:
            True if all conditions were set successfully.
        """
        ok = True
        ok = self.set_temperature(temperature_K) and ok
        ok = self.set_pressure(pressure_Pa) and ok
        ok = self.set_molar_flow(molar_flow_mol_s) and ok
        ok = self.set_composition(composition) and ok
        return ok

    def set_temperature(self, temperature_K: float) -> bool:
        """Set stream temperature.

        Args:
            temperature_K: Temperature in Kelvin.
        """
        if self._obj is None:
            return False
        try:
            self._obj.SetPropertyValue(self._PROP_T, float(temperature_K))
            return True
        except Exception as e:
            logger.error(f"Failed to set temperature: {e}")
            return False

    def set_pressure(self, pressure_Pa: float) -> bool:
        """Set stream pressure.

        Args:
            pressure_Pa: Pressure in Pascal.
        """
        if self._obj is None:
            return False
        try:
            self._obj.SetPropertyValue(self._PROP_P, float(pressure_Pa))
            return True
        except Exception as e:
            logger.error(f"Failed to set pressure: {e}")
            return False

    def set_molar_flow(self, flow_mol_s: float) -> bool:
        """Set stream molar flow rate.

        Args:
            flow_mol_s: Molar flow rate in mol/s.
        """
        if self._obj is None:
            return False
        try:
            self._obj.SetPropertyValue(self._PROP_F, float(flow_mol_s))
            return True
        except Exception as e:
            logger.error(f"Failed to set molar flow: {e}")
            return False

    def set_mass_flow(self, flow_kg_s: float) -> bool:
        """Set stream mass flow rate.

        Args:
            flow_kg_s: Mass flow rate in kg/s.
        """
        if self._obj is None:
            return False
        try:
            self._obj.SetPropertyValue(self._PROP_M, float(flow_kg_s))
            return True
        except Exception as e:
            logger.error(f"Failed to set mass flow: {e}")
            return False

    def set_volumetric_flow(self, flow_m3_s: float) -> bool:
        """Set stream volumetric flow rate.

        Args:
            flow_m3_s: Volumetric flow rate in m3/s.
        """
        if self._obj is None:
            return False
        try:
            self._obj.SetPropertyValue(self._PROP_V, float(flow_m3_s))
            return True
        except Exception as e:
            logger.error(f"Failed to set volumetric flow: {e}")
            return False

    def set_composition(
        self,
        composition: dict[str, float],
        basis: str = "molar",
    ) -> bool:
        """Set stream composition.

        Builds the composition array in flowsheet compound order and passes
        it via SetOverallComposition (molar) or SetOverallMassComposition
        (mass), using .NET reflection since the stream is ISimulationObject.

        Args:
            composition: {compound_name: fraction} dictionary.
            basis: "molar" (default) or "mass".

        Returns:
            True if composition was set successfully.
        """
        if self._obj is None:
            return False

        try:
            # Build array in flowsheet compound order
            selected_order = [c.Name for c in self._flowsheet.SelectedCompounds.Values]
            fractions = [composition.get(name, 0.0) for name in selected_order]

            # SetOverallComposition requires .NET Array types; import lazily
            from System import Array, Double, Object

            method_name = (
                "SetOverallComposition" if basis == "molar"
                else "SetOverallMassComposition"
            )
            method = self._obj.GetType().GetMethod(method_name)
            if method is None:
                logger.error(f"Method {method_name} not found on stream object")
                return False

            method.Invoke(self._obj, Array[Object]([Array[Double](fractions)]))
            return True

        except Exception as e:
            logger.error(f"Failed to set composition: {e}")
            return False

    def set_molar_composition(self, composition: dict[str, float]) -> bool:
        """Set molar composition."""
        return self.set_composition(composition, "molar")

    def set_mass_composition(self, composition: dict[str, float]) -> bool:
        """Set mass composition."""
        return self.set_composition(composition, "mass")

    def set_vapor_fraction(self, vf: float) -> bool:
        """Set vapor fraction (for PV/TV flash specifications).

        Args:
            vf: Vapor fraction (0.0 = bubble point, 1.0 = dew point).
        """
        if self._obj is None:
            return False
        try:
            self._obj.SetPropertyValue(self._PROP_VF, float(vf))
            return True
        except Exception as e:
            logger.error(f"Failed to set vapor fraction: {e}")
            return False

    def get_temperature(self) -> Optional[float]:
        """Return temperature in Kelvin."""
        if self._obj is None:
            return None
        try:
            return float(self._obj.GetPropertyValue(self._PROP_T))
        except Exception:
            return None

    def get_pressure(self) -> Optional[float]:
        """Return pressure in Pascal."""
        if self._obj is None:
            return None
        try:
            return float(self._obj.GetPropertyValue(self._PROP_P))
        except Exception:
            return None

    def get_molar_flow(self) -> Optional[float]:
        """Return molar flow rate in mol/s."""
        if self._obj is None:
            return None
        try:
            return float(self._obj.GetPropertyValue(self._PROP_F))
        except Exception:
            return None

    def get_mass_flow(self) -> Optional[float]:
        """Return mass flow rate in kg/s."""
        if self._obj is None:
            return None
        try:
            return float(self._obj.GetPropertyValue(self._PROP_M))
        except Exception:
            return None

    def get_vapor_fraction(self) -> Optional[float]:
        """Return vapor fraction (after calculation)."""
        if self._obj is None:
            return None
        try:
            return float(self._obj.GetPropertyValue(self._PROP_VF))
        except Exception:
            return None

    def get_enthalpy(self) -> Optional[float]:
        """Return enthalpy in kJ/kg (after calculation)."""
        if self._obj is None:
            return None
        try:
            return float(self._obj.GetPropertyValue(self._PROP_H))
        except Exception:
            return None

    def get_entropy(self) -> Optional[float]:
        """Return entropy in kJ/kg.K (after calculation)."""
        if self._obj is None:
            return None
        try:
            return float(self._obj.GetPropertyValue(self._PROP_S))
        except Exception:
            return None

    def get_composition(self, phase: str = "overall") -> dict[str, float]:
        """Return stream composition for a given phase.

        Uses .NET reflection to access the Phases property on the
        underlying ISimulationObject.

        Args:
            phase: "overall", "vapor", "liquid", or "liquid2".

        Returns:
            {compound_name: mole_fraction} dictionary.
        """
        if self._obj is None:
            return {}

        phase_index = {
            "overall": 0,
            "vapor": 2,
            "liquid": 3,
            "liquid2": 4,
        }.get(phase, 0)

        composition = {}
        try:
            phases_prop = self._obj.GetType().GetProperty("Phases")
            if phases_prop is None:
                return composition
            phases = phases_prop.GetValue(self._obj, None)
            phase_obj = phases[phase_index]
            for comp_name, comp in phase_obj.Compounds.items():
                try:
                    composition[str(comp_name)] = float(comp.MoleFraction)
                except Exception:
                    composition[str(comp_name)] = 0.0
        except Exception as e:
            logger.warning(f"Could not get composition for phase '{phase}': {e}")

        return composition

    def get_all_properties(self) -> dict:
        """Return all stream properties as a dictionary."""
        return {
            "name": self._name,
            "temperature_K": self.get_temperature(),
            "pressure_Pa": self.get_pressure(),
            "molar_flow_mol_s": self.get_molar_flow(),
            "mass_flow_kg_s": self.get_mass_flow(),
            "vapor_fraction": self.get_vapor_fraction(),
            "enthalpy_kJ_kg": self.get_enthalpy(),
            "entropy_kJ_kgK": self.get_entropy(),
            "composition": self.get_composition(),
            "vapor_composition": self.get_composition("vapor"),
            "liquid_composition": self.get_composition("liquid"),
        }

    def copy_to(self, target_name: str) -> Optional["MaterialStream"]:
        """Copy this stream to a new stream with a different name."""
        if self._obj is None:
            return None

        new_stream = MaterialStream(self._flowsheet, target_name)
        if not new_stream.create():
            return None

        props = self.get_all_properties()
        if props.get("temperature_K"):
            new_stream.set_temperature(props["temperature_K"])
        if props.get("pressure_Pa"):
            new_stream.set_pressure(props["pressure_Pa"])
        if props.get("molar_flow_mol_s"):
            new_stream.set_molar_flow(props["molar_flow_mol_s"])
        if props.get("composition"):
            new_stream.set_molar_composition(props["composition"])

        return new_stream
