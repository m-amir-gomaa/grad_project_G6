# Features

## Main flow

1. **Students:** choose a year and add registered courses for one student, or import that year's CSV.
2. **Generate:** select the term and teaching/examination schedule. Generate using all four year lists and the saved setup.
3. **Review, edit and download:** view the suggestion, move/swap whole weekly patterns within constraints, repeat until satisfied, and export PDF or images. Changing the displayed year never reruns a separate solve.

The operator is the setter. There are no student accounts or choices, publishing roles, public links, approval steps, or official-college integration.

## Saved setup

| Item | Entered manually by the setter |
|---|---|
| Course | Name and required components; the application supplies a stable course reference for CSV. |
| Component | Lecture, section, lab, or examination type; duration; required frequency; assigned professor(s). Teaching frequency is per teaching week; examination frequency is a required sitting/appointment count in its entered assessment window. |
| Professor | Label and individual availability. Assignments come from the setter; the scheduler chooses times, not replacement professors. |
| Room | Hall/lab label, type, capacity, and availability. Existing building/floor labels can be retained as simple location metadata. |
| Calendar | Term date range, working days/hours, teaching weeks or dated exceptions, and assessment windows when exams are scheduled. |

All required scheduling data are explicit. A course can contain several components with different durations, frequencies, and staff. Do not derive these from student year, credits, scraped timetables, or other unstated defaults.

## Acceptance criteria

| Feature | Accepted when |
|---|---|
| Manual student entry | The form asks only for registered courses. The selected year supplies context, and an internal ID keeps different students distinct. No name, national ID, contact details, or professor selection is requested. |
| Year CSV | One row represents one student's registered courses. Preview identifies unknown courses and bad rows; invalid files save nothing. Identical registration lists in different rows are valid separate students. See [format](STUDENT-CSV.md). |
| Manual setup | Courses, their components, duration/frequency, professor assignments, resources, and availability can be entered and edited. Required blanks lead directly to the relevant field. |
| Joint generation | One combined run considers all four years. Shared resources and a student's courses from another year cannot overlap. The year display is a filter on the same result. |
| Constrained editing | Preview whole-pattern moves and time-only/time-and-room swaps against every active date. Preserve durations, fixed professors, registrations, resolved group memberships, and each pattern's academic odd/even weeks. Apply all changes atomically or reject them all. Dated examinations remain dated. See [editing rules](EDITING.md). |
| Broader arrangement | If a direct edit is blocked, offer an explicit broader search. Preserve the requested targets and pins; minimize additional changed patterns. Review every extra change and affected-date count before Apply. A search alone changes nothing. |
| Calculated alternatives | Timetable targets and the focused graph reflect the same checked mode/scope/revision. Explain blocked edits through actual affected resources/classes. Unassessed is not valid. Recalculate after accepted edits or input/pin changes. |
| Editing history | Pin whole patterns. Undo/redo a whole operation with current constraint checks. Direct edits preserve unrelated classes; broader proposals expose all additional moves. Show the full before/after result before application. |
| Complete result | Every student's required component occurrences are covered, durations/frequencies are respected, and all mandatory resource/participant/capacity checks pass. Only complete validated results can be exported as generated schedules. |
| Clear failure | Show a concrete missing field or known conflict and a way to fix it. For an unresolved search, say the tool could not find a schedule; do not claim the problem is impossible after a timeout. Preserve entered data. |
| Output | PDF, PNG, and JPEG contain only the chosen timetable content. Offer one year or all four years. Multi-page images are separate files in one download bundle. No application controls or student registration lists appear on a timetable. |
| Regeneration | Editing inputs marks an old result as out of date. Regenerate together; do not quietly present the old output as current. |
| Term/activity coverage | First, second, and summer terms; lectures, sections, labs, and the previously requested midterm/final/practical/oral and applicable retake/deferred assessment types use the same rules-based engine. |

Teaching and exam modes use one resource calendar. Overlapping saved schedules reserve resources against each other; replacing the same schedule excludes its previous placements from that check. Exports are derived from the selected saved result and its inputs.

An empty year contributes no registrations; do not manufacture its courses. At least one student registration is needed to generate a schedule.

The first complete demonstration uses synthetic records from all four years, a professor shared across years, a shared lab, and a cross-year registration. Generate, validate, export, change availability, and regenerate. Measure performance on the combined dataset; no unmeasured faculty-scale runtime promise is made.
