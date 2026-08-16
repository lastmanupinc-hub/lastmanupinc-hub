#!/usr/bin/env python3
"""gov_lint.py — honesty + consistency linter for the ai-ecosystem-map
control plane. Must exit 0 before every commit.

Checks (G-numbered, modeled on AXIS-Foundry tools/gov_lint.py):
  G1  matrix parses; meta.row_count == len(rows) == targets slot_count
  G2  matrix rows correspond 1:1 with ECOSYSTEM_TARGETS categories/slots
  G3  every grade is in the enum
  G4  grade above absent  => peer_evidence non-empty, each entry names files,
      and every cited path exists on disk under /home/user (":line" stripped)
  G5  grade == absent     => search_expressions non-empty
  G6  grade == partial    => missing_for_peer present
  G7  parity_100_criteria matches rollup recomputation (via rollup.check)
  G8  matrix change_log is newest-first (dates non-increasing)
  G9  continuation next_candidate_id names a SCAN_TREE candidate (or the
      loop is closed: all candidates done)
  G10 every peer_evidence scan_ref and every SCAN_TREE done-repo has an
      evidence/<repo>.scan.yaml on disk
  G11 derived/rollup.json (if present) matches recomputation
  G12 no duplicate mapping keys in any governance YAML file (PyYAML's default
      safe_load silently keeps the LAST value on a duplicate key — a bad
      hand-edit that merges two list items, e.g. two change_log entries,
      parses "successfully" while quietly dropping the first one's fields;
      this is a strict re-parse that catches exactly that)
"""
import json
import os
import re
import sys

import yaml as _pyyaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yamlite
import rollup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = "/home/user"
GOVERNANCE_YAML_FILES = [
    "AI_ECOSYSTEM_CAPABILITY_MATRIX.yaml", "ECOSYSTEM_TARGETS.yaml",
    "SCAN_TREE.yaml", "continuation.yaml", "begin.yaml",
]
ERRORS = []


class _DupKeyLoader(_pyyaml.SafeLoader):
    """SafeLoader that raises on a duplicate key within one mapping, instead
    of silently keeping the last value like the stdlib default."""


