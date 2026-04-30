# -*- coding: utf-8 -*-
"""
Steam Boiler Heat Recovery Cycle
=================================
Rankine-cycle flowsheet with an economizer (shell-and-tube heat exchanger)
that recovers boiler exhaust heat to preheat the feed water before it enters
the boiler.

Cycle topology
--------------

  [SH1: Hot exhaust]──►[Economizer hot-in]
                              │
              [S1]──►[FeedPump]──►[S2]──►[Economizer cold-in]
                                               │
                                         [S3: preheated water]
                                               │
                                           [Boiler]──►[S4: 300 °C steam]
                                               │
                                          [Turbine]──►[S5: exhaust steam]
                                               │
                                          [Condenser]──►[S6: sat. liquid]

  [SH2: Cooled exhaust]◄──[Economizer hot-out]

Operating conditions
--------------------
  Property package : IAPWS-97 Steam Tables (pure water)
  Boiler pressure  : 2 000 kPa  (≈ 20 bar)
  Condenser pressure:   10 kPa  (≈ 0.1 bar, Tsat ≈ 45 °C)
  Boiler outlet T  :  300 °C   (573.15 K) – superheated steam
  Economizer target: cold side preheated to 150 °C (423.15 K)
  Feed pump η      :  75 %
  Turbine η        :  85 %

Equipment tags
--------------
  FeedPump   – pump raising condensate from condenser pressure to boiler pressure
  Economizer – shell-and-tube HX: hot = boiler exhaust, cold = pump outlet water
  Boiler     – heater to 300 °C at 2 000 kPa
  Turbine    – isentropic expander 2 000 kPa → 10 kPa
  Condenser  – cooler condensing exhaust steam to saturated liquid

Stream tags
-----------
  S1   Feed water inlet  (sat. liquid, 45 °C, 10 kPa)
  S2   Pump outlet       (~46 °C, 2 000 kPa)
  S3   Economizer cold outlet (preheated water, 150 °C, 2 000 kPa)
  S4   Boiler outlet     (superheated steam, 300 °C, 2 000 kPa)
  S5   Turbine outlet    (wet steam, 10 kPa)
  S6   Condenser outlet  (saturated liquid, ~45 °C, 10 kPa)
  SH1  Hot side inlet    (boiler exhaust hot water, 200 °C, 2 100 kPa)
  SH2  Hot side outlet   (cooled exhaust leaving economizer)

Energy stream tags
------------------
  E_Pump      – shaft work consumed by FeedPump
  E_Boiler    – heat input to Boiler
  E_Turbine   – shaft work produced by Turbine
  E_Condenser – heat rejected by Condenser
"""

import os
import sys
import json
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
logger = logging.getLogger("steam_heat_recovery")

# ── library imports ──────────────────────────────────────────────────────────
from src.core.automation import DWSIMAutomation
from src.core.flowsheet import FlowsheetManager
from src.unitops.exchangers import HeatExchangerMode


# ── constants ────────────────────────────────────────────────────────────────
P_BOILER_Pa   = 2_000_000.0   # 2 000 kPa = 20 bar
P_COND_Pa     =    10_000.0   # 10 kPa = 0.1 bar
T_BOILER_K    =       573.15  # 300 °C
T_COND_K      =       318.15  # ~45 °C (Tsat at 10 kPa)
T_ECON_COLD_K =       423.15  # 150 °C – economizer cold-side outlet target
T_HOT_IN_K    =       473.15  # 200 °C – boiler exhaust hot stream inlet
P_HOT_IN_Pa   = 2_100_000.0   # slightly above boiler pressure (hot side)

FLOW_MAIN_mol_s = 1.0    # main steam cycle flow rate  [mol/s]
FLOW_HOT_mol_s  = 2.0    # hot-side exhaust flow rate  [mol/s]

ETA_PUMP     = 0.75
ETA_TURBINE  = 0.85


# ── diagram layout helpers ───────────────────────────────────────────────────
# Objects are placed on a grid so the flowsheet diagram looks tidy.

def _pos(col: int, row: int) -> tuple[float, float]:
    """Convert (col, row) grid coordinates to canvas (x, y) pixels."""
    return 150 + col * 220, 100 + row * 180


