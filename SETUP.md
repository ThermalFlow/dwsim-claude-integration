# Setup Guide

This guide gets you from zero to running simulations with AI assistance in about 10 minutes.

---

## Step 1 — Install DWSIM

Download and install DWSIM from the official site:
**https://dwsim.org/index.php/download/**

DWSIM is free and open source. The default installer works fine — just click through it.

After installation, note where it was installed. The default paths are:

| OS | Default path |
|----|-------------|
| Windows | `C:\Program Files\DWSIM` |
| Linux | `/opt/dwsim` |
| macOS | `/Applications/DWSIM.app/Contents/Resources` |

---

## Step 2 — Install Python dependencies

You need Python 3.8 or newer. Check with:

```bash
python --version
```

Then install the library dependencies:

```bash
pip install -r requirements.txt
```

The most important package is **pythonnet**, which lets Python talk to DWSIM's .NET engine.

> **Linux users:** You may also need the Mono runtime before installing pythonnet:
> ```bash
> sudo apt-get install mono-complete   # Ubuntu / Debian
> sudo dnf install mono-complete       # Fedora / RHEL
> ```

---

## Step 3 — Configure the DWSIM path

You only need to do this once. Pick one of the two options below.
`DWSIM_PATH` environment variable **takes priority** over config.json — if both are set, the env var wins.

### Option A — Environment variable (recommended)

Set the `DWSIM_PATH` variable to your DWSIM installation folder.

**Windows (Command Prompt):**
```cmd
setx DWSIM_PATH "C:\Program Files\DWSIM"
```

**Windows (PowerShell):**
```powershell
[System.Environment]::SetEnvironmentVariable("DWSIM_PATH", "C:\Program Files\DWSIM", "User")
```

**Linux / macOS:**
```bash
echo 'export DWSIM_PATH="/opt/dwsim"' >> ~/.bashrc
source ~/.bashrc
```

Close and reopen your terminal after setting the variable.

### Option B — config.json file

Copy the example config and edit it:

```bash
# Linux / macOS
cp config.example.json config.json

# Windows (PowerShell)
Copy-Item config.example.json config.json
```

Open `config.json` and set `install_path` to your DWSIM folder:

```json
{
  "dwsim": {
    "install_path": "C:/Program Files/DWSIM"
  }
}
```

> Use forward slashes (`/`) even on Windows — both work in Python.

---

## Step 4 — Verify the setup

After configuring the DWSIM path (either option above), run the built-in check:

```bash
python run.py --check
```

Expected output:

```
DWSIM Automation - Environment Check
=====================================
Python:      3.11.x   OK
pythonnet:   3.0.3    OK
DWSIM path:  C:/Program Files/DWSIM   OK
DLLs found:  6/6   OK

All checks passed. Ready to simulate.
```

