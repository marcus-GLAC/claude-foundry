## In this Frappe app

Also check:
- DocType JSON and its controller agree (fields, types, options, permissions), and every field
  the frontend shows is changed on both sides.
- Schema or data changes come with a patch registered in `patches.txt`, safe to run twice.
- `hooks.py` changes (doc_events, scheduler, fixtures, overrides) are needed and scoped.
- User-facing strings are translatable: `_()` in Python, `__()` in JS and Vue.
- No `frappe.db.commit()` outside patches and tests; no queries in loops where one query does.
- Tests: new behaviour has a test, and fixtures a test creates are cleaned up. A new or
  changed user-facing flow has an e2e spec that the gate picks (`frappe-e2e --dry-run` from
  the worktree lists them); a spec that asserts nothing the criteria name doesn't count.