def build_flowsheet(manager: FlowsheetManager) -> dict:
    """Add all objects to the flowsheet and return references by tag."""

    objs: dict = {}

    # ── material streams ─────────────────────────────────────────────────────
    for tag, col, row in [
        ("S1",   0, 2),    # feed water (cold, loop inlet)
        ("S2",   1, 2),    # pump outlet
        ("S3",   2, 2),    # economizer cold outlet
        ("S4",   3, 1),    # boiler outlet (superheated steam)
        ("S5",   3, 3),    # turbine outlet (exhaust)
        ("S6",   2, 3),    # condenser outlet (sat. liquid)
        ("SH1",  2, 0),    # hot-side inlet (boiler exhaust)
        ("SH2",  1, 0),    # hot-side outlet (cooled exhaust)
    ]:
        x, y = _pos(col, row)
        objs[tag] = manager.add_object("material_stream", tag, x, y)

    # ── energy streams ───────────────────────────────────────────────────────
    for tag, col, row in [
        ("E_Pump",      0, 3),
        ("E_Boiler",    3, 0),
        ("E_Turbine",   4, 2),
        ("E_Condenser", 2, 4),
    ]:
        x, y = _pos(col, row)
        objs[tag] = manager.add_object("energy_stream", tag, x, y)

    # ── unit operations ──────────────────────────────────────────────────────
    for tag, utype, col, row in [
        ("FeedPump",   "pump",          1, 2),
        ("Economizer", "heat_exchanger",2, 1),
        ("Boiler",     "heater",        3, 2),
        ("Turbine",    "expander",      3, 2),  # positioned next to boiler
        ("Condenser",  "cooler",        2, 3),
    ]:
        x, y = _pos(col, row)
        # Offset overlapping equipment vertically for visual clarity
        if tag == "Turbine":
            x, y = _pos(4, 2)
        objs[tag] = manager.add_object(utype, tag, x, y)

    return objs


def configure_equipment(manager: FlowsheetManager, objs: dict) -> None:
    """Set operating parameters on all unit operations."""

    # FeedPump: condensate → boiler pressure (use Delta_P mode — confirmed working)
    pump = objs["FeedPump"]
    pump.set_pressure_increase(P_BOILER_Pa - P_COND_Pa)   # 1 990 000 Pa
    pump.set_efficiency(ETA_PUMP)

    # Economizer: specify cold-side outlet temperature (DWSIM CalcTempHotOut=0)
    # Pressure drops set to 0 — avoids issues with the property not being found
    # on the DWSIM interface (can be re-enabled once property names are confirmed).
    hx = objs["Economizer"]
    hx.set_calculation_mode(HeatExchangerMode.CALC_HOT_OUTLET)
    hx.set_cold_side_outlet_temperature(T_ECON_COLD_K)
    hx.set_flow_direction(countercurrent=True)
    hx.set_pressure_drop_hot(0.0)
    hx.set_pressure_drop_cold(0.0)

    # Boiler (heater): outlet = superheated steam at 300 °C
    boiler = objs["Boiler"]
    boiler.set_outlet_temperature(T_BOILER_K)
    boiler.set_pressure_drop(0.0)

    # Turbine (expander): expand to condenser pressure
    turbine = objs["Turbine"]
    turbine.set_outlet_pressure(P_COND_Pa)
    turbine.set_adiabatic_efficiency(ETA_TURBINE)

    # Condenser (cooler): outlet = saturated liquid (VF = 0)
    condenser = objs["Condenser"]
    condenser.set_vapor_fraction(0.0)
    condenser.set_pressure_drop(0.0)


def set_stream_conditions(manager: FlowsheetManager, objs: dict) -> None:
    """Set inlet stream conditions."""

    composition = {"Water": 1.0}

    # S1 – feed water (saturated liquid at condenser conditions)
    objs["S1"].set_conditions(
        temperature_K=T_COND_K,
        pressure_Pa=P_COND_Pa,
        molar_flow_mol_s=FLOW_MAIN_mol_s,
        composition=composition,
    )

    # SH1 – boiler exhaust hot stream entering the economizer
    objs["SH1"].set_conditions(
        temperature_K=T_HOT_IN_K,
        pressure_Pa=P_HOT_IN_Pa,
        molar_flow_mol_s=FLOW_HOT_mol_s,
        composition=composition,
    )


def connect_flowsheet(manager: FlowsheetManager) -> None:
    """Wire all streams and equipment together.

    Connection conventions for DWSIM ConnectObjects(source, target, src_port, tgt_port):
      Material stream  →  unit-op   : source = stream (port 0), target = unit-op inlet port
      Unit-op          →  material stream: source = unit-op outlet port, target = stream (port 0)
      Energy stream    →  unit-op   : source = energy stream (port 0), target = energy port on unit-op
      Unit-op          →  energy stream: source = unit-op energy outlet port, target = energy stream (port 0)

    HeatExchanger ports
      Inlet  port 0 = hot-side material in
      Inlet  port 1 = cold-side material in
      Outlet port 0 = hot-side material out
      Outlet port 1 = cold-side material out

    Pump / Heater / Cooler
      Inlet  port 0 = material in
      Outlet port 0 = material out
      Inlet  port 1 = energy in  (pump, heater)
      Outlet port 0 (energy) for cooler / expander → connect via energy stream as target

    Expander (turbine)
      Inlet  port 0 = material in
      Outlet port 0 = material out
      Outlet port 1 = energy out
    """

    c = manager.connect

    # ── main cycle ───────────────────────────────────────────────────────────
    # S1 → FeedPump
    c("S1",       "FeedPump",   0, 0)
    # FeedPump → S2
    c("FeedPump", "S2",         0, 0)

    # S2 → Economizer cold side (inlet port 1)
    c("S2",        "Economizer", 0, 1)
    # Economizer cold side out (outlet port 1) → S3
    c("Economizer", "S3",        1, 0)

    # S3 → Boiler
    c("S3",    "Boiler",  0, 0)
    # Boiler → S4
    c("Boiler", "S4",     0, 0)

    # S4 → Turbine
    c("S4",     "Turbine", 0, 0)
    # Turbine → S5
    c("Turbine", "S5",     0, 0)

    # S5 → Condenser
    c("S5",       "Condenser", 0, 0)
    # Condenser → S6
    c("Condenser", "S6",       0, 0)

    # ── hot side of economizer ───────────────────────────────────────────────
    # SH1 → Economizer hot side (inlet port 0)
    c("SH1",       "Economizer", 0, 0)
    # Economizer hot side out (outlet port 0) → SH2
    c("Economizer", "SH2",       0, 0)

    # ── energy connections ────────────────────────────────────────────────────
    # Note: DWSIM Pump only accepts energy as an INPUT (E_Pump → Pump), not as
    # an outlet, so E_Pump is left unconnected (shaft work is read from DeltaQ).
    # Boiler energy outlet (port 1) → E_Boiler   (calculated heat duty)
    c("Boiler",     "E_Boiler",    1, 0)
    # Turbine energy outlet (port 1) → E_Turbine (calculated power generated)
    c("Turbine",    "E_Turbine",   1, 0)
    # Condenser energy outlet (port 1) → E_Condenser (calculated heat rejected)
    c("Condenser",  "E_Condenser", 1, 0)


