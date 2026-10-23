# Simplified UI

## Three everyday screens

**Students → Generate → Review, edit and download.** A small Settings link opens course/resource setup separately. No dashboard, approvals, publication, account switching, or optimization terminology. A contextual editing panel appears only when editing a selected class.

| Screen | Visible controls |
|---|---|
| Students | Four year tabs, registered-course list, Add student, Upload CSV, Next. The add form contains course selection only. Import preview shows destination year and row errors. |
| Generate | Term (first/second/summer), teaching or examination mode, one Generate button. All four years are always included. Required blanks show one actionable message linked to setup. |
| Review/edit/download | Year tabs, readable suggestion, Edit and Download. Selecting a class exposes Move, Swap, Keep fixed, Undo/redo, exact preview and Apply. Download options are PDF or image and one year/all years. Switching year filters the combined result. |

## Setup

One settings page with tabs: Courses, Professors, Rooms, Days/hours. Enter only the manually specified data:

- Course name; component rows for lecture/section/lab/exam, duration, frequency, and assigned professors. Staff selection is performed by the setter here, never in student records.
- Professor labels and individual availability.
- Hall/lab labels, type, capacity, and availability; retain building/floor labels as simple room metadata when provided.
- Term dates, working days/hours, relevant week patterns/exceptions, and assessment windows.

No course selections, durations, frequencies, room capacities, professor assignments, or availability are pre-populated from presumed college records. Example values in FigCraft are explicitly synthetic.

## Interaction and states

- Manual entry: start with no courses selected → select registered courses → save. No personal fields or professor choices; saving is disabled while the selection is empty.
- CSV: choose year → choose file → preview → add records. Show row-specific errors without losing the existing list.
- Generation: show a short working message and Cancel. No invented percentage. A complete validated result leads to Download; an unresolved search offers retry or input correction.
- Editing: the timetable stays primary. Edits affect the whole weekly pattern, with academic odd/even view controls and an explicit affected-date count. A focused graph shows checked direct partners across all years: labelled green/solid eligible connections, red/dashed blocked choices and reasons, grey pinned/unchecked choices. Preview both patterns before Apply.
- Blocked edit: offer **اقتراح ترتيب أوسع**. Searching preserves the current schedule. Show requested changes and every additional change with before/after times, rooms and active-week scope; highlight additional patterns in purple. Apply all changes or cancel. Pins remain fixed; one Undo restores the whole proposal. See [editing semantics and visual states](EDITING.md).
- A missing duration says “أدخل مدة المعمل” and links to that field. Do not expose solver codes, audit records, revisions, or permission states in normal screens.
- Changed inputs make the previous result visibly out of date and disable its current-result download until regeneration. Saved historical files remain files; there is no publication lifecycle.
- Download renders timetable content only. Errors preserve the result and offer retry.

## Visual rules

Arabic RTL, plain labels, white surfaces, one blue accent, comfortable 16–18 px body text, generous spacing, and clear 48 px controls. No decorative metrics or institution branding. Latin course references and times use bidi isolation. Responsive implementation stacks forms and uses readable schedule rows on narrow screens. Exports retain the documented Arabic table layouts.

Use labelled controls, visible keyboard focus, semantic tables, and dialogs that return focus to their opener. Include loading, empty, error, disabled, and successful states as needed. Native previews are design evidence; usability and accessibility require testing in the implemented application.

See the [three-page review, separate editing review, and editable FigCraft file](../design/README.md). Supporting native frames are dialog/tab/state examples of these screens, not extra steps for the user. The [local interactive editing demo](../examples/editing-demo/README.md) executes actual checks on synthetic data.
