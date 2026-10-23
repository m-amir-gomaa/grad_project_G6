# Faculty-wide academic and examination scheduling for Tanta FCI

> Historical research: retain the software comparisons and source evidence, but use the [confirmed scope](../docs/SCOPE-REVISION.md) for current product requirements. See the [research index](README.md).

**Research date:** 22 October 2026. **Institution:** Faculty of Computers and Informatics, Tanta University, Egypt.

**Scope confirmed by the project owner:** lectures, sections/tutorials, labs, and all examination types in both main terms and the summer term, across the faculty's available spaces. The recommendations below retain that complete scope.

**Subsequent extension:** university-owned building profiles, dated architectural changes, a PDF-derived location registry, and registration-driven data/solver structures are described in [Architecture and algorithms](ARCHITECTURE-AND-ALGORITHMS.md). The actual scan is documented in [PDF space registry](PDF-SPACE-REGISTRY.md).

## 1. Assessment as a graduation project

This is a defensible computer science graduation project when it includes automatic schedule generation, conflict resolution, resource allocation, and an evaluated implementation. A system that only uploads schedules and highlights overlaps would leave much of the professor's requested problem unsolved.

The technical contribution can include requirements modelling, constraint programming, database design, student enrolment analysis, optimization, interactive editing, schedule repair, and experimental evaluation. Its academic merit does not depend on inventing a completely new scheduling algorithm. Final assessment requirements remain those agreed with the supervisor.

University timetabling is an established research and software domain. For example, Cairo University course scheduling has been modelled with Max-SAT, and UniTime provides a complete university scheduling application. Existing work establishes the problem's substance while making a claim of global novelty inappropriate. [Cairo University paper](https://arxiv.org/abs/1803.05027), [UniTime repository](https://github.com/UniTime/unitime).

The screenshot's original “medium” scope described a much narrower conflict detector. Full faculty coverage, examinations, three terms, and reactive rescheduling make the present proposal a substantially larger group project. Build it in stages, with every required activity and term represented in the final acceptance criteria.

**Recommended working title:** *Constraint-Based Academic and Examination Timetabling with Explainable Conflict Resolution: A Case Study at Tanta University's Faculty of Computers and Informatics.*

## 2. What the public faculty material establishes

The following are observations from published documents, not a substitute for a current room survey or interviews with the scheduling committee.

| Published evidence | Implication for the proposed system |
|---|---|
| The official teaching page lists levels, CS/IS/IT tracks, special-programme schedules, and summer schedules. | Organize offerings by programme, level, term, and curriculum version while allocating shared resources across the faculty. |
| The official exam page separates midterms, final schedules, practical/oral exams, old/new regulations, and graduation-related cases. | Exam category and regulation version must be explicit data, rather than inferred from a course name. |
| The linked 2026/2027 level-three CS PDF contains separate odd/even week timetables and online teaching. | Support recurring week patterns, delivery mode, and actual dates. A single repeating weekly grid is insufficient. |
| The published practical/oral timetable allocates batches to laboratories and short successive time windows, including students registered from other levels. | Model batch sittings and actual candidate membership. A cohort-only exam clash check can miss conflicts. |