def print_results(manager: FlowsheetManager, objs: dict) -> None:
    """Print a formatted results table.

    Args:
        manager: FlowsheetManager (for stream results).
        objs: Dict of tag → wrapper objects (for equipment results via get_results()).
    """

    def _stream_row(tag: str) -> None:
        r = manager.get_stream_results(tag)
        if r:
            T_C   = r["temperature_K"] - 273.15
            P_kPa = r["pressure_Pa"] / 1000.0
            VF    = r["vapor_fraction"]
            h     = r["enthalpy_kJ_kg"]
            F     = r["molar_flow_mol_s"]
            print(
                f"  {tag:<6}  {T_C:>8.2f} °C  "
                f"{P_kPa:>9.1f} kPa  "
                f"VF={VF:.3f}  "
                f"h={h:>9.2f} kJ/kg  "
                f"F={F:.3f} mol/s"
            )
        else:
            print(f"  {tag:<6}  (no results)")

    print("\n" + "=" * 75)
    print("  STEAM BOILER HEAT RECOVERY CYCLE – RESULTS")
    print("=" * 75)

    print("\n  STREAM RESULTS")
    print("  " + "-" * 70)
    print(f"  {'Tag':<6}  {'T':>11}  {'P':>12}  {'VF':>6}  {'h':>14}  {'F':>10}")
    print("  " + "-" * 70)
    for tag in ("S1", "S2", "S3", "S4", "S5", "S6", "SH1", "SH2"):
        _stream_row(tag)

    print("\n  EQUIPMENT RESULTS")
    print("  " + "-" * 70)

    # Use wrapper get_results() — these use reflection to read Nullable properties.
    pump_r  = objs["FeedPump"].get_results()
    hx_r    = objs["Economizer"].get_results()
    boil_r  = objs["Boiler"].get_results()
    turb_r  = objs["Turbine"].get_results()
    cond_r  = objs["Condenser"].get_results()

    pump_pw   = abs(pump_r.get("power_kW") or 0)
    boil_duty = abs(boil_r.get("duty_kW") or 0)
    turb_pw   = abs(turb_r.get("power_generated_kW") or 0)
    cond_duty = abs(cond_r.get("duty_kW") or 0)
    hx_duty   = abs(hx_r.get("duty_kW") or 0)
    hx_lmtd   = hx_r.get("lmtd_K") or 0
    hx_ua     = hx_r.get("ua_W_K") or 0

    print(f"  FeedPump    power consumed    : {pump_pw:.3f} kW")
    print(f"  Economizer  duty transferred  : {hx_duty:.3f} kW")
    print(f"  Economizer  LMTD              : {hx_lmtd:.3f} K")
    print(f"  Economizer  UA                : {hx_ua:.3f} W/K")
    print(f"  Boiler      heat input        : {boil_duty:.3f} kW")
    print(f"  Turbine     power generated   : {turb_pw:.3f} kW")
    print(f"  Condenser   heat rejected     : {cond_duty:.3f} kW")

    if boil_duty > 0:
        net_work  = turb_pw - pump_pw
        eta_cycle = net_work / boil_duty * 100.0
        print(f"\n  NET WORK OUTPUT   : {net_work:.3f} kW")
        print(f"  BOILER HEAT IN    : {boil_duty:.3f} kW")
        print(f"  CYCLE EFFICIENCY  : {eta_cycle:.2f} %")

    print("=" * 75 + "\n")


def main() -> None:
    logger.info("Initialising DWSIM …")
    dwsim = DWSIMAutomation()
    dwsim.initialize()

    logger.info("Creating flowsheet …")
    fs = dwsim.create_flowsheet()
    manager = FlowsheetManager(fs, dwsim)

    # Single compound – pure water, use IAPWS-97 Steam Tables
    manager.add_compounds(["Water"])
    manager.set_property_package("steam-tables")

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
