## In this Frappe app

- The app runs only inside the bench devcontainer. Run bench, yarn and node commands the way
  AGENTS.md says. Never migrate, write to or run tests on any site but your job's sandbox: not
  the source site (preview) and not the user's test sites.
- Your job's **sandbox** replaces the dev server and the port in your prompt:
  `python3 <main checkout>/factory/bin/frappe-sandbox up <job-id>` creates it the first time (a
  copy of the source site's data running your branch code, a few minutes) and prints its URL and
  login. After you change code, run `up` again: it rebuilds the assets, migrates when the schema
  changed and restarts. `refresh` does all of it even when nothing changed.
- Look at pages with `agent-browser` at that URL and sign in with the printed login. The sandbox
  is a throwaway copy: create and edit records there freely. Mail is muted and the scheduler
  paused; run a scheduled job yourself with
  `frappe-sandbox frappe <job-id> execute <dotted.path.to.function>`. Background jobs run your
  branch code on the sandbox's own worker.
- Save a screenshot of each criterion you checked on a page as
  `<job folder>/round-<N>/shots/builder-<what>.png`. The dashboard shows them to the human.
- One Python test module: `frappe-sandbox frappe <job-id> run-tests --module <module>`.
  `factory/checks.sh` runs every test linked to your changes there.
- Browser (e2e) tests: `python3 <main checkout>/factory/bin/frappe-e2e` from your worktree runs
  the specs linked to your changes against your sandbox (`--dry-run` lists them). A spec is
  linked when the branch changes it, when it is named like a changed file
  (`GuidelineExport.vue` → `guideline-export.spec.ts`), or through the app's feature map. A
  new user-facing flow gets a spec, named after its main component so it is picked next time;
  a changed flow gets its spec updated. Seed and clean up through the repo's e2e helpers.
  A test the baseline lists as failing on the base branch doesn't count against you, so don't
  "fix" unrelated broken specs; one that newly fails does.
- Leave the sandbox running when you finish: the reviewers and the human use it.
- Developer mode is off in the sandbox, so a migrate never writes DocType JSON for you: edit the
  JSON by hand, keep it consistent with the controller, and register patches in `patches.txt`.
