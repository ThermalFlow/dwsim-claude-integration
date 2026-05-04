# -*- coding: utf-8 -*-
"""
Heat Pump Cycle – R1233zd(E)
============================
Vapor-compression heat pump using R1233zd(E) (a low-GWP refrigerant) modelled
with the CoolProp property package.

Cycle topology
--------------

  [S1: wet vapor, 22.8 °C / 120 kPa]──►[Evaporator]──►[S2: sat. vapor]──►[C-1 Compressor]──►
          ▲                                    │                                   │
          │                                   E1                                  E2
          │                                                                        │
        [R-1]◄──[S5: wet vapor]◄──[VALVE-1]◄──[S6: sat. liquid]◄──[CL-1 Condenser]
                                                                          │
                                                                         E3

Operating conditions
--------------------
  Property package   : CoolProp
  Refrigerant        : R1233zd(E)
  Low-side pressure  :   120 kPa  (evaporator / valve outlet, Tsat ≈ 22.8 °C)
  High-side pressure : 2 800 kPa  (condenser / compressor outlet, Tsat ≈ 151.3 °C)
  Compressor η       : 85 %  (adiabatic)
  Mass flow rate     : 100 kg/s

Equipment tags
--------------
  Evaporator  – heater that fully vaporises the refrigerant (VF_out = 1.0)
  C-1         – adiabatic compressor, 120 kPa → 2 800 kPa
  CL-1        – cooler that fully condenses the refrigerant (VF_out = 0.0)
  VALVE-1     – isenthalpic expansion valve, 2 800 kPa → 120 kPa
  R-1         – recycle convergence block (closes the cycle loop)

Stream tags
-----------
  S1   Evaporator inlet  (wet vapor, ~22.8 °C, 120 kPa)  – recycle outlet
  S2   Compressor inlet  (saturated vapor, 22.8 °C, 120 kPa)
  S4   Condenser inlet   (superheated vapor, 151.3 °C, 2 800 kPa)
  S6   Valve inlet       (saturated liquid, 151.3 °C, 2 800 kPa)
  S5   Recycle inlet     (wet vapor, 22.8 °C, 120 kPa)  – valve outlet

Energy stream tags
------------------
  E1   Heat absorbed by evaporator   [kW]
  E2   Shaft work consumed by C-1    [kW]
  E3   Heat rejected by CL-1         [kW]
"""

import os
import sys
import logging

# ── resolve project root so imports work from any working directory ──────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s – %(message)s",
)
logger = logging.getLogger("heat_pump_r1233zd")

# ── library imports ──────────────────────────────────────────────────────────
from src.core.automation import DWSIMAutomation
from src.core.flowsheet import FlowsheetManager


# ── cycle operating conditions ───────────────────────────────────────────────
P_EVAP_Pa  =   120_000.0   # 120 kPa  – low-side (evaporator / valve outlet)
P_COND_Pa  = 2_800_000.0   # 2 800 kPa – high-side (condenser / compressor outlet)
T_EVAP_K   =      295.97   # ~22.8 °C – Tsat at 120 kPa; initial guess for recycle stream
ETA_COMP   =        0.85   # compressor adiabatic efficiency

# Refrigerant flow – R1233zd(E) molecular weight = 130.494 g/mol
MASS_FLOW_kg_s   = 100.0
MW_R1233ZDE      = 130.494   # g/mol
MOLAR_FLOW_mol_s = MASS_FLOW_kg_s * 1_000.0 / MW_R1233ZDE   # ≈ 766.3 mol/s


# ── diagram layout helpers ───────────────────────────────────────────────────
def _pos(col: int, row: int) -> tuple:
    """Convert (col, row) grid coordinates to canvas (x, y) pixels."""
    return 150.0 + col * 220.0, 100.0 + row * 180.0


