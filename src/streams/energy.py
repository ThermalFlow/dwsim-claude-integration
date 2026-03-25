# -*- coding: utf-8 -*-
"""Energy Stream - DWSIM energy streams."""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EnergyStream:
    """Represents an energy stream in DWSIM."""

    DWSIM_TYPE = "EnergyStream"

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        """Initialize the energy stream.

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
        """Create the energy stream in the flowsheet.

        Uses the ObjectType enum (not a string) as required by DWSIM's
        AddObject API, then resolves to the actual ISimulationObject.
        """
        try:
            from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType
            obj_type_enum = getattr(ObjectType, self.DWSIM_TYPE)
            ref = self._flowsheet.AddObject(obj_type_enum, self._x, self._y, self._name)
            self._obj = self._flowsheet.SimulationObjects[ref.Name]
            logger.info(f"Created EnergyStream '{self._name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to create energy stream '{self._name}': {e}")
            return False

    def set_power(self, power_kW: float) -> bool:
        """Set the energy stream power.

        Args:
            power_kW: Power in kW (positive = heat input, negative = heat output).
        """
        if self._obj is None:
            return False
        try:
            self._obj.EnergyFlow = power_kW
            return True
        except Exception as e:
            logger.error(f"Failed to set power: {e}")
            return False

    def get_power(self) -> Optional[float]:
        """Return power in kW."""
        if self._obj is None:
            return None
        try:
            return self._obj.EnergyFlow
        except Exception:
            return None

    def get_all_properties(self) -> dict:
        """Return all stream properties as a dictionary."""
        return {
            "name": self._name,
            "power_kW": self.get_power(),
        }

    def connect_to(self, equipment_name: str, port: int = 0) -> bool:
        """Connect this energy stream to a piece of equipment.

        Args:
            equipment_name: Name of the equipment object.
            port: Energy port index on the equipment.
        """
        if self._obj is None:
            return False

        try:
            equipment = None
            for obj in self._flowsheet.SimulationObjects.Values:
                if hasattr(obj, "GraphicObject"):
                    if obj.GraphicObject.Tag == equipment_name:
                        equipment = obj
                        break

            if equipment is None:
                logger.error(f"Equipment not found: {equipment_name}")
                return False

            self._flowsheet.ConnectObjects(
                self._obj.GraphicObject,
                equipment.GraphicObject,
                0,
                port,
            )
            logger.info(f"Connected {self._name} -> {equipment_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect energy stream: {e}")
            return False
