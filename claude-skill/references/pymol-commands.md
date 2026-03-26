# PyMOL Command Reference

Consult this reference when you need specific PyMOL commands for a task.
Sections are organized by task type — jump to what you need.

## Table of Contents
1. Loading & Cleaning
2. Selections
3. Representations
4. Coloring
5. Publication Settings
6. Distances, Contacts & Labels
7. Camera & Orientation
8. Goodsell (Flat Illustrative) Style
9. Surface + Cartoon Overlay
10. Multi-Structure Workflows
11. Useful Python Snippets

---

## 1. Loading & Cleaning

```
fetch 4HHB, async=0              # PDB — always use async=0
fetch 4HHB, type=cif, async=0    # mmCIF format
load /path/to/file.pdb, myobj    # local file
load /path/to/file.sdf, ligand   # small molecule

remove solvent                    # strip water
remove elem H                    # strip hydrogens
remove chain X                   # drop a chain
set valence, 0                   # hide bond-order lines (cleaner sticks)
```

**AlphaFold structures:**
```
load https://alphafold.ebi.ac.uk/files/AF-P12345-F1-model_v4.pdb, af_model, async=0
```

---

## 2. Selections

```
# By chain / residue / name
select chainA, chain A
select lig, resn LIG
select active, resi 100+150+200 and chain A
select helix1, resi 10-30 and chain A

# Proximity-based
select binding, byres (lig around 4.0) and not lig
select interface, byres (chain A around 4.0 and chain B)
select neighbors, (byres sele around 5.0) and not sele

# By property
select highB, b > 80
select backbone, name CA+C+N+O
select sidechains, (sc.) or (name CA) or (name N and resn PRO)
```

---

## 3. Representations

```
# Basics
hide everything
show cartoon                      # protein backbone
show sticks, sele                 # bonds
show spheres, sele                # space-filling
show surface, sele                # molecular surface
show ribbon, sele                 # simple ribbon
show lines, sele                  # thin lines

# Sidechain sticks (no backbone clutter)
cmd.show("sticks", "((byres sele) & (sc. | (n. CA) | (n. N & r. PRO)))")

# Ball-and-stick for ligands
show sticks, lig
show spheres, lig
set sphere_scale, 0.25, lig
set stick_radius, 0.15, lig

# Transparent cartoon (ghost context)
set cartoon_transparency, 0.7, sele
```

---

## 4. Coloring

```
# By chain (carbons only, then fix heteroatoms)
util.color_chains("(all) and elem C", _self=cmd)
util.cnc("all", _self=cmd)       # restores N=blue, O=red, S=yellow

# Specific colors on carbons
color marine, sele and elem C
color orange, sele and elem C
color gray80, context_sele and elem C    # muted context

# B-factor / pLDDT spectrum
spectrum b, blue_white_red, all
spectrum b, red_orange_yellow_green_cyan_blue, all    # pLDDT rainbow

# Per-residue property
spectrum count, rainbow, sele     # rainbow N→C

# Useful named colors
# marine, cyan, salmon, orange, yellow, lime, forest, violet, gray80, wheat
```

---

## 5. Publication Settings

Apply these before final rendering for clean, print-ready figures:

```
bg_color white
space cmyk
set ray_shadow, 0
set ray_trace_mode, 1
set antialias, 3
set ambient, 0.5
set spec_count, 5
set shininess, 50
set specular, 1
set reflect, 0.1
set orthoscopic, on
set opaque_background, off
set cartoon_discrete_colors, on
dss                                # recompute secondary structure
```

---

## 6. Distances, Contacts & Labels

```
# Hydrogen bonds / polar contacts
dist hbonds, sele1, sele2, mode=2

# Style the dashes
hide labels, hbonds
set dash_color, black, hbonds
set dash_gap, 0.3, hbonds
set dash_radius, 0.06, hbonds
set dash_round_ends, on

# Custom label
label sele and name CA, "%s %s" % (resn, resi)
set label_size, 14
set label_color, black
set label_font_id, 7              # bold sans-serif
set label_bg_color, white
set label_connector, on
set label_connector_color, gray50
```

---

## 7. Camera & Orientation

```
orient                            # fit everything in view
orient sele                       # fit selection
zoom sele, 8                      # zoom with 8Å buffer
center sele                       # center without zoom
turn y, 90                        # rotate 90° around Y
turn x, 30                        # tilt
clip slab, 20                     # adjust clipping for close-ups

# Store and recall views
set_view (\                       # paste a saved view matrix
    1.0, 0.0, 0.0, \
    ...)
```

---

## 8. Goodsell (Flat Illustrative) Style

Creates a flat, outline-based illustration look:

```
set ray_trace_mode, 3
set ray_trace_color, black
unset specular
set ray_trace_gain, 0
unset depth_cue
set ambient, 1.0
set direct, 0.0
set reflect, 0.0
set ray_shadow, 0
```

Best with cartoon or surface representations. Use bold, saturated colors.
Render at high resolution (3000+ wide) because outlines sharpen at larger sizes.

---

## 9. Surface + Cartoon Overlay

Show surface context while keeping cartoon detail underneath:

```
# Create a separate object for the surface (avoids conflicts)
create surf_obj, sele, zoom=0
show surface, surf_obj
set transparency, 0.5, surf_obj
color gray90, surf_obj            # light ghost surface

# The original object keeps its cartoon/sticks
show cartoon, original_obj
```

For binding-pocket surfaces only:
```
create pocket_surf, byres (lig around 6.0) and not lig, zoom=0
show surface, pocket_surf
set transparency, 0.4, pocket_surf
```

---

## 10. Multi-Structure Workflows

### Superposition / alignment
```
# Sequence-based alignment (better for homologs)
align mobile, target

# Structure-based (better for divergent structures)
super mobile, target

# Align specific chains
align mobile and chain A, target and chain A
```

### Side-by-side comparison
```
fetch 4HHB, prot1, async=0
fetch 1HHO, prot2, async=0
align prot2, prot1
# Color differently
color marine, prot1 and elem C
color orange, prot2 and elem C
util.cnc("all", _self=cmd)
```

### Split states (NMR ensembles)
```
split_states ensemble
# Now each state is a separate object: ensemble_0001, ensemble_0002, ...
```

---

## 11. Useful Python Snippets

Run these via the `/python` endpoint.

**List all objects and their atom counts:**
```python
for name in cmd.get_names('objects'):
    n = cmd.count_atoms(name)
    print(f"{name}: {n} atoms")
```

**Get all unique residue names in a selection (find ligand names):**
```python
myspace = {'resnames': set()}
cmd.iterate("all and not polymer", "resnames.add(resn)", space=myspace)
print(sorted(myspace['resnames']))
```

**Get unique chain IDs:**
```python
myspace = {'chains': set()}
cmd.iterate("all", "chains.add(chain)", space=myspace)
print(sorted(myspace['chains']))
```

**Color by chain with specific palette:**
```python
palette = {'A': 'marine', 'B': 'orange', 'C': 'forest', 'D': 'violet'}
for chain, color in palette.items():
    cmd.color(color, f"chain {chain} and elem C")
cmd.do("util.cnc all")
```

**Select residues within distance of ligand and label them:**
```python
cmd.select("binding_site", "byres (resn LIG around 4.0) and not resn LIG")
cmd.show("sticks", "binding_site")
cmd.label("binding_site and name CA", '"%s%s" % (oneletter, resi)')
```
