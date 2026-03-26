# Example: Publication-Quality Figure

## What You Say

```
/pymol make a publication figure of 4HHB with white background, ray traced
```

## What Happens

Claude Code will:

1. **Set up the scene** — fetch structure, style with cartoon
2. **Apply publication settings** — white background, CMYK color space, optimized lighting
3. **Ray trace** — render at high resolution (2400x1800, 300 DPI)
4. **Save both** — `.pse` session file for later editing, `.png` for the figure

## Commands Sent

```bash
# Style the structure
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "fetch 4HHB, async=0\nremove solvent\nhide everything\nshow cartoon\nutil.color_chains(\"(all) and elem C\", _self=cmd)\nutil.cnc all"}'

# Publication settings
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "bg_color white\nspace cmyk\nset ray_shadow, 0\nset ray_trace_mode, 1\nset antialias, 3\nset ambient, 0.5\nset spec_count, 5\nset shininess, 50\nset specular, 1\nset reflect, 0.1\nset orthoscopic, on\nset opaque_background, off\nset cartoon_discrete_colors, on\ndss"}'

# Orient and render
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "orient\nzoom all, 5"}'

# Save session
curl -sf -X POST http://127.0.0.1:9876/run \
  -H "Content-Type: application/json" \
  -d '{"commands": "save /tmp/4HHB_publication.pse"}'

# Ray-traced render
curl -sf -X POST http://127.0.0.1:9876/render \
  -H "Content-Type: application/json" \
  -d '{"path": "/tmp/4HHB_figure.png", "width": 2400, "height": 1800, "dpi": 300, "ray": true, "transparent_bg": false}'
```

## Result

A clean, print-ready figure suitable for journal submission.

![Publication figure of hemoglobin](screenshots/publication-figure.png)

## Tips

- Use `transparent_bg: true` if you want to composite the figure over a custom background
- For Goodsell-style flat illustrations, ask Claude: `/pymol render this in Goodsell style`
- Save the `.pse` file so you can make manual tweaks in PyMOL's GUI before final submission
