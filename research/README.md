# Research and historical pilots

The current product specification is in [confirmed scope](../docs/SCOPE-REVISION.md), [features](../docs/FEATURES.md), [UI](../docs/UI.md), [algorithms](../docs/SPECIFICATION.md), and [editing rules](../docs/EDITING.md). Those documents take precedence over earlier research recommendations.

The research below records the project's development and supporting evidence:

- [Existing-software and Tanta research](TANTA-TIMETABLING-RESEARCH.md), [initial brief](PROJECT-BRIEF.md), and [earlier architecture/model](ARCHITECTURE-AND-ALGORITHMS.md) predate the simplified standalone scope. Their university accounts, approval/publication, architectural geometry, extra student fields and optional policies are not current requirements.
- [PDF space-registry evidence](PDF-SPACE-REGISTRY.md), `sources/`, and `data/public/` preserve public-source observations and explicitly synthetic pilot results. These observations do not supply operational capacities, availability or student registrations.
- [Foundation verification](VERIFICATION.md) records the earlier pilot's 24-test check. Current editing evidence is described in the [editing contract](../docs/EDITING.md), [browser demo](../examples/editing-demo/README.md), and [FigCraft design](../design/README.md).

The older registry, records and solver modules, `scripts/`, `data/templates/`, and `examples/synthetic/` remain reproducible research references. Their CSV schemas are not the current application's student input. Use the [course-only student CSV specification](../docs/STUDENT-CSV.md) and `examples/simple-ui/` for that interface.

The current dated/weekly editing engine is in `timetabling/editing.py` and `timetabling/patterns.py`, with its browser adapter in `timetabling/editing_demo.py`. The full generator/group-allocation adapter, durable application storage, and production timetable exports remain implementation work.
