# Student CSV

This is the proposed application template, not an assumption about an existing college file.

Select the year before uploading. Each row is one student and contains only registered courses:

```csv
courses
C001|C002
C001
C001|C002
```

`C001` and `C002` are stable references shown beside manually registered courses. The application can supply references automatically, so an official course code is not a new required input. `|` separates multiple course references. A [blank template](../examples/simple-ui/students-template.csv) and [synthetic example](../examples/simple-ui/students-year-1.csv) are provided.

No student name/ID/contact/year/professor columns are required. The chosen year is import context. The application generates an internal ID per row; manually entered records use the same structure. Professors, durations, and frequencies come from the setter's saved course components.

The term chosen at Generate is saved with that run's registration snapshot. Changing the term does not change or invent registrations: enter/import the actual registered courses for the term being scheduled.

Validate the header, encoding (UTF-8, optional BOM), nonempty registrations, known course references, and duplicate references within one row. Reject invalid files atomically and point to row numbers. Two rows listing exactly the same courses represent two students and must both be retained.

Preview the number of records and destination year before adding them. Do not silently replace existing students. Warn when the exact same file is imported again. Without identifying input the system cannot detect whether different uploads describe the same real person; it must not pretend to do so.

Registers can include courses from any year. Do not infer unlisted courses from the student's year, especially for repeated courses or summer term.
