# College Timetabling — Graduation Project G6

A standalone tool with three steps: **Students → Generate → Review, edit and download**.

The setter manually defines courses and their lecture/section/lab/exam components, durations, frequencies, assigned professors, rooms, capacities, and availability. Student records contain only registered courses, entered individually or imported by year from CSV.

Generate the selected term's schedules for **all four years together**, checking students, professors, halls, and labs across the entire college. Export schedules as PDF or images. Support first, second, and summer terms. Tanta FCI schedules are layout references; the tool has no official college connection or publishing workflow.

The first suggestion can be revised through checked moves/swaps of whole weekly patterns, preserving academic odd/even weeks. If blocked, request a broader arrangement and review every additional change before Apply. Pins and undo/redo cover the whole operation. A focused graph shows calculated partners and blocking reasons. [Editing contract](docs/EDITING.md) · [Run the interactive synthetic demo](examples/editing-demo/README.md).

- [Features](docs/FEATURES.md) and [confirmed scope](docs/SCOPE-REVISION.md)
- [Minimal specification, data structures, and algorithms](docs/SPECIFICATION.md)
- [Student CSV format](docs/STUDENT-CSV.md)
- [UI specification](docs/UI.md) and [editable FigCraft design](design/README.md)
- [Recommended technology](docs/TECH-STACK.md)
- [Output layouts](docs/TIMETABLE-FORMAT.md) and [source research](docs/SOURCES.md)

The repository contains specifications, native FigCraft designs, a tested constrained-editing engine, and an interactive synthetic editing demo. The full student-entry/generation application, durable storage adapter, and production export pipeline remain to be implemented. Earlier research and the scheduling pilot are development references.

This checkpoint records the agreed feature, UI/UX, and algorithm specification for implementation. The documents in `docs/` define the current scope; see the [research index](research/README.md) for historical material and pilot boundaries. Design usability and the complete application's behavior still require validation during implementation.
