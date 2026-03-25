# -*- coding: utf-8 -*-
"""Visualization and Plotting for DWSIM results."""

import json
import logging
from pathlib import Path
from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


class DWSIMPlotter:
    """Generates plots for DWSIM simulation results."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the plotter.

        Args:
            config_path: Path to config.json. Defaults to the project root config.
        """
        self._config = self._load_config(config_path)
        self._setup_style()

    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load visualization configuration."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.json"
        else:
            config_path = Path(config_path)

        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)

        return {
            "visualization": {
                "default_dpi": 150,
                "figure_size": [10, 6],
                "style": "seaborn-v0_8-whitegrid",
            }
        }

    def _setup_style(self) -> None:
        """Apply the configured matplotlib style."""
        try:
            style = self._config["visualization"]["style"]
            plt.style.use(style)
        except Exception:
            plt.style.use("default")

    def phase_envelope(
        self,
        stream: Any,
        n_points: int = 50,
        save_path: Optional[str] = None,
    ) -> plt.Figure:
        """Generate a PT phase envelope diagram.

        Args:
            stream: MaterialStream with composition already set.
            n_points: Number of points on the envelope.
            save_path: File path to save the figure (optional).

        Returns:
            matplotlib Figure object.
        """
        fig, ax = plt.subplots(
            figsize=self._config["visualization"]["figure_size"],
        )

        try:
            pp = stream.PropertyPackage

            temperatures_bubble = []
            pressures_bubble = []
            temperatures_dew = []
            pressures_dew = []

            composition = stream.GetOverallComposition()

            p_min = 1e5   # 1 bar
            p_max = float(stream.GetPropertyValue("PROP_MS_1")) * 2

            for p in np.linspace(p_min, p_max, n_points):
                try:
                    t_bubble = pp.DW_CalcBubT_EXPERIMENT(p, composition)
                    temperatures_bubble.append(t_bubble - 273.15)
                    pressures_bubble.append(p / 1e5)
                except Exception:
                    pass

                try:
                    t_dew = pp.DW_CalcDewT_EXPERIMENT(p, composition)
                    temperatures_dew.append(t_dew - 273.15)
                    pressures_dew.append(p / 1e5)
                except Exception:
                    pass

            ax.plot(
                temperatures_bubble,
                pressures_bubble,
                "b-",
                label="Bubble Point",
                linewidth=2,
            )
            ax.plot(
                temperatures_dew,
                pressures_dew,
                "r-",
                label="Dew Point",
                linewidth=2,
            )

            ax.set_xlabel("Temperature (C)")
            ax.set_ylabel("Pressure (bar)")
            ax.set_title("Phase Envelope")
            ax.legend()
            ax.grid(True, alpha=0.3)

        except Exception as e:
            logger.error(f"Failed to generate phase envelope: {e}")
            ax.text(
                0.5,
                0.5,
                f"Error: {e}",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )

        if save_path:
            fig.savefig(
                save_path,
                dpi=self._config["visualization"]["default_dpi"],
                bbox_inches="tight",
            )
            logger.info(f"Saved phase envelope to: {save_path}")

        return fig

    def txy_diagram(
        self,
        compound1: str,
        compound2: str,
        pressure_Pa: float,
        flowsheet: Any,
        n_points: int = 50,
        save_path: Optional[str] = None,
    ) -> plt.Figure:
        """Generate a Txy diagram for a binary system.

        Args:
            compound1: Name of component 1.
            compound2: Name of component 2.
            pressure_Pa: System pressure in Pa.
            flowsheet: DWSIM Flowsheet object.
            n_points: Number of points.
            save_path: File path to save the figure (optional).

        Returns:
            matplotlib Figure object.
        """
        fig, ax = plt.subplots(
            figsize=self._config["visualization"]["figure_size"],
        )

        try:
            pp = flowsheet.PropertyPackages[0]

            x1_values = np.linspace(0.001, 0.999, n_points)
            t_bubble = []
            t_dew = []
            y1_values = []

            for x1 in x1_values:
                composition = [x1, 1 - x1]

                try:
                    t_b = pp.DW_CalcBubT_EXPERIMENT(pressure_Pa, composition)
                    t_bubble.append(t_b - 273.15)
                    # Vapor composition placeholder (simplified)
                    y1 = x1 * 1.2
                    y1_values.append(min(y1, 0.999))
                except Exception:
                    t_bubble.append(np.nan)
                    y1_values.append(np.nan)

                try:
                    t_d = pp.DW_CalcDewT_EXPERIMENT(pressure_Pa, composition)
                    t_dew.append(t_d - 273.15)
                except Exception:
                    t_dew.append(np.nan)

            ax.plot(x1_values, t_bubble, "b-", label="Liquid (Bubble)", linewidth=2)
            ax.plot(y1_values, t_bubble, "r-", label="Vapor (Dew)", linewidth=2)

            ax.set_xlabel(f"Mole Fraction of {compound1}")
            ax.set_ylabel("Temperature (C)")
            ax.set_title(f"Txy Diagram: {compound1}-{compound2} at {pressure_Pa/1e5:.1f} bar")
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, 1)

        except Exception as e:
            logger.error(f"Failed to generate Txy diagram: {e}")
            ax.text(
                0.5,
                0.5,
                f"Error: {e}",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )

        if save_path:
            fig.savefig(
                save_path,
                dpi=self._config["visualization"]["default_dpi"],
                bbox_inches="tight",
            )

        return fig

    def column_profiles(
        self,
        column: Any,
        save_path: Optional[str] = None,
    ) -> plt.Figure:
        """Generate distillation column profile plots.

        Args:
            column: DistillationColumn object with get_stage_profiles().
            save_path: File path to save the figure (optional).

        Returns:
            matplotlib Figure with four subplots.
        """
        fig, axes = plt.subplots(
            2,
            2,
            figsize=(12, 10),
        )

        try:
            profiles = column.get_stage_profiles()
            stages = range(1, len(profiles["temperature_K"]) + 1)

            axes[0, 0].plot(stages, profiles["temperature_K"], "b-o", linewidth=2)
            axes[0, 0].set_xlabel("Stage")
            axes[0, 0].set_ylabel("Temperature (K)")
            axes[0, 0].set_title("Temperature Profile")
            axes[0, 0].grid(True, alpha=0.3)

            axes[0, 1].plot(
                stages,
                [p / 1e5 for p in profiles["pressure_Pa"]],
                "g-o",
                linewidth=2,
            )
            axes[0, 1].set_xlabel("Stage")
            axes[0, 1].set_ylabel("Pressure (bar)")
            axes[0, 1].set_title("Pressure Profile")
            axes[0, 1].grid(True, alpha=0.3)

            axes[1, 0].plot(
                stages,
                profiles["vapor_flow_mol_s"],
                "r-o",
                label="Vapor",
                linewidth=2,
            )
            axes[1, 0].plot(
                stages,
                profiles["liquid_flow_mol_s"],
                "b-s",
                label="Liquid",
                linewidth=2,
            )
            axes[1, 0].set_xlabel("Stage")
            axes[1, 0].set_ylabel("Flow (mol/s)")
            axes[1, 0].set_title("Flow Profiles")
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)

            results = column.get_results()
            info_text = (
                f"Condenser Duty: {results.get('condenser_duty_kW', 0):.1f} kW\n"
                f"Reboiler Duty: {results.get('reboiler_duty_kW', 0):.1f} kW\n"
                f"Reflux Ratio: {results.get('reflux_ratio', 0):.2f}\n"
                f"Stages: {results.get('number_of_stages', 0)}"
            )
            axes[1, 1].text(
                0.5,
                0.5,
                info_text,
                ha="center",
                va="center",
                fontsize=12,
                transform=axes[1, 1].transAxes,
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
            )
            axes[1, 1].set_axis_off()
            axes[1, 1].set_title("Column Summary")

        except Exception as e:
            logger.error(f"Failed to generate column profiles: {e}")
            for ax in axes.flat:
                ax.text(0.5, 0.5, f"Error: {e}", ha="center", va="center")

        plt.tight_layout()

        if save_path:
            fig.savefig(
                save_path,
                dpi=self._config["visualization"]["default_dpi"],
                bbox_inches="tight",
            )

        return fig

    def sensitivity_analysis(
        self,
        results: list[dict],
        x_param: str,
        y_params: list[str],
        x_label: str = "",
        y_labels: Optional[list[str]] = None,
        title: str = "Sensitivity Analysis",
        save_path: Optional[str] = None,
    ) -> plt.Figure:
        """Generate a sensitivity analysis plot.

        Args:
            results: List of result dictionaries from a parameter sweep.
            x_param: Key name for the X-axis parameter.
            y_params: List of key names to plot on the Y-axis.
            x_label: X-axis label (defaults to x_param if empty).
            y_labels: Labels for each Y curve (defaults to y_params).
            title: Plot title.
            save_path: File path to save the figure (optional).

        Returns:
            matplotlib Figure object.
        """
        fig, ax = plt.subplots(
            figsize=self._config["visualization"]["figure_size"],
        )

        x_values = [r[x_param] for r in results]

        if y_labels is None:
            y_labels = y_params

        for y_param, y_label in zip(y_params, y_labels):
            y_values = [r.get(y_param, 0) or 0 for r in results]
            ax.plot(x_values, y_values, "-o", label=y_label, linewidth=2)

        ax.set_xlabel(x_label or x_param)
        ax.set_ylabel("Value")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            fig.savefig(
                save_path,
                dpi=self._config["visualization"]["default_dpi"],
                bbox_inches="tight",
            )

        return fig

    def stream_comparison(
        self,
        streams: list[dict],
        properties: list[str],
        save_path: Optional[str] = None,
    ) -> plt.Figure:
        """Compare properties of multiple streams as a bar chart.

        Args:
            streams: List of stream property dictionaries.
            properties: List of property keys to compare.
            save_path: File path to save the figure (optional).

        Returns:
            matplotlib Figure object.
        """
        fig, axes = plt.subplots(
            1,
            len(properties),
            figsize=(4 * len(properties), 5),
        )

        if len(properties) == 1:
            axes = [axes]

        stream_names = [s.get("name", f"Stream {i}") for i, s in enumerate(streams)]
        x = np.arange(len(stream_names))
        width = 0.6

        for ax, prop in zip(axes, properties):
            values = [s.get(prop, 0) or 0 for s in streams]
            ax.bar(x, values, width, color="steelblue")
            ax.set_xlabel("Stream")
            ax.set_ylabel(prop)
            ax.set_title(prop.replace("_", " ").title())
            ax.set_xticks(x)
            ax.set_xticklabels(stream_names, rotation=45, ha="right")
            ax.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()

        if save_path:
            fig.savefig(
                save_path,
                dpi=self._config["visualization"]["default_dpi"],
                bbox_inches="tight",
            )

        return fig
