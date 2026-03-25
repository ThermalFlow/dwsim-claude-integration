# -*- coding: utf-8 -*-
"""CLI entry point for DWSIM Automation.

Usage:
    python run.py --check      Verify environment setup
    python run.py --example    Run a quick PT flash example
"""

import argparse
import sys


def check_environment():
    """Verify that all dependencies and paths are properly configured."""
    print("DWSIM Automation - Environment Check")
    print("=" * 37)

    # Python version
    v = sys.version_info
    ok = v >= (3, 8)
    print(f"Python:          {v.major}.{v.minor}.{v.micro}   {'OK' if ok else 'FAIL (need >=3.8)'}")
    if not ok:
        return False

    # pythonnet
    try:
        import clr  # noqa: F401
        import importlib.metadata
        pn_ver = importlib.metadata.version("pythonnet")
        print(f"pythonnet:       {pn_ver}    OK")
    except Exception:
        print("pythonnet:       NOT FOUND   FAIL")
        print("  Install with: pip install pythonnet")
        return False

    # DWSIM path
    try:
        from src.core.automation import DWSIMAutomation
        dwsim = DWSIMAutomation()
        path = dwsim._dwsim_path
        print(f"DWSIM path:      {path}   OK")
    except Exception as e:
        print(f"DWSIM path:      FAIL - {e}")
        return False

    # DLLs
    dlls = dwsim._config.get("dwsim", {}).get("dlls", [])
    found = sum(1 for d in dlls if (path / d).exists())
    status = "OK" if found == len(dlls) else "WARN"
    print(f"DWSIM DLLs:      {found}/{len(dlls)} found   {status}")

    print()
    if found == len(dlls):
        print("All checks passed.")
        return True
    else:
        missing = [d for d in dlls if not (path / d).exists()]
        print(f"Missing DLLs: {', '.join(missing)}")
        return False


def run_example():
    """Run a minimal PT flash calculation to verify everything works."""
    from src.core.automation import DWSIMAutomation
    from src.core.flowsheet import FlowsheetManager

    print("Running example: CH4/C2H6/C3H8 PT flash at 200K, 30 bar")
    print("-" * 55)

    dwsim = DWSIMAutomation()
    dwsim.initialize()

    fs = dwsim.create_flowsheet()
    mgr = FlowsheetManager(fs, dwsim)

    mgr.add_compounds(["Methane", "Ethane", "Propane"])
    mgr.set_property_package("Peng-Robinson")

    feed = mgr.add_object("material_stream", "Feed", 100, 100)
    feed.set_conditions(
        temperature_K=200.0,
        pressure_Pa=3_000_000,
        molar_flow_mol_s=1.0,
        composition={"Methane": 0.80, "Ethane": 0.15, "Propane": 0.05},
    )

    result = dwsim.calculate(fs)
    print(f"Converged: {result['success']}")

    if result["errors"]:
        for err in result["errors"]:
            print(f"  Error: {err}")
    else:
        vf = feed.dwsim_object.GetPropertyValue("PROP_MS_27")
        t = feed.dwsim_object.GetPropertyValue("PROP_MS_0")
        p = feed.dwsim_object.GetPropertyValue("PROP_MS_1")
        print(f"Temperature:    {t:.2f} K")
        print(f"Pressure:       {p / 1e5:.2f} bar")
        print(f"Vapor fraction: {vf:.4f}")

    print()
    print("Example completed.")


def main():
    parser = argparse.ArgumentParser(description="DWSIM Automation CLI")
    parser.add_argument("--check", action="store_true", help="Verify environment setup")
    parser.add_argument("--example", action="store_true", help="Run a quick flash example")
    args = parser.parse_args()

    if args.check:
        success = check_environment()
        sys.exit(0 if success else 1)
    elif args.example:
        run_example()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
