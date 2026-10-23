# Confirmed scope

This replaces the earlier multi-user university workspace and approval/publication proposal.

- One isolated college scheduling tool; no university accounts, official integration, posting, or approval workflow.
- Four student year lists. Each student record contains only registered courses. Manual entry or a year-specific CSV is supported.
- The setter manually registers each course and its lecture, section, lab, and examination components, including frequencies and durations.
- The setter assigns the professor(s) for each component. Students cannot choose professors, and the scheduler cannot substitute them.
- Halls/labs, capacities, allowed scheduling days/hours, and individual professor availability are entered manually.
- Generate across all four years together for the selected first, second, or summer term.
- Check student, professor, hall, lab, capacity, and timing constraints before enabling schedule downloads.
- Output is schedules exported as PDF or images.
- The generated suggestion remains editable. Moves/swaps affect the whole weekly pattern, retaining academic odd/even weeks. Support checked previews, calculated alternatives, whole-pattern pins and undo/redo; repeated editing precedes final export.
- When a direct move/swap is blocked, offer a broader arrangement. Keep the requested targets and pins mandatory, minimize additional changes, and show every change for review before atomic application.
- Everyday UI: **Students → Generate → Review, edit and download**. Course/resource setup is a separate settings page.

No personal student fields, default course registrations, inferred durations, assumed teacher availability, or fabricated room data are required. Internal record IDs and course references are application metadata. CSV field names and transport conventions are specified in [STUDENT-CSV.md](STUDENT-CSV.md).

Further academic policies, such as examination spacing, session ordering, or batch eligibility, must be clarified before adding them as rules. A missing policy is not silently invented from historical PDFs.

Whole-pattern scope and explicitly requested broader arrangements are confirmed. The timetable remains primary, with a focused calculated graph as an alternative view. See [EDITING.md](EDITING.md).
