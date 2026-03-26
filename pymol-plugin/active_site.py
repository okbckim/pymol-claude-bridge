"""
Active site visualization plugin for PyMOL.

Part of pymol-claude-bridge: https://github.com/okbckim/pymol-claude-bridge

Install:
    cp active_site.py ~/.pymol/startup/
    echo 'run ~/.pymol/startup/active_site.py' >> ~/.pymolrc

Usage:
    active_site obj_name, ligand_resn [, cutoff]

Examples:
    active_site 8S9A, ZSB
    active_site 1HHP, AB1, 5.0
"""

from pymol import cmd


def active_site(obj, ligand_resn, cutoff=4.5):
    """Visualize protein-ligand binding site with H-bonds and labels."""
    cutoff = float(cutoff)
    lig_sel = f"{obj} and resn {ligand_resn}"
    poly_sel = f"{obj} and polymer"
    site_sel = f"{poly_sel} and byres ({lig_sel} around {cutoff})"

    hbonds_name = f"{obj}_hbonds"
    site_name = f"{obj}_binding_site"

    # Clean up previous run
    cmd.delete(hbonds_name)
    cmd.delete(site_name)

    # Protein cartoon
    cmd.hide("everything", obj)
    cmd.show("cartoon", poly_sel)
    cmd.color("gray80", poly_sel)

    # Ligand sticks (yellow carbons)
    cmd.show("sticks", lig_sel)
    cmd.color("yellow", f"{lig_sel} and elem C")
    cmd.do(f"util.cnc {lig_sel}")

    # Binding site residues (green carbons)
    cmd.select(site_name, site_sel)
    cmd.show("sticks", site_name)
    cmd.color("green", f"{site_name} and elem C")
    cmd.do(f"util.cnc {site_name}")

    # Hide nonpolar hydrogens
    cmd.hide("everything", f"{obj} and elem H and not (neighbor (elem N+O+S))")

    # Hydrogen bonds
    cmd.distance(hbonds_name, poly_sel, lig_sel, mode=2)
    cmd.color("yellow", hbonds_name)
    cmd.set("dash_width", 3, hbonds_name)
    cmd.set("dash_gap", 0.3, hbonds_name)

    # Labels
    cmd.label(f"{site_name} and name CA", '"%s%s" % (resn, resi)')
    cmd.set("label_size", 14)
    cmd.set("label_color", "white")

    # Zoom
    cmd.zoom(lig_sel, 8)
    cmd.clip("slab", 200)

    print(f"Active site visualization: {obj} / {ligand_resn} / {cutoff}A cutoff")


cmd.extend("active_site", active_site)
