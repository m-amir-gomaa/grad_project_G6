"""Validate pseudonymous enrolments and derive attendance for explicit sections/sittings."""
from __future__ import annotations
from collections import defaultdict
import csv
from pathlib import Path


def read_csv(path: str | Path, required: set[str]) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or set(reader.fieldnames) != required or len(reader.fieldnames) != len(required):
            raise ValueError("Student CSV header does not match its documented contract")
        rows = []
        for row in reader:
            if None in row or any(value is None or not value.strip() for value in row.values()):
                raise ValueError("Student CSV contains missing or extra fields")
            rows.append({key: value.strip() for key, value in row.items()})
        return rows


def memberships(university_id: str, offerings: dict[str, set[str]], teaching: list[dict],
                assessments: list[dict], sittings: list[dict], enrolments: list[dict],
                sections: list[dict], candidates: list[dict]) -> dict[str, frozenset[str]]:
    """Fail closed on missing choices, orphan rows, duplicate or ineligible exam candidates.

    teaching: event_id, offering_id, component, section_key (one row per dated occurrence)
    assessments: assessment_id, offering_id (distinct ID for each assessed component)
    sittings: event_id, assessment_id (explicit authorized batches or whole-course exams)
    All student rows must contain university_id. No grouping by study year is used.
    """
    for row in (*enrolments, *sections, *candidates):
        if row.get("university_id") != university_id:
            raise ValueError("Student records belong to another university")
    enrolled = set()
    for row in enrolments:
        key = row["student_key"], row["offering_id"]
        if row["offering_id"] not in offerings or key in enrolled:
            raise ValueError("Unknown offering or duplicate enrolment")
        enrolled.add(key)
    teaching_groups = defaultdict(list)
    result = defaultdict(set)
    for row in teaching:
        group = row["offering_id"], row["component"], row["section_key"]
        if row["component"] not in offerings.get(row["offering_id"], set()):
            raise ValueError("Teaching occurrence has an unknown offering/component")
        teaching_groups[group].append(row["event_id"])
        result[row["event_id"]]  # Keep empty events visible to coverage validation.
    choices = {}
    for row in sections:
        student, offering = row["student_key"], row["offering_id"]
        key = student, offering, row["component"]
        group = offering, row["component"], row["section_key"]
        if (student, offering) not in enrolled or key in choices or group not in teaching_groups:
            raise ValueError("Orphan, duplicate or unknown teaching section assignment")
        choices[key] = row["section_key"]
        for event_id in teaching_groups[group]:
            result[event_id].add(student)
    for student, offering in enrolled:
        if any((student, offering, component) not in choices for component in offerings[offering]):
            raise ValueError("Missing required teaching component assignment")
    assessment_map = {}
    for row in assessments:
        if row["assessment_id"] in assessment_map or row["offering_id"] not in offerings:
            raise ValueError("Duplicate assessment or unknown offering")
        assessment_map[row["assessment_id"]] = row["offering_id"]
    sitting_map = {}
    for row in sittings:
        if row["event_id"] in sitting_map or row["event_id"] in result or row["assessment_id"] not in assessment_map:
            raise ValueError("Duplicate sitting/event or unknown assessment")
        sitting_map[row["event_id"]] = row["assessment_id"]
        result[row["event_id"]]
    assigned = set()
    for row in candidates:
        student, assessment = row["student_key"], row["assessment_id"]
        key = student, assessment
        if assessment not in assessment_map or (student, assessment_map[assessment]) not in enrolled:
            raise ValueError("Ineligible assessment candidate")
        if key in assigned or sitting_map.get(row["event_id"]) != assessment:
            raise ValueError("Duplicate candidate or wrong assessment sitting")
        assigned.add(key)
        result[row["event_id"]].add(student)
    required = {(student, assessment) for assessment, offering in assessment_map.items()
                for student, registered in enrolled if registered == offering}
    if assigned != required:
        raise ValueError("Assessment candidate coverage is incomplete")
    return {event: frozenset(students) for event, students in result.items()}
