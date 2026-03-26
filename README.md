# pymol-claude-bridge

Control PyMOL from Claude Code using natural language.

An HTTP bridge that lets [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Anthropic's AI coding assistant) inspect, command, and capture screenshots from a live PyMOL session. No copy-pasting commands, no scripting — just describe what you want to see.

<!-- ![Demo](examples/screenshots/hero.png) -->

## How It Works

```
┌─────────────┐     curl/JSON      ┌─────────────┐
│ Claude Code  │ ──────────────────► │   PyMOL     │
│  (terminal)  │ ◄────────────────── │  (GUI app)  │
└─────────────┘   localhost:9876    └─────────────┘
```

1. **PyMOL bridge** (`pymol_bridge.py`) runs as a lightweight HTTP server inside PyMOL on `localhost:9876`
2. **Claude Code skill** (`SKILL.md`) teaches Claude how to use the bridge endpoints via `curl`
3. When you invoke `/pymol` in Claude Code, it connects to the bridge, inspects the session, executes commands, takes screenshots to verify, and iterates

## Features

- **Natural language control** — tell Claude "show me the binding site of 4HHB with hydrogen bonds" and it figures out the PyMOL commands
- **Visual feedback loop** — Claude takes screenshots after every change to verify its own work
- **Safety guardrails** — destructive commands (`quit`, `reinitialize`, `delete all`, shell access) are blocked server-side
- **GUI preservation** — the bridge saves and restores PyMOL's GUI state around rendering operations
- **Session inspection** — Claude queries loaded objects, chains, and selections before making changes
- **Threaded server** — long renders don't block other requests

## Requirements

- [PyMOL](https://pymol.org/) 2.x+ (open-source or incentive)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Anthropic's CLI)
- Python 3.7+
- macOS or Linux (Windows: untested, may work with WSL)

## Installation

### Quick Install

```bash
git clone https://github.com/okbckim/pymol-claude-bridge.git
cd pymol-claude-bridge
bash install.sh
```

The installer copies files to the right places, backs up any existing files, and prints verification steps.

### Manual Install

**Step 1: PyMOL plugins**

```bash
# Create the startup directory if it doesn't exist
mkdir -p ~/.pymol/startup

# Copy the bridge (required) and active_site plugin (optional)
cp pymol-plugin/pymol_bridge.py ~/.pymol/startup/
cp pymol-plugin/active_site.py ~/.pymol/startup/

# Add to ~/.pymolrc so they load automatically
echo 'run ~/.pymol/startup/active_site.py' >> ~/.pymolrc
echo 'run ~/.pymol/startup/pymol_bridge.py' >> ~/.pymolrc
```

**Step 2: Claude Code skill**

```bash
mkdir -p ~/.claude/skills/pymol/references
cp claude-skill/SKILL.md ~/.claude/skills/pymol/
cp claude-skill/references/pymol-commands.md ~/.claude/skills/pymol/references/
```

You may need to restart Claude Code for it to discover the new skill.

### Verify Installation

1. Open PyMOL — you should see: `PyMOL bridge started on http://127.0.0.1:9876`
2. In another terminal:
   ```bash
   curl -sf http://127.0.0.1:9876/ping | python3 -m json.tool
   ```
3. In Claude Code: `/pymol fetch 4HHB and show as cartoon`

### Uninstall

```bash
bash install.sh --uninstall
```

Or manually: remove the files from `~/.pymol/startup/` and `~/.claude/skills/pymol/`, and delete the `run` lines from `~/.pymolrc`.

## Usage

In Claude Code, use the `/pymol` skill:

```
/pymol fetch 4HHB and color by chain
/pymol show the binding site around the ZSB ligand with hydrogen bonds
/pymol make a publication-quality figure with white background
/pymol compare these two structures side by side: 4HHB and 1HHO
```

Claude Code also recognizes molecular visualization requests automatically — mentioning PDB IDs, structure files, or visualization concepts triggers the skill.

See [examples/](examples/) for detailed walkthroughs.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ping` | GET | Health check |
| `/session` | GET | Inspect loaded objects, chains, selections |
| `/fix_gui` | GET | Reset GUI panel to default sizes |
| `/run` | POST | Execute PyMOL commands (with safety guardrails) |
| `/python` | POST | Execute Python in PyMOL namespace (disabled by default) |
| `/screenshot` | POST | Capture viewport as base64 PNG |
| `/render` | POST | Ray-traced render to file |

See [docs/api-reference.md](docs/api-reference.md) for full request/response documentation.

## Configuration

### Port

The bridge defaults to port `9876`. Override with an environment variable:

```bash
export PYMOL_BRIDGE_PORT=9877
```

### Python Endpoint

The `/python` endpoint is **disabled by default** because it runs arbitrary code. To enable:

```bash
export PYMOL_BRIDGE_ALLOW_PYTHON=1
# Then start PyMOL
```

`GET /ping` reports whether `/python` is enabled.

## Bonus: active_site.py

A standalone PyMOL command for quick binding site visualization (works with or without Claude Code):

```
# In PyMOL console
active_site 4HHB, HEM
active_site 8S9A, ZSB, 5.0
```

Creates: gray cartoon protein, yellow ligand sticks, green binding-site sticks, hydrogen bonds, and residue labels — all in one command.

## Security

The bridge is designed for **trusted local use only**:

- **Localhost binding** — the server only listens on `127.0.0.1`, not exposed to the network
- **No CORS headers** — browsers cannot make cross-origin requests to the bridge
- **`/python` disabled by default** — the arbitrary code execution endpoint requires explicit opt-in via environment variable
- **Command blocklist** — common destructive commands are blocked on `/run` as a convenience guardrail. Note: this is **not** a security boundary and can be bypassed. It prevents accidental misuse, not deliberate attacks

If you are running PyMOL on a shared machine or in an environment where other local processes are untrusted, be aware that any process on localhost can access the bridge while it is running.

## Troubleshooting

See [docs/troubleshooting.md](docs/troubleshooting.md) for common issues including:
- Connection problems
- Screenshot/render issues
- GUI panel fixes
- PyMOL installation variants (conda, Schrodinger, open-source)
- Windows notes

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
