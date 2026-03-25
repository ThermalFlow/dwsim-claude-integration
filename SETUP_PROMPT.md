# DWSIM Automation — AI Setup Prompt

Paste the prompt below into Claude Code (or any AI assistant with file and shell access)
at the root of this project. The AI will detect your environment, configure everything,
and verify the setup is working.

---

## How to use

1. Open this project folder in Claude Code (or your AI tool of choice)
2. Copy the prompt between the `---` lines below
3. Paste it as your first message
4. The AI will walk through setup automatically and fix any issues it finds

---

```
I need you to set up the DWSIM Automation library on this machine.
Work through the steps below in order. At each step, check the actual
state of the system before doing anything — don't assume what is or
isn't already configured.

---

STEP 1 — Find the DWSIM installation

Search for DWSIM on this machine. Look for a file called
"DWSIM.Automation.dll" in common installation paths.

On Windows, check:
  - C:\Program Files\DWSIM
  - C:\Program Files (x86)\DWSIM
  - C:\DWSIM
  - Any folder named "DWSIM" under Program Files

On Linux, check:
  - /opt/dwsim
  - /usr/local/dwsim
  - ~/dwsim

On macOS, check:
  - /Applications/DWSIM.app/Contents/Resources
  - ~/Applications/DWSIM.app/Contents/Resources

Search ONLY the common installation paths listed above.
Do NOT scan the entire filesystem (no "find /" or "Get-ChildItem C:\").

Run a targeted search command appropriate for this OS.
Report exactly where it was found (full path to the folder containing
the DLL, not the DLL itself).

If DWSIM is not installed, tell me and stop here — I need to install
it first from https://dwsim.org before continuing.

---

STEP 2 — Check Python environment

Verify:
  a) Python version (must be 3.8 or newer)
  b) Whether pythonnet is installed (pip show pythonnet)
  c) Whether the other dependencies in requirements.txt are installed

If pythonnet is missing or outdated (needs >= 3.0.3), install it.
If other dependencies are missing, install them all at once.
Report what was already installed and what you had to install.

---

STEP 3 — Configure the DWSIM path

Check if the DWSIM_PATH environment variable is already set and
points to the correct folder found in Step 1.

If it is already set correctly, skip to Step 4.

If it is not set or points to the wrong folder:
  - Copy config.example.json to config.json (if config.json does not exist)
  - Open config.json and set "install_path" to the folder found in Step 1
  - Use forward slashes in the path even on Windows

Show me the exact value you wrote into the file so I can confirm it.

---

STEP 4 — Run the environment check

Run: python run.py --check

Read the output carefully. If all checks pass, move to Step 5.

If any check fails:
  - "Python version" failure → report that Python needs to be updated
  - "pythonnet" failure → run: pip install "pythonnet>=3.0.3,<4.0"
  - "DWSIM path" failure → re-examine Step 1, the path may be wrong
  - "DLL not found" failure → the install_path is a parent folder, not
    the folder containing the DLL — adjust the path and retry
  - Any other failure → show me the exact error message

Do not move on until python run.py --check passes completely.

---

STEP 5 — Run the example simulation

Run: python run.py --example

If it runs without errors and prints results, setup is complete.

If it fails, read the error message, diagnose the cause, and fix it
before reporting back to me.

---

STEP 6 — Install the Claude Code integration (optional)

Ask me: "Do you want to install the dwsim-expert agent and commands
for Claude Code?"

If I say yes:
  - Detect the Claude Code user directory (~/.claude on Linux/macOS,
    %USERPROFILE%\.claude on Windows)
  - Check if that directory exists — if not, inform me that Claude Code
    may not be installed and skip this step
  - Copy .claude/agents/dwsim-expert.md to ~/.claude/agents/
  - Copy .claude/commands/dwsim*.md to ~/.claude/commands/
  - Create ~/.claude/skills/dwsim/ if it does not exist
  - Copy .claude/skills/dwsim/SKILL.md to ~/.claude/skills/dwsim/
  - Confirm what was copied

If I say no, skip this step.

---

STEP 7 — Summary

Report the final state of the setup:
  - DWSIM installation path used
  - Python version
  - pythonnet version
  - Which packages were already installed vs newly installed
  - Whether the example simulation ran successfully
  - Whether Claude Code integration was installed
  - Any issues that remain unresolved and what I should do about them

If everything is working, tell me the exact command to run my first
simulation and show me the minimal Python snippet to get started.
```

---

## Notes for specific AI tools

**Claude Code** — Paste the prompt directly into the chat. It has shell
access and can run all the commands automatically without manual steps.

**ChatGPT with Code Interpreter** — It can run Python but not arbitrary
shell commands. Steps 1, 4, and 5 may need to be run manually in your
terminal while ChatGPT guides you through the values to use.

**Cursor / Windsurf / Copilot** — These work similarly to Claude Code.
Paste the prompt in the chat panel with the project open.

**Any other AI** — If your AI cannot run commands, use the prompt as a
checklist: ask the AI to tell you exactly what to run at each step,
then run the commands yourself and paste the output back.
