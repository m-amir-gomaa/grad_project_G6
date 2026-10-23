# Constrained editing after generation

The normal flow is **Students → Generate → Review, edit and download**. Generation supplies a first suggestion. The setter can revise it repeatedly, undo/redo, and export the current complete valid result. Editing introduces no additional student-record fields.

## Inputs remain the confirmed inputs

- Student registrations only, entered individually or through a selected year's CSV. Local record IDs distinguish students; year is context. Students never choose professors.
- Manually registered courses and their lecture/section/lab/exam components, durations, frequencies, and setter-assigned professors.
- Manually entered halls/labs, type/capacity, resource and professor availability, term calendar, and relevant assessment windows.
- First, second, or summer term. All four years are considered together, including cross-year registrations and overlapping saved bookings.

Do not infer additional staff, buffers, examination spacing, or registrations from the visualization. Additional academic policies require explicit agreement before adding them as rules.

## Confirmed weekly scope

**A teaching edit changes the whole recurring weekly pattern.** A recurring slot records its own component/group, local weekday/time, room group, and explicitly active academic weeks. A frequency of several sessions per week produces several recurring slots; recurrence is never guessed from a course name.

Preserve the existing **odd/even academic-week format**. Week numbers come from the term's teaching calendar, not ISO calendar-week numbers. Holidays do not silently renumber later weeks. Moving or swapping an odd-week pattern retains its odd weeks; the same applies to even-week patterns. An odd/even view is only a display filter: validation still includes every active date and all four years.

