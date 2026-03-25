# -*- coding: utf-8 -*-
"""Main interface to DWSIM Automation via pythonnet."""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DWSIMAutomation:
    """Primary interface to DWSIM via pythonnet."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the DWSIM interface.

        The DWSIM installation path is resolved in priority order:
          1. ``DWSIM_PATH`` environment variable (highest priority)
          2. ``install_path`` inside config.json
          3. ``install_path`` inside config.example.json (fallback)

        Args:
            config_path: Path to config.json. Defaults to the config.json
                         in the project root (parent of src/).
        """
        self._config = self._load_config(config_path)
        self._dwsim_path = self._resolve_dwsim_path()
        self._initialized = False
        self._automation = None

    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load configuration from JSON file.

        Falls back to config.example.json when config.json is absent,
        then allows DWSIM_PATH env var to override the install path.
        """
        project_root = Path(__file__).parent.parent.parent

        if config_path is not None:
            p = Path(config_path)
            if not p.exists():
                raise FileNotFoundError(f"Config file not found: {p}")
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)

        # Try config.json first, then config.example.json
        for name in ("config.json", "config.example.json"):
            candidate = project_root / name
            if candidate.exists():
                with open(candidate, "r", encoding="utf-8") as f:
                    return json.load(f)

        raise FileNotFoundError(
            "No config.json or config.example.json found. "
            "Copy config.example.json to config.json and set your DWSIM path, "
            "or set the DWSIM_PATH environment variable."
        )

    def _resolve_dwsim_path(self) -> Path:
        """Resolve the DWSIM install directory.

        DWSIM_PATH env var takes priority over the config file value.
        The path is canonicalized and validated.
        """
        import os

        env_path = os.environ.get("DWSIM_PATH")
        if env_path:
            resolved = Path(env_path).resolve()
        else:
            raw = self._config.get("dwsim", {}).get("install_path", "")
            if not raw:
                raise ValueError(
                    "DWSIM path not configured. Set the DWSIM_PATH environment "
                    "variable or fill 'install_path' in config.json."
                )
            resolved = Path(raw).resolve()

        if not resolved.is_dir():
            raise FileNotFoundError(
                f"DWSIM install directory not found: {resolved}"
            )

        return resolved

    def initialize(self) -> bool:
        """Initialize pythonnet and load DWSIM DLLs.

        Returns:
            True if initialization succeeded.
        """
        if self._initialized:
            return True

        try:
            import clr

            # Add DWSIM install path to the .NET runtime search path
            sys.path.append(str(self._dwsim_path))

            # Load required DLLs listed in config, validating each path
            for dll in self._config["dwsim"]["dlls"]:
                dll_path = (self._dwsim_path / dll).resolve()

                # Ensure the DLL resolves inside the DWSIM directory
                try:
                    # Python 3.9+ canonical parent check
                    if not dll_path.is_relative_to(self._dwsim_path):
                        logger.error(f"DLL path escapes DWSIM directory: {dll}")
                        continue
                except AttributeError:
                    # Python 3.8 fallback: compare resolved parents
                    try:
                        dll_path.relative_to(self._dwsim_path)
                    except ValueError:
                        logger.error(f"DLL path escapes DWSIM directory: {dll}")
                        continue

                if dll_path.exists():
                    clr.AddReference(str(dll_path))
                    logger.info(f"Loaded DLL: {dll}")
                else:
                    logger.warning(f"DLL not found: {dll_path}")

            from DWSIM.Automation import Automation3

            self._automation = Automation3()
            self._initialized = True
            logger.info("DWSIM Automation initialized successfully")
            return True

        except ImportError as e:
            logger.error(f"Failed to import DWSIM modules: {e}")
            raise RuntimeError(
                "pythonnet not installed or DWSIM not found. "
                "Install with: pip install pythonnet"
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize DWSIM: {e}")
            raise

    def create_flowsheet(self) -> Any:
        """Create a new empty flowsheet.

        Returns:
            DWSIM Flowsheet object.
        """
        self._ensure_initialized()
        flowsheet = self._automation.CreateFlowsheet()
        logger.info("Created new flowsheet")
        return flowsheet

    def load_flowsheet(self, path: str) -> Any:
        """Load a flowsheet from file.

        Args:
            path: Path to a .dwxmz or .dwxml file.

        Returns:
            Loaded Flowsheet object.
        """
        self._ensure_initialized()
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Flowsheet file not found: {path}")

        flowsheet = self._automation.LoadFlowsheet(str(path))
        logger.info(f"Loaded flowsheet from: {path}")
        return flowsheet

    def save_flowsheet(self, flowsheet: Any, path: str) -> bool:
        """Save a flowsheet to file.

        Args:
            flowsheet: DWSIM Flowsheet object.
            path: Destination path (.dwxmz or .dwxml).

        Returns:
            True if saved successfully.
        """
        self._ensure_initialized()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        self._automation.SaveFlowsheet(flowsheet, str(path), True)
        logger.info(f"Saved flowsheet to: {path}")
        return True

    def calculate(
        self,
        flowsheet: Any,
        timeout: Optional[int] = None,
    ) -> dict:
        """Run the flowsheet solver.

        Calls CalculateFlowsheet4 and returns a status dictionary with
        any errors found in the simulation objects afterwards.

        Args:
            flowsheet: DWSIM Flowsheet object.
            timeout: Unused; kept for API compatibility.

        Returns:
            Dictionary with keys: success (bool), errors (list), warnings (list),
            message (str).
        """
        self._ensure_initialized()

        try:
            self._automation.CalculateFlowsheet4(flowsheet)

            # Collect any error messages from simulation objects
            errors = []
            for obj in flowsheet.SimulationObjects.Values:
                try:
                    msg = getattr(obj, "ErrorMessage", None)
                    if msg:
                        tag = obj.GraphicObject.Tag if hasattr(obj, "GraphicObject") else "?"
                        errors.append(f"{tag}: {msg}")
                except Exception:
                    pass

            return {
                "success": len(errors) == 0,
                "errors": errors,
                "warnings": [],
                "message": "Calculation completed" if not errors else "Calculation completed with errors",
            }

        except Exception as e:
            logger.error(f"Calculation failed: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "warnings": [],
                "message": "Calculation failed",
            }

    def get_available_compounds(self) -> list[str]:
        """Return a sorted list of compounds available in DWSIM.

        Returns:
            List of compound names.
        """
        self._ensure_initialized()
        compounds = []

        try:
            from DWSIM.Thermodynamics import Databases

            db = Databases.ChEDLThermoLink()
            for comp in db.GetCompoundList():
                compounds.append(comp)
        except Exception as e:
            logger.warning(f"Could not load compound database: {e}")

        return sorted(compounds)

    def get_version(self) -> str:
        """Return the DWSIM version from config."""
        return self._config["dwsim"]["version"]

    def _ensure_initialized(self) -> None:
        """Raise RuntimeError if DWSIM has not been initialized."""
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("DWSIM not initialized")
