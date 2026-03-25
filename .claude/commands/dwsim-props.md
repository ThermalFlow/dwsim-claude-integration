# /dwsim-props - Compound Properties

Queries physical and thermodynamic properties from the DWSIM compound database.

## Usage

```
/dwsim-props <compound>
/dwsim-props search <term>
/dwsim-props critical <compound>
/dwsim-props formation <compound>
/dwsim-props list
```

## Commands

### Full Properties

```
/dwsim-props Water
```

Returns:
- Critical properties (Tc, Pc, Vc, omega, Zc)
- Formation properties (Hf, Gf, Sf at 298.15 K)
- Physical properties (MW, Tb, Tf, liquid density)

### Search Compounds

```
/dwsim-props search propyl
```

Returns list of compounds containing "propyl" in their name.

### Critical Properties Only

```
/dwsim-props critical Propane
```

Returns: Tc, Pc, Vc, acentric factor, Zc.

### Formation Properties Only

```
/dwsim-props formation Methane
```

Returns: Hf, Gf, Sf at standard state (298.15 K, 1 atm).

### List All Compounds

```
/dwsim-props list
```

Lists all compounds available in the DWSIM database.

---

## Python Implementation

```python
# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.automation import DWSIMAutomation
from src.thermo.compound_properties import CompoundDatabase

# Initialize DWSIM to access compound database
dwsim = DWSIMAutomation()
dwsim.initialize()
db = CompoundDatabase()

# --- Search ---
results = db.search("propyl")
print(f"Found {len(results)} compounds matching 'propyl':")
for name in results[:20]:
    print(f"  {name}")

# --- Full info ---
info = db.get_info("Water")
if info:
    print(f"\nCompound: {info.name} ({info.formula})")
    print(f"CAS Number: {info.cas_number}")
    print()
    print("Critical Properties:")
    print(f"  Tc:    {info.critical.critical_temperature_K:.2f} K  ({info.critical.critical_temperature_K - 273.15:.1f} C)")
    print(f"  Pc:    {info.critical.critical_pressure_Pa / 1e6:.4f} MPa  ({info.critical.critical_pressure_Pa / 101325:.2f} atm)")
    print(f"  Vc:    {info.critical.critical_volume_m3_mol:.5f} m3/mol")
    print(f"  omega: {info.critical.acentric_factor:.4f}")
    print(f"  Zc:    {info.critical.critical_compressibility:.4f}")
    print()
    print("Formation Properties (298.15 K, 1 atm):")
    print(f"  Hf: {info.formation.enthalpy_kJ_mol:.2f} kJ/mol")
    print(f"  Gf: {info.formation.gibbs_kJ_mol:.2f} kJ/mol")
    print(f"  Sf: {info.formation.entropy_J_molK:.2f} J/mol.K")
    print()
    print("Physical Properties:")
    print(f"  Molecular Weight:       {info.physical.molecular_weight:.3f} g/mol")
    print(f"  Normal Boiling Point:   {info.physical.normal_boiling_point_K:.2f} K  ({info.physical.normal_boiling_point_K - 273.15:.1f} C)")
    print(f"  Normal Freezing Point:  {info.physical.normal_freezing_point_K:.2f} K  ({info.physical.normal_freezing_point_K - 273.15:.1f} C)")
    print(f"  Liquid Density (298K):  {info.physical.liquid_density_kg_m3:.1f} kg/m3")
```

---

## Expected Output Example

```
Compound: Water (H2O)
CAS Number: 7732-18-5

Critical Properties:
  Tc:    647.14 K  (373.99 C)
  Pc:    22.0640 MPa  (217.75 atm)
  Vc:    0.00005590 m3/mol
  omega: 0.3449
  Zc:    0.2294

Formation Properties (298.15 K, 1 atm):
  Hf: -285.83 kJ/mol
  Gf: -237.14 kJ/mol
  Sf:  69.91 J/mol.K

Physical Properties:
  Molecular Weight:       18.015 g/mol
  Normal Boiling Point:   373.15 K  (100.0 C)
  Normal Freezing Point:  273.15 K  (0.0 C)
  Liquid Density (298K):  997.0 kg/m3
```

---

## Notes

- Compound names must match DWSIM's internal database (case-sensitive for exact match).
- Use `/dwsim-props search` to find the correct name if unsure.
- DWSIM's database contains approximately 2700 pure compounds.
- For mixtures and derived properties (activity coefficients, fugacities), use `/dwsim-flash`.
