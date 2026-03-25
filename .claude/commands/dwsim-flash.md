# /dwsim-flash - Flash Calculations

Runs phase equilibrium (flash) calculations for a given mixture.

## Usage

```
/dwsim-flash <type> <parameters> <composition>
```

## Flash Types

### PT Flash (Pressure-Temperature)

```
/dwsim-flash PT <T_K> <P_Pa> <Compound1:frac,Compound2:frac,...>
```

Example:
```
/dwsim-flash PT 350 101325 Water:0.5,Ethanol:0.5
```

### PH Flash (Pressure-Enthalpy)

```
/dwsim-flash PH <P_Pa> <H_kJ_kg> <composition>
```

### PS Flash (Pressure-Entropy)

```
/dwsim-flash PS <P_Pa> <S_kJ_kgK> <composition>
```

### PV Flash (Pressure-Vapor Fraction)

```
/dwsim-flash PV <P_Pa> <VF_0to1> <composition>
```

Example (saturated vapor):
```
/dwsim-flash PV 202650 1.0 Methane:0.9,Ethane:0.1
```

### Bubble Point (at fixed pressure)

```
/dwsim-flash bubble <P_Pa> <composition>
```

### Dew Point (at fixed pressure)

```
/dwsim-flash dew <P_Pa> <composition>
```

### Bubble Point (at fixed temperature)

```
/dwsim-flash bubble-T <T_K> <composition>
```

### Dew Point (at fixed temperature)

```
/dwsim-flash dew-T <T_K> <composition>
```

---

## Composition Format

Use: `CompoundName:mole_fraction` separated by commas.
Fractions must sum to 1.0.

Examples:
- `Water:0.5,Ethanol:0.5`
- `Methane:0.85,Ethane:0.08,Propane:0.05,n-Butane:0.02`
- `Benzene:0.4,Toluene:0.3,Xylene:0.3`

---

## Python Implementation

```python
# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.automation import DWSIMAutomation
from src.core.flowsheet import FlowsheetManager
from src.thermo.flash_calculations import FlashCalculator
from src.thermo.property_packages import PropertyPackageManager

# --- PARAMETERS (fill from user input) ---
compounds = ["Water", "Ethanol"]
composition = {"Water": 0.5, "Ethanol": 0.5}
T_K = 350.0
P_Pa = 101325.0

# --- SETUP ---
dwsim = DWSIMAutomation()
dwsim.initialize()
fs = dwsim.create_flowsheet()
manager = FlowsheetManager(fs, dwsim)

manager.add_compounds(compounds)

# Auto-recommend property package
pp_manager = PropertyPackageManager()
has_water = "Water" in compounds
# Simplified polarity heuristic — covers common cases only.
# For other polar compounds (acetic acid, amines, glycols, etc.),
# set has_polar=True manually before calling recommend_for_system.
KNOWN_POLAR = {"Ethanol", "Methanol", "Acetone", "Ammonia", "Acetic Acid",
               "Monoethanolamine", "Diethanolamine", "Diethylamine"}
has_polar = bool(set(compounds) & KNOWN_POLAR)
recommended = pp_manager.recommend_for_system(
    compounds, has_polar=has_polar, has_water=has_water
)
manager.set_property_package(recommended[0])

# Create feed stream
stream = manager.add_object("material_stream", "Feed", 100, 100)
stream.set_conditions(
    temperature_K=T_K,
    pressure_Pa=P_Pa,
    molar_flow_mol_s=1.0,
    composition=composition
)

# Run flash
dwsim.calculate(fs)
calculator = FlashCalculator(fs)
result = calculator.pt_flash(stream.dwsim_object, T_K, P_Pa)

# Print results
print("Flash PT Results")
print("=" * 40)
print(f"Temperature:    {result.temperature_K:.2f} K  ({result.temperature_K - 273.15:.1f} C)")
print(f"Pressure:       {result.pressure_Pa / 1e5:.3f} bar")
print(f"Vapor Fraction: {result.vapor_fraction:.4f}")
print(f"Liquid Fraction: {1 - result.vapor_fraction:.4f}")
print()
print("Vapor Composition:")
for comp, frac in result.vapor_composition.items():
    print(f"  {comp}: {frac:.4f}")
print()
print("Liquid Composition:")
for comp, frac in result.liquid_composition.items():
    print(f"  {comp}: {frac:.4f}")
print()
print(f"Enthalpy: {result.enthalpy_kJ_kg:.2f} kJ/kg")
print(f"Entropy:  {result.entropy_kJ_kgK:.4f} kJ/kg.K")
```

---

## Expected Output Example

```
Flash PT Results
========================================
Temperature:    350.00 K  (76.9 C)
Pressure:       1.013 bar
Vapor Fraction: 0.3254
Liquid Fraction: 0.6746

Vapor Composition:
  Ethanol: 0.6521
  Water: 0.3479

Liquid Composition:
  Ethanol: 0.4123
  Water: 0.5877

Enthalpy: -245.3 kJ/kg
Entropy:  1.2340 kJ/kg.K
```

---

## Notes

- For systems near the critical point, results may be sensitive to the property package choice.
- If vapor fraction is 0, the mixture is subcooled liquid at these conditions.
- If vapor fraction is 1, the mixture is superheated vapor.
- Values between 0 and 1 indicate two-phase (VLE) region.
