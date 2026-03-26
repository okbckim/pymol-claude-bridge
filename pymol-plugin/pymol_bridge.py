"""
PyMOL Bridge — lightweight HTTP server for remote control of PyMOL.

Part of pymol-claude-bridge: https://github.com/okbckim/pymol-claude-bridge

Install:
    cp pymol_bridge.py ~/.pymol/startup/
    echo 'run ~/.pymol/startup/pymol_bridge.py' >> ~/.pymolrc

Endpoints:
    GET  /ping              — health check
    GET  /session           — inspect session (objects, chains, atoms, selections)
    GET  /fix_gui           — reset GUI panel width and control size to defaults
    POST /run               — execute PyMOL commands  {"commands": "..."}
    POST /render            — render image            {"path": "...", ...}
    POST /screenshot        — capture viewport PNG, returns base64 image
    POST /python            — execute Python code in PyMOL namespace {"code": "..."}
                              (disabled by default; set PYMOL_BRIDGE_ALLOW_PYTHON=1 to enable)
"""

import json
import os
import re
import base64
import tempfile
import time
import threading
import http.server

from pymol import cmd, util

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BRIDGE_PORT = int(os.environ.get("PYMOL_BRIDGE_PORT", 9876))
ALLOW_PYTHON = os.environ.get("PYMOL_BRIDGE_ALLOW_PYTHON", "0") == "1"

BLOCKED_COMMANDS = [
    ("blocked: delete all", re.compile(r"^\s*delete\s+all\s*$", re.I)),
    ("blocked: remove all", re.compile(r"^\s*remove\s+all\s*$", re.I)),
    ("blocked: reinitialize", re.compile(r"^\s*reinitialize(?:\s|$)", re.I)),
    ("blocked: quit", re.compile(r"^\s*quit(?:\s|$)", re.I)),
    (
        "blocked: shell/system",
        re.compile(
            r"^\s*(?:!|shell(?:\s|$)|system(?:\s|$)|os\.system|subprocess\.)", re.I
        ),
    ),
]


def _blocked_reason(line):
    for reason, pattern in BLOCKED_COMMANDS:
        if pattern.search(line):
            return reason
    return ""


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _get_object_type(obj):
    """Return the PyMOL object type as a string."""
    try:
        otype = cmd.get_type(obj)
        return otype if otype else "unknown"
    except Exception:
        return "unknown"


def tool_inspect_session(include_view=False):
    """Return structured JSON about the current PyMOL session."""
    objects = cmd.get_names("objects")
    selections = cmd.get_names("selections")
    details = []
    for obj in objects:
        otype = _get_object_type(obj)
        if otype in ("object:molecule",):
            try:
                details.append({
                    "name": obj,
                    "type": otype,
                    "atoms": cmd.count_atoms(obj),
                    "polymer_atoms": cmd.count_atoms(f"({obj}) and polymer"),
                    "hetatm_atoms": cmd.count_atoms(f"({obj}) and hetatm"),
                    "chains": cmd.get_chains(obj),
                    "states": cmd.count_states(obj),
                })
            except Exception:
                details.append({"name": obj, "type": otype, "error": "could not inspect"})
        else:
            # CGO, map, group, etc. — no atom-level inspection
            info = {"name": obj, "type": otype}
            try:
                info["states"] = cmd.count_states(obj)
            except Exception:
                pass
            details.append(info)
    out = {
        "ok": True,
        "object_count": len(objects),
        "selection_count": len(selections),
        "objects": details,
        "selections": selections,
    }
    if include_view:
        out["view"] = list(cmd.get_view())
    return out


