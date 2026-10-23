# Sources and evidence notes

Checked **22 October 2026**. This is a focused review of relevant implementations and primary documentation, not an exhaustive global product inventory.

## Faculty evidence

| Source | Evidence used | Inspection |
|---|---|---|
| [Official teaching timetable page](https://ci.tanta.edu.eg/stu_study_tables.aspx) | Programme/level schedules; links to main and summer teaching PDFs. | Web and HTML link inspection. |
| [Official examination page](https://ci.tanta.edu.eg/stu-exam-tables.aspx) | Midterm/final/practical/oral schedules and regulation/graduation categories. | Web and HTML link inspection. The filename uses hyphens, not underscores. |
| [Student guide linked by faculty](https://ci.tanta.edu.eg/files/%D8%AF%D9%84%D9%8A%D9%84%20%D8%A7%D9%84%D8%B7%D8%A7%D9%84%D8%A8%2026.pdf) | Calendar and inventory observations described in the report. | Downloaded; text extracted; inventory pages rendered and visually inspected. |
| [Level-three CS, first term 2026/2027](https://ci.tanta.edu.eg/files/2026-2027/stu_tables/1st-term/%D8%A7%D9%84%D9%85%D8%B3%D8%AA%D9%88%D9%89%20%D8%A7%D9%84%D8%AB%D8%A7%D9%84%D8%AB%20CS.pdf) | Odd/even weeks, online teaching, room and group identifiers. | Downloaded; both pages rendered and visually inspected after web-tool retrieval failed. |
| [General summer timetable, 2025/2026](https://ci.tanta.edu.eg/files/2025-2026/stu_tables/summer/%D8%A7%D9%84%D8%AC%D8%AF%D9%88%D9%84%20%D8%A7%D9%84%D8%B9%D8%A7%D9%85.pdf) | Confirms a separate published summer teaching schedule. | Downloaded; heading checked in text extraction. |
| [Practical/oral exam timetable](https://ci.tanta.edu.eg/files/exam-table-practical2026.pdf) | Laboratory sittings, candidate batches, and cross-level registrations. | Web-extracted PDF text. Individual student numbers are not reproduced in the report or archived as a dataset. |

The archived PDFs are public reference documents, not live faculty data. Their original URLs, retrieval date, size, and SHA-256 checksums are in [manifest.json](sources/manifest.json). Rendered PNGs and text extractions are inspection aids. Room inventory and calendars require current faculty confirmation before operational use.

## Open-source software and technical references

- [UniTime application](https://github.com/UniTime/unitime) — full application scope and current repository licence.
- [UniTime CPSolver](https://github.com/UniTime/cpsolver) and [licence](https://raw.githubusercontent.com/UniTime/cpsolver/master/LICENSE) — separate solver component and licence.
- [UniTime system highlights](https://help-unitime.unitime.org/unitime_intro.php) — course/exam/sectioning/event coverage.
- [FET official site](https://lalescu.ro/liviu/fet/) and [features](https://lalescu.ro/liviu/fet/features.html) — scheduling, Arabic localization, constraints, data formats, licence.
- [Older FET GitHub mirror](https://github.com/fet-project/fet) — shows why a search result may not represent the current release.
- [Timefold Solver](https://timefold.ai/solver) — Java/Kotlin Community Edition and licence.
- [Timefold teaching quickstart](https://github.com/TimefoldAI/timefold-quickstarts/tree/stable/use-cases/school-timetabling) and [README](https://raw.githubusercontent.com/TimefoldAI/timefold-quickstarts/stable/use-cases/school-timetabling/README.md) — actual example scope and optional licensed editions.
- [OR-Tools repository](https://github.com/google/or-tools) — library and licence.
- [Contributed school-scheduling example](https://github.com/google/or-tools/blob/stable/examples/contrib/school_scheduling_sat.py) — illustrative implementation, not a complete university product.
- [CP-SAT documentation](https://developers.google.com/optimization/cp/cp_solver) — integer modelling and solver result statuses.
- [Infeasibility troubleshooting](https://github.com/google/or-tools/blob/stable/ortools/sat/docs/troubleshooting.md) — assumptions and explanation limitations.
- [UniTime examination benchmarks](https://www.unitime.org/exam_datasets.php) — public examination datasets and model details.
- [ITC 2019 problem format](https://www.itc2019.org/format) — course/student/resource/distribution model. Search indexing exposed the format; direct page parsing returned no readable body. Confirm current download access when preparing experiments.

GitHub API metadata was read for the main repositories. The UniTime application, CPSolver, OR-Tools, Timefold Solver, and Timefold quickstarts were not marked archived and had recent pushes at inspection. Recent pushes are evidence of repository activity, not a quality guarantee. No software was installed or performance-tested.

## Commercial primary sources

- TimeEdit: [product catalogue](https://www.academy.timeedit.com/products), [AutoPilot](https://www.academy.timeedit.com/products/autopilot), [exam product](https://www.academy.timeedit.com/products/exam), [developer hub](https://developer.timeedit.com/reference/introduction).
- TimeEdit: [2024 UK procurement pricing document](https://assets.applytosupply.digitalmarketplace.service.gov.uk/g-cloud-14/documents/719636/871656448042845-pricing-document-2024-05-07-1055.pdf). Historical procurement evidence only.
- CELCAT: [official website](https://celcat.com/), [exam scheduling](https://celcat.com/timetabler/extensions/exam-scheduling/), [automated scheduling](https://celcat.com/timetabler/extensions/automated-premium/).
- TechnologyOne: [product](https://www.technology1.com/products/timetabling-and-scheduling), [UK brochure](https://www.technology1.co.uk/__data/assets/pdf_file/0006/263670/TNS-Timetabling-and-Scheduling-brochure-UK.pdf), [2022 annual report recording Scientia rebranding](https://technologyonecorp.com/__data/assets/pdf_file/0003/215454/2022-Annual-Report-TechnologyOne.pdf).
- Infosilem: [current products](https://infosilem.com/en), [functional FAQ](https://infosilem.com/en/faq).
- EventMAP: [product suite](https://www.eventmapsolutions.com/), [Optime Exam](https://www.eventmapsolutions.com/products/exam).
- Coursedog: [official product documentation](https://coursedog.my.site.com/support/articles/Knowledge/CoursedogProductsExplained67fd7ad6a397b). This is the vendor's support site.
- Ad Astra: [official website](https://www.aais.com/).
- aSc: [official trial/pricing page](https://asctt.edupage.org/a/ceny). No current Egyptian institutional price established.

Vendor features were documented, not independently verified. No vendor was contacted, no quotation was requested, and no product purchase or trial account was created. The report does not adopt vendor performance, fairness, “AI,” or optimality claims as measured facts.

## Egyptian precedents

- [Solving the Course-timetabling Problem of Cairo University Using Max-SAT](https://arxiv.org/abs/1803.05027), Mohamed El Halaby, submitted 2018 — read primary abstract and submission record.
- [Constraint-Based University Timetabling for the German University in Cairo](https://met.guc.edu.eg/Repository/Faculty/Publications/67/Paper.pdf), Slim Abdennadher and Mohamed Aly — primary university-hosted paper indexed by search; direct web retrieval timed out and terminal retrieval failed certificate validation. Indexed abstract used; full paper not archived.
- [EJUST-inspired CSP/greedy prototype](https://github.com/OmarElHawy/Automated-Timetable-Generation-as-a-Constraint-Satisfaction-Problem-CSP-) — read repository README and visible file list; deployment claims not inferred.
- [Lumen](https://github.com/UniLumen/Lumen) — read indexed project README and repository metadata; student-side optimization of existing options.

Neither small public repository had a GitHub-detected licence at inspection. Source visibility is distinguished from verified open-source licensing.

## Remaining evidence gaps

The review did not establish the faculty's current internal scheduling software, full room inventory, operational computer counts, exact scheduling rules, complete student registrations, current commercial quotations, or availability of an authorized registration-system API. These are faculty-discovery tasks. No source establishes that the proposed system would be the first of its kind at Tanta.
