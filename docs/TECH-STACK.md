# Recommended technology

The confirmed product is one isolated tool. The earlier multi-user deployment proposal is superseded.

| Part | Recommendation |
|---|---|
| Interface | React, TypeScript, Vite; CSS tokens/logical properties and native controls. Three screens plus setup. |
| Local API | Python 3.13 and FastAPI with typed request validation. Serve the built UI from the same local application. |
| Saved data | SQLite through Python's `sqlite3`, foreign keys and explicit schema migrations. One college setup, registrations, and saved results. |
| Scheduling | OR-Tools CP-SAT; reuse the pilot's pinned version initially, then validate any upgrade. |
| Editing | Immutable Python snapshots, explicit recurring-series/academic-week maps, `zoneinfo` local-time expansion, independent resource/participant audits, revision checks and atomic history. Direct checks need no optimization; broader proposals use CP-SAT with fixed requested targets/pins and minimum additional changes. |
| Long work | One supervised Python child process for generation/export, with a persisted job ID and status. The UI polls; cancellation stops the owned job. |
| Export | Escaped local HTML/CSS templates rendered by Playwright/Chromium to PDF, PNG, or JPEG. Bundle fonts; do not load remote template resources. |
| Development checks | uv and a frontend lockfile; pytest for model/import/export rules and Playwright for the actual three-screen flow. |

This is a proposed local deployment: one operator opens a browser connected to the local process. Bind it to loopback, serve the UI/API on one origin, and reject unexpected hosts/origins for mutation requests. A shared/network deployment would require a separate decision about access control. Accounts, multi-tenancy, PostgreSQL, Redis, and Celery are unnecessary for this initial scope.

FastAPI documents SQLite as a local database option. [Official database tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/). Python exposes owned child-process management without adding a queue service. [Python subprocess](https://docs.python.org/3.13/library/subprocess.html). Playwright provides PDF and image rendering. [PDF API](https://playwright.dev/python/docs/api/class-page#page-pdf), [screenshots](https://playwright.dev/python/docs/screenshots).

## Implementation contracts

- Keep course/component creation and professor assignment separate from student registration. A student stores only registered course references, plus generated internal ID and year/term context.
- Load one immutable input snapshot across all four years for a run. Persist job status and saved results in SQLite. Never run optimization inside the request handler.
- Permit one generating/exporting child process at a time for the initial local tool. On restart, mark an interrupted run as interrupted and allow retry; retain previous valid data.
- Validate CSV before one transaction adds its records. Preserve distinct rows with identical registrations. Never auto-complete a student's course list.
- Generate groups/placements under [the specified constraints](SPECIFICATION.md), then independently validate complete attendance, duration/frequency, resources, and capacity.
- A download checks that the selected result is complete, validated, and current. PDF/images share the same placement data. Timetables omit student registration rows and application controls.
- Persist checked edits and history with the same compare-and-apply transaction as the in-memory [editing contract](EDITING.md). Swap target colours are derived from checked requests, never from visual proximity or matching durations. Ignore out-of-order preview responses and reject stale applications server-side.
- Expand every weekly edit across its explicit active dates, retaining academic odd/even parity and local time across DST. Store broader proposals on the server, show all additional changes, and revalidate the original requested targets and current pins on atomic Apply. Run production broader searches in the supervised worker, not a request handler.
- Cover cross-year conflicts, fixed professor assignments, a course with multiple component durations/frequencies, unknown CSV courses, identical registration rows, missing availability, cancellation, stale results, and PDF/image content in implementation tests.

Exact package versions are selected and locked together when implementing the application. The [standalone editing demonstrator](../examples/editing-demo/README.md) uses a standard-library local HTTP server and plain JS/SVG to exercise the real editor without adding framework dependencies. It is a test/design artifact, not a replacement decision for the full React/FastAPI application.
