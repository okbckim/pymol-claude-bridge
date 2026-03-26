# Example: Fetch and Style a Protein

## What You Say

```
/pymol fetch 4HHB and show it as a cartoon colored by chain
```

## What Happens

Claude Code will:

1. **Check the bridge** — verify PyMOL is running and the bridge responds
2. **Inspect the session** — see what's already loaded
3. **Fetch the structure** — download 4HHB (hemoglobin) from the PDB
4. **Style it** — show as cartoon, color each chain differently
5. **Take a screenshot** — verify the result looks correct
6. **Iterate** — fix any issues (wrong orientation, missing chains, etc.)

## Commands Sent (behind the scenes)

```bash
# Fetch structure
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "fetch 4HHB, async=0\nremove solvent\nhide everything\nshow cartoon"}'

# Color by chain
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "util.color_chains(\"(all) and elem C\", _self=cmd)\nutil.cnc all"}'

# Fix viewport
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "orient\nzoom all, 5\nclip slab, 200"}'
```

## Result

A clean cartoon representation of hemoglobin with each of its four chains in a distinct color.

![Hemoglobin cartoon colored by chain](screenshots/fetch-and-style.png)
