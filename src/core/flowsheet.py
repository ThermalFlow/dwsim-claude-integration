# -*- coding: utf-8 -*-
"""Flowsheet Manager - Abstracts DWSIM flowsheet operations."""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FlowsheetManager:
    """Manages operations on a DWSIM flowsheet."""

    # Map of user-friendly type keys to DWSIM ObjectType enum names
    OBJECT_TYPES = {
        # Streams
        "material_stream": "MaterialStream",
        "energy_stream": "EnergyStream",
        # Mixers/Splitters
        "mixer": "Mixer",
        "splitter": "Splitter",
        # Heat Exchange
        "heater": "Heater",
        "cooler": "Cooler",
        "heat_exchanger": "HeatExchanger",
        # Separators
        "flash": "Vessel",
        "separator": "ComponentSeparator",
        # Columns
        "distillation": "DistillationColumn",
        "absorption": "AbsorptionColumn",
        "shortcut": "ShortcutColumn",
        # Reactors
        "cstr": "CSTR",
        "pfr": "PFR",
        "gibbs": "RGibbs",
        "equilibrium": "REquilibrium",
        # Pressure Changers
        "pump": "Pump",
        "compressor": "Compressor",
        "expander": "Expander",
        "valve": "Valve",
        # Others
        "recycle": "Recycle",
        "adjust": "Adjust",
        "spec": "Spec",
    }

    def __init__(self, flowsheet: Any, automation: Any):
        """Initialize the flowsheet manager.

        Args:
            flowsheet: DWSIM Flowsheet object.
            automation: DWSIMAutomation instance.
        """
        self._flowsheet = flowsheet
        self._automation = automation
        self._objects: dict[str, Any] = {}

    @property
    def flowsheet(self) -> Any:
        """Return the underlying flowsheet object."""
        return self._flowsheet

    def add_compound(self, name: str) -> bool:
        """Add a compound to the flowsheet.

        Args:
            name: Compound name (e.g. "Water", "Ethanol").

        Returns:
            True if added successfully.
        """
        try:
            self._flowsheet.AddCompound(name)
            logger.info(f"Added compound: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add compound {name}: {e}")
            return False

    def add_compounds(self, names: list[str]) -> dict[str, bool]:
        """Add multiple compounds to the flowsheet.

        Args:
            names: List of compound names.

        Returns:
            Dictionary with success status per compound.
        """
        results = {}
        for name in names:
            results[name] = self.add_compound(name)
        return results

    def get_compounds(self) -> list[str]:
        """Return the list of compounds in the flowsheet."""
        compounds = []
        for comp in self._flowsheet.SelectedCompounds.Values:
            compounds.append(comp.Name)
        return compounds

    def set_property_package(self, name: str) -> bool:
        """Set the property package for the flowsheet.

        Accepts either a user-friendly key (e.g. "peng-robinson") or the
        exact DWSIM internal name (e.g. "Peng-Robinson (PR)").

        Args:
            name: Property package name or key.

        Returns:
            True if set successfully.
        """
        # Try catalog lookup first (translates friendly key -> DWSIM internal name)
        try:
            from ..thermo.property_packages import PROPERTY_PACKAGES
            pp_info = PROPERTY_PACKAGES.get(name.lower())
            if pp_info is not None:
                dwsim_name = pp_info.dwsim_name
            else:
                # Fall back to using name as-is (allows passing the exact DWSIM name)
                dwsim_name = name
        except ImportError:
            dwsim_name = name

        try:
            self._flowsheet.CreateAndAddPropertyPackage(dwsim_name)
            logger.info(f"Set property package: {dwsim_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set property package '{dwsim_name}': {e}")
            return False

    def add_object(
        self,
        obj_type: str,
        name: str,
        x: float = 100,
        y: float = 100,
    ) -> Optional[Any]:
        """Add an object to the flowsheet.

        For material_stream and energy_stream types, returns the corresponding
        Python wrapper (MaterialStream / EnergyStream) which provides
        set_conditions(), dwsim_object, and other helper methods.

        For all other types, returns the raw DWSIM ISimulationObject.

        Args:
            obj_type: Object type key from OBJECT_TYPES.
            name: Name/tag for the object.
            x: X position in the diagram.
            y: Y position in the diagram.

        Returns:
            Wrapper or simulation object, or None on failure.
        """
        if obj_type not in self.OBJECT_TYPES:
            logger.error(f"Unknown object type: {obj_type}")
            return None

        try:
            if obj_type == "material_stream":
                from ..streams.material import MaterialStream
                wrapper = MaterialStream(self._flowsheet, name, x, y)
                if not wrapper.create():
                    return None
                # Store the raw sim object for connect()/get_object() use
                self._objects[name] = wrapper.dwsim_object
                logger.info(f"Added material_stream '{name}' at ({x}, {y})")
                return wrapper

            if obj_type == "energy_stream":
                from ..streams.energy import EnergyStream
                wrapper = EnergyStream(self._flowsheet, name, x, y)
                if not wrapper.create():
                    return None
                self._objects[name] = wrapper.dwsim_object
                logger.info(f"Added energy_stream '{name}' at ({x}, {y})")
                return wrapper

            # Generic unit operation — return raw simulation object
            dwsim_type_name = self.OBJECT_TYPES[obj_type]
            from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType
            obj_type_enum = getattr(ObjectType, dwsim_type_name)
            ref = self._flowsheet.AddObject(obj_type_enum, x, y, name)
            obj = self._flowsheet.SimulationObjects[ref.Name]
            self._objects[name] = obj
            logger.info(f"Added {obj_type} '{name}' at ({x}, {y})")
            return obj

        except Exception as e:
            logger.error(f"Failed to add object '{name}': {e}")
            return None

    def get_object(self, name: str) -> Optional[Any]:
        """Return a simulation object by name/tag.

        Args:
            name: Object name/tag.

        Returns:
            The simulation object, or None if not found.
        """
        if name in self._objects:
            return self._objects[name]

        # Search the flowsheet
        for obj in self._flowsheet.SimulationObjects.Values:
            if hasattr(obj, "GraphicObject"):
                if obj.GraphicObject.Tag == name:
                    self._objects[name] = obj
                    return obj

        return None

    def connect(
        self,
        source_name: str,
        target_name: str,
        source_port: int = 0,
        target_port: int = 0,
    ) -> bool:
        """Connect two objects in the flowsheet.

        Args:
            source_name: Name of the source object.
            target_name: Name of the target object.
            source_port: Output port index (default 0).
            target_port: Input port index (default 0).

        Returns:
            True if connected successfully.
        """
        source = self.get_object(source_name)
        target = self.get_object(target_name)

        if source is None:
            logger.error(f"Source object not found: {source_name}")
            return False

        if target is None:
            logger.error(f"Target object not found: {target_name}")
            return False

        try:
            self._flowsheet.ConnectObjects(
                source.GraphicObject,
                target.GraphicObject,
                source_port,
                target_port,
            )
            logger.info(f"Connected {source_name} -> {target_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect {source_name} -> {target_name}: {e}")
            return False

    def disconnect(self, source_name: str, target_name: str) -> bool:
        """Disconnect two objects.

        Args:
            source_name: Name of the source object.
            target_name: Name of the target object.

        Returns:
            True if disconnected successfully.
        """
        source = self.get_object(source_name)
        target = self.get_object(target_name)

        if source is None or target is None:
            return False

        try:
            self._flowsheet.DisconnectObjects(
                source.GraphicObject,
                target.GraphicObject,
            )
            logger.info(f"Disconnected {source_name} -> {target_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")
            return False

    def remove_object(self, name: str) -> bool:
        """Remove an object from the flowsheet.

        Args:
            name: Object name/tag.

        Returns:
            True if removed successfully.
        """
        obj = self.get_object(name)
        if obj is None:
            return False

        try:
            self._flowsheet.DeleteObject(obj.GraphicObject.Tag)
            self._objects.pop(name, None)
            logger.info(f"Removed object: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove object {name}: {e}")
            return False

    def list_objects(self) -> list[dict]:
        """List all objects in the flowsheet.

        Returns:
            List of dictionaries with object info.
        """
        objects = []
        for obj in self._flowsheet.SimulationObjects.Values:
            obj_info = {
                "name": obj.GraphicObject.Tag if hasattr(obj, "GraphicObject") else "Unknown",
                "type": obj.GetType().Name,
                "calculated": getattr(obj, "Calculated", False),
            }
            objects.append(obj_info)
        return objects

    def get_stream_results(self, name: str) -> Optional[dict]:
        """Return results for a material stream.

        Uses PROP_MS_* property codes and .NET reflection for phase access.

        Args:
            name: Stream name/tag.

        Returns:
            Dictionary with stream properties, or None on failure.
        """
        stream = self.get_object(name)
        if stream is None:
            return None

        try:
            results = {
                "temperature_K": float(stream.GetPropertyValue("PROP_MS_0")),
                "pressure_Pa": float(stream.GetPropertyValue("PROP_MS_1")),
                "molar_flow_mol_s": float(stream.GetPropertyValue("PROP_MS_2")),
                "mass_flow_kg_s": float(stream.GetPropertyValue("PROP_MS_3")),
                "vapor_fraction": float(stream.GetPropertyValue("PROP_MS_27")),
                "enthalpy_kJ_kg": float(stream.GetPropertyValue("PROP_MS_7")),
                "entropy_kJ_kgK": float(stream.GetPropertyValue("PROP_MS_8")),
            }

            # Phase compositions via reflection (stream is ISimulationObject)
            phases_prop = stream.GetType().GetProperty("Phases")
            results["composition"] = {}
            if phases_prop is not None:
                phases = phases_prop.GetValue(stream, None)
                compound_names = self.get_compounds()
                for phase_key, phase_index in [("overall", 0), ("vapor", 2), ("liquid", 3)]:
                    phase_comp = {}
                    try:
                        phase = phases[phase_index]
                        for comp_name in compound_names:
                            comp = phase.Compounds[comp_name]
                            phase_comp[comp_name] = float(comp.MoleFraction)
                    except Exception:
                        pass
                    results["composition"][phase_key] = phase_comp

            return results

        except Exception as e:
            logger.error(f"Failed to get stream results for {name}: {e}")
            return None
