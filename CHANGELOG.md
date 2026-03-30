# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] - 2026-03-30

### Fixed

- **`FlowsheetManager.add_object()` — critical bug with unit operation wrappers**
  Previously, calling `add_object()` with any unit operation type
  (`"shortcut"`, `"distillation"`, `"heater"`, `"pump"`, etc.) returned
  the raw DWSIM `ISimulationObject` instead of the Python wrapper class.
  This made all helper methods (`set_light_key()`, `set_efficiency()`,
  `set_outlet_temperature()`, etc.) inaccessible after object creation.

  Reported by Prof. Roymel Rodriguez Carpio (EQ/UFRJ).

  **Before (broken):**
  ```python
  sc = mgr.add_object("shortcut", "SC", 100, 100)
  sc.set_light_key("Benzene", 0.98)  # AttributeError: ISimulationObject has no set_light_key
  ```

  **After (fixed):**
  ```python
  sc = mgr.add_object("shortcut", "SC", 100, 100)
  sc.set_light_key("Benzene", 0.98)  # works correctly
  ```

### Changed

- `FlowsheetManager` now populates `_UNITOP_WRAPPERS` lazily via
  `_ensure_wrappers_loaded()` to avoid circular imports at module load time.
  The dict maps every unit op type key to its Python wrapper class.

### Notes

- Streams (`material_stream`, `energy_stream`) behaviour is unchanged —
  they already returned wrappers correctly.
- `get_object()` still returns the raw `ISimulationObject` (correct behaviour,
  used internally for `connect()` / `disconnect()`).

---

## [0.1.0] - 2026-03-25

### Added

- Initial public release.
- `FlowsheetManager` — core abstraction over DWSIM flowsheet operations:
  - `add_compound()`, `add_compounds()`, `get_compounds()`
  - `set_property_package()` with friendly-key lookup catalog
  - `add_object()` for streams and unit operations
  - `connect()`, `disconnect()`, `remove_object()`
  - `list_objects()`, `get_stream_results()`
- `DWSIMAutomation` — session lifecycle (open, save, calculate, close):
  - `DWSIM_PATH` environment variable takes priority over `config.json`
  - Fallback to `config.example.json` when `config.json` is absent
  - DLL path validation uses `Path.is_relative_to()` (Python 3.9+) with
    `Path.relative_to()` fallback for Python 3.8 compatibility
- Python wrapper classes for all major unit operation categories:
  - Columns: `DistillationColumn`, `AbsorptionColumn`, `ShortcutColumn`
  - Exchangers: `HeatExchanger`, `Heater`, `Cooler`
  - Pumps/Compressors: `Pump`, `Compressor`, `Expander`, `Valve`
  - Reactors: `CSTR`, `PFR`, `GibbsReactor`, `EquilibriumReactor`
  - Separators: `FlashSeparator`, `ComponentSeparator`, `Filter`
  - Mixers/Splitters: `Mixer`, `Splitter`, `Recycle`
- Stream wrappers: `MaterialStream`, `EnergyStream` with `set_conditions()`
- Thermodynamics catalog (`PROPERTY_PACKAGES`) with friendly-key lookup
- HTML/PDF report generation via `ReportGenerator` (lazy Jinja2 + pandas)
- Claude Code integration layer:
  - `.claude/agents/dwsim-expert.md` — specialized agent for DWSIM tasks
  - `.claude/commands/dwsim.md` — slash command with usage examples
  - `.claude/skills/dwsim/SKILL.md` — skill descriptor
- `run.py` — CLI entry point with `--check` (validate config) and
  `--example` (run demo simulation) flags
- `SETUP.md` — step-by-step Windows setup guide with PowerShell examples
- `config.example.json` — annotated configuration template
- `requirements.txt` — `pythonnet>=3.0.3`
- MIT License

---

[0.2.0]: https://github.com/fdias78git/dwsim-claude-integration/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/fdias78git/dwsim-claude-integration/releases/tag/v0.1.0