Sources: [teaching schedules](https://ci.tanta.edu.eg/stu_study_tables.aspx), [examination schedules](https://ci.tanta.edu.eg/stu-exam-tables.aspx), [level-three CS timetable](https://ci.tanta.edu.eg/files/2026-2027/stu_tables/1st-term/%D8%A7%D9%84%D9%85%D8%B3%D8%AA%D9%88%D9%89%20%D8%A7%D9%84%D8%AB%D8%A7%D9%84%D8%AB%20CS.pdf), [practical/oral examinations](https://ci.tanta.edu.eg/files/exam-table-practical2026.pdf).

The faculty's linked student guide describes 16–17-week main terms and a 7–8-week summer term, including examinations. Its inventory shows different seat and computer counts: lab C has 57 seats and 37 computers; lab D has 57 and 50. It also lists three 120-seat lecture theatres and eight 35-seat classrooms. These are published inventory figures, not verified present-day availability or exam capacities. [Student guide, PDF pages 19, 56–57](https://ci.tanta.edu.eg/files/%D8%AF%D9%84%D9%8A%D9%84%20%D8%A7%D9%84%D8%B7%D8%A7%D9%84%D8%A8%2026.pdf).

**Proposed response to those observations:** distinguish seated capacity, approved exam capacity, and currently usable computers; represent odd/even weeks and online meetings; import cross-level registrations; and configure the teaching and assessment calendar separately for each term. Confirm room aliases and external hall access with staff. The public inventory does not prove that every space in a current timetable belongs to the faculty or is always available.

Public schedules show outputs. They do not establish whether staff currently use Excel, a commercial package, an internal optimizer, or several tools to produce those outputs. No claim is made that this would be Tanta's first scheduling system.

## 3. Open-source applications and solver building blocks

The distinction between a complete application and an optimization library matters. A library solves the mathematical model you implement; it does not supply the faculty's administrative workflow.

| System | Verified type and licence | Relevant functionality | Recommended use in this project |
|---|---|---|---|
| **UniTime** | Full university application; main application repository is Apache-2.0. Java. | Course and examination timetabling, student sectioning, instructor scheduling, event/room coordination, changes to schedules. | Strongest functional reference and a candidate baseline; also an adaptation option if deployment is prioritized. |
| **FET** | Full timetabling application; GNU AGPL v3. C++/Qt. | Automatic/manual scheduling; teachers, rooms, student sets, availability, many time/space constraints, CSV/XML input/output. Arabic localization exists. | Useful teaching-timetable baseline and constraint catalogue. Verify exam workflows rather than assuming it supplies a complete examination-management product. |
| **Timefold Solver Community Edition** | Embeddable Java/Kotlin optimization engine; Apache-2.0. Commercial editions also exist. | Hard/soft constraints; official school-timetabling example assigns lessons to times and rooms. | Good foundation for a Java team; university exams, term calendars, candidate batches, imports, and approval workflows remain project work. |
| **Google OR-Tools CP-SAT** | Optimization library; Apache-2.0. Supports Python and other languages. | Integer/Boolean models and scheduling constraints; official repository includes a contributed school-scheduling example. | Recommended starting engine for a Python team building its own Tanta application. |
| **UniTime CPSolver** | Separate Java solver library; LGPL v3. | Local-search constraint solving, including academic scheduling models. | Useful research/reference implementation, particularly when studying UniTime internals. |

Sources: [UniTime application](https://github.com/UniTime/unitime), [FET](https://lalescu.ro/liviu/fet/), [FET features](https://lalescu.ro/liviu/fet/features.html), [Timefold Solver](https://timefold.ai/solver), [Timefold teaching example](https://github.com/TimefoldAI/timefold-quickstarts/tree/stable/use-cases/school-timetabling), [OR-Tools](https://github.com/google/or-tools), [OR-Tools example](https://github.com/google/or-tools/blob/stable/examples/contrib/school_scheduling_sat.py), [CPSolver](https://github.com/UniTime/cpsolver), [CPSolver licence](https://raw.githubusercontent.com/UniTime/cpsolver/master/LICENSE).

Two details avoid misleading comparisons. First, Arabic support alone is already present in FET, so it is not an adequate novelty claim. Second, the UniTime application and its solver have different licences. Historical papers and old mirrors can describe older versions; check the actual components selected. The FET project's official download site is a better starting point than the old GitHub mirror encountered in search. [FET official site](https://lalescu.ro/liviu/fet/), [older mirror](https://github.com/fet-project/fet).

Use these implementations as references with clear attribution. A renamed installation or a lightly reskinned tutorial would need a separate, substantial contribution to meet the proposed graduation-project objectives.

## 4. Commercial landscape

These descriptions summarize vendor documentation. Products were not installed or benchmarked during this research. “Study this feature” identifies useful design references, not a claim that the product is missing other functionality.

| Product | Published scope relevant to Tanta | What to study |
|---|---|---|
| **TimeEdit** | Teaching scheduling/AutoPilot, assessment/exam scheduling, allocation, room booking, publication, integrations. | Separate constraint profiles; data preparation; explanations of failed scheduling jobs; exam and invigilator workflows. |
| **CELCAT / Celcat AI** | Interactive timetabling, automated course scheduling, room booking, examination scheduling, publication. | Live clash feedback, manual adjustments, constraint configuration, timetable rollover. |
| **TechnologyOne Timetabling & Scheduling**, formerly Scientia/Syllabus Plus | Class scheduling, exam scheduling, invigilators and seats, room/resource bookings, personalized publication. | Connected modules using shared operational data; managing changes and publishing schedules. |
| **Infosilem Academic / Exams / Campus** | Course scheduling, examination scheduling, and campus resource/event bookings. | Student-demand modelling, multi-room exams, room suitability, alternative requirements, change impact. |
| **EventMAP Optime Timetabler / Exam** | Academic activities, examination and invigilation scheduling, with related booking products. | Candidate-specific requirements, exam seating, staff allocation, and adjustment suggestions. |
| **Coursedog** | Academic section/room scheduling and academic workflows, with related curriculum and event products. | Instructor preference collection, policy validation, departmental approvals, room assignment. |
| **Ad Astra** | Academic scheduling, room/event scheduling, demand and utilization analysis. | Course demand, classroom utilization, collaboration across departments. |
| **aSc Timetables** | Automatic timetable generation with online and desktop versions. Official trial has export/printing restrictions. | Accessible timetable editing and a smaller product benchmark; establish exact university/exam fit in a trial. |

Sources: [TimeEdit products](https://www.academy.timeedit.com/products), [AutoPilot](https://www.academy.timeedit.com/products/autopilot), [TimeEdit exams](https://www.academy.timeedit.com/products/exam), [CELCAT exams](https://celcat.com/timetabler/extensions/exam-scheduling/), [CELCAT automation](https://celcat.com/timetabler/extensions/automated-premium/), [TechnologyOne](https://www.technology1.com/products/timetabling-and-scheduling), [TechnologyOne brochure](https://www.technology1.co.uk/__data/assets/pdf_file/0006/263670/TNS-Timetabling-and-Scheduling-brochure-UK.pdf), [Scientia rebranding evidence](https://technologyonecorp.com/__data/assets/pdf_file/0003/215454/2022-Annual-Report-TechnologyOne.pdf), [Infosilem products](https://infosilem.com/en), [Infosilem FAQ](https://infosilem.com/en/faq), [Optime products](https://www.eventmapsolutions.com/), [Optime Exam](https://www.eventmapsolutions.com/products/exam), [Coursedog product documentation](https://coursedog.my.site.com/support/articles/Knowledge/CoursedogProductsExplained67fd7ad6a397b), [Ad Astra](https://www.aais.com/), [aSc official trial information](https://asctt.edupage.org/a/ceny).

**Costs:** the open-source software above has no software licence purchase price, but hosting, integration, support, and maintenance still require effort. This review did not establish current Egyptian institutional quotations for the commercial suites. A historical public TimeEdit UK procurement rate card lists a £10,000 annual minimum, excluding VAT; it is a 2024 procurement document, not a current price for Tanta. Obtain a scope-specific quote if a build-versus-buy comparison becomes necessary. [Published rate card](https://assets.applytosupply.digitalmarketplace.service.gov.uk/g-cloud-14/documents/719636/871656448042845-pricing-document-2024-05-07-1055.pdf).

For the graduation project, the most useful commercial references are TimeEdit, CELCAT, TechnologyOne, Infosilem, and Optime because they explicitly address teaching and/or examination scheduling in depth. Course scheduling, calendar display, and full exam scheduling should not be treated as interchangeable capabilities. Lack of a confirmed feature in this review is not proof of its absence.

## 5. Egyptian research and public implementations

| Example | What is established | Relevance and limits |
|---|---|---|
| **Cairo University, mathematics department: Max-SAT timetabling** | A 2018 paper models department course scheduling as Max-SAT. | Direct Egyptian academic precedent for constraint-based scheduling; it does not establish a faculty-wide Tanta implementation. |
| **German University in Cairo: constraint-based timetabling** | A university-hosted paper describes a Prolog constraint-satisfaction model tailored to the institution. | Supports the case for local constraint modelling. The paper is historical; its operational figures should not be presented as current. |
| **EJUST-inspired public Python prototype** | Its README describes greedy scheduling for lectures, labs, tutorials, staff, rooms, and four undergraduate levels, using manually created data based on EJUST structures. | Useful small implementation to inspect. It is not evidence of official deployment at EJUST or independently verified performance. |
| **Lumen, focused on FCIS Ain Shams** | Its README describes students choosing existing lecture/lab/tutorial alternatives to reduce timetable gaps. | Relevant student-facing design, but selecting among existing sections differs from creating the institution's master timetable. |

Sources: [Cairo paper](https://arxiv.org/abs/1803.05027), [GUC paper](https://met.guc.edu.eg/Repository/Faculty/Publications/67/Paper.pdf), [EJUST-inspired prototype](https://github.com/OmarElHawy/Automated-Timetable-Generation-as-a-Constraint-Satisfaction-Problem-CSP-), [Lumen](https://github.com/UniLumen/Lumen).

At inspection, GitHub did not identify a licence for either small public prototype. Treat them as publicly visible code references rather than established, reusable open-source dependencies until the relevant terms are established. No operational-quality claims from their READMEs were tested. The GUC PDF was indexed by web search, but direct retrieval failed in this session; this assessment relies on its indexed abstract.

The defensible claim is therefore **a Tanta-specific engineering contribution, supported by evaluation**. Neither “first in Egypt” nor “nobody has combined exams and teaching” is supported by the evidence.

## 6. Scope of the proposed product

Use a shared institutional model with different scheduling rules for recurring teaching, cohort exams, laboratory sittings, and individual appointments.

| Activity | Required scheduling behaviour |
|---|---|
| Lectures | Allocate staff, time, delivery mode, room capacity, and recurrence weeks. Support shared lectures across multiple groups. |
| Sections/tutorials | Link each section to its course and lecture group; allocate teaching assistants and the correct student subgroup. |
| Practical laboratory teaching | Allocate compatible equipment/software and sufficient usable workstations, with appropriate preparation/reset time. |
| Midterm tests and quizzes | Allocate dated assessments during the teaching term, checking against ongoing classes and other tests. |
| Final written exams | Allocate dated sessions, candidates, one or more rooms, approved seating capacity, duration, and invigilators. |
| Practical/computer-based exams | Allocate candidates to authorized batches, machines/stations, assessors, laboratories, and successive sittings. |
| Oral exams/vivas | Allocate appointments or batches, examiner panels, rooms, durations, and candidate availability. |
| Retake, deferred, and graduation-related exams | Support distinct exam instances and irregular enrolments using the relevant regulation and eligibility data. |
| Project defenses or other scheduled assessments | Represent as panel-based appointments where the faculty includes them in its assessment calendar. |
| Synchronous online activities | Reserve student/staff time; require a physical space only when actual delivery needs one. |
| Asynchronous assessment | Track assessment windows/deadlines without falsely blocking the entire student timetable. |

These are proposed configurable categories. Confirm the faculty's terminology, policies, and actual offerings; the public pages alone do not establish that every category operates in every term.

The **first, second, and summer terms are all core scope**. Each term needs its own dates, teaching weeks, exception dates, offering list, staff availability, assessment windows, and contact-hour requirements. Do not assume that summer is an unchanged weekly timetable or that course credit count equals hours of teaching. Weekly meetings must cover the course's approved contact requirements within the actual teaching calendar, excluding closures and assessment-only dates as appropriate. Supporting the academic year does not require solving every term at once: solve the relevant period while checking the shared reservation calendar, including delayed exams or other activities that overlap its dates.

Faculty-wide scope includes shared halls and laboratories available to the faculty. For spaces or staff also used elsewhere, import external commitments as fixed reservations. Full optimization of other faculties' schedules is a separate institutional expansion, but their existing bookings must still constrain this system.

Scheduling student attendance means providing a feasible set of activities for students to attend. Recording actual attendance is a separate feature and is not needed to prove the scheduling contribution.

## 7. Shared data model

| Entity | Important fields and relationships |
|---|---|
| Academic year / term / calendar | Term type, date range, teaching-week numbers, holidays, exam windows, local timezone. |
| Programme / curriculum version | Programme, department, regulation/version, study level. |
| Course / term offering | Stable course identifier; term-specific offering; component contact-hour requirements; linked exam components. |
| Teaching component / event series | Lecture, tutorial, or lab; duration; meeting count; week pattern; mode; assigned/eligible staff; eligible rooms. |
| Event occurrence | Actual date, start/end, resource reservations, participants, exceptions to recurrence. |
| Student / enrolment / group | Pseudonymous student key; enrolled offerings; actual section assignment; cohort/subgroup membership. |
| Staff member / role | Qualifications, teaching and examining eligibility, availability, workload, roles on panels or invigilation teams. |
| Space / equipment / capacity | Canonical room ID, aliases, location, seat capacity, exam capacity, usable computers, software/equipment tags, accessibility, availability dates. |
| Exam / sitting / batch / candidate | Exam type and component, duration, candidate membership, allowed dates, batch allocation, linked simultaneous sittings. |
| Constraint / policy profile | Rule type, affected entities, hard/soft status, priority, scope, effective dates, human-readable reason. |
| Schedule version / assignment | Draft/approved/published state; changes from prior version; author; dataset and solver settings. |

Keep a course distinct from an offering, a teaching series distinct from its dated occurrences, and an exam distinct from its sittings. Without those distinctions, repeated summer offerings, odd/even weeks, and practical batches become difficult to represent correctly.

Choose one canonical ID per space. A hall called “1” and a laboratory called “1” are different resources; a named central hall may also appear under several aliases. Imported aliases must be resolved before scheduling.

## 8. Hard constraints and optimization preferences

Hard constraints define whether a candidate schedule is publishable. Soft constraints express preferences among otherwise valid schedules. The scheduling committee should explicitly classify disputed policies.

| Hard constraint | Example |
|---|---|
| Room and equipment availability | A room cannot host overlapping exclusive bookings; shared equipment cannot be overallocated. |
| Staff availability and role eligibility | A lecturer, teaching assistant, examiner, or invigilator cannot occupy overlapping assignments. |
| Student availability | A student cannot attend two assigned mandatory activities or sit two examinations simultaneously. |
| Capacity and suitability | Enough seats, approved exam places, or usable workstations; required equipment/software must exist. |
| Course coverage | Every required component receives its prescribed sessions/contact time in the permitted weeks. |
| Calendar and duration | Meetings occur within permitted dates; activity duration plus preparation/reset time fits. |
| Academic links | Students receive exactly the required section/lab choices and correct lecture links. |
| Examination policy | Common exams, permitted batching, examiner panels, required invigilator counts, and mandated breaks are respected. |
| Locked assignments | An approved fixed event remains fixed unless an authorized revision explicitly changes it. |

Proposed soft objectives include shorter student gaps, fewer unnecessary campus days, balanced teaching loads, reasonable daily spans, adequate exam spacing beyond mandatory minima, suitable room usage, fewer room changes, and less disruption after publication.

Use priority levels rather than one unexamined weighted sum. A suggested order is: achieve complete hard-feasible coverage; protect published commitments during repair; then improve student/staff preferences and resource efficiency. The exact priority between disruption and other preferences is an explicit faculty decision.

Student groups need particular care. If a course offers four alternative lab sections, a student attends one appropriate alternative, not all four. A cohort-only model can overconstrain electives and miss irregular registrations. Use actual assignments/enrolments where available; label an early cohort-only prototype's guarantees accordingly.

Multi-room exams must allocate candidates without exceeding each room's approved exam capacity. Splitting one exam simultaneously across rooms differs from offering different candidates the same paper at different times. The latter requires an explicit academic/security policy. Do not enable it merely because the solver finds it convenient.

## 9. What could distinguish the Tanta implementation

The following are proposed contributions to validate, not claims that commercial systems lack them.

1. **A documented Tanta constraint catalogue.** Represent programmes, regulation versions, irregular registrations, term calendars, and actual room aliases in one maintained model.
2. **Different capacity measures for different activities.** A tutorial may need seats; a practical exam may need one usable computer per candidate, specific software, and staff. Track operational availability separately from inventory counts.
3. **All-term, dated scheduling.** Resolve conflicts across odd/even teaching patterns, summer offerings, midterms during classes, and practical/oral exam batches through shared calendars.
4. **Explanations that identify the relevant facts.** For example, explain which students, room requirement, and instructor commitment block an activity, then show permitted changes with their effects.
5. **Repair with limited disruption.** After a lab closure, preserve fixed events and search for a valid revision that moves as few published assignments and participants as possible.
6. **Transparent scenario comparison.** Compare options such as another lab sitting, a changed permitted time window, or a newly available hall. Show changes in gaps, exam spacing, resource use, and affected people.
7. **Operational fit.** Arabic/English interfaces, familiar Excel import/export, readable printed schedules, and an installation model that the faculty can maintain.

The strongest coherent package is a Tanta rule model plus explainable schedule repair, evaluated on all three terms. A map, chatbot, or attendance QR feature would not substitute for that contribution.

## 10. Recommended technical approach

**Default recommendation:** a custom application using **Python and OR-Tools CP-SAT**, PostgreSQL, and a web interface. Keep optimization in a background worker so a long solve does not block normal requests. A Java-focused team could reasonably use Timefold instead. Choose based on team capability and a small representative feasibility experiment, not marketing claims.

Use an existing solver as the computational engine. Your contribution is the model, data preparation, constraint implementation, administrative workflow, explanations, repairs, and evidence of usefulness. There is no requirement for a large language model or a learned scheduling model.

| Implementation route | When it makes sense | Graduation-project implication |
|---|---|---|
| Adapt UniTime | Its model already fits most confirmed faculty requirements and deployment is a priority. | Define and evaluate a substantial extension, such as local data adapters, additional policies, or a repair/explanation workflow. |
| Build a custom application on a solver | The project needs a focused faculty workflow and a clearly owned model. | Recommended provisional route; more application work, with the contribution easy to identify and evaluate. |
| Procure a commercial suite | The faculty prioritizes supported institutional operation and can fund procurement/integration. | Useful build-versus-buy comparison; procurement alone does not supply the proposed implementation contribution. |

Before committing to custom development, map the confirmed faculty rules against UniTime and a representative solver prototype. This can reveal whether adaptation is sufficient and prevent inventing requirements to justify new software.

Suggested flow:

```text
Validated faculty data + calendar + policy profile + current bookings
                  |
          immutable input snapshot
                  |
      optimizer: generate or repair assignments
                  |
      independent coverage and conflict validator
                  |
    draft timetable + explanations + quality metrics
                  |
       staff review -> approval -> publication
```

This is a proposed architecture, not implemented software. Teaching and examination models should share identities, bookings, validation, and versioning, while retaining different decision variables and rules. One universal undifferentiated solver model is unnecessary. Conversely, separate solvers must account for one another's committed reservations; independently “valid” schedules can still conflict when combined.

Represent time in integers and validate overlapping date intervals, not just equal slot labels. Filter impossible room/time choices before solving. Expand or reason over recurring dates so holidays, alternating weeks, and special sessions affect availability correctly. Use programme decomposition only when shared resources and student links remain coordinated.

For a first implementation, use fixed section memberships imported from faculty data, with validation for every required assignment. Automatic section balancing can follow within the same design if staff need it; it should not be assumed necessary for every timetable.

## 11. Explainability and solver limits

An invalid manual edit is relatively easy to explain: identify overlapping reservations, insufficient capacity, or a forbidden time. Explaining why an entire scheduling problem has no solution requires additional modelling and diagnostic work.

CP-SAT supports assumptions that can help identify a sufficient set of contradictory constraints. That set is not guaranteed to be the smallest possible explanation. Implement diagnostic models for supported rule types, keep rule identifiers and input provenance, and translate findings into understandable messages. [OR-Tools infeasibility documentation](https://github.com/google/or-tools/blob/stable/ortools/sat/docs/troubleshooting.md).

Treat solver statuses correctly: a feasible result is usable after validation but may not be optimal; an infeasible result means impossibility has been established for the encoded input; an unknown result can mean the search ran out of time without a conclusion. Neither a timeout nor an unscheduled activity alone proves impossibility. [CP-SAT statuses](https://developers.google.com/optimization/cp/cp_solver).

Never silently relax a hard student, staff, or capacity constraint. Offer an explicitly labelled scenario with changed assumptions for staff to consider. A partial result must list every unallocated event and candidate and must not be published as a complete timetable.

## 12. Import, editing, and publication workflow

Start with controlled Excel/CSV templates for rooms, staff, offerings, components, groups/enrolments, exams, and calendars. Check identifiers, durations, duplicate records, unknown aliases, missing participants, and incompatible capacities before launching the solver. Show row-level errors to the administrator.

Import published PDF schedules as a reference or a draft when practical, but require human review of extracted cells. Arabic text, merged cells, visual grouping, and scanned tables can lose essential structure. Prefer a structured export from the faculty's source spreadsheet or registration system. Public student-number ranges in a practical timetable must not be assumed to be a complete enrolment list.

Provide views by programme/group, individual student, instructor, room, date, and exam. Allow staff to drag an event, see immediate conflict information, request alternatives, and pin approved assignments. Keep draft and published versions distinct and record a readable change list.

The faculty website links course registration services, but this review did not establish an authorized integration API. Plan a documented file-import boundary first, with a future connector if faculty IT supplies one. Do not make project completion depend on access that has not been agreed.

## 13. How to demonstrate and evaluate the project

Use a common input snapshot and an independent validator to evaluate every method. Compare a manually produced faculty schedule where usable, a simple greedy baseline, and your optimizer. Add UniTime or FET on a compatible subset where the comparison is fair. Different hard/soft rules must be recorded rather than hidden in a single headline score.

| Metric | Definition or measurement |
|---|---|
| Coverage | Assigned required event occurrences / all required event occurrences; account for every candidate requiring a sitting. |
| Hard violations | Separate room overlaps, staff overlaps, student overlaps, capacity violations, and other mandatory policy failures. |
| Student clashes | Report both conflicting student-event pairs and distinct affected students to avoid ambiguous counts. |
| Teaching quality | Student gap hours, daily spans, campus days, and delivered contact hours. |
| Exam quality | Mandatory/desired spacing, back-to-back exams, overload days, correct practical batch allocation. |
| Resource use | Room-time utilization and seat/workstation occupancy as separate measures, using actual available windows. |
| Repair stability | Changed published occurrences, moved candidate appointments, affected students/staff, and locked assignments preserved. |
| Solve performance | Time to first valid solution, total runtime, hardware, solver version, limits, seed/settings, objective and bound where available. |
| Staff effort | Measured preparation/revision time and manual edits under a defined task. |

Acceptance should require **zero hard violations and complete coverage for agreed feasible cases**, plus correct reporting of infeasible, invalid, or unresolved cases. Do not promise a fixed percentage improvement before measuring a baseline. If both manual and generated schedules are conflict-free, gap reduction, preparation time, and repair stability can demonstrate value.

Use public benchmarks for additional algorithm checks. UniTime publishes Purdue examination datasets; ITC 2019 provides a richer course-timetabling format with rooms, courses, student requests, and distribution constraints. Map their rules faithfully and do not present a simplified subset as directly comparable to published competition scores. [Exam datasets](https://www.unitime.org/exam_datasets.php), [ITC 2019 format](https://www.itc2019.org/format).

Use multiple runs when randomness or parallel search affects results, with the same time budget and machine. Check whether improvements survive different instance sizes and deliberate disruptions.

## 14. A graduation demonstration that exercises the full scope

1. Load an anonymized faculty dataset with programmes, shared spaces, staff, registrations, and all three term profiles.
2. Generate a main-term timetable containing lectures, sections, labs, and alternating-week/online activities.
3. Schedule midterms into that same calendar; validate collisions with teaching.
4. Add final written, practical, and oral exams, including a cross-level candidate and an authorized multi-room or batch case.
5. Select the second main term and summer term; demonstrate their different offerings, dates, and contact-hour plans using the same system.
6. Make a lab unavailable or remove an examiner. Request a repair while preserving locked assignments; show what changed and who is affected.
7. Introduce a deliberately impossible capacity or availability combination. Explain the obstruction, or accurately report that the solve is unresolved; never manufacture a valid-looking result.
8. Review the metrics, approve a schedule, and export the faculty's required views.

This demonstrates automatic resolution and operational handling, not only conflict highlighting.

## 15. Delivery stages that retain the full requirement

| Stage | Concrete deliverable |
|---|---|
| 1. Requirements and faculty data | Reviewed rule catalogue, resource aliases, three-term calendar model, exam taxonomy, anonymized data plan. |
| 2. Shared foundation | Imports, data validation, enrolments, resource reservations, schedule versions, independent conflict/coverage checker. |
| 3. Teaching generation | Lectures, sections, labs, odd/even patterns, online meetings, and term-specific contact-hour plans. |
| 4. All examination modes | Written exams, midterms during teaching, practical batches, oral appointments, irregular registrations, and required staff roles. |
| 5. Repair and staff workflow | Pins, alternatives, minimum-disruption objective, explanations, draft approval, publication/export. |
| 6. Evaluation | Full first/second/summer-term acceptance cases, baseline comparison, disruption experiments, and staff feedback. |

All activity types and all three term types belong in the final delivery. A representative department or synthetic instance can be used for early development, while the final evaluation expands to the agreed faculty inventory. Team size, remaining months, available data, and supervisor expectations are needed before making a credible delivery estimate.

Features to consider after the scheduling acceptance criteria are met include detailed visual seat maps, automated section reassignment, predictive enrolment, native mobile applications, actual attendance capture, and live student-information-system synchronization.

## 16. Information to obtain from the faculty

| Required information | Why it matters |
|---|---|
| Current timetable source spreadsheets for the three terms | Establish real input/output formats and the existing baseline. |
| Current room and equipment inventory | Establish ownership, approved capacity, usable computers, accessibility, shared halls, and unavailable periods. |
| Staff availability and scheduling roles | Differentiate lecturers, assistants, examiners, and invigilators. |
| Course offerings and component requirements | Establish contact hours, recurrence, duration, delivery mode, and section relationships. |
| Pseudonymized student registrations and section allocations | Establish actual clashes, electives, retakes, and cross-level students. |
| Academic calendars and current exam policies | Establish term dates, teaching/exam windows, rest rules, holidays, batching, and common papers. |
| Old/new regulation mapping and special-programme rules | Prevent accidental merging of different offerings or requirements. |
| Resource commitments outside the faculty | Prevent otherwise hidden room and staff conflicts. |
| Scheduling/approval authority and existing tools | Ensure the application supports the actual workflow and a useful comparison. |
| Historical changes and staff effort | Evaluate repair behaviour and whether the system reduces real work. |

For development, pseudonymous student keys and enrolment relationships are normally sufficient; names and national identity numbers are not needed to solve conflicts. Public schedules alone cannot certify a complete student-level conflict-free timetable.

## 17. Recommended decision

Proceed with the idea as a **faculty-wide academic and examination scheduling system**. Preserve all three terms and all required activity/exam types in the agreed scope. Use UniTime as the principal functional reference, FET as an additional teaching baseline, and an established optimizer for the custom implementation.

The central project question should be: **Can a model of Tanta FCI's actual constraints generate complete valid timetables and repair disruptions with less administrative effort and less disturbance to students?** Answer that with a working system and measured results. That is a stronger, supportable contribution than claiming to have invented university timetabling.
