## In this Frappe app

There is no dev server to start and no port to use: the job has a **sandbox** site running the
branch code on a copy of real data.

- Read its URL and login from `<job folder>/sandbox.json`. If the file is missing or says it isn't
  running, run `python3 <main checkout>/factory/bin/frappe-sandbox up <job-id>`; it waits for
  anyone else starting it and doesn't rebuild what already runs. Never run `down`, `drop` or
  `refresh` on it.
- Sign in with that login: the "don't sign in or submit forms" rule above doesn't apply to the
  sandbox, which is a throwaway copy. Walk the flow the spec describes, end to end.
- When the change depends on a role, check it as a user with that role too. Give one a known
  password with `frappe-sandbox frappe <job-id> set-password <user> <password>`.
- Save screenshots as `<job folder>/round-<N>/shots/ux-<what>.png` (desktop and phone widths);
  the dashboard shows them. If you couldn't look at it, say so under Summary.