def _construct_mapping_no_dupes(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError("duplicate key %r at line %d" % (key, key_node.start_mark.line + 1))
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_DupKeyLoader.add_constructor(
    _pyyaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping_no_dupes)


def err(gate, msg):
    ERRORS.append("%s: %s" % (gate, msg))


def main():
    matrix = yamlite.load(os.path.join(ROOT, "AI_ECOSYSTEM_CAPABILITY_MATRIX.yaml"))
    targets = yamlite.load(os.path.join(ROOT, "ECOSYSTEM_TARGETS.yaml"))
    scan_tree = yamlite.load(os.path.join(ROOT, "SCAN_TREE.yaml"))
    continuation = yamlite.load(os.path.join(ROOT, "continuation.yaml"))

    rows = matrix["rows"]
    enum = set(matrix["meta"]["grade_enum"])

    # G1
    want = targets["meta"]["slot_count"]
    if not (matrix["meta"]["row_count"] == len(rows) == want):
        err("G1", "row_count meta=%s actual=%s targets=%s"
            % (matrix["meta"]["row_count"], len(rows), want))

    # G2
    prefixes = targets["meta"]["row_id_prefixes"]
    expected = {
        "%s_%s" % (prefixes[c], s.upper()): (c, s)
        for c, cd in targets["categories"].items() for s in cd["slots"]
    }
    if set(rows) != set(expected):
        err("G2", "row ids diverge from targets: only-in-matrix=%s only-in-targets=%s"
            % (sorted(set(rows) - set(expected)), sorted(set(expected) - set(rows))))
    for rid, r in rows.items():
        if rid in expected and (r["category"], r["slot"]) != expected[rid]:
            err("G2", "%s category/slot mismatch" % rid)

    above_absent = {"peer", "peer_plus", "bench", "partial", "scaffold"}
    for rid, r in sorted(rows.items()):
        g = r.get("grade")
        if g not in enum:
            err("G3", "%s grade %r not in enum" % (rid, g))
            continue
        if g in above_absent:
            ev = r.get("peer_evidence") or []
            if not any(e.get("files") for e in ev):
                err("G4", "%s graded %s with no peer_evidence files" % (rid, g))
            for e in ev:
                # Files are relative to the evidence entry's own `repo` field
                # (each row can cite evidence from multiple repos), e.g.
                # {repo: AXIS-Foundry, files: ["engine/foo.py:12-34"]} ->
                # /home/user/AXIS-Foundry/engine/foo.py
                repo = e.get("repo")
                for f in (e.get("files") or []):
                    clean = re.sub(r":\d+(-\d+)?$", "", f)
                    path = os.path.join(REPO_ROOT, repo, clean) if repo else os.path.join(REPO_ROOT, clean)
                    if not os.path.exists(path):
                        err("G4", "%s cites missing path %s (repo=%s)" % (rid, f, repo))
        if g == "absent" and not (r.get("search_expressions") or []):
            err("G5", "%s absent without search_expressions" % rid)
        if g == "partial" and not r.get("missing_for_peer"):
            err("G6", "%s partial without missing_for_peer" % rid)

    # G7
    _, result = rollup.compute()
    class _Sink:
        def write(self, *_): pass
    real_stdout, sys.stdout = sys.stdout, _Sink()
    try:
        rc = rollup.check(matrix, result)
    finally:
        sys.stdout = real_stdout
    if rc != 0:
        err("G7", "parity_100_criteria stale — run tools/rollup.py --write")

    # G8
    dates = [e.get("date", "") for e in (matrix.get("change_log") or [])]
    if dates != sorted(dates, reverse=True):
        err("G8", "matrix change_log not newest-first: %s" % dates)

    # G9
    loop = continuation["project_continuation"]["automated_loop_state"]
    cand_ids = {c["id"]: c for c in scan_tree["candidates"]}
    nxt = loop.get("next_candidate_id")
    all_done = all(c.get("status") == "done" for c in scan_tree["candidates"])
    if nxt is not None and nxt not in cand_ids:
        err("G9", "next_candidate_id %r not in SCAN_TREE" % nxt)
    if nxt is None and not all_done:
        err("G9", "next_candidate_id null but SCAN_TREE has pending candidates")

    # G10
    refs = set()
    for r in rows.values():
        for e in r.get("peer_evidence") or []:
            if e.get("scan_ref"):
                refs.add(e["scan_ref"])
    for c in scan_tree["candidates"]:
        if c.get("status") == "done":
            for repo in c.get("repos") or []:
                refs.add("evidence/%s.scan.yaml" % repo)
    for ref in sorted(refs):
        if not os.path.exists(os.path.join(ROOT, ref)):
            err("G10", "missing evidence shard %s" % ref)

    # G11
    rj = os.path.join(ROOT, "derived", "rollup.json")
    if os.path.exists(rj):
        with open(rj, encoding="utf-8") as f:
            on_disk = json.load(f)
        if on_disk != json.loads(json.dumps(result)):
            err("G11", "derived/rollup.json stale — run tools/rollup.py --write")

    # G12
    for fname in GOVERNANCE_YAML_FILES:
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                _pyyaml.load(f, Loader=_DupKeyLoader)
        except ValueError as exc:
            err("G12", "%s has a duplicate YAML key: %s" % (fname, exc))
        except _pyyaml.YAMLError as exc:
            err("G12", "%s failed strict re-parse: %s" % (fname, exc))

    if ERRORS:
        print("gov_lint: FAIL (%d)" % len(ERRORS))
        for e in ERRORS:
            print("  " + e)
        sys.exit(1)
    print("gov_lint: PASS (G1-G12)")


if __name__ == "__main__":
    main()
