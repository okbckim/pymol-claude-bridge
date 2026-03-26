# API Reference

The PyMOL bridge exposes a JSON API on `http://127.0.0.1:9876` (configurable via `PYMOL_BRIDGE_PORT`).

All responses are JSON with a top-level `ok` field indicating success or failure.

## Error Response Format

All endpoints return errors in this format:

```json
{
  "ok": false,
  "error": "Human-readable error message"
}
```

HTTP status codes:
- `200` — success
- `400` — bad request (missing fields, invalid JSON)
- `403` — forbidden (`/python` endpoint when disabled)
- `404` — unknown endpoint

---

## GET /ping

Health check. Returns bridge status.

**Response:**
```json
{
  "ok": true,
  "status": "PyMOL bridge active",
  "port": 9876,
  "python_enabled": false
}
```

---

## GET /session

Inspect the current PyMOL session. Returns all loaded objects, selections, and metadata.

**Query parameters:**
- `?view=1` — include the camera view matrix

**Response:**
```json
{
  "ok": true,
  "object_count": 2,
  "selection_count": 1,
  "objects": [
    {
      "name": "4HHB",
      "type": "object:molecule",
      "atoms": 4779,
      "polymer_atoms": 4406,
      "hetatm_atoms": 373,
      "chains": ["A", "B", "C", "D"],
      "states": 1
    }
  ],
  "selections": ["sele"]
}
```

Non-molecule objects (CGO, maps, groups) include `name`, `type`, and `states` only.

---

## GET /fix_gui

Reset the PyMOL GUI panel to default sizes. Fixes layout issues caused by bridge rendering.

**Response:**
```json
{
  "ok": true,
  "status": "GUI reset to defaults"
}
```

---

## POST /run

Execute one or more PyMOL commands (newline-separated).

**Request:**
```json
{
  "commands": "fetch 4HHB, async=0\nremove solvent\nshow cartoon"
}
```

**Response (success):**
```json
{
  "ok": true,
  "executed_count": 3,
  "blocked_count": 0,
  "error_count": 0,
  "executed": ["fetch 4HHB, async=0", "remove solvent", "show cartoon"],
  "blocked": [],
  "errors": []
}
```

**Response (with blocked commands):**
```json
{
  "ok": false,
  "executed_count": 1,
  "blocked_count": 1,
  "error_count": 0,
  "executed": ["show cartoon"],
  "blocked": [{"command": "delete all", "reason": "blocked: delete all"}],
  "errors": []
}
```

### Blocked Commands

These commands are blocked as an accidental-misuse guardrail:
- `delete all`
- `remove all`
- `reinitialize`
- `quit`
- Shell/system calls (`!`, `shell`, `system`, `os.system`, `subprocess.`)

**Note:** This blocklist is a convenience feature, not a security boundary. It can be bypassed through PyMOL's inline Python mode. The bridge is designed for trusted local use only.

---

## POST /render

Render the current scene to a file (optionally with ray tracing).

**Request:**
```json
{
  "path": "/tmp/pymol_render.png",
  "width": 2400,
  "height": 1800,
  "dpi": 300,
  "ray": true,
  "transparent_bg": true
}
```

All fields except `path` are optional:
- `width` — default 1400
- `height` — default 1050
- `dpi` — default 150
- `ray` — default false (ray tracing can be slow for large scenes)
- `transparent_bg` — default true

**Response:**
```json
{
  "ok": true,
  "path": "/tmp/pymol_render.png",
  "width": 2400,
  "height": 1800,
  "dpi": 300,
  "ray": true,
  "bytes": 1234567
}
```

---

## POST /screenshot

Capture the current viewport as a base64-encoded PNG. Used by Claude Code to verify visual output.

**Request:**
```json
{}
```

**Response:**
```json
{
  "ok": true,
  "base64_png": "iVBORw0KGgo...",
  "bytes": 234567
}
```

The image is 1200x900 pixels, no ray tracing (fast capture).

---

## POST /python

Execute arbitrary Python code in PyMOL's namespace. Has access to `cmd` and `util`.

**Disabled by default.** Set `PYMOL_BRIDGE_ALLOW_PYTHON=1` before starting PyMOL to enable.

**Request:**
```json
{
  "code": "for name in cmd.get_names('objects'):\n    print(f'{name}: {cmd.count_atoms(name)} atoms')"
}
```

**Response (enabled):**
```json
{
  "ok": true,
  "output": "4HHB: 4779 atoms\n"
}
```

**Response (disabled — default):**
```json
{
  "ok": false,
  "error": "The /python endpoint is disabled by default for security. Set PYMOL_BRIDGE_ALLOW_PYTHON=1 before starting PyMOL to enable it."
}
```
HTTP status: 403

**Response (code error):**
```json
{
  "ok": false,
  "output": "",
  "error": "name 'undefined_var' is not defined"
}
```
