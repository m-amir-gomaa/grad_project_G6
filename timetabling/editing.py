"""Exact, atomic editing of a resolved timetable; standard-library only.

This module consumes dated occurrences and their actual participants from a
validated generation adapter. It does not infer registrations, weekly recurrence,
professors, room capacity, or policy from year labels. Direct edits are complete
feasibility checks, not a heuristic re-optimization of the rest of the timetable.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from itertools import combinations
from threading import RLock
from typing import Literal


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


@dataclass(frozen=True, order=True)
class Interval:
    start: int
    end: int

    def __post_init__(self):
        if not integer(self.start) or not integer(self.end) or self.end <= self.start:
            raise ValueError('Intervals require integer minutes and positive duration')


def covers(windows: tuple[Interval, ...], start: int, end: int) -> bool:
    """Coverage by the union, including adjacent manually entered intervals."""
    until = start
    for window in sorted(windows):
        if window.end <= until:
            continue
        if window.start > until:
            return False
        until = window.end
        if until >= end:
            return True
    return False


def overlap(a, b):
    return a[0] < b[1] and b[0] < a[1]


@dataclass(frozen=True)
class Room:
    id: str
    kind: str
    capacity: int
    openings: tuple[Interval, ...]
    closures: tuple[Interval, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, 'openings', tuple(self.openings))
        object.__setattr__(self, 'closures', tuple(self.closures))


@dataclass(frozen=True)
class Professor:
    id: str
    openings: tuple[Interval, ...]

    def __post_init__(self):
        object.__setattr__(self, 'openings', tuple(self.openings))


@dataclass(frozen=True)
class Occurrence:
    id: str
    course: str
    component: str
    duration: int
    students: frozenset[str]
    professors: frozenset[str]
    windows: tuple[Interval, ...]
    room_kinds: frozenset[str]
    # Resolved eligible single/multi-room groups, derived by the generation adapter.
    room_options: tuple[tuple[str, ...], ...]
    # None means any integer minute fitting the entered windows; otherwise an
    # explicit, internally expanded domain (not a new student input field).
    starts: frozenset[int] | None = None
    years: frozenset[int] = frozenset()

    def __post_init__(self):
        for field in ('students', 'professors', 'room_kinds', 'years'):
            object.__setattr__(self, field, frozenset(getattr(self, field)))
        object.__setattr__(self, 'windows', tuple(self.windows))
        object.__setattr__(self, 'room_options', tuple(tuple(g) for g in self.room_options))
        if self.starts is not None:
            object.__setattr__(self, 'starts', frozenset(self.starts))


@dataclass(frozen=True)
class Reservation:
    id: str
    window: Interval
    rooms: frozenset[str] = frozenset()
    professors: frozenset[str] = frozenset()
    students: frozenset[str] = frozenset()

    def __post_init__(self):
        for field in ('rooms', 'professors', 'students'):
            object.__setattr__(self, field, frozenset(getattr(self, field)))


@dataclass(frozen=True)
class Problem:
    occurrences: tuple[Occurrence, ...]
    rooms: tuple[Room, ...]
    professors: tuple[Professor, ...]
    reservations: tuple[Reservation, ...] = ()

    def __post_init__(self):
        for name in ('occurrences', 'rooms', 'professors', 'reservations'):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        for rows in (self.occurrences, self.rooms, self.professors, self.reservations):
            if len({r.id for r in rows}) != len(rows) or any(not r.id for r in rows):
                raise ValueError('Empty or duplicate resource/occurrence/reservation IDs')
        if {o.id for o in self.occurrences} & {r.id for r in self.reservations}:
            raise ValueError('Reservation and occurrence IDs must be distinct')
        rooms = {r.id: r for r in self.rooms}
        staff = {p.id for p in self.professors}
        for r in self.rooms:
            if not integer(r.capacity) or r.capacity <= 0 or not r.kind:
                raise ValueError('Room type and positive entered capacity are required')
        for o in self.occurrences:
            if not integer(o.duration) or o.duration <= 0:
                raise ValueError('Manually entered positive duration is required')
            if not o.course or not o.component or not o.students or not o.professors:
                raise ValueError('Resolved course, component, participants, and fixed professors are required')
            if not o.professors <= staff:
                raise ValueError('Unknown assigned professor')
            if o.starts is not None and any(not integer(t) for t in o.starts):
                raise ValueError('Start domain uses integer minutes')
            if not o.room_options:
                raise ValueError('Resolved room options are required')
            for group in o.room_options:
                if not group or len(set(group)) != len(group) or not set(group) <= rooms.keys():
                    raise ValueError('Invalid resolved room group')
            if not o.years <= {1, 2, 3, 4}:
                raise ValueError('Unknown year label')
        for r in self.reservations:
            if not r.rooms <= rooms.keys() or not r.professors <= staff:
                raise ValueError('Reservation references unknown resources')


@dataclass(frozen=True)
class Placement:
    start: int
    end: int
    rooms: tuple[str, ...]
    allocation: tuple[tuple[str, str], ...]

    def __post_init__(self):
        object.__setattr__(self, 'rooms', tuple(sorted(self.rooms)))
        object.__setattr__(self, 'allocation', tuple(sorted(tuple(row) for row in self.allocation)))


def placement(problem: Problem, occurrence: str, start: int, rooms: tuple[str, ...]) -> Placement:
    """Preserve THIS occurrence's duration and students, even for unequal swaps."""
    event = next((o for o in problem.occurrences if o.id == occurrence), None)
    if event is None:
        raise ValueError('Unknown occurrence')
    if not integer(start):
        raise ValueError('Start uses integer minutes')
    groups = tuple(sorted(rooms))
    if len(set(groups)) != len(groups):
        raise ValueError('Duplicate room in placement')
    catalog = {r.id: r for r in problem.rooms}
    if not groups or not set(groups) <= catalog.keys():
        raise ValueError('Unknown or empty room group')
    remaining = sorted(event.students)
    assigned = []
    for room in groups:
        take = remaining[:catalog[room].capacity]
        assigned.extend((student, room) for student in take)
        remaining = remaining[len(take):]
    # Insufficient capacity deliberately leaves missing allocations for the audit.
    return Placement(start, start + event.duration, groups, tuple(assigned))


