## In this Frappe app

Frappe's hot spots, on top of the project's own list in AGENTS.md:
- `@frappe.whitelist()` endpoints: every one checks permission on the server
  (`frappe.has_permission`, `doc.check_permission`, the app's own helpers). Hiding a button is no
  check. `allow_guest=True` needs a reason and input validation.
- `ignore_permissions=True`, `frappe.get_all` (skips permissions) vs `frappe.get_list`, and
  `frappe.db.get_value` on user-chosen DocTypes or names.
- SQL built by string formatting or f-strings in `frappe.db.sql`; use parameters or the query
  builder. Same for `order_by` and field names taken from the request.
- HTML from users rendered without escaping (Jinja `| safe`, `v-html`, `frappe.render_template`).
- File access: private files, `is_private`, path joins with user input.
- Secrets: Password fields read with `get_password` only where needed, never returned to the client.
