# -*- coding: utf-8 -*-
"""Base class for unit operations."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class UnitOperationBase(ABC):
    """Abstract base class for all DWSIM unit operations."""

    # DWSIM ObjectType enum name for this operation (override in subclasses)
    DWSIM_TYPE: str = ""

    def __init__(
        self,
        flowsheet: Any,
        name: str,
        x: float = 100,
        y: float = 100,
    ):
        """Initialize the unit operation.

        Args:
            flowsheet: DWSIM Flowsheet object.
            name: Equipment name/tag.
            x: X position in the diagram.
            y: Y position in the diagram.
        """
        self._flowsheet = flowsheet
        self._name = name
        self._x = x
        self._y = y
        self._obj: Optional[Any] = None
        self._inlet_streams: list[str] = []
        self._outlet_streams: list[str] = []

    @property
    def name(self) -> str:
        """Return equipment name/tag."""
        return self._name

    @property
    def dwsim_object(self) -> Optional[Any]:
        """Return the underlying DWSIM simulation object."""
        return self._obj

    @property
    def is_calculated(self) -> bool:
        """Return True if the equipment has been calculated."""
        if self._obj is None:
            return False
        return getattr(self._obj, "Calculated", False)

    def create(self) -> bool:
        """Create the unit operation in the flowsheet.

        Uses the ObjectType enum (not a string) as required by DWSIM's
        AddObject API, then resolves to the actual ISimulationObject.

        Returns:
            True if created successfully.
        """
        if not self.DWSIM_TYPE:
            logger.error(f"DWSIM_TYPE not defined for {self.__class__.__name__}")
            return False

        try:
            from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType
            obj_type_enum = getattr(ObjectType, self.DWSIM_TYPE)
            ref = self._flowsheet.AddObject(obj_type_enum, self._x, self._y, self._name)
            self._obj = self._flowsheet.SimulationObjects[ref.Name]
            logger.info(f"Created {self.DWSIM_TYPE} '{self._name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to create '{self._name}': {e}")
            return False

    def set_property(self, name: str, value: Any) -> bool:
        """Set a property on the equipment object.

        Args:
            name: Property name.
            value: Value to set.

        Returns:
            True if set successfully.
        """
        if self._obj is None:
            logger.error(f"Object '{self._name}' not created")
            return False

        try:
            setattr(self._obj, name, value)
            logger.debug(f"Set {self._name}.{name} = {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to set {name} on '{self._name}': {e}")
            return False

    def get_property(self, name: str) -> Optional[Any]:
        """Return the value of a property.

        Args:
            name: Property name.

        Returns:
            Property value, or None on failure.
        """
        if self._obj is None:
            return None

        try:
            return getattr(self._obj, name, None)
        except Exception:
            return None

    def connect_inlet(self, stream_name: str, port: int = 0) -> bool:
        """Connect an inlet stream to this equipment.

        Args:
            stream_name: Name of the inlet stream.
            port: Input port index.

        Returns:
            True if connected successfully.
        """
        if self._obj is None:
            logger.error(f"Object '{self._name}' not created")
            return False

        try:
            stream = None
            for obj in self._flowsheet.SimulationObjects.Values:
                if hasattr(obj, "GraphicObject"):
                    if obj.GraphicObject.Tag == stream_name:
                        stream = obj
                        break

            if stream is None:
                logger.error(f"Stream not found: {stream_name}")
                return False

            self._flowsheet.ConnectObjects(
                stream.GraphicObject,
                self._obj.GraphicObject,
                0,
                port,
            )
            self._inlet_streams.append(stream_name)
            logger.info(f"Connected {stream_name} -> {self._name}[{port}]")
            return True

        except Exception as e:
            logger.error(f"Failed to connect inlet: {e}")
            return False

    def connect_outlet(self, stream_name: str, port: int = 0) -> bool:
        """Connect an outlet stream from this equipment.

        Args:
            stream_name: Name of the outlet stream.
            port: Output port index.

        Returns:
            True if connected successfully.
        """
        if self._obj is None:
            logger.error(f"Object '{self._name}' not created")
            return False

        try:
            stream = None
            for obj in self._flowsheet.SimulationObjects.Values:
                if hasattr(obj, "GraphicObject"):
                    if obj.GraphicObject.Tag == stream_name:
                        stream = obj
                        break

            if stream is None:
                logger.error(f"Stream not found: {stream_name}")
                return False

            self._flowsheet.ConnectObjects(
                self._obj.GraphicObject,
                stream.GraphicObject,
                port,
                0,
            )
            self._outlet_streams.append(stream_name)
            logger.info(f"Connected {self._name}[{port}] -> {stream_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect outlet: {e}")
            return False

    @abstractmethod
    def get_results(self) -> dict:
        """Return equipment-specific results after calculation.

        Returns:
            Dictionary with results specific to this unit operation.
        """
        pass

    def get_error_message(self) -> Optional[str]:
        """Return the error message from the last calculation, if any."""
        if self._obj is None:
            return "Object not created"
        return getattr(self._obj, "ErrorMessage", None)
