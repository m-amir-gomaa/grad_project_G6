# Default timetable format: Tanta FCI

Use Arabic, right-to-left printable tables. Include university/faculty, academic year, term, programme/level, and week pattern or exam category in the title. Preserve official course codes, group labels, and room names. Store dates/times unambiguously; display the source-style time ranges.

## Teaching timetable

The default programme/level view follows the published 2026/2027 grids:

- Weekday and location columns on the right; merged weekday groups.
- Periods, read from right to left: **9–11, 11–1, 1–3, 3–5**, corresponding to 09:00–17:00.
- Each occupied cell contains activity type, course, lecturer/assistant, and student group/section labels.
- Days run Saturday through Thursday. First/second/summer calendars can override the permitted dates and periods.
- Separate odd/even week pages where applicable; show dated exceptions explicitly.
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

Follow the published matrix: **day/date → course → location → timed candidate batches**, read from right to left. Merge day/course cells across their room rows. Display the authorized candidate assignments in each slot, including exceptions to any displayed number range. Use assessment-specific periods; the inspected example uses consecutive 30-minute columns. [Practical/oral source](https://ci.tanta.edu.eg/files/exam-table-practical2026.pdf).

Rendering these layouts is the default output requirement. Importing a table requires review of extracted cells. Blank cells do not establish room availability, and candidate-number ranges do not establish a complete registration list. Approval/footer fields are populated through the university's workflow.
