# -*- coding: utf-8 -*-
"""Report generation for DWSIM simulations."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Report generator for DWSIM simulation results."""

    def __init__(self, template_dir: Optional[str] = None):
        """Initialize the report generator.

        Args:
            template_dir: Directory containing Jinja2 HTML templates.
        """
        self._template_dir = template_dir
        self._env = None  # Initialized lazily when templates are needed

    def _get_jinja_env(self):
        """Return a Jinja2 Environment, initializing it on first use."""
        if self._env is None:
            try:
                from jinja2 import Environment, FileSystemLoader, select_autoescape
            except ImportError:
                raise ImportError(
                    "jinja2 is required for HTML report generation. "
                    "Install it with: pip install jinja2"
                )
            if self._template_dir is None:
                raise ValueError("template_dir must be set to generate HTML reports")
            self._env = Environment(
                loader=FileSystemLoader(self._template_dir),
                autoescape=select_autoescape(["html", "xml"]),
            )
        return self._env

    def stream_report(self, stream: Any) -> dict:
        """Build a report dictionary for a material stream.

        Args:
            stream: MaterialStream wrapper object or a property dict.

        Returns:
            Dictionary with stream report data.
        """
        if hasattr(stream, "get_all_properties"):
            props = stream.get_all_properties()
        else:
            props = stream

        report = {
            "name": props.get("name", "Unknown"),
            "generated_at": datetime.now().isoformat(),
            "conditions": {
                "temperature_C": (props.get("temperature_K", 0) or 0) - 273.15,
                "temperature_K": props.get("temperature_K"),
                "pressure_bar": (props.get("pressure_Pa", 0) or 0) / 1e5,
                "pressure_Pa": props.get("pressure_Pa"),
            },
            "flows": {
                "molar_flow_mol_s": props.get("molar_flow_mol_s"),
                "molar_flow_kmol_h": (props.get("molar_flow_mol_s", 0) or 0) * 3.6,
                "mass_flow_kg_s": props.get("mass_flow_kg_s"),
                "mass_flow_kg_h": (props.get("mass_flow_kg_s", 0) or 0) * 3600,
            },
            "phase_distribution": {
                "vapor_fraction": props.get("vapor_fraction"),
                "liquid_fraction": 1 - (props.get("vapor_fraction", 0) or 0),
            },
            "thermal": {
                "enthalpy_kJ_kg": props.get("enthalpy_kJ_kg"),
                "entropy_kJ_kgK": props.get("entropy_kJ_kgK"),
            },
            "composition": props.get("composition", {}),
            "vapor_composition": props.get("vapor_composition", {}),
            "liquid_composition": props.get("liquid_composition", {}),
        }

        return report

    def equipment_report(self, equipment: Any) -> dict:
        """Build a report dictionary for a unit operation.

        Args:
            equipment: Unit operation wrapper object or a results dict.

        Returns:
            Dictionary with equipment report data.
        """
        if hasattr(equipment, "get_results"):
            results = equipment.get_results()
        else:
            results = equipment

        report = {
            "name": getattr(equipment, "name", "Unknown"),
            "type": equipment.__class__.__name__ if hasattr(equipment, "__class__") else "Unknown",
            "generated_at": datetime.now().isoformat(),
            "calculated": getattr(equipment, "is_calculated", False),
            "results": results,
            "error_message": getattr(equipment, "get_error_message", lambda: None)()
            if hasattr(equipment, "get_error_message")
            else None,
        }

        return report

    def flowsheet_summary(self, flowsheet: Any) -> dict:
        """Build a summary dictionary for a complete flowsheet.

        Args:
            flowsheet: DWSIM Flowsheet object.

        Returns:
            Dictionary with flowsheet summary data.
        """
        streams = []
        equipment = []

        try:
            for obj in flowsheet.SimulationObjects.Values:
                obj_type = obj.GetType().Name

                if "Stream" in obj_type:
                    streams.append({
                        "name": obj.GraphicObject.Tag,
                        "type": obj_type,
                        "calculated": getattr(obj, "Calculated", False),
                    })
                else:
                    equipment.append({
                        "name": obj.GraphicObject.Tag,
                        "type": obj_type,
                        "calculated": getattr(obj, "Calculated", False),
                    })

        except Exception as e:
            logger.error(f"Error generating flowsheet summary: {e}")

        return {
            "generated_at": datetime.now().isoformat(),
            "total_streams": len(streams),
            "total_equipment": len(equipment),
            "streams": streams,
            "equipment": equipment,
            "compounds": [c.Name for c in flowsheet.SelectedCompounds.Values]
            if hasattr(flowsheet, "SelectedCompounds")
            else [],
            "property_package": flowsheet.PropertyPackages[0].Tag
            if hasattr(flowsheet, "PropertyPackages") and len(flowsheet.PropertyPackages) > 0
            else "Not set",
        }

    def export_to_excel(
        self,
        flowsheet: Any,
        output_path: str,
        include_streams: bool = True,
        include_equipment: bool = True,
    ) -> bool:
        """Export flowsheet data to an Excel workbook.

        Args:
            flowsheet: DWSIM Flowsheet object.
            output_path: Path for the output Excel file.
            include_streams: Include a sheet with stream data.
            include_equipment: Include a sheet with equipment data.

        Returns:
            True if exported successfully.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas and openpyxl are required for Excel export. "
                "Install them with: pip install pandas openpyxl"
            )

        try:
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                # Summary sheet
                summary = self.flowsheet_summary(flowsheet)
                summary_df = pd.DataFrame([{
                    "Property": "Total Streams",
                    "Value": summary["total_streams"],
                }, {
                    "Property": "Total Equipment",
                    "Value": summary["total_equipment"],
                }, {
                    "Property": "Property Package",
                    "Value": summary["property_package"],
                }, {
                    "Property": "Compounds",
                    "Value": ", ".join(summary["compounds"]),
                }])
                summary_df.to_excel(writer, sheet_name="Summary", index=False)

                if include_streams:
                    stream_data = []
                    for obj in flowsheet.SimulationObjects.Values:
                        if "Stream" in obj.GetType().Name:
                            # Use GetPropertyValue with PROP_MS_* codes to avoid
                            # direct Phases access, which fails on ISimulationObject
                            try:
                                t_k = obj.GetPropertyValue("PROP_MS_0")
                                p_pa = obj.GetPropertyValue("PROP_MS_1")
                                flow = obj.GetPropertyValue("PROP_MS_2")
                                vf = obj.GetPropertyValue("PROP_MS_27")
                            except Exception:
                                t_k = p_pa = flow = vf = None

                            stream_data.append({
                                "Name": obj.GraphicObject.Tag,
                                "T (K)": t_k,
                                "P (Pa)": p_pa,
                                "Flow (mol/s)": flow,
                                "Vapor Frac": vf,
                            })

                    if stream_data:
                        streams_df = pd.DataFrame(stream_data)
                        streams_df.to_excel(writer, sheet_name="Streams", index=False)

                if include_equipment:
                    equip_data = []
                    for obj in flowsheet.SimulationObjects.Values:
                        if "Stream" not in obj.GetType().Name:
                            equip_data.append({
                                "Name": obj.GraphicObject.Tag,
                                "Type": obj.GetType().Name,
                                "Calculated": getattr(obj, "Calculated", False),
                                "Error": getattr(obj, "ErrorMessage", ""),
                            })

                    if equip_data:
                        equip_df = pd.DataFrame(equip_data)
                        equip_df.to_excel(writer, sheet_name="Equipment", index=False)

            logger.info(f"Exported flowsheet to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export to Excel: {e}")
            return False

    def export_to_csv(
        self,
        data: list[dict],
        output_path: str,
    ) -> bool:
        """Export a list of dictionaries to a CSV file.

        Args:
            data: List of data dictionaries.
            output_path: Path for the output CSV file.

        Returns:
            True if exported successfully.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for CSV export. "
                "Install it with: pip install pandas"
            )

        try:
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            logger.info(f"Exported to CSV: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return False

    def generate_html_report(
        self,
        flowsheet: Any,
        output_path: str,
        template_name: str = "flowsheet_report.html",
    ) -> bool:
        """Generate an HTML report from a Jinja2 template.

        Args:
            flowsheet: DWSIM Flowsheet object.
            output_path: Path for the output HTML file.
            template_name: Template file name inside template_dir.

        Returns:
            True if generated successfully.
        """
        try:
            env = self._get_jinja_env()
        except (ImportError, ValueError) as e:
            logger.error(str(e))
            return False

        try:
            template = env.get_template(template_name)
            summary = self.flowsheet_summary(flowsheet)

            html = template.render(
                summary=summary,
                generated_at=datetime.now().isoformat(),
            )

            Path(output_path).write_text(html, encoding="utf-8")
            logger.info(f"Generated HTML report: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            return False
