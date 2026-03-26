# Changelog

## v0.1.0 — Initial Release

### PyMOL Bridge (`pymol_bridge.py`)
- HTTP server embedded in PyMOL on `localhost:9876`
- Endpoints: `/ping`, `/session`, `/fix_gui`, `/run`, `/render`, `/screenshot`, `/python`
- Safety guardrails: blocked destructive commands (delete all, reinitialize, quit, shell)
- `/python` endpoint disabled by default (opt-in via `PYMOL_BRIDGE_ALLOW_PYTHON=1`)
- GUI state preservation around `cmd.png()` calls
- Threaded server (`ThreadingHTTPServer`) — long renders don't block other requests
- Graceful handling of multiple PyMOL instances
- Configurable port via `PYMOL_BRIDGE_PORT` environment variable

### Claude Code Skill
- Skill definition (`SKILL.md`) for natural language PyMOL control
- Comprehensive command reference (`pymol-commands.md`) covering 11 categories
- 7-step workflow: Inspect, Plan, Execute, Checkpoint, Verify, Iterate, Final Output

### Active Site Plugin (`active_site.py`)
- One-command binding site visualization: `active_site obj, ligand_resn [, cutoff]`
- Gray cartoon, yellow ligand, green binding site, H-bonds, residue labels

### Installer
- `install.sh` with `--uninstall` support
- Backs up existing files before overwriting
- Idempotent (safe to run multiple times)
