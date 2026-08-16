#!/usr/bin/env python3
"""build_capability_map.py — deterministic renderer for the capability picture.

Reads ECOSYSTEM_TARGETS.yaml (layout order) + derived/rollup.json (grades and
percentages; regenerate with tools/rollup.py --write first) and emits a single
self-contained derived/capability_map.html: hub + diagonal cascade of the 11
category bubbles, each with its row of 89 tool chips — mirroring the source
infographic's layout. No external assets, no timestamps: same inputs produce
byte-identical output.
"""
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yamlite

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "derived", "capability_map.html")

# grade -> (glyph, css class, legend text)
GRADES = [
    ("peer",      "✓",  "Full in-house peer — vendor never needed (evidence-backed)"),
    ("peer_plus", "✓+", "Exceeds the vendor on at least one axis"),
    ("bench",     "●",  "Working in-house implementation, equivalence not yet proven"),
    ("partial",   "◐",  "Real code covers part of the capability"),
    ("scaffold",  "○",  "Hints/stubs/design only — no working implementation read"),
    ("absent",    "✕",  "Searched, not found (search expressions recorded)"),
    ("unaudited", "?",  "Not yet scanned — counts as 0 until evidence lands"),
]
GLYPH = {g: y for g, y, _ in GRADES}

CSS = """
:root { color-scheme: light dark; }
.map-root {
  --surface-1:#fcfcfb; --page:#f9f9f7; --ink-1:#0b0b0b; --ink-2:#52514e;
  --muted:#898781; --grid:#e1e0d9; --border:rgba(11,11,11,0.10);
  --good:#0ca30c; --warning:#fab219; --serious:#ec835a; --critical:#d03b3b;
  --bench:#2a78d6; --hub:#4a3aa7;
  --good-wash:rgba(12,163,12,0.12); --bench-wash:rgba(42,120,214,0.12);
  --warn-wash:rgba(250,178,25,0.16); --serious-wash:rgba(236,131,90,0.14);
  color-scheme: light;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  background: var(--page); color: var(--ink-1);
  margin: 0 auto; max-width: 1180px; padding: 28px 24px 48px;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .map-root {
    color-scheme: dark;
    --surface-1:#1a1a19; --page:#0d0d0d; --ink-1:#ffffff; --ink-2:#c3c2b7;
    --muted:#898781; --grid:#2c2c2a; --border:rgba(255,255,255,0.10);
    --bench:#3987e5; --hub:#9085e9;
  }
}
:root[data-theme="dark"] .map-root {
  color-scheme: dark;
  --surface-1:#1a1a19; --page:#0d0d0d; --ink-1:#ffffff; --ink-2:#c3c2b7;
  --muted:#898781; --grid:#2c2c2a; --border:rgba(255,255,255,0.10);
  --bench:#3987e5; --hub:#9085e9;
}
.map-root h1 { font-size: 26px; margin: 0 0 4px; }
.map-root .sub { color: var(--ink-2); margin: 0 0 20px; font-size: 14px; max-width: 72ch; }
.tiles { display:flex; gap:12px; flex-wrap:wrap; margin-bottom: 26px; }
.tile { background: var(--surface-1); border:1px solid var(--border); border-radius:10px;
        padding:12px 18px; min-width:150px; }
.tile .v { font-size: 30px; font-weight:650; }
.tile .l { font-size: 12px; color: var(--ink-2); margin-top:2px; }
.cascade { position:relative; }
.spine { position:absolute; left:34px; top:0; bottom:0; width:2px; background:var(--grid); }
.crow { display:flex; align-items:flex-start; gap:14px; margin:0 0 18px; position:relative; }
.bubble { flex:0 0 148px; margin-left: var(--indent, 0px); background:var(--surface-1);
  border:2px solid var(--hub); border-radius:999px; padding:10px 6px; text-align:center; }
.bubble .cname { font-weight:650; font-size:13px; }
.bubble .cpct { font-size:19px; font-weight:700; }
.bubble .cmeta { font-size:11px; color:var(--muted); }
.chips { display:flex; flex-wrap:wrap; gap:6px; padding-top:4px; }
.chip { display:inline-flex; align-items:center; gap:6px; border-radius:8px;
  padding:5px 9px; font-size:12.5px; background:var(--surface-1);
  border:1.5px solid var(--grid); color:var(--ink-1); }
.chip .g { font-weight:700; font-size:11px; }
.chip.peer      { background:var(--good); border-color:var(--good); color:#fff; }
.chip.peer_plus { background:var(--good); border-color:var(--ink-1); color:#fff;
                  box-shadow:0 0 0 2px var(--good); }
.chip.bench     { background:var(--bench-wash); border-color:var(--bench); }
.chip.bench .g  { color:var(--bench); }
.chip.partial   { background:var(--warn-wash); border-color:var(--warning); }
.chip.scaffold  { background:var(--serious-wash); border-color:var(--serious); }
.chip.absent    { color:var(--ink-2); }
.chip.absent .g { color:var(--critical); }
.chip.unaudited { border-style:dashed; color:var(--muted);
  background:repeating-linear-gradient(45deg, transparent 0 6px, var(--grid) 6px 8px); }
.chip .dep { width:7px; height:7px; border-radius:50%; background:var(--warning);
  display:inline-block; }
.legend { display:flex; flex-wrap:wrap; gap:8px 18px; margin:26px 0 8px;
  font-size:12.5px; color:var(--ink-2); }
.legend .chip { pointer-events:none; }
.map-root table { border-collapse:collapse; width:100%; margin-top:18px;
  background:var(--surface-1); font-size:13px; }
.map-root th, .map-root td { border:1px solid var(--grid); padding:7px 10px; text-align:left; }
.map-root th { color:var(--ink-2); font-weight:600; }
.map-root td.n { text-align:right; font-variant-numeric: tabular-nums; }
.foot { margin-top:22px; font-size:12px; color:var(--muted); }
"""


