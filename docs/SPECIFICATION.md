# Minimal specification and algorithms

## Inputs and output

One saved college setup. The setter enters courses, their required components, durations/frequencies, assigned professors, rooms/capacities, and calendar/availability manually. Student records supply only registered courses; their year comes from the chosen list. No student chooses a professor.

A course can require multiple lectures, sections, labs, or assessment components. Use explicitly entered teaching-week frequencies or assessment counts/windows. Preserve first, second, and summer terms. See [confirmed scope](SCOPE-REVISION.md).

Generate all four years together. Output is validated schedules exportable to PDF, PNG, or JPEG. There is no posting, approval, official integration, or multi-university account model.

## Data structures

| Structure | Purpose |
|---|---|
| ID maps | Stable course, component, professor, room, and internal student IDs. Names are display labels, not join keys. |
| Registration sets and inverted indexes | Student → registered courses; course → students. Student year is display/import context and never the sole test of conflict. |
| Component records | Course, type, duration, frequency, fixed staff, required room type, and applicable term/window. |
| Resource records and interval lists | Room type/capacity, optional building/floor labels, professor availability, openings/closures/reservations. Intervals use `[start, end)`. |
| Recurring series and active-week maps | A recurring slot's dated members, academic week numbers, odd/even pattern, local weekday/time, room group and timezone. Multiple weekly sessions are distinct slots. Dated exams are singleton appointments. |
| Conflict graph | Fixed cohorts sharing students or staff. Conditional group membership is represented in the solver rather than treating every alternative group as mandatory. |
| Placement and group variables | Eligible dated time/room choices; section/lab/batch membership when a component needs multiple groups. |
| Saved result | Assignments, group allocations, validation results, input snapshot, and input revision for stale-result detection. |
| Edit requests, proposals and history stacks | Whole-pattern targets expanded to dated occurrences, swap mode, immutable constraints, pins, schedule/input revisions, server-held broader proposals, and atomic undo/redo snapshots. |
| Dynamic swap neighborhood | An edge represents an independently checked swap for one specific mode, scope and revision; it is distinct from the shared-participant conflict graph. |

## Algorithm

1. **Validate inputs.** Resolve course references, retain separate student records even with identical course lists, and reject missing duration, frequency, staff, capacity, or availability. Do not fill gaps from PDFs.
2. **Expand requirements.** Create recurring teaching slots and their dated occurrences, or dated examination sittings, from manually entered frequencies, durations and calendar. Retain academic odd/even weeks and calendar exceptions; do not infer parity from ISO week numbers. Convert each local start independently to UTC so local times survive daylight-saving changes. For sections/labs/batches, represent alternative groups while requiring each enrolled student to attend one complete group of each required component. Group allocation uses registered students and entered capacities; it does not require another student input field or a new professor choice.
3. **Generate eligible placements.** Sort/merge openings, subtract closures and occupied intervals, and retain starts/rooms that fit the entire entered duration and resource type. Use integer-minute times without rounding durations to a standard two-hour period.
4. **Solve jointly with OR-Tools CP-SAT.** Placement variables select time/room choices; membership variables allocate students to component groups when necessary. Require every necessary occurrence, fixed professor assignment, capacity, and availability. Forbid overlapping room use, overlapping assigned professors, and overlapping required attendance for every student, including across years. Enforce the entered frequency consistently for each group's members. Report configured group/domain bounds with the technical result; infeasibility applies to the modeled bounds.
5. **Check independently.** Recompute registration coverage, exact durations/frequencies, group membership, capacities, and all room/staff/student overlaps across the four years and overlapping saved scopes. Export only a complete valid result from the current inputs.
6. **Edit within constraints.** Expand whole-pattern moves/swaps across their own active weeks, preserving duration, students and professors. Audit the complete candidate across all years. If blocked, offer a CP-SAT broader arrangement with requested targets and pins fixed, minimizing additional pattern changes. Review every extra change before Apply. Recheck revisions/constraints; commit all or nothing with one undo entry. Show calculated direct partners and blocked reasons. [Exact editing contract](EDITING.md).
7. **Render.** Filter the same current validated edited result by year. Generate PDF and page images using the selected [timetable layout](TIMETABLE-FORMAT.md), excluding application controls.

Inverted-index graph construction takes `O(sum(d_s²))` for fixed required activities per student; interval sorting is `O(n log n)`. Optimization is bounded by a configurable internal time limit. Distinguish feasible/optimal, infeasible, invalid, cancelled/failed execution, and unresolved search. A timeout is not proof of impossibility. [OR-Tools statuses](https://developers.google.com/optimization/cp/cp_solver).

The earlier generation pilot predates this scope: joint automatic group membership, simplified records, and the export application still need implementation. The separate dated/whole-pattern editor, bounded broader rearrangement and synthetic interactive demonstrator are implemented and tested; they do not complete those pending application layers.
