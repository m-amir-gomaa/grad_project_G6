# Interactive constrained-editing demonstrator

From the repository root:

```sh
nix-shell --run '.venv/bin/python -m timetabling.editing_demo --port 8765'
```

Open **http://127.0.0.1:8765**. This is a temporary synthetic editing example, not the finished college application. The local HTTP server uses Python's standard library and serves only loopback requests. Broader searches use the project's OR-Tools dependency. Stop it with Ctrl+C. Outside NixOS, run the same module using a Python environment with the locked dependencies installed.

Select a class, inspect the timetable or its swap graph, choose **times only** or **times and places**, and click a target. Every teaching edit affects the **whole weekly pattern**. Odd/even view controls filter the timetable; checks include every active date and all years. Valid choices show the full before/after difference. Blocked choices show reasons and offer **اقتراح ترتيب أوسع**. Every additional change appears in purple before Apply; searching alone does not change the schedule.

Try swapping Programming 1 with Data Structures: the direct request is blocked by Computational Mathematics. A broader proposal also moves that pattern, while preserving the original requested swap. Apply changes all nine dated appointments together; one Undo restores them all. Swapping Programming 1 with Databases works directly despite their different durations and repetition counts. Also try moving Programming 1 to 17:00, undo/redo, and whole-pattern pins.

The eight recurring patterns expand into **21 dated occurrences**, including academic odd/even weeks across a Cairo daylight-saving change, all four years, a cross-year registration, shared professors/rooms/lab, unequal durations, and one pinned pattern. The 09:00–19:00 window and three-week dates are synthetic fixture data, not assumed Tanta availability. Student names, identity numbers, and actual university records are absent.

The core also supports explicit dated assessments, without inventing recurrence. The demo UI uses fixed weekly fixtures and an in-memory history. Actual student-entry, initial generation, durable project storage, and timetable PDF/image exports belong to the full application. Production broader searches will use the supervised worker; this small local demo runs a bounded search in its HTTP worker.

- [Editing specification and correctness contract](../../docs/EDITING.md)
- [Engine-calculated snapshot](verified-snapshot.json)
- [Browser verification](browser-verification.json)

Run algorithm checks with:

```sh
nix-shell --run '.venv/bin/python -m unittest discover -s tests -v'
```

The browser harness uses installed Playwright and Chromium without downloading packages. On this workspace:

```sh
nix-shell --run 'NODE_PATH=/home/qwerty/.npm-global/lib/node_modules node examples/editing-demo/verify.cjs'
```

It starts an owned temporary server and browser, checks actual edits/graph states, writes screenshots under ignored `design/.work/`, and closes its processes. Native FigCraft and the separate editing review are linked in [design/README.md](../../design/README.md).