If something fails, see the [Troubleshooting](#troubleshooting) section at the end of this file.

---

## Step 5 — Install the Claude Code integration

If you use Claude Code, copy the `.claude/` folder into your project
(or into your global Claude Code directory to use across all projects).

### For this project only

Just open the `dwsim-automation` folder in Claude Code — it will automatically
detect the `.claude/` folder and load the agent and commands.

### For all your projects (global install)

**Windows (PowerShell):**
```powershell
$dest = "$env:USERPROFILE\.claude"
Copy-Item .claude\agents\dwsim-expert.md "$dest\agents\" -Force
Copy-Item .claude\commands\dwsim.md      "$dest\commands\" -Force
Copy-Item .claude\commands\dwsim-flash.md "$dest\commands\" -Force
Copy-Item .claude\commands\dwsim-props.md "$dest\commands\" -Force
New-Item -ItemType Directory -Force "$dest\skills\dwsim" | Out-Null
Copy-Item .claude\skills\dwsim\SKILL.md "$dest\skills\dwsim\" -Force
```

**Linux / macOS:**
```bash
mkdir -p ~/.claude/agents ~/.claude/commands ~/.claude/skills/dwsim
cp .claude/agents/dwsim-expert.md ~/.claude/agents/
cp .claude/commands/dwsim*.md     ~/.claude/commands/
cp .claude/skills/dwsim/SKILL.md  ~/.claude/skills/dwsim/
```

---

## Using the agent in Claude Code

Once installed, you can talk to the `dwsim-expert` agent in natural language:

```
Which property package should I use for CO2 capture in amine solutions?
```

```
My distillation column for ethanol-water is not converging. 20 stages,
reflux ratio 3.0, feed at stage 12. What should I check?
```

```
Write a script to calculate the bubble point of propane-butane 70/30
at pressures from 1 to 20 bar.
```

You can also use the slash commands:

| Command | What it does |
|---------|-------------|
| `/dwsim <request>` | Natural language simulation request |
| `/dwsim-flash PT 300 500000 Methane:0.9,Ethane:0.1` | Run a PT flash |
| `/dwsim-props Water` | Look up compound properties |
| `/dwsim-props search butyl` | Search the compound database |

---

## Running your first simulation manually

```bash
python run.py --example
```

This runs a simple water-ethanol flash at 80 C and 1 atm and prints the results.

To write your own simulation, copy this template:

```python
# -*- coding: utf-8 -*-
from src.core.automation import DWSIMAutomation
from src.core.flowsheet import FlowsheetManager

dwsim = DWSIMAutomation()
dwsim.initialize()

fs  = dwsim.create_flowsheet()
mgr = FlowsheetManager(fs, dwsim)

mgr.add_compounds(["Water", "Ethanol"])
mgr.set_property_package("NRTL")

feed = mgr.add_object("material_stream", "Feed", 100, 100)
feed.set_conditions(
    temperature_K=353.15,   # 80 C
    pressure_Pa=101325.0,   # 1 atm
    molar_flow_mol_s=1.0,
    composition={"Water": 0.5, "Ethanol": 0.5}
)

result = dwsim.calculate(fs)
print("Converged:", result["success"])
```

---

## Troubleshooting

### "DWSIM path not found"

The library cannot locate your DWSIM installation. Fix by setting the path:

```bash
# Check if the variable is set
echo $DWSIM_PATH           # Linux/macOS
echo %DWSIM_PATH%          # Windows cmd
echo $env:DWSIM_PATH       # PowerShell
```

If it prints nothing, go back to Step 3.

### "pythonnet not installed" or import error

```bash
pip install "pythonnet>=3.0.3,<4.0"
```

On some Linux systems you may also need:
```bash
sudo apt-get install mono-complete   # Ubuntu/Debian
```

### "DLL not found" errors

The `install_path` points to a folder that exists but does not contain DWSIM DLLs.
Make sure you are pointing to the DWSIM root folder (the one that contains
`DWSIM.Automation.dll`), not a subfolder.

To find the right folder:

**Windows:**
```powershell
Get-ChildItem "C:\Program Files" -Recurse -Filter "DWSIM.Automation.dll" 2>$null | Select-Object FullName
```

**Linux/macOS:**
```bash
find /opt /usr/local /home /Applications -name "DWSIM.Automation.dll" 2>/dev/null
```

Use the folder containing that file as your `DWSIM_PATH`.

### Simulation does not converge

This is usually a property package or specification issue, not a library problem.
Ask the `dwsim-expert` agent to help diagnose it, or see the convergence guide
in the agent's knowledge base (`.claude/agents/dwsim-expert.md`).

---

## Using with other AI tools (not Claude Code)

The `dwsim-expert` agent is written in plain Markdown and works as a system prompt
for any LLM. Paste the contents of `.claude/agents/dwsim-expert.md` as your
system prompt in ChatGPT, Gemini, or any other tool that supports custom instructions.

The Python library (`src/`) works independently of any AI tool.
