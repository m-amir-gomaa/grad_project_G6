"""Run a clearly synthetic scheduling and lab-closure repair example."""
from __future__ import annotations
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import ortools

from .records import memberships, read_csv
from .solver import Event, Problem, SpaceVersion, Window, conflict_graph, solve, validate

ROOT = Path(__file__).resolve().parents[1]
UNIVERSITY = "synthetic-university"


def minute(iso: str) -> int:
    date = datetime.fromisoformat(iso)
    if date.tzinfo is None:
        raise ValueError("A UTC offset is required")
    return int(date.timestamp() // 60)


def demo_problem() -> Problem:
    first = minute("2027-01-04T07:00:00+00:00")
    second = minute("2027-03-01T07:00:00+00:00")
    summer = minute("2027-07-05T07:00:00+00:00")
    teaching = [
        {"event_id": "lecture", "offering_id": "CS101-first", "component": "lecture", "section_key": "all"},
        {"event_id": "lab-A", "offering_id": "CS101-first", "component": "lab", "section_key": "A"},
        {"event_id": "lab-B", "offering_id": "CS101-first", "component": "lab", "section_key": "B"},
        {"event_id": "repeat-course", "offering_id": "MATH-repeat", "component": "lecture", "section_key": "all"},
        {"event_id": "second-term-lecture", "offering_id": "CS102-second", "component": "lecture", "section_key": "all"},
        {"event_id": "summer-lecture", "offering_id": "CS103-summer", "component": "lecture", "section_key": "all"},
    ]
    assessments = [{"assessment_id": key, "offering_id": "CS101-first"}
                   for key in ("midterm", "written", "practical", "oral")]
    sittings = [{"event_id": key + "-sitting", "assessment_id": key}
                for key in ("midterm", "written", "oral")]
    sittings += [{"event_id": "practical-" + group, "assessment_id": "practical"} for group in ("A", "B")]
    folder = ROOT / "examples/synthetic"
    attendance = memberships(UNIVERSITY, {
        "CS101-first": {"lecture", "lab"}, "MATH-repeat": {"lecture"},
        "CS102-second": {"lecture"}, "CS103-summer": {"lecture"}}, teaching, assessments, sittings,
        read_csv(folder / "enrolments.csv", {"university_id", "student_key", "offering_id"}),
        read_csv(folder / "component_assignments.csv", {"university_id", "student_key", "offering_id", "component", "section_key"}),
        read_csv(folder / "assessment_candidates.csv", {"university_id", "student_key", "assessment_id", "event_id"}))
    starts = tuple(first + value for value in (0, 75, 150, 225))
    span = Window(first - 10, summer + 600)
    openings = (Window(first - 10, first + 600), Window(first + 1440, first + 2040),
                Window(first + 2880, first + 3480), Window(second, second + 600),
                Window(summer, summer + 600))
    rooms = tuple(SpaceVersion(UNIVERSITY, key, key + "-v1", kind, span, seats, exam, pcs,
                               openings, reviewed=True, features=frozenset({"python"}) if pcs else frozenset())
                  for key, kind, seats, exam, pcs in [
                      ("hall", "lecture_hall", 20, 10, 0),
                      ("lab-1", "laboratory", 2, 2, 2),
                      ("lab-2", "laboratory", 2, 2, 2)])
    events = []
    for row in teaching:
        is_lab = row["component"] == "lab"
        term = "first" if row["event_id"] not in {"second-term-lecture", "summer-lecture"} else (
            "second" if row["event_id"] == "second-term-lecture" else "summer")
        allowed = starts if term == "first" else (second,) if term == "second" else (summer,)
        events.append(Event(UNIVERSITY, row["event_id"], term, "lab" if is_lab else "lecture",
                            attendance[row["event_id"]], frozenset({"assistant" if is_lab else "lecturer"}),
                            allowed, 60, room_kinds=frozenset({"laboratory" if is_lab else "lecture_hall"}),
                            capacity_type="workstations" if is_lab else "seats",
                            preferred_spaces=frozenset({"lab-1"}) if is_lab else frozenset()))
    for row in sittings:
        practical = row["assessment_id"] == "practical"
        start = first + (300 if row["assessment_id"] == "midterm" else 1440)
        events.append(Event(UNIVERSITY, row["event_id"], "first", row["assessment_id"] + "_exam",
                            attendance[row["event_id"]], frozenset({"examiner"}),
                            tuple(start + x for x in (0, 75, 150, 225)), 30 if row["assessment_id"] == "oral" else 60,
                            room_kinds=frozenset({"laboratory" if practical else "lecture_hall"}),
                            capacity_type="workstations" if practical else "exam", is_exam=True,
                            preferred_spaces=frozenset({"lab-1"}) if practical else frozenset()))
    graph = {"hall": [("lab-1", 5), ("lab-2", 10)],
             "lab-1": [("hall", 5), ("lab-2", 5)], "lab-2": [("hall", 10), ("lab-1", 5)]}
    return Problem(UNIVERSITY, tuple(events), rooms,
                   {staff: openings for staff in ("assistant", "lecturer", "examiner")},
                   {"standard": graph}, minimum_exam_gap=10)


def main():
    problem = demo_problem()
    snapshot = json.dumps(asdict(problem), default=lambda value: sorted(value), sort_keys=True, indent=2)
    (ROOT / "data/public/synthetic_solver_input.json").write_text(snapshot + "\n")
    baseline = solve(problem)
    if baseline["status"] not in {"FEASIBLE", "OPTIMAL"}:
        raise RuntimeError("The synthetic baseline was not solved")
    if validate(problem, baseline["assignments"]):
        raise RuntimeError("The synthetic baseline failed validation")
    previous = {key: p.identity for key, p in baseline["assignments"].items()}
    closure = next(room for room in problem.spaces if room.space_id == "lab-1")
    first = min(e.permitted_starts[0] for e in problem.events)
    revised = [room for room in problem.spaces if room.space_id != "lab-1"]
    revised += [replace(closure, valid=Window(closure.valid.start, first)),
                replace(closure, version_id="lab-1-v2-closed", valid=Window(first, closure.valid.end), state="closed")]
    repair_problem = replace(problem, spaces=tuple(revised), previous=previous)
    repaired = solve(repair_problem)
    errors = validate(repair_problem, repaired["assignments"]) if repaired["assignments"] else ["No solution"]
    result = {"data_kind": "synthetic; no real Tanta registrations or floor plan used",
              "baseline_input_sha256": hashlib.sha256((snapshot + "\n").encode()).hexdigest(),
              "solver_version": ortools.__version__, "random_seed": 0, "search_workers": 1,
              "activity_count": len(problem.events), "term_types": sorted({e.term_id for e in problem.events}),
              "student_conflict_edges": len(conflict_graph(problem.events)),
              "baseline": {**baseline, "assignments": {k: asdict(v) for k, v in baseline["assignments"].items()}},
              "after_lab_closure": {**repaired, "assignments": {k: asdict(v) for k, v in repaired["assignments"].items()}},
              "validation_errors": errors}
    out = ROOT / "data/public/synthetic_solver_result.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"baseline": baseline["status"], "repair": repaired["status"],
                      "events": len(problem.events), "changed_events": repaired.get("changed_events", []),
                      "validation_errors": errors, "result_file": str(out.relative_to(ROOT))}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
