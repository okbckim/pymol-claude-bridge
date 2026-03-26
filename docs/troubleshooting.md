# Troubleshooting

## Connection Issues

### "Connection refused" when running curl

The bridge isn't running. Check:

1. **Is PyMOL open?** The bridge runs inside PyMOL — it starts when PyMOL starts.
2. **Did the bridge start?** Look for `PyMOL bridge started on http://127.0.0.1:9876` in the PyMOL console.
3. **Port conflict?** If another PyMOL instance is already running the bridge, the second instance prints a warning. Close the first instance or stop its bridge with `stop_bridge` in the PyMOL console.
4. **Custom port?** If you set `PYMOL_BRIDGE_PORT`, make sure your curl commands use the same port.

### "Another PyMOL instance is likely already running the bridge"

Only one PyMOL instance can run the bridge at a time. The first instance claims the port. Options:
- Use the first instance (the bridge is already running there)
- In the first instance, run `stop_bridge` in the PyMOL console, then `start_bridge` in the second
- Use a different port: `export PYMOL_BRIDGE_PORT=9877` before starting the second PyMOL

## Screenshot/Render Issues

### Screenshot shows a black or empty viewport

- The structure might be off-screen. Run: `orient` or `zoom all` via `/run`
- All representations might be hidden. Check with `GET /session` to see what's loaded
- The viewport might be too small. Resize the PyMOL window

### Render produces an empty or tiny file

- `cmd.png()` is asynchronous in some PyMOL builds. The bridge adds brief delays, but extremely large scenes may need more time
- Try rendering at a lower resolution first to verify the scene is correct

### Render is very slow

Ray tracing large surfaces is computationally expensive. Options:
- Skip ray tracing for drafts: set `"ray": false`
- Reduce resolution: use 1200x900 instead of 2400x1800
- Hide surfaces before rendering, or reduce surface quality

### GUI panel looks wrong after rendering

The bridge saves and restores GUI settings around `cmd.png()` calls, but if something goes wrong:
- Run `GET /fix_gui` to reset the panel
- Or in PyMOL: `set internal_gui_width, 250` and `set internal_gui_control_size, 20`
- **Never** set `internal_gui_control_size` to `-1` — it locks the panel permanently

## /python Endpoint

### 403 Forbidden

The `/python` endpoint is disabled by default for security. To enable:

```bash
export PYMOL_BRIDGE_ALLOW_PYTHON=1
# Then start (or restart) PyMOL
```

Verify with `GET /ping` — the response includes `"python_enabled": true` when active.

## PyMOL Installation Variants

The bridge is tested primarily with **PyMOL 2.x on macOS**. Notes on other installations:

### Conda-installed PyMOL
- `~/.pymol/startup/` should work. If not, check `pymol -c 'import pymol; print(pymol.__path__)'` for the correct plugin directory.

### Schrodinger PyMOL
- The incentive (commercial) version uses the same plugin mechanism. `~/.pymolrc` and `~/.pymol/startup/` should work.

### Open-source compiled PyMOL
- Ensure Python 3.7+ (required for `ThreadingHTTPServer`).
- If PyMOL was compiled without the GUI, screenshots and renders still work but produce headless output.

### Linux
- Same installation steps as macOS. Paths are identical (`~/.pymol/startup/`, `~/.pymolrc`).
- Ensure the PyMOL binary is in your PATH.

### Windows
- **Not officially supported.** The bridge may work under WSL (Windows Subsystem for Linux) with a Linux PyMOL installation.
- Native Windows PyMOL uses different config paths. PRs welcome to add Windows support.

## Claude Code Skill

### `/pymol` skill not recognized

- The skill files must be in `~/.claude/skills/pymol/`
- You may need to restart Claude Code after installing the skill
- Verify: `ls ~/.claude/skills/pymol/SKILL.md` should show the file

### Skill triggers on unrelated content

The skill has broad trigger keywords (e.g., "surface", "sticks"). If it activates unexpectedly, just tell Claude Code you don't need PyMOL for this task.
