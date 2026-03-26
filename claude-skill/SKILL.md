---
name: pymol
description: >
  Control a live PyMOL session through an HTTP bridge from Claude Code.
  Use this skill whenever the user asks to visualize a protein structure, make a molecular figure,
  style a PDB, render a publication image, show interactions, color chains, or anything involving
  PyMOL. Also trigger when the user mentions PDB IDs (e.g. "4HHB"), structure files (.pdb, .cif,
  .sdf, .mol2), or molecular visualization concepts like cartoon, surface, sticks, B-factors,
  ligand binding, hydrogen bonds, or Goodsell style. Trigger even for vague requests like
  "make a nice figure of this protein" or "show me what this structure looks like."
---

# PyMOL Bridge Skill

You control a live PyMOL session via an HTTP bridge at `http://127.0.0.1:9876`.

<!-- $ARGUMENTS is a Claude Code skill variable — it is replaced at runtime
     with whatever the user typed after /pymol. On GitHub this appears as
     literal text; that is expected. -->
The user's request: $ARGUMENTS

For the full PyMOL command reference (representations, coloring, selections, publication
presets, Goodsell style, etc.), read `references/pymol-commands.md` in this skill directory.

## Connection

Before doing anything, verify the bridge is alive:

```bash
curl -sf http://127.0.0.1:9876/ping
```

If it fails, tell the user:
> The PyMOL bridge isn't reachable. Please run this inside PyMOL:
> `run ~/.pymol/startup/pymol_bridge.py`

Do not proceed until `/ping` succeeds.

After confirming the bridge is alive, always run this to fix the GUI panel and viewport:

```bash
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "set internal_gui_width, 250\nset internal_gui_control_size, 20"}'
```

Also run this **after every batch of commands** that changes the view to prevent
truncated/clipped molecules:

```bash
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "zoom all, 5\nclip slab, 200"}'
```

These two steps fix recurring issues where bridge commands disrupt the GUI panel
(not resizable, weird look) and viewport clipping (molecules truncated).

## Endpoints

### GET /session
Inspect what's currently loaded — objects, chains, atom counts, selections.
Add `?view=1` for the camera matrix.

```bash
curl -sf http://127.0.0.1:9876/session | python3 -m json.tool
```

### POST /run
Execute one or more PyMOL commands (newline-separated).
Destructive commands (reinitialize, quit, delete all, shell) are blocked server-side.

```bash
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "fetch 4HHB, async=0\nremove solvent\nshow cartoon"}'
```

### POST /python
Run arbitrary Python in PyMOL's namespace. Has access to `cmd` and `util`.
Use this for logic that's awkward as raw commands (loops, conditionals, queries).

**Note:** This endpoint is disabled by default. The user must set
`PYMOL_BRIDGE_ALLOW_PYTHON=1` before starting PyMOL to enable it.

```bash
curl -sf -X POST http://127.0.0.1:9876/python \
  -H "Content-Type: application/json" \
  -d '{"code": "print(cmd.get_names())"}'
```

### POST /screenshot
Capture the current viewport as a base64 PNG. Use this to verify your work.

```bash
curl -sf -X POST http://127.0.0.1:9876/screenshot \
  -H "Content-Type: application/json" -d '{}' | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
if data.get('ok'):
    with open('/tmp/pymol_viewport.png', 'wb') as f:
        f.write(base64.b64decode(data['base64_png']))
    print('Saved to /tmp/pymol_viewport.png')
else:
    print('Error:', data.get('error'))
"
```

Then **read the saved PNG** to see what PyMOL is showing.

### POST /render
Ray-traced render to a file. For final publication output.

```bash
curl -sf -X POST http://127.0.0.1:9876/render \
  -H "Content-Type: application/json" \
  -d '{"path": "/tmp/pymol_render.png", "width": 2400, "height": 1800, "dpi": 300, "ray": true}'
```

## Workflow

Follow this loop for every task:

### 1. Inspect
Always start with `GET /session` to understand what's loaded. Never assume the session
is empty — the user may already have structures open.

### 2. Plan
Before sending commands, briefly state what you're going to do and why. For complex
visualizations, outline the steps so the user can course-correct early.

### 3. Execute
Send commands via `/run` (or `/python` for complex logic). Batch related commands into
a single `/run` call where possible — this avoids race conditions and is faster.

Always use `async=0` with `fetch` so the structure loads before subsequent commands run.

### 4. Checkpoint
Save a session snapshot after major steps so the user can revert:

```
save /tmp/pymol_checkpoint.pse
```

### 5. Verify (critical)
After every visual change, take a screenshot and **actually look at it**. Describe what
you see: colors, representations, orientation, any problems. This is your feedback loop.
Don't skip this — PyMOL commands can fail silently, and the only way to catch issues
is to look.

### 6. Iterate
If something looks off, fix it and screenshot again. Common issues:
- Structure didn't load (check spelling of PDB ID, try lowercase)
- Selection is empty (verify chain/residue names via `/session` or `/python`)
- Colors wrong (carbon coloring overrides — apply `util.cnc` after chain coloring)
- Clutter (hide everything first, then selectively show what matters)

### 7. Final output
When the user is happy:
1. Save the session: `save ~/path/to/project_name.pse`
2. Render high-quality: `/render` with `ray: true`, 2400x1800+, dpi 300
3. Tell the user where both files are

Always offer to save the `.pse` so they can tweak in the GUI later.

## Error Handling

**curl fails (connection refused):**
Bridge is down. Ask user to restart it in PyMOL.

**`/run` returns `{"ok": false, "error": "..."}`:**
Read the error message. Common causes: typo in command, object doesn't exist,
selection syntax error. Fix and retry — don't just report the error and stop.

**`fetch` returns nothing / object not in session after fetch:**
- PDB ID might be wrong — double-check with the user
- Try lowercase: `fetch 4hhb` instead of `fetch 4HHB`
- For AlphaFold structures, use the full URL with `load` instead of `fetch`

**Screenshot shows a black/empty viewport:**
- The structure might be off-screen: run `orient` or `zoom all`
- Representations might all be hidden: check with `GET /session`

**Render hangs or is very slow:**
Ray tracing large surfaces is slow. Warn the user if the scene has surfaces on
large complexes. Offer to reduce resolution or skip ray tracing for drafts.

**`/python` returns 403:**
The endpoint is disabled by default. Ask the user to set `PYMOL_BRIDGE_ALLOW_PYTHON=1`
before starting PyMOL, then restart PyMOL.

## Rules

1. **Inspect before modifying** — always check `/session` first
2. **Never issue destructive commands** — no `reinitialize`, `quit`, `delete all`
3. **Verify visually after every change** — screenshot + describe what you see
4. **Checkpoint sessions** — save `.pse` before major changes and at the end
5. **Batch commands** — group related commands into one `/run` call
6. **Handle errors gracefully** — read error messages, diagnose, fix, retry
7. **Use `async=0`** — always, with every `fetch` command
8. **Stay within the user's request** — don't restyle things the user didn't ask about