Expand a requested local weekday/time separately in every active week, using the term timezone (`Africa/Cairo` for this college). Preserve the local hour across daylight-saving changes rather than adding one constant UTC offset. Reject ambiguous or nonexistent local times instead of guessing. A closure or staff conflict in even one active week blocks the complete direct edit. See [Python timezone support](https://docs.python.org/3/library/zoneinfo.html).

Examinations with explicit dates remain dated appointments. Do not turn them into weekly teaching recurrences. A dated assessment can be moved/swapped within its entered domain; a weekly/dated cross-swap is rejected.

## Edit operations

| Operation | Exact meaning |
|---|---|
| Move | Change a recurring slot's weekday/start and/or eligible room group in every active week. Keep its duration, participants, component, and assigned professors. |
| Swap times | Exchange two patterns' local weekday/start. Each keeps its own rooms, duration and active weeks, even when the patterns have different repetition counts. |
| Swap times and places | Exchange the weekly starts and room groups. Each retains its own duration, participants, professors and active weeks. Recheck room type, capacity and availability. |
| Keep fixed | Pin the entire recurring pattern. A pin prevents a direct edit, broader proposal or undo from moving any of its dates until released. |
| Broader arrangement | On the setter's request, keep the requested target(s) mandatory and search for a feasible arrangement that changes as few additional patterns as possible. Present every extra change before Apply. |
| Apply / cancel | Apply the complete preview atomically, or cancel without changing any placement. There is no partial application of a repeating pattern or broader proposal. |
| Undo / redo | Restore the complete operation through current constraint checks, including pins. An invalid restoration leaves the result and history unchanged. |

A direct move/swap keeps all unselected patterns fixed. If blocked, offer **Suggest a broader arrangement**. Searching does not change the schedule. The setter reviews the full result, then explicitly applies or cancels it. Changing registrations, duration, frequency, or professor assignment belongs to setup and requires recalculation/revalidation.

## Data structures and direct checks

Immutable ID-indexed placements contain dated UTC-minute intervals and exact student-to-room allocations. Recurring-series records map each slot to its dated members, academic week numbers, parity and timezone. Finite placement domains come from entered calendars/resources. Pins are dated occurrence IDs expanded from the selected series. Revision counters and before/after history snapshots prevent stale writes and support atomic undo.

1. Expand the requested pattern(s), including both sides of a swap, into one complete candidate. Sequentially moving the two sides can wrongly reject a valid simultaneous swap.
2. Derive each end time as `new start + own duration`. Rebuild room allocation only when rooms change; time-only edits retain existing allocations.
3. Audit exact occurrence/student coverage, duration, placement domain, eligible room type/capacity, full-interval openings/closures, fixed professor availability, reservations, and every room/professor/student overlap. Use half-open intervals `[start,end)`.
4. Also check weekly coherence, assigned active weeks and pins. A raw one-date request cannot bypass the whole-pattern rule.
5. Return the exact changed patterns and dated occurrences plus blocked reasons. On Apply, check schedule/input revisions and recompute the full audit under one lock; never trust client validity or graph colour.
6. Commit every change and one history entry together, or nothing. Input changes and pin changes invalidate old previews. Revalidate before export.

Resource-indexed interval sweeps cost `O(M log M + K)` for `M` resource-attendance intervals and `K` intersecting pairs visited, plus per-occurrence checks. Dense conflicts can still have quadratic output. Checking `N` potential partners costs `N` complete audits; production should bound the neighborhood and mark remaining targets unchecked. Cache keys must include both revisions, selection, scope and mode. No faculty-scale latency promise follows from this small demo.

## Broader arrangement algorithm

The implemented search uses **OR-Tools CP-SAT** over finite whole-pattern choices:

1. Fix the selected requested target(s). Fix pinned patterns and bookings outside the movable pattern set. Never relax professors, students, duration, frequency, capacities or availability.
2. Build eligible whole-pattern choices from the entered calendar/resource domains. Test all active dates against immutable constraints. Do not prune against the current positions of movable classes: those positions may change in the proposal.
3. Use exactly one Boolean-selected choice per pattern. For each incompatible pair of choices, forbid selecting both. An independent interval audit constructs these incompatibilities across all students and resources.
4. Minimize lexicographically: **additional patterns changed**, then **additional dated occurrences changed**, then total time displacement with a small room-change penalty. Dominating integer weights preserve that ordering. The original requested change is mandatory rather than an optimization preference.
5. Budget candidate construction, pair checks and solving. Worst-case pair construction is quadratic in the total candidate count, with an interval audit per pair; measure larger datasets before choosing optimizations.
6. Audit the complete solver result independently, including pins and weekly coherence. Return a read-only proposal tied to its input/schedule revisions. Apply rechecks both the constraints and the original requested target(s).

`OPTIMAL` proves minimum disruption only within the supplied finite domains and pins. `FEASIBLE` is a valid proposal without that minimum proof. `INFEASIBLE` concerns those modeled choices, never every conceivable college timetable. A timeout without a solution remains `UNKNOWN`, not “impossible.” [Official solver statuses](https://developers.google.com/optimization/cp/cp_solver).

The demo stores proposals on the server; Apply refers to an opaque proposal ID rather than accepting arbitrary client placements. The full application must persist results/history and compare-and-apply transactions atomically in SQLite. In-memory locking is not durable storage.

## Visual design

Keep the timetable primary. Selecting a class exposes Move, Swap and Keep fixed. A focused graph shows checked direct partners across all years, with text and line styles accompanying colour:

- **Green, solid:** this exact direct edit passed for the current mode, scope and revision.
- **Red, dashed:** blocked; show the actual conflicting class/resource, including another year or a third class.
- **Grey:** pinned, unchanged, or unchecked; unchecked never means valid or impossible.
- **Purple in a broader proposal:** distinguish the requested patterns from additional changes. The before/after list is authoritative and lists every affected pattern plus the total dated count.

Preview original/proposed times and rooms, preserved durations and active-week scope. Recompute partners after edits, pins or input changes. Edges are not transitive; several green edges do not authorize a combined operation. A full-college graph is optional, never the sole editor. Click/time controls and keyboard operation provide an alternative to dragging. [W3C dragging alternatives](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html).

## Implementation evidence and limits

Implemented: [dated editor](../timetabling/editing.py), [weekly and broader editor](../timetabling/patterns.py), [direct tests](../tests/test_editing.py), [pattern tests](../tests/test_patterns.py), and [interactive demonstrator](../examples/editing-demo/README.md). Tests cover whole-pattern scope, academic parity, different repetition counts, DST, one-week closures, whole-pattern pins, multi-pattern chains, minimum disruption, fixed bookings, atomic undo, forged targets and stale proposals. Separate minute-occupancy checks exhaustively compare small swap and rearrangement cases; this is bounded regression evidence rather than proof of arbitrary future policies.

The synthetic demo has eight recurring patterns and 21 dated occurrences across all four years. The FigCraft flow uses engine-produced prepared states; the browser runs real calculations. The generator/adapter must still expand manually entered component frequencies and resolve student groups before editing. The full student-entry/generation application, durable storage adapter, production PDF/image exports and faculty-scale performance measurements remain to be implemented.