@dataclass(frozen=True, order=True)
class Violation:
    code: str
    occurrences: tuple[str, ...]
    resource: str = ''
    detail: str = ''


def validate(problem: Problem, schedule: dict[str, Placement]) -> tuple[Violation, ...]:
    """Independent whole-calendar audit. Does not use edit/target classifications."""
    errors = set()
    events = {o.id: o for o in problem.occurrences}
    rooms = {r.id: r for r in problem.rooms}
    staff = {p.id: p for p in problem.professors}
    if set(schedule) != set(events):
        errors.add(Violation('coverage', tuple(sorted(set(schedule) ^ set(events)))))
    resources = defaultdict(list)
    for key, event in events.items():
        p = schedule.get(key)
        if p is None:
            continue
        if not integer(p.start) or not integer(p.end) or p.end != p.start + event.duration:
            errors.add(Violation('duration', (key,)))
            continue
        if event.starts is not None and p.start not in event.starts:
            errors.add(Violation('start_domain', (key,)))
        if not covers(event.windows, p.start, p.end):
            errors.add(Violation('calendar', (key,)))
        if (not p.rooms or len(set(p.rooms)) != len(p.rooms) or
                frozenset(p.rooms) not in {frozenset(g) for g in event.room_options}):
            errors.add(Violation('room_group', (key,)))
        allocated = Counter(s for s, _ in p.allocation)
        if set(allocated) != event.students or any(v != 1 for v in allocated.values()):
            errors.add(Violation('student_coverage', (key,)))
        used = Counter(r for _, r in p.allocation)
        if not set(used) <= set(p.rooms):
            errors.add(Violation('allocation_room', (key,)))
        for room_id in p.rooms:
            room = rooms.get(room_id)
            if room is None:
                errors.add(Violation('unknown_room', (key,), room_id))
                continue
            if room.kind not in event.room_kinds:
                errors.add(Violation('room_type', (key,), room_id))
            if used[room_id] > room.capacity:
                errors.add(Violation('capacity', (key,), room_id))
            if not covers(room.openings, p.start, p.end):
                errors.add(Violation('room_availability', (key,), room_id))
            if any(overlap((p.start, p.end), (w.start, w.end)) for w in room.closures):
                errors.add(Violation('room_closure', (key,), room_id))
            resources['room', room_id].append((p.start, p.end, key))
        if sum(rooms[r].capacity for r in p.rooms if r in rooms) < len(event.students):
            errors.add(Violation('capacity', (key,)))
        for professor in event.professors:
            if not covers(staff[professor].openings, p.start, p.end):
                errors.add(Violation('professor_availability', (key,), professor))
            resources['professor', professor].append((p.start, p.end, key))
        for student in event.students:
            resources['student', student].append((p.start, p.end, key))
    for reservation in problem.reservations:
        for kind, ids in [('room', reservation.rooms), ('professor', reservation.professors),
                          ('student', reservation.students)]:
            for resource in ids:
                resources[kind, resource].append((reservation.window.start, reservation.window.end, reservation.id))
    # Sweep each actual resource. Adjacent [a,b), [b,c) intervals do not collide.
    # Ignore pre-existing reservation-vs-reservation overlaps; they are immutable
    # outside bookings, not a change to this schedule.
    for (kind, resource), items in resources.items():
        active = []
        for start, end, key in sorted(items):
            active = [item for item in active if item[1] > start]
            for _, _, other in active:
                if key != other and (key in events or other in events):
                    errors.add(Violation(kind + '_overlap', tuple(sorted((key, other))), resource))
            active.append((start, end, key))
    return tuple(sorted(errors))


