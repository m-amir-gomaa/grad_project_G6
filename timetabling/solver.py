"""Finite-domain CP-SAT pilot for dated activities with real participant membership.

Inputs must already contain approved room data, permitted starts, and explicit
teaching-section/exam-batch membership. This is not a full faculty scheduler.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
import heapq
from itertools import combinations
import math

from ortools.sat.python import cp_model


@dataclass(frozen=True)
class Window:
    start: int  # Integer UTC minutes from a fixed epoch, not a weekday slot number.
    end: int

    def __post_init__(self):
        if self.end <= self.start:
            raise ValueError("A window must have positive duration")


@dataclass(frozen=True)
class SpaceVersion:
    university_id: str
    space_id: str
    version_id: str
    kind: str
    valid: Window
    seats: int | None
    exam_places: int | None
    workstations: int | None
    openings: tuple[Window, ...]
    blocked: tuple[Window, ...] = ()
    features: frozenset[str] = frozenset()
    reviewed: bool = False
    state: str = "open"
    occupancy_atoms: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Event:
    university_id: str
    event_id: str
    term_id: str
    kind: str
    students: frozenset[str]
    staff: frozenset[str]
    permitted_starts: tuple[int, ...]
    duration: int
    room_kinds: frozenset[str] = frozenset({"lecture_hall"})
    capacity_type: str = "seats"  # seats / exam / workstations
    features: frozenset[str] = frozenset()
    max_rooms: int = 1
    preparation: int = 0
    cleanup: int = 0
    online: bool = False
    is_exam: bool = False
    locked: bool = False
    preferred_starts: frozenset[int] = frozenset()
    preferred_spaces: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Placement:
    event_id: str
    start: int
    end: int
    spaces: tuple[str, ...]
    space_versions: tuple[str, ...]
    student_spaces: tuple[tuple[str, str | None], ...]
    preference_cost: int = 0
    occupancy_atoms: tuple[str, ...] = ()

    @property
    def identity(self):
        return self.start, self.spaces


@dataclass
class Problem:
    university_id: str
    events: tuple[Event, ...]
    spaces: tuple[SpaceVersion, ...]
    staff_openings: dict[str, tuple[Window, ...]]
    # Directed navigation graphs: profile -> node -> [(neighbour, minutes)].
    navigation: dict[str, dict[str, list[tuple[str, int]]]]
    student_profiles: dict[str, str] = field(default_factory=dict)
    student_blackouts: dict[str, tuple[Window, ...]] = field(default_factory=dict)
    previous: dict[str, tuple[int, tuple[str, ...]]] = field(default_factory=dict)
    minimum_exam_gap: int = 0
    online_transition: int = 0


def overlaps(a: Window, b: Window) -> bool:
    return a.start < b.end and b.start < a.end


def fits(window: Window, openings: tuple[Window, ...]) -> bool:
    covered_until = window.start
    for opening in sorted(openings, key=lambda w: w.start):
        if opening.start > covered_until:
            break
        covered_until = max(covered_until, opening.end)
        if covered_until >= window.end:
            return True
    return False


def shortest_paths(graph: dict[str, list[tuple[str, int]]], start: str) -> dict[str, int]:
    """Dijkstra on an approved walking/accessibility graph; no path stays unknown."""
    if any(weight < 0 for edges in graph.values() for _, weight in edges):
        raise ValueError("Travel times cannot be negative")
    distances = {start: 0}
    queue = [(0, start)]
    while queue:
        distance, node = heapq.heappop(queue)
        if distance != distances[node]:
            continue
        for neighbour, weight in graph.get(node, []):
            next_distance = distance + weight
            if next_distance < distances.get(neighbour, math.inf):
                distances[neighbour] = next_distance
                heapq.heappush(queue, (next_distance, neighbour))
    return distances


def conflict_graph(events: tuple[Event, ...]) -> dict[tuple[str, str], int]:
    """Inverted enrolment index: edge weight is shared student count."""
    attendance = defaultdict(set)
    for event in events:
        for student in event.students:
            attendance[student].add(event.event_id)
    edges = defaultdict(int)
    for required_events in attendance.values():
        for pair in combinations(sorted(required_events), 2):
            edges[pair] += 1
    return dict(edges)


def check_input(problem: Problem) -> None:
    if len({e.event_id for e in problem.events}) != len(problem.events):
        raise ValueError("Duplicate event IDs")
    if set(problem.previous) - {e.event_id for e in problem.events}:
        raise ValueError("Previous assignments contain unknown events")
    for item in (*problem.events, *problem.spaces):
        if item.university_id != problem.university_id:
            raise ValueError("Cross-university input is not allowed")
    versions = defaultdict(list)
    for room in problem.spaces:
        if room.state not in {"open", "closed", "retired"}:
            raise ValueError("Unknown space state")
        if any(x is not None and (not isinstance(x, int) or x < 0)
               for x in (room.seats, room.exam_places, room.workstations)):
            raise ValueError("Invalid room capacity")
        versions[room.space_id].append(room)
    if len({r.version_id for r in problem.spaces}) != len(problem.spaces):
        raise ValueError("Duplicate space version IDs")
    for revisions in versions.values():
        for a, b in combinations(revisions, 2):
            if overlaps(a.valid, b.valid):
                raise ValueError("Overlapping effective versions of the same space")
    for event in problem.events:
        if event.duration <= 0 or event.max_rooms < 1 or min(event.preparation, event.cleanup) < 0:
            raise ValueError("Invalid duration, room count or buffer")
        if event.capacity_type not in {"seats", "exam", "workstations"}:
            raise ValueError("Unknown capacity type")
        if not all(isinstance(s, int) for s in event.permitted_starts):
            raise ValueError("Permitted starts must be integer UTC minutes")
        if event.locked and event.event_id not in problem.previous:
            raise ValueError("A locked event needs an existing assignment")
        if any(staff not in problem.staff_openings for staff in event.staff):
            raise ValueError("Missing staff availability")
    if min(problem.minimum_exam_gap, problem.online_transition) < 0:
        raise ValueError("Minimum gaps cannot be negative")
    for graph in problem.navigation.values():
        if any(not isinstance(w, int) or w < 0 for rows in graph.values() for _, w in rows):
            raise ValueError("Travel times must be nonnegative integer minutes")


def effective_capacity(room: SpaceVersion, event: Event) -> int | None:
    if room.seats is None:
        return None
    other = {"seats": room.seats, "exam": room.exam_places,
             "workstations": room.workstations}[event.capacity_type]
    return None if other is None else min(room.seats, other)


def atoms(room: SpaceVersion) -> frozenset[str]:
    return room.occupancy_atoms or frozenset({room.space_id})


def candidates(problem: Problem, event: Event) -> list[Placement]:
    found = []
    for start in sorted(set(event.permitted_starts)):
        meeting = Window(start, start + event.duration)
        booking = Window(start - event.preparation, meeting.end + event.cleanup)
        if any(not fits(meeting, problem.staff_openings[s]) for s in event.staff):
            continue
        if any(overlaps(meeting, blocked) for student in event.students
               for blocked in problem.student_blackouts.get(student, ())):
            continue
        penalty = int(bool(event.preferred_starts) and start not in event.preferred_starts)
        if event.online:
            alternatives = [()]
        else:
            rooms = [r for r in problem.spaces
                     if r.reviewed and r.state == "open" and r.kind in event.room_kinds
                     and r.valid.start <= booking.start and booking.end <= r.valid.end
                     and fits(booking, r.openings) and not any(overlaps(booking, x) for x in r.blocked)
                     and event.features <= r.features and effective_capacity(r, event) is not None]
            alternatives = [group for count in range(1, event.max_rooms + 1)
                            for group in combinations(sorted(rooms, key=lambda r: r.space_id), count)
                            if sum(effective_capacity(r, event) for r in group) >= len(event.students)
                            and not any(atoms(a) & atoms(b) for a, b in combinations(group, 2))]
        for rooms in alternatives:
            allocation = []
            students = sorted(event.students)
            offset = 0
            for room in rooms:
                end = offset + effective_capacity(room, event)
                allocation.extend((s, room.space_id) for s in students[offset:end])
                offset = end
            if event.online:
                allocation = [(s, None) for s in students]
            placement = Placement(event.event_id, start, meeting.end,
                                  tuple(r.space_id for r in rooms), tuple(r.version_id for r in rooms),
                                  tuple(allocation), penalty + int(bool(event.preferred_spaces) and
                                      any(r.space_id not in event.preferred_spaces for r in rooms)),
                                  tuple(sorted({atom for r in rooms for atom in atoms(r)})))
            if event.locked and placement.identity != problem.previous[event.event_id]:
                continue
            found.append(placement)
    return found


def incompatible(problem: Problem, a: Event, pa: Placement, b: Event, pb: Placement,
                 paths: dict) -> bool:
    occupied_a = Window(pa.start - a.preparation, pa.end + a.cleanup)
    occupied_b = Window(pb.start - b.preparation, pb.end + b.cleanup)
    if set(pa.occupancy_atoms) & set(pb.occupancy_atoms) and overlaps(occupied_a, occupied_b):
        return True
    students = a.students & b.students
    staff = a.staff & b.staff
    if not students and not staff:
        return False
    if overlaps(Window(pa.start, pa.end), Window(pb.start, pb.end)):
        return True
    if pb.start < pa.start:
        a, pa, b, pb = b, pb, a, pa
    gap = pb.start - pa.end
    if students and a.is_exam and b.is_exam and gap < problem.minimum_exam_gap:
        return True
    student_a, student_b = dict(pa.student_spaces), dict(pb.student_spaces)

    def travel(origin, destination, profile):
        if origin is None or destination is None:
            return problem.online_transition
        if origin == destination:
            return 0
        key = profile, origin
        if key not in paths:
            paths[key] = shortest_paths(problem.navigation.get(profile, {}), origin)
        if destination not in paths[key]:
            paths.setdefault("missing_routes", set()).add((profile, origin, destination))
        return paths[key].get(destination, math.inf)

    for student in students:
        profile = problem.student_profiles.get(student, "standard")
        if gap < travel(student_a[student], student_b[student], profile):
            return True
    # A team may supervise any assigned room. Conservative worst-case transition.
    for _ in staff:
        if any(gap < travel(origin, destination, "standard")
               for origin in pa.spaces or (None,) for destination in pb.spaces or (None,)):
            return True
    return False


def solve(problem: Problem, seconds: float = 10) -> dict:
    check_input(problem)
    if seconds <= 0:
        raise ValueError("Time limit must be positive")
    domains = {event.event_id: candidates(problem, event) for event in problem.events}
    empty = [key for key, rows in domains.items() if not rows]
    if empty:
        return {"status": "INFEASIBLE", "assignments": {},
                "diagnostics": {"events_without_eligible_placements": empty},
                "scope": "Encoded input and permitted starts only"}
    model = cp_model.CpModel()
    variables = {key: [model.new_bool_var(f"{key}:{i}") for i in range(len(rows))]
                 for key, rows in domains.items()}
    for rows in variables.values():
        model.add_exactly_one(rows)
    paths = {}
    for a, b in combinations(problem.events, 2):
        for i, pa in enumerate(domains[a.event_id]):
            for j, pb in enumerate(domains[b.event_id]):
                if incompatible(problem, a, pa, b, pb, paths):
                    model.add(variables[a.event_id][i] + variables[b.event_id][j] <= 1)
    max_preferences = sum(max(p.preference_cost for p in rows) for rows in domains.values())
    move_weight = max_preferences + 1  # Proven dominance over all preference penalties.
    objective = []
    for event_id, rows in domains.items():
        for i, placement in enumerate(rows):
            moved = event_id in problem.previous and placement.identity != problem.previous[event_id]
            objective.append((move_weight * int(moved) + placement.preference_cost) * variables[event_id][i])
    model.minimize(sum(objective))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    status = solver.solve(model)
    result = {"status": solver.status_name(status), "assignments": {},
              "runtime_seconds": solver.wall_time, "move_weight": move_weight,
              "scope": "Encoded finite candidates and supplied availability/navigation only",
              "diagnostics": {"unreachable_or_unconfirmed_routes": sorted(paths.get("missing_routes", set()))}}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        result["assignments"] = {key: next(p for i, p in enumerate(rows)
                                          if solver.boolean_value(variables[key][i]))
                                 for key, rows in domains.items()}
        result["changed_events"] = [key for key, p in result["assignments"].items()
                                    if key in problem.previous and p.identity != problem.previous[key]]
        result["objective"] = solver.objective_value
        result["best_bound"] = solver.best_objective_bound
    return result


def validate(problem: Problem, assignments: dict[str, Placement]) -> list[str]:
    """Audit externally supplied assignments without accepting solver variable values."""
    check_input(problem)
    errors = []
    expected = {event.event_id for event in problem.events}
    if set(assignments) != expected:
        errors.append("Required event coverage differs from the supplied assignments")
    for event in problem.events:
        placement = assignments.get(event.event_id)
        if placement is None:
            continue
        # Regenerate legal alternatives from the input rather than trusting output capacity/version claims.
        if placement not in candidates(problem, event):
            errors.append(f"{event.event_id}: invalid time, membership, space version, capacity or availability")
    paths = {}
    for a, b in combinations(problem.events, 2):
        if a.event_id in assignments and b.event_id in assignments:
            if incompatible(problem, a, assignments[a.event_id], b, assignments[b.event_id], paths):
                errors.append(f"{a.event_id}/{b.event_id}: resource, participant, travel or exam-gap conflict")
    return errors
