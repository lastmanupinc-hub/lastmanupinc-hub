#!/usr/bin/env python3
"""rollup.py — SINGLE SOURCE of the percentage math.

Reads AI_ECOSYSTEM_CAPABILITY_MATRIX.yaml + ECOSYSTEM_TARGETS.yaml, computes
per-category and overall capability percentages (conservative floors:
unaudited and absent both weigh 0), and:

  --write   refresh derived/rollup.json AND restate the matrix's
            parity_100_criteria block (the only writer of those numbers)
  --check   recompute and diff against the matrix block; exit 1 on mismatch

Percentage formula: category_pct = 100 * sum(weight(grade(slot))) / slots_in_category.
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yamlite

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATRIX = os.path.join(ROOT, "AI_ECOSYSTEM_CAPABILITY_MATRIX.yaml")
TARGETS = os.path.join(ROOT, "ECOSYSTEM_TARGETS.yaml")
ROLLUP_JSON = os.path.join(ROOT, "derived", "rollup.json")
REPOS_TOTAL = 31


def compute():
    matrix = yamlite.load(MATRIX)
    targets = yamlite.load(TARGETS)
    weights = matrix["meta"]["grade_weights"]
    rows = matrix["rows"]

    counts = {g: 0 for g in matrix["meta"]["grade_enum"]}
    categories = {}
    repos_seen = set()
    slots_audited = 0
    total_weight = 0.0

    for cat_key, cat in targets["categories"].items():
        cat_rows = {rid: r for rid, r in rows.items() if r["category"] == cat_key}
        cat_weight = 0.0
        cat_audited = 0
        slot_out = {}
        for rid, r in sorted(cat_rows.items()):
            g = r["grade"]
            counts[g] += 1
            w = float(weights[g])
            cat_weight += w
            total_weight += w
            if g != "unaudited":
                cat_audited += 1
                slots_audited += 1
            repos_seen.update(r.get("repos_scanned") or [])
            slot_out[rid] = {
                "label": r["slot_label"],
                "grade": g,
                "vendor_in_use_count": len(r.get("vendor_in_use") or []),
                "evidence_count": len(r.get("peer_evidence") or []),
            }
        n = len(cat_rows)
        categories[cat_key] = {
            "label": cat["label"],
            "pct": round(100.0 * cat_weight / n, 1) if n else 0.0,
            "audited": cat_audited,
            "total": n,
            "slots": slot_out,
        }

    total_slots = len(rows)
    result = {
        "schema": 1,
        "categories": categories,
        "counts": counts,
        "overall_pct": round(100.0 * total_weight / total_slots, 1) if total_slots else 0.0,
        "coverage": {
            "repos_scanned": len(repos_seen),
            "repos_total": REPOS_TOTAL,
            "slots_audited": slots_audited,
            "slots_total": total_slots,
        },
    }
    return matrix, result


def parity_block_text(result):
    counts = result["counts"]
    pcts = {k: v["pct"] for k, v in sorted(result["categories"].items())}
    cov = result["coverage"]
    lines = [
        "parity_100_criteria:",
        '  audit_method: "python3 tools/rollup.py --check"',
        '  last_run: "%s"' % datetime.date.today().isoformat(),
        "  current_counts: {%s}" % ", ".join("%s: %d" % (g, counts[g]) for g in counts),
        "  current_percentages:",
    ]
    for k, v in pcts.items():
        lines.append("    %s: %.1f" % (k, v))
    lines.append("  overall_percentage: %.1f" % result["overall_pct"])
    lines.append(
        "  coverage: {repos_scanned: %d, repos_total: %d, slots_audited: %d, slots_total: %d}"
        % (cov["repos_scanned"], cov["repos_total"], cov["slots_audited"], cov["slots_total"])
    )
    return "\n".join(lines) + "\n"


def write(result):
    os.makedirs(os.path.dirname(ROLLUP_JSON), exist_ok=True)
    with open(ROLLUP_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")

    with open(MATRIX, "r", encoding="utf-8") as f:
        text = f.read()
    marker = "\nparity_100_criteria:"
    idx = text.find(marker)
    if idx < 0:
        sys.exit("rollup: parity_100_criteria block not found in matrix")
    # Preserve the comment lines directly above the block; replace block → EOF.
    text = text[: idx + 1] + parity_block_text(result)
    with open(MATRIX, "w", encoding="utf-8") as f:
        f.write(text)
    print("rollup: wrote derived/rollup.json and restated parity_100_criteria "
          "(overall %.1f%%, %d/%d slots audited, %d/%d repos)" % (
              result["overall_pct"], result["coverage"]["slots_audited"],
              result["coverage"]["slots_total"], result["coverage"]["repos_scanned"],
              result["coverage"]["repos_total"]))


def check(matrix, result):
    """Compare recomputed numbers to the matrix block (ignoring last_run)."""
    block = matrix.get("parity_100_criteria") or {}
    mismatches = []
    if block.get("current_counts") != result["counts"]:
        mismatches.append("current_counts: matrix=%r recomputed=%r"
                          % (block.get("current_counts"), result["counts"]))
    want_pcts = {k: v["pct"] for k, v in result["categories"].items()}
    if block.get("current_percentages") != want_pcts:
        mismatches.append("current_percentages: matrix=%r recomputed=%r"
                          % (block.get("current_percentages"), want_pcts))
    if block.get("overall_percentage") != result["overall_pct"]:
        mismatches.append("overall_percentage: matrix=%r recomputed=%r"
                          % (block.get("overall_percentage"), result["overall_pct"]))
    if block.get("coverage") != result["coverage"]:
        mismatches.append("coverage: matrix=%r recomputed=%r"
                          % (block.get("coverage"), result["coverage"]))
    if mismatches:
        print("rollup --check: STALE parity_100_criteria — run tools/rollup.py --write")
        for m in mismatches:
            print("  " + m)
        return 1
    print("rollup --check: parity_100_criteria matches recomputation")
    return 0


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = ap.parse_args()
    matrix, result = compute()
    if args.write:
        write(result)
    else:
        sys.exit(check(matrix, result))


if __name__ == "__main__":
    main()
