## Software factory

`/factory run` builds every open GitHub issue labeled `factory` through
intake → spec → build → gate → review → approve, one PR per issue. State is in
`factory/jobs/` (gitignored); `factory/bin/job` is its only writer. Checks:
`factory/checks.sh`. Dashboard: `cd factory && python3 -m http.server`, then
open http://localhost:8000/dashboard.html.

Each job works in its own git worktree (`worktree_path` in `factory/config.json`)
on a branch `factory/<job-id>`, and has its own **sandbox**: a throwaway site
copied from <SOURCE SITE> that runs the job's branch code
(`factory/bin/frappe-sandbox up <job-id>` prints its URL and login). Agents look
at pages, run Python and e2e tests and try flows there, never on <SOURCE SITE> or the
test sites people use. The sandbox is dropped when the job is merged or rejected.

Rules for the factory's agents that replace the general ones above:
- Push the job branch `factory/<job-id>` and open its draft PR: that is the
  factory's job. The approver merges only through `factory/bin/job merge`.
- The spec lives in the job folder (`factory/jobs/<job-id>/spec.md`), not in the repo.
- Don't run scripts that build or migrate <SOURCE SITE> or the shared test sites;
  use the sandbox.
