# Default timetable format: Tanta FCI

Use Arabic, right-to-left printable tables. Include the entered title when supplied, term, year level, and applicable week pattern or exam category. Tanta layouts are presentation references; no official logo, signature, approval, or college connection is implied. Use entered course/room names and application course references; an official course code is used only if supplied. Store dates/times unambiguously; display the source-style time ranges.

## Teaching timetable

The default programme/level view follows the published 2026/2027 grids:

- Weekday and location columns on the right; merged weekday groups.
- Periods, read from right to left: **9–11, 11–1, 1–3, 3–5**, corresponding to 09:00–17:00.
- Each occupied cell contains activity type, course, lecturer/assistant, and student group/section labels.
- Days run Saturday through Thursday. First/second/summer calendars can override the permitted dates and periods.
- Separate odd/even academic-week pages where applicable; show dated exceptions explicitly. Use the entered term's academic week numbers rather than ISO parity. Whole-pattern edits retain these active weeks and validate all their dates. See [editing rules](EDITING.md).
- Use the source legend for lecture, section, online, and location shading. Keep text labels meaningful without colour.

Reading-order example; placeholder content is illustrative:

| اليوم | المكان | 9–11 | 11–1 | 1–3 | 3–5 |
|---|---|---|---|---|---|
| السبت | مدرج 1 | محاضرة: [المقرر] / [المحاضر] / [المجموعة] | | | |
| السبت | معمل C | | سكشن: [المقرر] / [المعيد] / [السكشن] | | |

The general faculty view follows the published summer matrix: **rooms as rows**, with columns grouped by weekday and then period. It is a second view of the same assignments. Online is a delivery mode, not a physical room.

Sources: [programme grid with odd/even weeks](https://ci.tanta.edu.eg/files/2026-2027/stu_tables/1st-term/%D8%A7%D9%84%D9%85%D8%B3%D8%AA%D9%88%D9%89%20%D8%A7%D9%84%D8%AB%D8%A7%D9%84%D8%AB%20CS.pdf), [general summer matrix](https://ci.tanta.edu.eg/files/2025-2026/stu_tables/summer/%D8%A7%D9%84%D8%AC%D8%AF%D9%88%D9%84%20%D8%A7%D9%84%D8%B9%D8%A7%D9%85.pdf).

## Written examination timetable

Follow the published column order, read from right to left:

| م | اليوم | المقرر | كود المقرر | التوقيت |
|---|---|---|---|---|
| 1 | [اليوم والتاريخ] | [اسم المقرر] | [الكود] | [بداية–نهاية] |

Keep room and candidate allocations internally; provide a room-allocation view alongside this course-facing table. The example PDF does not include a room column. [Written exam source](https://ci.tanta.edu.eg/files/2025-2026/stu_exams/2nd_term_exam_tables/Level_3_CS.pdf).

## Practical and oral examination timetable

Follow the published matrix: **day/date → course → location → timed candidate batches**, read from right to left. Merge day/course cells across their room rows. Derive batches from the entered registrations and show application group labels or local record references; do not require an extra roster of student identities. Use the manually entered assessment durations; the inspected source uses consecutive 30-minute columns only as a presentation example. [Practical/oral source](https://ci.tanta.edu.eg/files/exam-table-practical2026.pdf).

Render these layouts from generated placements for PDF and PNG/JPEG downloads. Output contains timetable content, without application buttons, approval/signature fields, or posting links. Periods and durations follow the setter's manual setup; the historical periods are a layout example, not assumed availability. Blank source cells do not establish room availability, and historical candidate-number ranges do not supply student registrations.
