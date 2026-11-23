## Software factory

`/factory run` builds every open GitHub issue labeled `factory` through
intake → spec → build → gate → review → approve, one PR per issue. State is in
`factory/jobs/` (gitignored); `factory/bin/job` is its only writer. Checks:
`factory/checks.sh`. Dashboard: `cd factory && python3 -m http.server`, then
open http://localhost:8000/dashboard.html.

Each job works in its own git worktree at
`../../../.factory-sandboxes/candy_wiki/<job-id>/apps/candy_wiki` (from this
app folder) on a branch `factory/<job-id>`, and has its own **sandbox**: a
throwaway site copied from `preview.localhost` that runs the job's branch code
(`factory/bin/frappe-sandbox up <job-id>` prints its URL and login). Mail is
muted, the scheduler paused, and semantic search uses the sandbox's own copy of
the Qdrant index; Candy AI works as on preview. Agents look at pages, run
Python tests and Playwright specs and try flows there, never on `preview.localhost` or the
`candy-test-*` / `semantic-test` sites. The sandbox is dropped when the job is
merged or rejected.

Rules for the factory's agents that replace the general ones above:
- Push the job branch `factory/<job-id>` and open its draft PR with
  `gh pr create --draft --base version-16`: that is the factory's job, so the
  rules "push only when the user asks" and "branch names start with feat/ or
  fix/" don't apply to it. The approver merges only through
  `factory/bin/job merge`. Commit messages stay conventional and in English.
- The spec lives in the job folder (`factory/jobs/<job-id>/spec.md`), not in `specs/`.
- Don't run `scripts/preview.sh`, `scripts/verify.py` or `scripts/test-parallel.sh`:
  they build or test on preview and the shared test sites. Use the sandbox and
  `factory/checks.sh`.
- Run e2e specs with `factory/bin/frappe-e2e` (it points Playwright at the
  sandbox), never a bare `yarn test:e2e`, whose default address is another site.
- Screenshots of the sandbox go in the job folder (`round-<N>/shots/`), not `.verify/`.

Hot spots for the security reviewer: `permissions.py`, `read_scope.py`,
`access_policy.py` and `system_roles.py` (who reads and writes what), `mcp.py`
(OAuth, draft-only writes), every endpoint in `api/` and `ai/`, the public
reader in `portal/` (guest access), and private attachments in `attachments/`.