def build():
    targets = yamlite.load(os.path.join(ROOT, "ECOSYSTEM_TARGETS.yaml"))
    with open(os.path.join(ROOT, "derived", "rollup.json"), encoding="utf-8") as f:
        roll = json.load(f)
    matrix_meta = yamlite.load(os.path.join(ROOT, "AI_ECOSYSTEM_CAPABILITY_MATRIX.yaml"))["meta"]
    prefixes = targets["meta"]["row_id_prefixes"]
    cov = roll["coverage"]

    p = []
    p.append("<title>AI Ecosystem Capability Map</title>")
    p.append("<style>%s</style>" % CSS)
    p.append('<div class="map-root">')
    p.append("<h1>AI Ecosystem Capability Map</h1>")
    p.append('<p class="sub">The lastmanupinc-hub portfolio graded against the 89 targets of '
             '"The Modern AI Ecosystem — Tools" under the <b>peer-independence doctrine</b>: '
             'the ability to <i>never need</i> each vendor, not the ability to use it. '
             'Percentages are conservative floors — unaudited and absent both count 0, so '
             'numbers only rise as file evidence lands.</p>')

    p.append('<div class="tiles">')
    p.append('<div class="tile"><div class="v">%.1f%%</div><div class="l">overall capability floor</div></div>'
             % roll["overall_pct"])
    p.append('<div class="tile"><div class="v">%d/%d</div><div class="l">slots audited</div></div>'
             % (cov["slots_audited"], cov["slots_total"]))
    p.append('<div class="tile"><div class="v">%d/%d</div><div class="l">repos scanned</div></div>'
             % (cov["repos_scanned"], cov["repos_total"]))
    p.append("</div>")

    p.append('<div class="cascade"><div class="spine"></div>')
    n_cats = len(targets["categories"])
    for i, (cat_key, cat) in enumerate(targets["categories"].items()):
        cdata = roll["categories"][cat_key]
        indent = round(56.0 * i / max(n_cats - 1, 1))
        p.append('<div class="crow" style="--indent:%dpx">' % indent)
        p.append('<div class="bubble"><div class="cname">%s</div><div class="cpct">%.1f%%</div>'
                 '<div class="cmeta">%d/%d audited</div></div>'
                 % (html.escape(cat["label"]), cdata["pct"], cdata["audited"], cdata["total"]))
        p.append('<div class="chips">')
        for slot_key, slot in cat["slots"].items():
            rid = "%s_%s" % (prefixes[cat_key], slot_key.upper())
            s = cdata["slots"][rid]
            dep = '<span class="dep" title="vendor currently in use (dependence)"></span>' \
                if s["vendor_in_use_count"] else ""
            p.append('<span class="chip %s" title="%s — %s">%s<span class="g">%s</span>%s</span>'
                     % (s["grade"], html.escape(rid), s["grade"],
                        html.escape(slot["label"]), GLYPH[s["grade"]], dep))
        p.append("</div></div>")
    p.append("</div>")

    p.append('<div class="legend">')
    for g, glyph, desc in GRADES:
        p.append('<span><span class="chip %s">%s<span class="g">%s</span></span> %s</span>'
                 % (g, g.replace("_", "+") if g == "peer_plus" else g, glyph, html.escape(desc)))
    p.append('<span><span class="chip"><span class="dep"></span>dot</span> vendor in use today (dependence marker)</span>')
    p.append("</div>")

    p.append("<table><thead><tr><th>Category</th><th>Floor %</th><th>Audited</th>"
             + "".join("<th>%s</th>" % g for g, _, _ in GRADES) + "</tr></thead><tbody>")
    for cat_key, cat in targets["categories"].items():
        cdata = roll["categories"][cat_key]
        by_grade = {g: 0 for g, _, _ in GRADES}
        for s in cdata["slots"].values():
            by_grade[s["grade"]] += 1
        p.append("<tr><td>%s</td><td class='n'>%.1f</td><td class='n'>%d/%d</td>"
                 % (html.escape(cat["label"]), cdata["pct"], cdata["audited"], cdata["total"])
                 + "".join("<td class='n'>%d</td>" % by_grade[g] for g, _, _ in GRADES)
                 + "</tr>")
    p.append("</tbody></table>")

    p.append('<p class="foot">Generated by tools/build_capability_map.py from '
             'AI_ECOSYSTEM_CAPABILITY_MATRIX.yaml (last_updated %s) via derived/rollup.json. '
             'Doctrine + taxonomy: ECOSYSTEM_TARGETS.yaml. Regenerate: '
             '<code>python3 tools/rollup.py --write &amp;&amp; python3 tools/build_capability_map.py</code></p>'
             % html.escape(str(matrix_meta.get("last_updated"))))
    p.append("</div>")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(p) + "\n")
    print("built %s (%d categories, %d chips)" % (
        os.path.relpath(OUT, ROOT), len(targets["categories"]), cov["slots_total"]))


if __name__ == "__main__":
    build()
