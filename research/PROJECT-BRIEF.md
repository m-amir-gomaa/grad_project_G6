# Proposed graduation-project brief

> Historical proposal: superseded by the [confirmed standalone scope](../docs/SCOPE-REVISION.md). See the [research index](README.md) for retained evidence and pilot boundaries.

**Working title:** Constraint-Based Academic and Examination Timetabling with Explainable Conflict Resolution — Tanta University, Faculty of Computers and Informatics.

**Status:** Proposed scope following initial supervisor approval of the idea; detailed faculty rules and acceptance criteria still require agreement. Research checked 22 October 2026.

## Problem and objective

The faculty must coordinate students, lecturers, teaching assistants, examiners, rooms, laboratories, and assessment requirements across the first, second, and summer terms. Changes to one activity can affect many other schedules.

The project will implement a system that **generates, validates, improves, and repairs complete faculty timetables**, showing the reasons for conflicts and the consequences of proposed changes.

## Required coverage

- All three term types, each with its own dates, offerings, teaching requirements, and examination periods.
- Lectures, sections/tutorials, and laboratory teaching, including alternating-week and online activities where used.
- Midterms, final written examinations, practical/computer-based examinations, oral examinations, and applicable retake, deferred, and graduation-related sittings.
- Candidate batches and examiner appointments where the assessment format requires them.
- The faculty's available halls, classrooms, laboratories, equipment, and imported external bookings affecting shared resources.
- Actual enrolment and section relationships, including students taking courses from different levels or regulation versions.
- University-owned profiles containing campus/building/floor/space inventories, floor-plan references, dated architecture changes, and location availability.
- PDF-assisted discovery of location labels with source provenance and staff reconciliation before operational use.

## Main functions

1. Import and validate structured faculty data.
2. Configure mandatory constraints and scheduling preferences.
3. Generate teaching and examination schedules using a constraint optimizer.
4. Validate complete coverage, capacity, availability, and student/staff/room conflicts.
5. Support manual editing, fixed assignments, and proposed alternatives.
6. Repair disruptions while minimizing changes to a published schedule.
7. Explain conflicts and supported infeasibility diagnoses in clear language.
8. Review, approve, version, publish, and export schedules by student/group, staff member, room, and examination.

## Proposed contribution

A documented and evaluated model of Tanta FCI's constraints, combined with explainable conflict resolution and limited-disruption schedule repair. Arabic/English support and faculty-compatible imports/outputs will make the implementation usable. Global novelty is not claimed; established systems already cover substantial parts of this domain.

Architecture changes are represented through effective revisions rather than hardcoded room lists. Earlier published schedules retain their original building/space versions. Shared occupancy and travel/accessibility relationships constrain placements where applicable.

## Proposed implementation

Use an established optimizer, provisionally OR-Tools CP-SAT, within a custom application and shared database. Teaching and examination scheduling use common resources and dated calendars, with distinct rules for each activity format. The final technology choice follows a representative modelling experiment and the team's skills.

## Evaluation and completion

Evaluate the optimizer against a faculty schedule and a simple algorithmic baseline; compare with UniTime or FET where their models are compatible. Measure coverage, hard violations, student gaps, examination spacing, runtime, manual work, and disruption after changes.

Completion requires all three term types and required activity/exam types to be demonstrated. Agreed feasible cases must have complete coverage and zero mandatory violations. Infeasible, invalid, partial, and time-limited results must be reported accurately. Test a room closure and an examiner absence, preserving fixed commitments and displaying the impact of the repair.

## Faculty inputs needed

Current source spreadsheets, room/equipment inventories, course/component requirements, staff availability, pseudonymized registrations, group allocations, calendars, examination policies, and approval workflow. A staff member who prepares timetables should review the rule catalogue and evaluation cases.

An initial [PDF-derived space registry](PDF-SPACE-REGISTRY.md), [architecture and algorithm design](ARCHITECTURE-AND-ALGORITHMS.md), and synthetic solver pilot are now available. Actual building/floor mappings and student registrations remain required for a real Tanta evaluation.

## Research basis

The faculty's [teaching schedules](https://ci.tanta.edu.eg/stu_study_tables.aspx) and [examination schedules](https://ci.tanta.edu.eg/stu-exam-tables.aspx) provide initial operational examples. [UniTime](https://github.com/UniTime/unitime), [FET](https://lalescu.ro/liviu/fet/), and [Cairo University timetabling research](https://arxiv.org/abs/1803.05027) establish relevant existing work. See the [full research report](TANTA-TIMETABLING-RESEARCH.md) for comparisons, sources, design details, and limitations.