def build_flowsheet(manager: FlowsheetManager) -> dict:
    """Add all objects to the flowsheet and return references keyed by tag."""
    objs: dict = {}

    # ── material streams ─────────────────────────────────────────────────────
    for tag, col, row in [
        ("S1", 0, 2),   # evaporator inlet  (recycle outlet / initial-guess stream)
        ("S2", 1, 2),   # compressor inlet  (evaporator outlet, saturated vapor)
        ("S4", 2, 1),   # condenser inlet   (compressor outlet, superheated vapor)
        ("S6", 2, 3),   # valve inlet       (condenser outlet, saturated liquid)
        ("S5", 1, 3),   # recycle inlet     (valve outlet, wet vapor)
    ]:
        x, y = _pos(col, row)
        objs[tag] = manager.add_object("material_stream", tag, x, y)

    # ── energy streams ───────────────────────────────────────────────────────
    for tag, col, row in [
        ("E1", 0, 3),   # evaporator heat duty
        ("E2", 3, 1),   # compressor shaft work
        ("E3", 3, 3),   # condenser heat duty
    ]:
        x, y = _pos(col, row)
        objs[tag] = manager.add_object("energy_stream", tag, x, y)

    # ── unit operations ──────────────────────────────────────────────────────
    for tag, utype, col, row in [
        ("Evaporator", "heater",     1, 2),
        ("C-1",        "compressor", 2, 2),
        ("CL-1",       "cooler",     2, 2),   # shifted below in the next block
        ("VALVE-1",    "valve",      1, 3),
        ("R-1",        "recycle",    0, 3),
    ]:
        x, y = _pos(col, row)
        if tag == "CL-1":
            x, y = _pos(3, 2)
        objs[tag] = manager.add_object(utype, tag, x, y)

    return objs


def configure_equipment(manager: FlowsheetManager, objs: dict) -> None:
    """Set operating parameters on all unit operations."""

    # Evaporator (heater): bring refrigerant to saturated vapor (VF = 1.0)
    evaporator = objs["Evaporator"]
    evaporator.set_vapor_fraction(1.0)
    evaporator.set_pressure_drop(0.0)

    # Compressor C-1: adiabatic compression to high-side pressure
    compressor = objs["C-1"]
    compressor.set_outlet_pressure(P_COND_Pa)
    compressor.set_adiabatic_efficiency(ETA_COMP)

    # Condenser CL-1 (cooler): bring refrigerant to saturated liquid (VF = 0.0)
    condenser = objs["CL-1"]
    condenser.set_vapor_fraction(0.0)
    condenser.set_pressure_drop(0.0)

    # Expansion valve VALVE-1: isenthalpic throttle to low-side pressure
    valve = objs["VALVE-1"]
    valve.set_outlet_pressure(P_EVAP_Pa)


def set_stream_conditions(manager: FlowsheetManager, objs: dict) -> None:
    """Seed the recycle stream S1 with its initial-guess inlet conditions."""
    composition = {"R1233zd(E)": 1.0}

    # S1 is the recycle-seed stream (evaporator inlet).  Temperature and
    # pressure are held at the low-side saturation point; the recycle block
    # R-1 iterates until the loop converges on the correct wet-vapor state.
    objs["S1"].set_conditions(
        temperature_K=T_EVAP_K,
        pressure_Pa=P_EVAP_Pa,
        molar_flow_mol_s=MOLAR_FLOW_mol_s,
        composition=composition,
    )


def connect_flowsheet(manager: FlowsheetManager) -> None:
    """Wire all streams and equipment together.

    Port conventions (identical to steam_boiler_heat_recovery.py):
      Material stream → unit-op inlet    : stream port 0 → equipment port 0
      Unit-op outlet  → material stream  : equipment port 0 → stream port 0
      Unit-op energy port (1) → energy stream (port 0) for all duties / work
    """
    c = manager.connect

    # ── refrigerant loop ──────────────────────────────────────────────────────
    # S1 → Evaporator → S2
    c("S1",         "Evaporator", 0, 0)
    c("Evaporator", "S2",         0, 0)

    # S2 → Compressor C-1 → S4
    c("S2",  "C-1", 0, 0)
    c("C-1", "S4",  0, 0)

    # S4 → Condenser CL-1 → S6
    c("S4",   "CL-1", 0, 0)
    c("CL-1", "S6",   0, 0)

    # S6 → Expansion valve VALVE-1 → S5
    c("S6",      "VALVE-1", 0, 0)
    c("VALVE-1", "S5",      0, 0)

    # S5 → Recycle R-1 → S1  (closes the loop)
    c("S5",  "R-1", 0, 0)
    c("R-1", "S1",  0, 0)

    # ── energy connections ────────────────────────────────────────────────────
    c("Evaporator", "E1", 1, 0)   # evaporator heat absorbed
    c("C-1",        "E2", 1, 0)   # compressor shaft work
    c("CL-1",       "E3", 1, 0)   # condenser heat rejected