@dataclass(frozen=True)
class Move:
    occurrence: str
    start: int
    rooms: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, 'rooms', tuple(self.rooms))


@dataclass(frozen=True)
class Request:
    kind: Literal['move', 'swap', 'undo', 'redo']
    moves: tuple[Move, ...] = ()
    pair: tuple[str, str] | tuple = ()
    mode: Literal['time_only', 'time_and_rooms'] = 'time_only'

    def __post_init__(self):
        object.__setattr__(self, 'moves', tuple(self.moves))
        object.__setattr__(self, 'pair', tuple(self.pair))
        if self.kind not in {'move', 'swap', 'undo', 'redo'}:
            raise ValueError('Unknown edit operation')
        if self.kind == 'move':
            if not self.moves or self.pair or len({m.occurrence for m in self.moves}) != len(self.moves):
                raise ValueError('Move explicitly lists distinct occurrence targets')
        elif self.kind == 'swap':
            if self.moves or len(self.pair) != 2 or self.pair[0] == self.pair[1]:
                raise ValueError('Swap requires two distinct occurrences')
            if self.mode not in {'time_only', 'time_and_rooms'}:
                raise ValueError('Unknown swap mode')
        elif self.moves or self.pair:
            raise ValueError('Undo/redo has no supplied placements')


@dataclass(frozen=True)
class State:
    revision: int
    input_revision: int
    placements: tuple[tuple[str, Placement], ...]
    locked: frozenset[str]
    violations: tuple[Violation, ...]
    can_undo: bool = False
    can_redo: bool = False

    @property
    def valid(self):
        return not self.violations


@dataclass(frozen=True)
class Preview:
    revision: int
    input_revision: int
    request: Request
    changed: tuple[str, ...]
    violations: tuple[Violation, ...]
    placements: tuple[tuple[str, Placement], ...]

    @property
    def valid(self):
        return not self.violations


class StaleEdit(ValueError):
    pass


class RejectedEdit(ValueError):
    def __init__(self, violations):
        self.violations = tuple(violations)
        super().__init__(', '.join(v.code for v in self.violations))


