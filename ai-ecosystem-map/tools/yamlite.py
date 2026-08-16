#!/usr/bin/env python3
"""yamlite — YAML loading shim for the ai-ecosystem-map control plane.

Primary path is PyYAML (present in the standard scan environment). If PyYAML
is ever missing, fail with a actionable message instead of a stack trace.
Tools in this repo only READ YAML; all writes are targeted text edits (to
preserve comments) or JSON/HTML, so no dumper is exposed.
"""
import sys

try:
    import yaml as _yaml
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "yamlite: PyYAML is required (pip install pyyaml). The scan loop's\n"
        "standard remote environment ships it; install it before rerunning.\n"
    )
    raise


def load(path):
    """Parse a YAML file into plain Python objects (safe_load).

    On a parse error, re-raise with a short pointer to the known-gotchas
    section of SONNET5_ECOSYSTEM_SCAN_STRATEGY.md instead of leaving a
    scan session to puzzle over a raw PyYAML traceback (this has happened
    twice: a doubled-backslash regex fragment, and a Python \\" escape
    silently collapsing to a literal " inside a matrix-generation script's
    replacement text, both breaking a YAML double-quoted scalar).
    """
    with open(path, "r", encoding="utf-8") as f:
        try:
            return _yaml.safe_load(f)
        except _yaml.YAMLError as exc:
            raise _yaml.YAMLError(
                "%s\n\n--> Failed to parse %s.\n"
                "    If this is a hand-generated matrix-update script's output, see the\n"
                "    'Known gotcha' sections in SONNET5_ECOSYSTEM_SCAN_STRATEGY.md before\n"
                "    debugging from scratch — two prior sessions hit variants of this\n"
                "    exact failure mode (a literal backslash or quote leaking into a\n"
                "    YAML double-quoted scalar via Python string escaping)."
                % (exc, path)
            ) from exc
