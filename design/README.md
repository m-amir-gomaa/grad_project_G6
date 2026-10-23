# Timetabling and constrained-editing design

The everyday flow stays **Students → Generate → Review, edit and download**.

- [Three-page UI review](g6-ui-review.pdf)
- **[Five-page editing review](g6-editing-review.pdf)**: timetable, calculated swap graph, exact before/after preview, a blocked cross-year conflict, and a broader arrangement proposal.
- [Editable native FigCraft file](g6-timetabling.figcraft)
- **[Run the interactive editing demonstrator](../examples/editing-demo/README.md)** to try actual whole-pattern moves/swaps, broader arrangements, pins, and undo/redo.

## Main screens and editing

1. [Students](previews/01-students.png): choose a year, enter registered courses, or upload its CSV.
2. [Generate](previews/02-generate.png): choose term/type; all four years are considered together.
3. [Review/edit/download](previews/03-schedule.png): review the suggestion, edit if needed, then export.

The [editing timetable](previews/17-edit-calendar.png) keeps a selected class in focus. Its [swap graph](previews/18-swap-graph.png) uses actual checked partners across years. Clicking a partner leads to the [two-class preview](previews/19-swap-preview.png) or an [actual conflict explanation](previews/20-swap-blocked.png). [Accepted direct edits](previews/21-edit-applied.png) retain unrelated placements. A blocked choice offers a [broader proposal](previews/22-broader-preview.png), showing the additional pattern in purple. Its [application](previews/23-broader-applied.png) has a single Undo for the complete change.

Edits affect every active date of the recurring pattern and preserve academic odd/even weeks. The fixture has eight recurring patterns and 21 dated occurrences. The broader example changes the two requested patterns plus one additional pattern, totaling nine dated appointments; pinned patterns remain fixed.

The graph and its labels come from [engine-generated evidence](assets/editing-evidence.json), with an [editable SVG](assets/swap-neighborhood.svg). They are different from a static graph of courses sharing students: green means the particular swap passed, for the chosen mode and current snapshot.

## Manual setup

Setup is separate: [course parts/durations/frequencies/fixed professors](previews/06-courses.png), [professor availability](previews/07-professors.png), [rooms/capacities/availability](previews/08-rooms.png), and [calendar](previews/09-calendar.png).

Supporting frames cover the [initial empty selection](previews/04-add-student.png), [CSV preview](previews/05-csv-preview.png), [download choices](previews/10-download.png), [loading](previews/11-running.png), [missing inputs](previews/12-fix-input.png), empty lists, and compact layout examples. These are dialog/tab/state examples, not extra workflow steps.

All values are synthetic. Student record labels are generated metadata, and student forms ask only for course registrations. No actual college records or assumed input defaults are embedded.

## Evidence and limits

[Tokens](tokens.json), [CSS variables](tokens.css), [frame/hotspot manifest](manifest.json), and [native verification](verification.json) accompany the design. The native flow navigates prepared states; the separate browser demonstrator executes the real editing engine. Neither claims to be the full student-entry/generation/export application.

The [editing contract](../docs/EDITING.md) defines whole-pattern swaps, odd/even preservation, bounded minimum-disruption search, full-calendar validation, revision checks, pins and history. Both whole-pattern scope and offering broader proposals are confirmed. Browser accessibility and full-scale performance require their own implementation checks.

## Rebuild

Requires installed FigCraft, Noto Sans Arabic, Poppler `pdfunite`, and the project's Python/OR-Tools environment. No package download is performed by the build.

```sh
nix-shell --run '.venv/bin/python design/tools/build_figcraft.py'
python3 design/tools/verify_figcraft.py \
  --session-helper /home/qwerty/.codex/skills/artcraft-creative-work/scripts/session.py
```

Regeneration overwrites generated outputs; preserve manual native changes in a copy first. The build uses a temporary headless FigCraft process, and verification opens/closes an owned GUI instance. Prior designs, logs and temporary browser screenshots are preserved under ignored `design/.work/`.