def tool_run_commands(commands_text):
    """Execute newline-separated PyMOL commands with safety guardrails.

    Note: The command blocklist is a convenience guardrail to prevent accidental
    misuse (e.g., accidentally deleting everything). It is NOT a security boundary
    and can be bypassed. The bridge should only be used on trusted local machines.
    """
    lines = [
        ln.strip()
        for ln in commands_text.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    executed, blocked, errors = [], [], []
    for line in lines:
        reason = _blocked_reason(line)
        if reason:
            blocked.append({"command": line, "reason": reason})
            continue
        try:
            cmd.do(line)
            executed.append(line)
        except Exception as exc:
            errors.append({"command": line, "error": str(exc)})
    return {
        "ok": not blocked and not errors,
        "executed_count": len(executed),
        "blocked_count": len(blocked),
        "error_count": len(errors),
        "executed": executed,
        "blocked": blocked,
        "errors": errors,
    }


def _save_gui_state():
    """Save GUI settings that cmd.png can disrupt."""
    return {
        "internal_gui_width": cmd.get("internal_gui_width"),
        "internal_gui_control_size": cmd.get("internal_gui_control_size"),
    }


def _restore_gui_state(state):
    """Restore GUI settings after cmd.png."""
    for key, val in state.items():
        cmd.set(key, val)


def tool_render(path, width=1400, height=1050, dpi=150, ray=False, transparent_bg=True):
    """Render current scene to an image file."""
    out_path = os.path.abspath(os.path.expanduser(path))
    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    try:
        width = max(256, int(width))
        height = max(256, int(height))
        dpi = max(72, int(dpi))
    except (TypeError, ValueError):
        width, height, dpi = 1400, 1050, 150

    gui_state = _save_gui_state()
    ray_flag = 1 if ray else 0
    cmd.set("ray_opaque_background", 0 if transparent_bg else 1)
    cmd.png(out_path, width=width, height=height, dpi=dpi, ray=ray_flag, quiet=1)
    # Wait briefly for file to be written
    time.sleep(0.3)
    _restore_gui_state(gui_state)

    exists = os.path.exists(out_path)
    size = os.path.getsize(out_path) if exists else 0
    return {
        "ok": exists and size > 0,
        "path": out_path,
        "width": width,
        "height": height,
        "dpi": dpi,
        "ray": bool(ray_flag),
        "bytes": size,
    }


def tool_screenshot():
    """Capture current viewport as base64 PNG (for Claude Code to view)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp_path = tmp.name
    tmp.close()
    gui_state = _save_gui_state()
    try:
        cmd.png(tmp_path, width=1200, height=900, ray=0, quiet=1)
        time.sleep(0.5)
        with open(tmp_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("ascii")
        size = os.path.getsize(tmp_path)
        return {"ok": True, "base64_png": img_b64, "bytes": size}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    finally:
        _restore_gui_state(gui_state)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def tool_python(code):
    """Execute Python code in PyMOL's namespace. Returns captured output.

    WARNING: This endpoint runs arbitrary code with full access to the Python
    interpreter. It is disabled by default and must be explicitly enabled by
    setting the environment variable PYMOL_BRIDGE_ALLOW_PYTHON=1 before
    starting PyMOL.
    """
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        exec(code, {"cmd": cmd, "util": util, "__builtins__": __builtins__})
        output = buffer.getvalue()
        return {"ok": True, "output": output}
    except Exception as exc:
        output = buffer.getvalue()
        return {"ok": False, "output": output, "error": str(exc)}
    finally:
        sys.stdout = old_stdout


# ---------------------------------------------------------------------------
# HTTP Server
# ---------------------------------------------------------------------------


class BridgeHandler(http.server.BaseHTTPRequestHandler):
    """JSON API handler for PyMOL bridge."""

    def log_message(self, fmt, *args):
        # Suppress default logging; print our own
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw)

    def do_GET(self):
        if self.path == "/ping":
            self._send_json({
                "ok": True,
                "status": "PyMOL bridge active",
                "port": BRIDGE_PORT,
                "python_enabled": ALLOW_PYTHON,
            })
        elif self.path == "/session" or self.path.startswith("/session?"):
            include_view = "view=1" in self.path or "view=true" in self.path.lower()
            result = tool_inspect_session(include_view=include_view)
            self._send_json(result)
        elif self.path == "/fix_gui":
            cmd.set("internal_gui_width", 250)
            cmd.set("internal_gui_control_size", 20)
            self._send_json({"ok": True, "status": "GUI reset to defaults"})
        else:
            self._send_json({"ok": False, "error": f"Unknown endpoint: {self.path}"}, 404)

    def do_POST(self):
        try:
            body = self._read_json()
        except Exception as exc:
            self._send_json({"ok": False, "error": f"Invalid JSON: {exc}"}, 400)
            return

        if self.path == "/run":
            commands = body.get("commands", "")
            if not commands:
                self._send_json({"ok": False, "error": "Missing 'commands' field"}, 400)
                return
            result = tool_run_commands(commands)
            self._send_json(result)

        elif self.path == "/render":
            path = body.get("path", "")
            if not path:
                self._send_json({"ok": False, "error": "Missing 'path' field"}, 400)
                return
            result = tool_render(
                path=path,
                width=body.get("width", 1400),
                height=body.get("height", 1050),
                dpi=body.get("dpi", 150),
                ray=body.get("ray", False),
                transparent_bg=body.get("transparent_bg", True),
            )
            self._send_json(result)

        elif self.path == "/screenshot":
            result = tool_screenshot()
            self._send_json(result)

        elif self.path == "/python":
            if not ALLOW_PYTHON:
                self._send_json({
                    "ok": False,
                    "error": (
                        "The /python endpoint is disabled by default for security. "
                        "Set PYMOL_BRIDGE_ALLOW_PYTHON=1 before starting PyMOL to enable it."
                    ),
                }, 403)
                return
            code = body.get("code", "")
            if not code:
                self._send_json({"ok": False, "error": "Missing 'code' field"}, 400)
                return
            result = tool_python(code)
            self._send_json(result)

        else:
            self._send_json({"ok": False, "error": f"Unknown endpoint: {self.path}"}, 404)


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

_server = None
_thread = None


def start_bridge(port=None):
    """Start the PyMOL bridge HTTP server."""
    global _server, _thread, BRIDGE_PORT
    if port:
        BRIDGE_PORT = int(port)

    # Stop existing server if running (allows clean reload)
    if _server is not None:
        try:
            _server.shutdown()
        except Exception:
            pass
        _server = None
        _thread = None

    try:
        http.server.ThreadingHTTPServer.allow_reuse_address = True
        _server = http.server.ThreadingHTTPServer(("127.0.0.1", BRIDGE_PORT), BridgeHandler)
    except OSError as exc:
        _server = None
        print(f"WARNING: Could not start bridge on port {BRIDGE_PORT} ({exc})")
        print(f"  Another PyMOL instance is likely already running the bridge.")
        print(f"  This session will work normally, but without Claude Code control.")
        print(f"  To use the bridge here instead, stop it in the other session first.")
        return

    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()
    print(f"PyMOL bridge started on http://127.0.0.1:{BRIDGE_PORT}")
    print(f"  Endpoints: /ping  /session  /fix_gui  /run  /render  /screenshot  /python")
    if ALLOW_PYTHON:
        print(f"  /python endpoint is ENABLED (PYMOL_BRIDGE_ALLOW_PYTHON=1)")
    else:
        print(f"  /python endpoint is disabled (set PYMOL_BRIDGE_ALLOW_PYTHON=1 to enable)")
    print(f"  Use in Claude Code: /pymol")


def stop_bridge():
    """Stop the PyMOL bridge HTTP server."""
    global _server, _thread
    if _server is None:
        print("Bridge is not running.")
        return
    _server.shutdown()
    _server = None
    _thread = None
    print("PyMOL bridge stopped.")


def bridge_status():
    """Show bridge server status."""
    if _server is not None:
        print(f"Bridge is RUNNING on http://127.0.0.1:{BRIDGE_PORT}")
        print(f"  /python endpoint: {'ENABLED' if ALLOW_PYTHON else 'disabled'}")
    else:
        print("Bridge is NOT running. Use: start_bridge")


# Register PyMOL commands
cmd.extend("start_bridge", start_bridge)
cmd.extend("stop_bridge", stop_bridge)
cmd.extend("bridge_status", bridge_status)

# Auto-start on load
start_bridge()
