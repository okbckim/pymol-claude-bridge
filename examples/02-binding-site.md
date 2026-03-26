# Example: Visualize a Binding Site

## What You Say

```
/pymol show me the binding site of 8S9A around the ZSB ligand
```

## What Happens

Claude Code will:

1. **Fetch 8S9A** from the PDB
2. **Identify the ligand** — find ZSB in the structure
3. **Use the `active_site` command** (or equivalent manual steps):
   - Gray cartoon for the protein
   - Yellow sticks for the ZSB ligand
   - Green sticks for binding site residues within 4.5A
   - Yellow dashed lines for hydrogen bonds
   - Residue labels on CA atoms
4. **Screenshot and verify** — check the binding site looks correct

## Commands Sent

```bash
# Fetch and clean
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "fetch 8S9A, async=0\nremove solvent"}'

# Use the active_site command
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "active_site 8S9A, ZSB"}'
```

Or if building manually, Claude sends individual commands to select the ligand, find nearby residues, style everything, and create H-bond distance objects.

## Result

A focused view of the ZSB binding pocket with protein-ligand interactions clearly visible.

![Binding site of 8S9A with ZSB ligand](screenshots/binding-site.png)
