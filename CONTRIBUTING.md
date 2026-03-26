# Contributing

Thanks for your interest in pymol-claude-bridge!

## Reporting Bugs

Open a GitHub issue with:
- Your OS (macOS, Linux distribution)
- PyMOL version and installation method (conda, Schrodinger, open-source compiled)
- Python version
- The error message or unexpected behavior
- Steps to reproduce

## Suggesting Features

Open a GitHub issue describing the use case. We especially welcome:
- New endpoints for the bridge
- Improvements to the Claude Code skill workflow
- PyMOL command reference additions
- Support for additional PyMOL installation methods

## Pull Requests

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Test manually (see below)
4. Open a PR with a clear description of what and why

### Guidelines

- **No external dependencies** — the bridge uses only Python stdlib + PyMOL API
- **Keep it simple** — the target audience is structural biologists, not software engineers
- **Test your changes** — there are no automated tests yet; see manual testing below

### Manual Testing

1. Copy the modified `pymol_bridge.py` to `~/.pymol/startup/`
2. Start PyMOL — verify the bridge starts (`PyMOL bridge started on ...`)
3. Run these checks:

```bash
# Health check
curl -sf http://127.0.0.1:9876/ping | python3 -m json.tool

# Session inspection
curl -sf http://127.0.0.1:9876/session | python3 -m json.tool

# Execute a command
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "fetch 4HHB, async=0\nshow cartoon"}'

# Screenshot
curl -sf -X POST http://127.0.0.1:9876/screenshot \
  -H "Content-Type: application/json" -d '{}' | python3 -c "
import sys, json; data = json.load(sys.stdin); print('OK' if data.get('ok') else data)"

# Verify blocked commands
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "delete all"}'
# Should return blocked_count: 1

# Verify /python is gated
curl -sf -X POST http://127.0.0.1:9876/python \
  -H "Content-Type: application/json" \
  -d '{"code": "print(1)"}'
# Should return 403 unless PYMOL_BRIDGE_ALLOW_PYTHON=1
```

4. If you modified the Claude Code skill, test with `/pymol` in Claude Code.