class Editor:
    """Serialized compare-and-apply. Preview success never bypasses commit checks."""
    def __init__(self, problem: Problem, schedule: dict[str, Placement]):
        failures = validate(problem, schedule)
        if failures:
            raise RejectedEdit(failures)
        self._problem = problem
        self._schedule = dict(schedule)
        self._revision = 0
        self._input_revision = 0
        self._locked = frozenset()
        self._undo = []
        self._redo = []
        self._mutex = RLock()

    def state(self):
        with self._mutex:
            return State(self._revision, self._input_revision, tuple(sorted(self._schedule.items())),
                         self._locked, validate(self._problem, self._schedule), bool(self._undo), bool(self._redo))

    def _check_revision(self, revision, input_revision):
        if revision != self._revision or input_revision != self._input_revision:
            raise StaleEdit('Schedule or inputs changed; recalculate this edit')

    def _candidate(self, request):
        current = self._schedule
        if request.kind in {'undo', 'redo'}:
            stack = self._undo if request.kind == 'undo' else self._redo
            if not stack:
                raise ValueError('Nothing to ' + request.kind)
            return dict(stack[-1])
        result = dict(current)
        def at(key, start, rooms):
            proposed = placement(self._problem, key, start, rooms)
            # A time-only edit must not shuffle students between unchanged rooms.
            if proposed.rooms == current[key].rooms:
                proposed = replace(proposed, allocation=current[key].allocation)
            return proposed
        if request.kind == 'move':
            for move in request.moves:
                if move.occurrence not in current:
                    raise ValueError('Unknown occurrence')
                result[move.occurrence] = at(move.occurrence, move.start, move.rooms)
        else:
            a, b = request.pair
            if a not in current or b not in current:
                raise ValueError('Unknown swap occurrence')
            pa, pb = current[a], current[b]
            # Both originals are replaced simultaneously, never by sequential moves.
            ra, rb = ((pa.rooms, pb.rooms) if request.mode == 'time_only' else (pb.rooms, pa.rooms))
            result[a] = at(a, pb.start, ra)
            result[b] = at(b, pa.start, rb)
        return result

    def preview(self, request: Request, revision: int, input_revision: int) -> Preview:
        with self._mutex:
            self._check_revision(revision, input_revision)
            target = self._candidate(request)
            changed = tuple(sorted(k for k in self._schedule if target.get(k) != self._schedule[k]))
            failures = list(validate(self._problem, target))
            failures.extend(Violation('locked', (key,)) for key in changed if key in self._locked)
            return Preview(self._revision, self._input_revision, request, changed,
                           tuple(sorted(set(failures))), tuple(sorted(target.items())))

    def commit(self, request: Request, revision: int, input_revision: int) -> State:
        with self._mutex:
            # Recompute under the same lock; client previews/colouring are not trusted.
            preview = self.preview(request, revision, input_revision)
            if not preview.valid:
                raise RejectedEdit(preview.violations)
            if not preview.changed:
                return self.state()
            old = tuple(sorted(self._schedule.items()))
            if request.kind == 'undo':
                self._undo.pop()
                self._redo.append(old)
            elif request.kind == 'redo':
                self._redo.pop()
                self._undo.append(old)
            else:
                self._undo.append(old)
                self._redo.clear()
            self._schedule = dict(preview.placements)
            self._revision += 1
            return self.state()

    def set_locked(self, keys: frozenset[str], locked: bool, revision: int, input_revision: int):
        with self._mutex:
            self._check_revision(revision, input_revision)
            if not keys <= self._schedule.keys():
                raise ValueError('Unknown occurrence')
            self._locked = (self._locked | keys) if locked else (self._locked - keys)
            self._revision += 1  # Invalidate all previously drawn targets/previews.
            return self.state()

    def replace_inputs(self, problem: Problem, revision: int, input_revision: int):
        with self._mutex:
            self._check_revision(revision, input_revision)
            self._problem = problem
            self._input_revision += 1
            return self.state()  # Can be stale/invalid; an audit still blocks export.

    def swap_options(self, selected: str, mode: str, limit: int | None = None):
        with self._mutex:
            if mode not in {'time_only', 'time_and_rooms'}:
                raise ValueError('Unknown swap mode')
            if selected not in self._schedule:
                raise ValueError('Unknown selected occurrence')
            if limit is not None and (not integer(limit) or limit < 0):
                raise ValueError('Invalid assessment limit')
            rows = []
            for index, other in enumerate(sorted(set(self._schedule) - {selected})):
                if limit is not None and index >= limit:
                    rows.append({'occurrence': other, 'status': 'unchecked', 'reasons': ()})
                    continue
                preview = self.preview(Request('swap', pair=(selected, other), mode=mode),
                                       self._revision, self._input_revision)
                status = 'blocked' if not preview.valid else 'valid' if preview.changed else 'unchanged'
                rows.append({'occurrence': other, 'status': status, 'reasons': preview.violations})
            return {'revision': self._revision, 'input_revision': self._input_revision,
                    'selected': selected, 'mode': mode, 'targets': rows}

    def inspect_swaps(self, selected: str, mode: str):
        """The view and its target colours belong to exactly the same revision."""
        with self._mutex:
            return self.state(), self.swap_options(selected, mode)
