"""Extra test picks: the tests of every feature that owns a changed file.

Reads the changed files on stdin. Prints Python test modules (for frappe-test), or with --e2e
the feature's e2e spec files (for frappe-e2e). Uses scripts/feature_map.py (FEATURE_MAP.md) when
the branch has it; prints nothing otherwise, and the scripts' own picks still run.
Runs from the job's worktree.
"""

import importlib.util
import sys
from pathlib import Path

script = Path("scripts/feature_map.py")
if script.exists():
	spec = importlib.util.spec_from_file_location("feature_map", script)
	feature_map = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(feature_map)
	changed = [line.strip() for line in sys.stdin if line.strip()]
	picked = feature_map.tests_for(feature_map.load(), changed)
	print("\n".join(picked["e2e"] if "--e2e" in sys.argv else picked["python_modules"]))
