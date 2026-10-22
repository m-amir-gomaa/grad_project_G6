# Minimal project specification

## Scope

Generate, validate, and repair faculty schedules for lectures, sections/tutorials, labs, midterms, written finals, practical/computer exams, oral exams, and applicable retake/deferred sittings. Support first, second, and summer terms with their own calendars. Use the [Tanta timetable formats](TIMETABLE-FORMAT.md) by default.

University setup contains a simple building layout. A geometric floor-plan editor, CAD/BIM processing, and route modelling are outside this initial specification.

## Building layout

```text
University
  Building
    Floor
      Room
```

Store stable IDs and display names for each level. A room contains its type (lecture hall, classroom, laboratory), seated/exam/computer capacities, availability intervals, and active/closed state. Scope every record to its university. Staff accounts access the university's saved layout through membership.

Record layout changes as effective revisions. Renaming or closing a room preserves its identity and earlier schedules; splitting or merging rooms creates new identities and retires the predecessors. Unconfirmed PDF labels remain import candidates until mapped to a building, floor, and physical room. Preserve source labels as aliases.

## Scheduling inputs

- Term dates, teaching weeks, odd/even patterns, assessment windows, and holidays.
- Course offerings, activity types/durations, required sessions, and assigned staff with availability.
- Pseudonymous student registrations, teaching-section allocations, and assessment candidates or authorized batches.
- Confirmed rooms, capacities, and existing reservations.

Student membership follows registrations and assigned alternatives. A student attends their assigned lab section, and each required exam component, including courses taken from another level.

## Data structures

| Structure | Contents and purpose |
|---|---|
| University-scoped ID maps | Buildings, floors, rooms, offerings, students, and staff; fast lookup without identifying a room by its name alone. |
| Layout revision records | Effective room configuration and the version referenced by each schedule. |
| Sorted interval lists | Room/staff openings, closures, reservations, and dated assignments. Intervals use `[start, end)`. |
| Registration indexes and participant sets | Student → required activities; activity → students/staff. Set intersections identify shared participants. |
| Conflict graph | Activities as vertices; edges connect activities sharing students or staff. Shared-student counts can weight edges. |
| Activity and placement records | Type, term, duration, recurrence; candidate date/time, room set, and candidate-to-room allocation. |
| Schedule map | Activity occurrence → selected placement, with previous assignments and locked events for repair. |

## Algorithms

| Stage | Algorithm |
|---|---|
| Import locations | Extract positioned PDF text; use Arabic/English OCR for image pages. Normalize labels and retain source/page evidence. Reconcile aliases before creating physical rooms. |
| Form activities | Expand teaching patterns into dated occurrences, keeping the same pattern within an odd/even week group except for explicit dated exceptions. Form the required exam sittings or appointments. |
| Find available slots | Sort and merge opening intervals, subtract closures/reservations, then enumerate starts that fit the full duration and preparation/reset time. |
| Build conflicts | Use the inverted registration index to connect required activities sharing students; add staff conflicts. Avoid treating every alternative section as mandatory. |
| Generate placement domains | Filter time/room alternatives by availability, type, capacity, calendar, and locks. Written exams may use simultaneous rooms; practical batches and oral appointments follow their supplied policies. |
| Assign placements | Use **OR-Tools CP-SAT** with one Boolean variable per eligible placement. Choose exactly one placement per required occurrence; forbid overlapping placements sharing a room, student, or staff member. |
| Improve and repair | Keep hard constraints mandatory. For revisions, minimize moved published activities before optimizing student gaps, exam-spacing preferences, and room use. Retain authorized locks and save a new schedule version. |

The conflict graph can be constructed in `O(sum(d_s²))`, where `d_s` is the number of relevant activities required by student `s`; interval sorting takes `O(n log n)`. CP-SAT search is time-limited and reports feasible, optimal, infeasible, invalid, or unresolved outcomes. A timeout does not prove impossibility. [CP-SAT documentation](https://developers.google.com/optimization/cp/cp_solver).

## Required checks

Every required activity and exam candidate must be allocated. Validate room/student/staff overlaps, effective room state, capacity, duration, required contact time, section membership, and mandatory exam rules before publishing. Keep incomplete results as drafts with their unresolved activities listed. Check both newly generated and manually edited schedules.

Completion includes all three term types, the required teaching/exam categories, and a room-change scenario that preserves the earlier timetable and repairs affected assignments. Measure coverage, mandatory violations, solve/revision time, and moved activities using a common validated input snapshot.