def print_results(manager: FlowsheetManager, objs: dict) -> None:
    """Print a formatted stream and equipment results summary."""

    def _stream_row(tag: str) -> None:
        r = manager.get_stream_results(tag)
        if r:
            T_C   = r["temperature_K"] - 273.15
            P_kPa = r["pressure_Pa"] / 1_000.0
            vf    = r["vapor_fraction"]
            h     = r["enthalpy_kJ_kg"]
            mdot  = r["molar_flow_mol_s"] * MW_R1233ZDE / 1_000.0  # → kg/s
            print(
                f"  {tag:<8}  {T_C:>8.2f} °C  "
                f"{P_kPa:>9.1f} kPa  "
                f"VF={vf:.3f}  "
                f"h={h:>9.2f} kJ/kg  "
                f"ṁ={mdot:.2f} kg/s"
            )
        else:
            print(f"  {tag:<8}  (no results)")

    print("\n" + "=" * 75)
    print("  HEAT PUMP CYCLE – R1233zd(E) – RESULTS")
    print("=" * 75)

    print("\n  STREAM RESULTS")
    print("  " + "-" * 70)
    print(f"  {'Tag':<8}  {'T':>11}  {'P':>12}  {'VF':>6}  {'h':>14}  {'ṁ':>10}")
    print("  " + "-" * 70)
    for tag in ("S1", "S2", "S4", "S6", "S5"):
        _stream_row(tag)

    print("\n  EQUIPMENT RESULTS")
    print("  " + "-" * 70)

    evap_r = objs["Evaporator"].get_results()
    comp_r = objs["C-1"].get_results()
    cond_r = objs["CL-1"].get_results()

    q_evap = abs(evap_r.get("duty_kW") or 0.0)
    w_comp = abs(comp_r.get("power_kW") or 0.0)
    q_cond = abs(cond_r.get("duty_kW") or 0.0)

    print(f"  Evaporator   heat absorbed     : {q_evap:.2f} kW")
    print(f"  Compressor   shaft work input  : {w_comp:.2f} kW")
    print(f"  Condenser    heat rejected     : {q_cond:.2f} kW")

    print(f"\n  Energy balance  Q_evap + W_comp = {q_evap + w_comp:.2f} kW")
    print(f"                  Q_cond          = {q_cond:.2f} kW")

    if w_comp > 0.0:
        cop_heat = q_cond / w_comp
        cop_cool = q_evap / w_comp
        print(f"\n  COP (heating)  = Q_cond / W_comp = {cop_heat:.3f}")
        print(f"  COP (cooling)  = Q_evap / W_comp = {cop_cool:.3f}")

    print("=" * 75 + "\n")


def main() -> None:
    logger.info("Initialising DWSIM …")
    dwsim = DWSIMAutomation()
    dwsim.initialize()

    logger.info("Creating flowsheet …")
    fs = dwsim.create_flowsheet()
    manager = FlowsheetManager(fs, dwsim)

    # Single pure refrigerant – CoolProp handles all transport properties
    manager.add_compounds(["R1233zd(E)"])
    manager.set_property_package("coolprop")

    logger.info("Building flowsheet objects …")
    objs = build_flowsheet(manager)

    logger.info("Configuring equipment …")
    configure_equipment(manager, objs)

    logger.info("Setting stream conditions …")
    set_stream_conditions(manager, objs)

    logger.info("Connecting streams …")
    connect_flowsheet(manager)

    logger.info("Running calculation …")
    result = dwsim.calculate(fs)

    if not result.get("success", True):
        logger.error("Simulation errors: %s", result.get("errors", []))
    else:
        logger.info("Calculation complete.")

    print_results(manager, objs)


if __name__ == "__main__":
    main()
