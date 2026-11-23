#!/usr/bin/env bash
# candy_wiki's checks for the factory gate. Exit 0 only when the branch is fit to review.
#
# The gate runs this file from the main checkout, with the job's worktree as the working
# directory. Steps that need a script the branch doesn't have yet (the semgrep gate and the
# feature map arrive with chore/state-tests) are skipped until it has them.
set -euo pipefail

FACTORY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN="$(dirname "$FACTORY_DIR")"
CONTAINER=frappe_docker_devcontainer-frappe-1
HERE="$(pwd)"
IN_CONTAINER="/workspace/${HERE#"$HOME/frappe_docker/"}"
failed=()

step() {
	local name=$1
	shift
	printf '▶ %s\n' "$name"
	if ! "$@"; then
		failed+=("$name")
	fi
}

# A fresh worktree has no node_modules: borrow the main checkout's (gitignored, same lockfile).
for dir in node_modules frontend/node_modules; do
	if [ ! -e "$dir" ] && [ -d "$MAIN/$dir" ]; then
		ln -sr "$MAIN/$dir" "$dir"  # relative: the container resolves it too
	fi
done

# ruff (pinned like .pre-commit-config.yaml) on the Python files this branch changed: only the
# findings it adds fail, since version-16 still has old ones the branch didn't write.
step "ruff" "$FACTORY_DIR/bin/ruff-new" --ruff ruff@0.8.1
step "biome" node_modules/.bin/biome check --diagnostic-level=error .
if [ -f scripts/semgrep_gate.py ]; then
	step "semgrep gate" python3 scripts/semgrep_gate.py --all
fi
if [ -f scripts/feature_map.py ]; then
	step "feature map" python3 scripts/feature_map.py check
fi
step "JS unit tests" docker exec -u frappe -w "$IN_CONTAINER/frontend" "$CONTAINER" bash -lc \
	'node --test "src/**/*.test.js" > /tmp/factory-js-$$.log 2>&1 || { tail -40 /tmp/factory-js-$$.log; exit 1; }'
step "Python tests (sandbox)" "$FACTORY_DIR/bin/frappe-test"
# Playwright specs linked to the changes, plus a smoke pair, in a real browser against the
# sandbox. Last: it needs the built SPA and a running server, the slowest steps.
step "e2e (sandbox)" "$FACTORY_DIR/bin/frappe-e2e"

if [ ${#failed[@]} -gt 0 ]; then
	printf '\n✘ Failed: %s\n' "${failed[*]}"
	exit 1
fi
printf '\n✔ All checks passed.\n'
