from dataclasses import replace
import importlib.util
import sqlite3
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile

from timetabling.demo import demo_problem
from timetabling.availability import available_starts
from timetabling.records import memberships
from timetabling.registry import connect, import_candidates, spaces_at
from timetabling.solver import Event, Placement, Problem, SpaceVersion, Window, solve, validate, conflict_graph


def room(key="r1", **changes):
    return replace(SpaceVersion("u1", key, key + "-v1", "laboratory", Window(0, 1000),
                                50, 20, 10, (Window(0, 1000),), reviewed=True), **changes)


def event(key="e1", **changes):
    return replace(Event("u1", key, "summer", "practical_exam", frozenset({"s1"}),
                         frozenset(), (0, 60, 120), 60, room_kinds=frozenset({"laboratory"}),
                         capacity_type="workstations", is_exam=True), **changes)


def problem(events=None, spaces=None, **changes):
    return replace(Problem("u1", tuple(events or [event()]), tuple(spaces or [room()]), {},
                           {"standard": {"r1": [("r2", 5)], "r2": [("r1", 5)]}}), **changes)


class SolverTests(unittest.TestCase):
    def test_location_slots_merge_openings_subtract_closures_and_include_buffers(self):
        space = room(openings=(Window(0, 60), Window(60, 180)), blocked=(Window(60, 90),))
        self.assertEqual(available_starts(space, Window(0, 180), 30, step=15, preparation=15, cleanup=15),
                         (15, 105, 120, 135))
        self.assertEqual(available_starts(replace(space, openings=()), Window(0, 180), 30), ())
        self.assertEqual(available_starts(replace(space, reviewed=False), Window(0, 180), 30), ())

    def test_all_three_terms_and_lab_closure(self):
        data = demo_problem()
        result = solve(data)
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual({e.term_id for e in data.events}, {"first", "second", "summer"})
        self.assertEqual(validate(data, result["assignments"]), [])
        self.assertTrue(any("lab-1" in p.spaces for p in result["assignments"].values()))
        revised = replace(data, spaces=tuple(replace(r, state="closed") if r.space_id == "lab-1" else r for r in data.spaces),
                          previous={key: p.identity for key, p in result["assignments"].items()})
        repaired = solve(revised)
        self.assertEqual(repaired["status"], "OPTIMAL")
        self.assertTrue(repaired["changed_events"])
        self.assertEqual(validate(revised, repaired["assignments"]), [])
        self.assertTrue(all("lab-1" not in p.spaces for p in repaired["assignments"].values()))

    def test_usable_machines_constrain_large_seated_room(self):
        data = problem([event(students=frozenset({"s1", "s2", "s3"}))], [room(workstations=2)])
        self.assertEqual(solve(data)["status"], "INFEASIBLE")

    def test_unknown_capacity_and_unreviewed_room_are_excluded(self):
        self.assertEqual(solve(problem(spaces=[room(workstations=None)]))["status"], "INFEASIBLE")
        self.assertEqual(solve(problem(spaces=[room(reviewed=False)]))["status"], "INFEASIBLE")

    def test_multi_room_capacity_and_exact_candidate_coverage(self):
        data = problem([event(capacity_type="exam", max_rooms=2, students=frozenset({"s1", "s2", "s3"}))],
                       [room(exam_places=2), room("r2", exam_places=2)])
        result = solve(data)
        assignment = result["assignments"]["e1"]
        self.assertEqual(len(assignment.spaces), 2)
        self.assertEqual({s for s, _ in assignment.student_spaces}, {"s1", "s2", "s3"})
        self.assertEqual(validate(data, result["assignments"]), [])

    def test_partition_and_combined_hall_cannot_be_double_booked(self):
        a = room(features=frozenset({"a"}), occupancy_atoms=frozenset({"shared-half"}))
        b = room("r2", features=frozenset({"b"}), occupancy_atoms=frozenset({"shared-half", "other-half"}))
        events = [event(features=frozenset({"a"}), permitted_starts=(0,)),
                  event("e2", features=frozenset({"b"}), students=frozenset({"s2"}), permitted_starts=(0,))]
        self.assertEqual(solve(problem(events, [a, b]))["status"], "INFEASIBLE")
        single = event(max_rooms=2, capacity_type="exam", students=frozenset({"s1", "s2", "s3"}))
        self.assertEqual(solve(problem([single], [replace(a,exam_places=2),replace(b,exam_places=2)]))["status"], "INFEASIBLE")

    def test_actual_shared_student_and_walking_time(self):
        a, b = room(features=frozenset({"a"})), room("r2", features=frozenset({"b"}))
        first = event(features=frozenset({"a"}), permitted_starts=(0,))
        later = event("e2", features=frozenset({"b"}), permitted_starts=(60,))
        self.assertEqual(solve(problem([first, later], [a, b]))["status"], "INFEASIBLE")
        result = solve(problem([first, replace(later, permitted_starts=(65,))], [a, b]))
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(conflict_graph((first, later)), {("e1", "e2"): 1})

    def test_missing_route_is_never_assumed_zero(self):
        a, b = room(features=frozenset({"a"})), room("r2", features=frozenset({"b"}))
        events = [event(features=frozenset({"a"}), permitted_starts=(0,)),
                  event("e2", features=frozenset({"b"}), permitted_starts=(120,))]
        result = solve(problem(events, [a, b], navigation={}))
        self.assertEqual(result["status"], "INFEASIBLE")
        self.assertTrue(result["diagnostics"]["unreachable_or_unconfirmed_routes"])

    def test_locked_assignment_cannot_silently_move(self):
        data = problem([event(locked=True)], [room(state="closed"), room("r2")],
                       previous={"e1": (0, ("r1",))})
        self.assertEqual(solve(data)["status"], "INFEASIBLE")

    def test_repair_priority_preserves_assignment_over_preference(self):
        data = problem([event(preferred_starts=frozenset({60}))], previous={"e1": (0, ("r1",))})
        result = solve(data)
        self.assertEqual(result["assignments"]["e1"].start, 0)
        self.assertEqual(result["changed_events"], [])

    def test_architecture_versions_apply_at_event_date(self):
        old = room(valid=Window(0, 60))
        closed = room(version_id="r1-v2", valid=Window(60, 1000), state="closed")
        self.assertEqual(solve(problem([event(permitted_starts=(60,))], [old, closed]))["status"], "INFEASIBLE")
        result = solve(problem([event(permitted_starts=(0,))], [old, closed]))
        self.assertEqual(result["assignments"]["e1"].space_versions, ("r1-v1",))

    def test_tenant_mismatch_and_overlapping_versions_rejected(self):
        with self.assertRaisesRegex(ValueError, "university"):
            solve(problem(spaces=[room(university_id="u2")]))
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            solve(problem(spaces=[room(), room(version_id="r1-v2")]))

    def test_staff_availability_and_room_reset_time(self):
        staffed = event(staff=frozenset({"teacher"}), permitted_starts=(0,))
        self.assertEqual(solve(problem([staffed], staff_openings={"teacher": (Window(60, 180),)}))["status"], "INFEASIBLE")
        events = [event(permitted_starts=(0,), cleanup=15),
                  event("e2", students=frozenset({"s2"}), permitted_starts=(60,))]
        self.assertEqual(solve(problem(events))["status"], "INFEASIBLE")

    def test_auditor_rejects_forged_or_missing_assignment(self):
        data = problem()
        result = solve(data)
        forged = replace(result["assignments"]["e1"], space_versions=("invented",))
        self.assertTrue(validate(data, {"e1": forged}))
        self.assertTrue(validate(data, {}))


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        self.db.executemany("INSERT INTO universities VALUES (?,?,?,?)", [
            ("u1", "One", "Africa/Cairo", "draft"), ("u2", "Two", "Africa/Cairo", "draft")])

    def tearDown(self):
        self.db.close()

    def test_cross_university_foreign_key(self):
        self.db.execute("INSERT INTO campuses VALUES ('u2','campus','Campus')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO buildings VALUES ('u1','building','campus','Building')")

    def test_approved_architecture_and_space_history_are_immutable(self):
        self.db.execute("INSERT INTO architecture_revisions VALUES ('u1','a1','2027-01-01','approved','Original')")
        self.db.execute("INSERT INTO spaces VALUES ('u1','r1','Lab-1')")
        self.db.execute("""INSERT INTO space_versions (university_id,id,space_id,architecture_revision_id,name,kind,state)
                           VALUES ('u1','r1-v1','r1','a1','Lab 1','laboratory','open')""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE space_versions SET name='Renamed' WHERE id='r1-v1'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE architecture_revisions SET effective_from='2026-01-01' WHERE id='a1'")

    def test_date_queries_preserve_the_original_layout(self):
        self.db.execute("INSERT INTO spaces VALUES ('u1','r1','Lab-1')")
        for version, date, state in [('a1','2027-01-01T00:00:00Z','open'),('a2','2027-06-01T00:00:00Z','closed')]:
            self.db.execute("INSERT INTO architecture_revisions VALUES (?,?,?,'approved','change')", ('u1',version,date))
            self.db.execute("""INSERT INTO space_versions (university_id,id,space_id,architecture_revision_id,name,kind,state)
                               VALUES (?,?,?,?,?,'laboratory',?)""", ('u1','r1-'+version,'r1',version,'Lab',state))
        self.assertEqual(spaces_at(self.db,'u1','2027-02-01T00:00:00Z')[0][3], 'open')
        self.assertEqual(spaces_at(self.db,'u1','2027-07-01T00:00:00Z')[0][3], 'closed')
        self.assertEqual(spaces_at(self.db,'u2','2027-07-01T00:00:00Z'), [])

    def test_pdf_import_is_idempotent_and_preserves_old_document_versions(self):
        docs = [{"source_id": "d1", "url": "https://example.test/t.pdf", "sha256": "hash-a"}]
        rows = [{"candidate_key": "lab-1", "display_label": "Lab 1", "proposed_kind": "laboratory",
                 "evidence": [{"source_id": "d1", "page": 1, "method": "embedded_text", "bbox_fraction": [0, 0, .1, .1]}]}]
        self.db.commit()
        import_candidates(self.db, "u1", docs, rows)
        import_candidates(self.db, "u1", docs, rows)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM import_observations").fetchone()[0], 1)
        docs[0]["sha256"] = "hash-b"
        import_candidates(self.db, "u1", docs, rows)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM source_documents").fetchone()[0], 2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM import_observations").fetchone()[0], 2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM spaces").fetchone()[0], 0)


class RecordTests(unittest.TestCase):
    def fixture(self):
        return dict(university_id="u1", offerings={"cs": {"lab"}},
                    teaching=[dict(event_id="lab-a", offering_id="cs", component="lab", section_key="A"),
                              dict(event_id="lab-b", offering_id="cs", component="lab", section_key="B")],
                    assessments=[dict(assessment_id="exam", offering_id="cs")],
                    sittings=[dict(event_id="exam-a", assessment_id="exam"), dict(event_id="exam-b", assessment_id="exam")],
                    enrolments=[dict(university_id="u1", student_key="s1", offering_id="cs")],
                    sections=[dict(university_id="u1", student_key="s1", offering_id="cs", component="lab", section_key="A")],
                    candidates=[dict(university_id="u1", student_key="s1", assessment_id="exam", event_id="exam-a")])

    def test_student_attends_one_assigned_section_and_sitting(self):
        data = memberships(**self.fixture())
        self.assertEqual(data["lab-a"], {"s1"})
        self.assertEqual(data["lab-b"], set())
        self.assertEqual(data["exam-b"], set())

    def test_missing_sections_candidates_and_wrong_tenant_rejected(self):
        for field in ("sections", "candidates"):
            data = self.fixture(); data[field] = []
            with self.assertRaises(ValueError): memberships(**data)
        data = self.fixture(); data["enrolments"][0]["university_id"] = "u2"
        with self.assertRaises(ValueError): memberships(**data)

    def test_duplicate_sitting_assignment_rejected(self):
        data = self.fixture()
        data["candidates"].append({**data["candidates"][0], "event_id": "exam-b"})
        with self.assertRaises(ValueError): memberships(**data)


class PdfLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("scanner", "scripts/scan_faculty_pdfs.py")
        cls.scanner = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.scanner)

    def test_visual_arabic_and_numeric_direction(self):
        self.assertEqual(self.scanner.space_label("12 جردم", True)[0], "hall-12")
        self.assertEqual(self.scanner.space_label("نيلانوأ", True)[0], "virtual-online")

    def test_room_types_and_unscoped_letters_are_distinct(self):
        self.assertNotEqual(self.scanner.space_label("مدرج 1", True)[0], self.scanner.space_label("معمل 1", True)[0])
        self.assertIsNone(self.scanner.space_label("C", False))
        self.assertNotEqual(self.scanner.space_label("C", True)[0], self.scanner.space_label("معمل C", True)[0])

    def test_cache_refresh_preserves_changed_pdf_versions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); cache = root / "pdf-cache"; cache.mkdir()
            document = {"source_id": "d1", "url": "https://example.test/schedule.pdf"}
            with patch.object(self.scanner, "ROOT", root), patch.object(self.scanner, "fetch", side_effect=[b"%PDF-1.7\nold",b"%PDF-1.7\nnew"]) as fetch:
                old = self.scanner.download(document, cache)
                new = self.scanner.download(document, cache)
                repeated = self.scanner.download(new, cache, reuse_cache=True)
            self.assertEqual(fetch.call_count, 2)
            self.assertNotEqual(old['sha256'],new['sha256'])
            self.assertEqual(new['sha256'],repeated['sha256'])
            self.assertTrue((root / old['cache_file']).exists())


if __name__ == "__main__":
    unittest.main()
