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
    """Parse a YAML file into plain Python objects (safe_load)."""
    with open(path, "r", encoding="utf-8") as f:
        return _yaml.safe_load(f)
