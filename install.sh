#!/bin/bash
# install.sh — Install or uninstall pymol-claude-bridge components.
#
# Usage:
#   bash install.sh              Install everything
#   bash install.sh --uninstall  Remove installed files
#
# What it does (install):
#   1. Copies pymol_bridge.py and active_site.py to ~/.pymol/startup/
#   2. Adds 'run' lines to ~/.pymolrc if not already present
#   3. Copies the Claude Code skill to ~/.claude/skills/pymol/
#   4. Backs up existing files before overwriting (.bak suffix)
#
# Safe to run multiple times (idempotent).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYMOL_STARTUP="$HOME/.pymol/startup"
PYMOLRC="$HOME/.pymolrc"
SKILL_DIR="$HOME/.claude/skills/pymol"

# --- Uninstall mode ---
if [ "${1:-}" = "--uninstall" ]; then
    echo "Uninstalling pymol-claude-bridge..."

    # Remove plugin files
    for f in pymol_bridge.py active_site.py; do
        if [ -f "$PYMOL_STARTUP/$f" ]; then
            rm "$PYMOL_STARTUP/$f"
            echo "  Removed $PYMOL_STARTUP/$f"
        fi
    done

    # Remove run lines from .pymolrc
    if [ -f "$PYMOLRC" ]; then
        sed -i.bak '/run ~\/.pymol\/startup\/pymol_bridge\.py/d' "$PYMOLRC"
        sed -i.bak '/run ~\/.pymol\/startup\/active_site\.py/d' "$PYMOLRC"
        rm -f "${PYMOLRC}.bak"
        echo "  Cleaned $PYMOLRC"
    fi

    # Remove skill directory
    if [ -d "$SKILL_DIR" ]; then
        rm -rf "$SKILL_DIR"
        echo "  Removed $SKILL_DIR"
    fi

    echo ""
    echo "Uninstall complete. Restart PyMOL and Claude Code to take effect."
    exit 0
fi

# --- Install mode ---
echo "Installing pymol-claude-bridge..."
echo ""

# 1. PyMOL plugins
echo "Step 1: PyMOL plugins"
mkdir -p "$PYMOL_STARTUP"

for f in pymol_bridge.py active_site.py; do
    src="$SCRIPT_DIR/pymol-plugin/$f"
    dst="$PYMOL_STARTUP/$f"
    if [ -f "$dst" ]; then
        cp "$dst" "${dst}.bak"
        echo "  Backed up existing $f -> ${f}.bak"
    fi
    cp "$src" "$dst"
    echo "  Installed $f -> $PYMOL_STARTUP/"
done

# 2. Update .pymolrc
echo ""
echo "Step 2: PyMOL startup config"
touch "$PYMOLRC"

# active_site.py should load before pymol_bridge.py (bridge auto-starts on load)
if ! grep -qF 'run ~/.pymol/startup/active_site.py' "$PYMOLRC"; then
    echo 'run ~/.pymol/startup/active_site.py' >> "$PYMOLRC"
    echo "  Added active_site.py to $PYMOLRC"
else
    echo "  active_site.py already in $PYMOLRC (skipped)"
fi

if ! grep -qF 'run ~/.pymol/startup/pymol_bridge.py' "$PYMOLRC"; then
    echo 'run ~/.pymol/startup/pymol_bridge.py' >> "$PYMOLRC"
    echo "  Added pymol_bridge.py to $PYMOLRC"
else
    echo "  pymol_bridge.py already in $PYMOLRC (skipped)"
fi

# 3. Claude Code skill
echo ""
echo "Step 3: Claude Code skill"
mkdir -p "$SKILL_DIR/references"

for f in SKILL.md; do
    src="$SCRIPT_DIR/claude-skill/$f"
    dst="$SKILL_DIR/$f"
    if [ -f "$dst" ]; then
        cp "$dst" "${dst}.bak"
        echo "  Backed up existing $f -> ${f}.bak"
    fi
    cp "$src" "$dst"
    echo "  Installed $f -> $SKILL_DIR/"
done

src="$SCRIPT_DIR/claude-skill/references/pymol-commands.md"
dst="$SKILL_DIR/references/pymol-commands.md"
if [ -f "$dst" ]; then
    cp "$dst" "${dst}.bak"
fi
cp "$src" "$dst"
echo "  Installed pymol-commands.md -> $SKILL_DIR/references/"

# Done
echo ""
echo "========================================="
echo "  Installation complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Open PyMOL — you should see:"
echo "     'PyMOL bridge started on http://127.0.0.1:9876'"
echo ""
echo "  2. Verify the bridge:"
echo "     curl -sf http://127.0.0.1:9876/ping"
echo ""
echo "  3. In Claude Code, type:"
echo "     /pymol fetch 4HHB and show as cartoon"
echo ""
echo "Note: You may need to restart Claude Code for it to"
echo "discover the new /pymol skill."
echo ""
echo "To enable the /python endpoint (advanced):"
echo "  export PYMOL_BRIDGE_ALLOW_PYTHON=1"
echo "  # then start PyMOL"
echo ""
echo "To uninstall:"
echo "  bash install.sh --uninstall"
