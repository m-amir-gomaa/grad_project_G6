"""Whole-weekly-pattern edits and bounded, minimum-disruption rearrangement.

The calendar adapter explicitly identifies each recurring teaching slot and its
active weeks. No recurrence is inferred from a course name or student year.
OR-Tools is imported only when a broader proposal is requested.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta, timezone
from itertools import combinations
import math
import time as clock
from zoneinfo import ZoneInfo

from .editing import (Editor, Move, Problem, Request, Preview, Placement, Reservation,
                      RejectedEdit, Violation, integer, placement, validate)


class PatternTargetError(ValueError):
    pass


def local_minute(day: date, minute: int, zone: str) -> int:
    """Exact local civil time -> UTC minute; never guess a DST fold/gap."""
    if not integer(minute) or not 0 <= minute < 1440:
        raise PatternTargetError('Time of day must be an integer minute within the day')
    naive = datetime.combine(day, time.min) + timedelta(minutes=minute)
    tz = ZoneInfo(zone)
    candidates = set()
    for fold in (0, 1):
        aware = naive.replace(tzinfo=tz, fold=fold)
        utc = aware.astimezone(timezone.utc)
        if utc.astimezone(tz).replace(tzinfo=None) == naive:
            stamp = utc.timestamp()
            if stamp % 60:
                raise PatternTargetError('Local time is not representable at minute precision')
            candidates.add(int(stamp // 60))
    if len(candidates) != 1:
        raise PatternTargetError('Ambiguous or nonexistent local time; choose another time')
    return candidates.pop()


def civil(stamp: int, zone: str):
    return datetime.fromtimestamp(stamp * 60, ZoneInfo(zone))


@dataclass(frozen=True, order=True)
class Slot:
    day: int | str  # Monday=0..Sunday=6 for weekly; ISO local date for dated.
    minute: int
    rooms: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, 'rooms', tuple(sorted(self.rooms)))
        if not integer(self.minute) or not 0 <= self.minute < 1440:
            raise PatternTargetError('Invalid local time of day')
        if not self.rooms or len(set(self.rooms)) != len(self.rooms):
            raise PatternTargetError('Choose distinct rooms')


@dataclass(frozen=True)
class Member:
    occurrence: str
    week: date  # Explicit Monday of this active teaching week.
    teaching_week: int | None = None  # Academic week number, never ISO-week parity.


@dataclass(frozen=True)
class Series:
    id: str
    timezone: str
    members: tuple[Member, ...]
    kind: str = 'weekly'
    week_pattern: str = 'all'

    def __post_init__(self):
        object.__setattr__(self, 'members', tuple(self.members))
        ZoneInfo(self.timezone)
        if not self.id or not self.members or self.kind not in {'weekly', 'dated'}:
            raise ValueError('Explicit series identity, members, and recurrence kind required')
        if len({m.occurrence for m in self.members}) != len(self.members):
            raise ValueError('Duplicate series occurrence')
        if self.kind == 'weekly':
            if len({m.week for m in self.members}) != len(self.members) or any(m.week.weekday() != 0 for m in self.members):
                raise ValueError('A weekly slot has one occurrence per explicitly active week')
            if self.week_pattern not in {'all', 'odd', 'even'}:
                raise ValueError('Unknown teaching week pattern')
            for m in self.members:
                if m.teaching_week is not None and (not integer(m.teaching_week) or m.teaching_week <= 0):
                    raise ValueError('Invalid academic week number')
                if self.week_pattern in {'odd', 'even'}:
                    if m.teaching_week is None or m.teaching_week % 2 != int(self.week_pattern == 'odd'):
                        raise ValueError('Members must match their entered academic odd/even weeks')
        elif len(self.members) != 1:
            raise ValueError('A dated assessment is a singleton, not an invented recurrence')


@dataclass(frozen=True)
class Plan:
    base: Problem
    series: tuple[Series, ...]
    # Internal finite search candidates expanded from entered calendar/resources.
    domains: tuple[tuple[str, tuple[Slot, ...]], ...] = ()

    def __post_init__(self):
        object.__setattr__(self, 'series', tuple(self.series))
        object.__setattr__(self, 'domains', tuple((key, tuple(values)) for key, values in self.domains))
        ids = {s.id for s in self.series}
        if len(ids) != len(self.series) or len({key for key, _ in self.domains}) != len(self.domains):
            raise ValueError('Duplicate series or search-domain identity')
        if any(key not in ids for key, _ in self.domains):
            raise ValueError('Unknown series domain')
        events = {o.id: o for o in self.base.occurrences}
        seen = set()
        for s in self.series:
            for m in s.members:
                if m.occurrence not in events or m.occurrence in seen:
                    raise ValueError('Series members must be known and belong to one series only')
                seen.add(m.occurrence)
            rows = [events[m.occurrence] for m in s.members]
            signatures = {(o.course, o.component, o.duration, o.students, o.professors, o.room_kinds) for o in rows}
            if len(signatures) != 1:
                raise ValueError('A recurring slot preserves its course/component/group/duration/fixed professors')

    def get(self, key):
        found = next((s for s in self.series if s.id == key), None)
        if found is None:
            raise ValueError('Unknown weekly pattern')
        return found


@dataclass(frozen=True)
class Intent:
    kind: str
    selected: str
    other: str | None = None
    target: Slot | None = None
    mode: str = 'time_only'

    def __post_init__(self):
        if self.kind not in {'move', 'swap'}:
            raise ValueError('Expected a weekly-pattern move or swap')
        if self.kind == 'move' and (self.target is None or self.other is not None):
            raise ValueError('Pattern move requires a target slot')
        if self.kind == 'swap' and (not self.other or self.other == self.selected or self.target is not None):
            raise ValueError('Pattern swap requires two distinct patterns')
        if self.mode not in {'time_only', 'time_and_rooms'}:
            raise ValueError('Unknown swap mode')


def series_slot(series: Series, schedule: dict[str, Placement]) -> Slot:
    rows = []
    for member in series.members:
        p = schedule.get(member.occurrence)
        if p is None:
            raise PatternTargetError('Incomplete weekly pattern')
        local = civil(p.start, series.timezone)
        if series.kind == 'weekly':
            if local.date() - timedelta(days=local.weekday()) != member.week:
                raise PatternTargetError('Occurrence left its assigned teaching week')
            day = local.weekday()
        else:
            day = local.date().isoformat()
        # Reject unresolved local folds even on an externally supplied baseline.
        if local_minute(local.date(), local.hour * 60 + local.minute, series.timezone) != p.start:
            raise PatternTargetError('Unresolved local time')
        rows.append(Slot(day, local.hour * 60 + local.minute, p.rooms))
    if len(set(rows)) != 1:
        raise PatternTargetError('All active weeks must share the same local weekly slot and room group')
    return rows[0]


def series_moves(series: Series, slot: Slot) -> tuple[Move, ...]:
    if series.kind == 'weekly':
        if not integer(slot.day) or not 0 <= slot.day < 7:
            raise PatternTargetError('Choose a weekday for a weekly pattern')
        dates = [m.week + timedelta(days=slot.day) for m in series.members]
    else:
        if not isinstance(slot.day, str):
            raise PatternTargetError('Choose an explicit date for a dated assessment')
        dates = [date.fromisoformat(slot.day)]
    return tuple(Move(m.occurrence, local_minute(day, slot.minute, series.timezone), slot.rooms)
                 for m, day in zip(series.members, dates))


def intent_targets(plan: Plan, schedule, intent: Intent) -> dict[str, Slot]:
    left = plan.get(intent.selected)
    if intent.kind == 'move':
        return {left.id: intent.target}
    right = plan.get(intent.other)
    if left.kind != right.kind:
        raise PatternTargetError('Weekly teaching and dated assessments need separate edit operations')
    a, b = series_slot(left, schedule), series_slot(right, schedule)
    return {left.id: Slot(b.day, b.minute, a.rooms if intent.mode == 'time_only' else b.rooms),
            right.id: Slot(a.day, a.minute, b.rooms if intent.mode == 'time_only' else a.rooms)}


def request_for(plan: Plan, targets: dict[str, Slot]) -> Request:
    return Request('move', moves=tuple(move for key, slot in targets.items() for move in series_moves(plan.get(key), slot)))


def candidate_for(plan: Plan, current, targets):
    result = dict(current)
    for move in request_for(plan, targets).moves:
        proposed = placement(plan.base, move.occurrence, move.start, move.rooms)
        if proposed.rooms == current[move.occurrence].rooms:
            proposed = replace(proposed, allocation=current[move.occurrence].allocation)
        result[move.occurrence] = proposed
    return result


def pattern_errors(plan: Plan, schedule):
    failures = []
    for s in plan.series:
        try:
            series_slot(s, schedule)
        except (PatternTargetError, ValueError) as exc:
            failures.append(Violation('weekly_pattern', tuple(m.occurrence for m in s.members), s.id, str(exc)))
    return tuple(failures)


@dataclass(frozen=True)
class Proposal:
    status: str
    revision: int
    input_revision: int
    intent: Intent
    request: Request | None = None
    preview: Preview | None = None
    requested: tuple[str, ...] = ()
    additional: tuple[str, ...] = ()
    minimum_proven: bool = False
    objective: float | None = None
    best_bound: float | None = None
    detail: str = 'Finite supplied pattern domains; all active weeks and all four years'


class PatternEditor(Editor):
    def __init__(self, plan: Plan, schedule):
        self._plan = plan
        super().__init__(plan.base, schedule)
        failures = pattern_errors(plan, schedule)
        if failures:
            raise RejectedEdit(failures)

    @property
    def plan(self):
        with self._mutex:
            return self._plan

    def state(self):
        with self._mutex:
            state = super().state()
            return replace(state, violations=tuple(sorted(set(state.violations + pattern_errors(self._plan, dict(state.placements))))))

    def preview(self, request, revision, input_revision):
        with self._mutex:
            result = super().preview(request, revision, input_revision)
            extra = pattern_errors(self._plan, dict(result.placements))
            return replace(result, violations=tuple(sorted(set(result.violations + extra))))

    def preview_intent(self, intent: Intent, revision, input_revision):
        with self._mutex:
            self._check_revision(revision, input_revision)
            try:
                targets = intent_targets(self._plan, self._schedule, intent)
                req = request_for(self._plan, targets)
                return self.preview(req, revision, input_revision)
            except PatternTargetError as exc:
                series = self._plan.get(intent.selected)
                identities = tuple(Move(m.occurrence, self._schedule[m.occurrence].start,
                                        self._schedule[m.occurrence].rooms) for m in series.members)
                return Preview(revision, input_revision, Request('move', moves=identities), (),
                    (Violation('weekly_target', tuple(m.occurrence for m in series.members), series.id, str(exc)),),
                    tuple(sorted(self._schedule.items())))

    def commit_intent(self, intent, revision, input_revision):
        with self._mutex:
            preview = self.preview_intent(intent, revision, input_revision)
            if not preview.valid:
                raise RejectedEdit(preview.violations)
            return super().commit(preview.request, revision, input_revision)

    def set_series_locked(self, keys, locked, revision, input_revision):
        with self._mutex:
            ids = frozenset(m.occurrence for key in keys for m in self._plan.get(key).members)
            return super().set_locked(ids, locked, revision, input_revision)

    def replace_inputs(self, *args, **kwargs):
        raise ValueError('Replace the calendar/series plan together with its input records')

    def replace_plan(self, plan, revision, input_revision):
        with self._mutex:
            self._check_revision(revision, input_revision)
            self._plan, self._problem = plan, plan.base
            self._input_revision += 1
            return self.state()

    def inspect_patterns(self, selected, mode):
        with self._mutex:
            self._plan.get(selected)
            if mode not in {'time_only', 'time_and_rooms'}:
                raise ValueError('Unknown swap mode')
            state = self.state()
            targets = []
            for other in self._plan.series:
                if other.id == selected:
                    continue
                p = self.preview_intent(Intent('swap', selected, other.id, mode=mode), state.revision, state.input_revision)
                targets.append({'occurrence': other.id,
                    'status': 'blocked' if not p.valid else 'valid' if p.changed else 'unchanged', 'reasons': p.violations})
            return state, {'revision':state.revision,'input_revision':state.input_revision,
                           'selected':selected,'mode':mode,'targets':targets,'scope':'whole_weekly_pattern'}

    def propose(self, intent: Intent, revision, input_revision, seconds=3.0) -> Proposal:
        """Read-only search; the pinned/requested patterns remain hard constraints."""
        if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or not math.isfinite(seconds) or seconds <= 0:
            raise ValueError('Positive bounded search time required')
        with self._mutex:
            self._check_revision(revision, input_revision)
            plan, state = self._plan, self.state()
        result = _search(plan, state, intent, seconds)
        with self._mutex:
            self._check_revision(revision, input_revision)
        return result

    def apply_proposal(self, proposal: Proposal):
        with self._mutex:
            self._check_revision(proposal.revision, proposal.input_revision)
            if proposal.status not in {'OPTIMAL', 'FEASIBLE'} or proposal.request is None:
                raise ValueError('No valid rearrangement to apply')
            intended = intent_targets(self._plan, self._schedule, proposal.intent)
            preview = self.preview(proposal.request, proposal.revision, proposal.input_revision)
            if not preview.valid:
                raise RejectedEdit(preview.violations)
            candidate = dict(preview.placements)
            if any(series_slot(self._plan.get(key), candidate) != slot for key, slot in intended.items()):
                raise RejectedEdit((Violation('requested_target', tuple(intended)),))
            return super().commit(proposal.request, proposal.revision, proposal.input_revision)


def _search(plan: Plan, state, intent, seconds) -> Proposal:
    from ortools.sat.python import cp_model
    deadline = clock.monotonic() + seconds
    current = dict(state.placements)
    common = dict(revision=state.revision,input_revision=state.input_revision,intent=intent)
    try:
        forced = intent_targets(plan, current, intent)
    except PatternTargetError as exc:
        return Proposal('INVALID_REQUEST', **common, detail=str(exc))
    requested = tuple(sorted(forced))
    scope = {m.occurrence for s in plan.series for m in s.members}
    events = {o.id:o for o in plan.base.occurrences}
    fixed = list(plan.base.reservations)
    used = {r.id for r in fixed} | set(events)
    for key in sorted(set(events) - scope):
        label = 'fixed:' + key
        while label in used:
            label = 'fixed:' + label
        used.add(label)
        p,o = current[key],events[key]
        from .editing import Interval
        fixed.append(Reservation(label,Interval(p.start,p.end),frozenset(p.rooms),o.professors,o.students))
    catalog = dict(plan.domains)
    domains, originals = {}, {}
    for s in plan.series:
        if clock.monotonic() >= deadline:
            return Proposal('UNKNOWN', **common,requested=requested,detail='Candidate-building time limit; no result applied')
        old = series_slot(s,current);originals[s.id] = old
        slots = (forced[s.id],) if s.id in forced else tuple(dict.fromkeys((old,*catalog.get(s.id,()))))
        if any(m.occurrence in state.locked for m in s.members):
            slots = tuple(slot for slot in slots if slot == old)
        rows = []
        local_problem = Problem(tuple(events[m.occurrence] for m in s.members),plan.base.rooms,plan.base.professors,tuple(fixed))
        for slot in slots:
            if clock.monotonic() >= deadline:
                return Proposal('UNKNOWN', **common,requested=requested,detail='Candidate-building time limit; no result applied')
            try:
                candidate = candidate_for(plan,current,{s.id:slot})
            except (PatternTargetError, ValueError):
                continue
            assignments = {m.occurrence:candidate[m.occurrence] for m in s.members}
            if not validate(local_problem,assignments):
                rows.append((slot,assignments))
        if not rows:
            return Proposal('INFEASIBLE', **common,requested=requested,detail=f'No eligible whole-pattern choice for {s.id} within supplied domains/pins')
        domains[s.id] = rows
    model = cp_model.CpModel()
    variables = {key:[model.new_bool_var(f'{key}:{i}') for i in range(len(rows))] for key,rows in domains.items()}
    for row in variables.values():model.add_exactly_one(row)
    for left,right in combinations(plan.series,2):
        ids = {m.occurrence for m in (*left.members,*right.members)}
        pair_problem = Problem(tuple(o for o in plan.base.occurrences if o.id in ids),plan.base.rooms,plan.base.professors)
        for i,(_,a) in enumerate(domains[left.id]):
            for j,(_,b) in enumerate(domains[right.id]):
                if clock.monotonic() >= deadline:
                    return Proposal('UNKNOWN', **common,requested=requested,detail='Conflict-building time limit; no result applied')
                if validate(pair_problem,{**a,**b}):
                    model.add(variables[left.id][i] + variables[right.id][j] <= 1)
    # Proven lexicographic dominance: fewer additional patterns, then fewer
    # dated copies, then smaller time shifts (room changes break close ties).
    max_occurrences = sum(len(s.members) for s in plan.series if s.id not in forced)
    max_distance = sum(max(sum(abs(p.start-current[key].start) + int(p.rooms!=current[key].rooms)
                              for key,p in assignments.items()) for _,assignments in domains[s.id])
                       for s in plan.series if s.id not in forced)
    dated_weight = max_distance + 1
    pattern_weight = (max_occurrences + 1) * dated_weight
    objective = []
    for s in plan.series:
        for i,(slot,assignments) in enumerate(domains[s.id]):
            if s.id not in forced:
                moved = sum(assignments[key] != current[key] for key in assignments)
                distance = sum(abs(p.start-current[key].start) + int(p.rooms!=current[key].rooms)
                               for key,p in assignments.items())
                objective.append((pattern_weight * int(slot != originals[s.id]) + dated_weight * moved + distance)
                                 * variables[s.id][i])
    model.minimize(sum(objective))
    remaining = deadline - clock.monotonic()
    if remaining <= 0:return Proposal('UNKNOWN',**common,requested=requested,detail='Search budget exhausted before solve')
    solver = cp_model.CpSolver();solver.parameters.max_time_in_seconds=remaining
    solver.parameters.num_search_workers=1;solver.parameters.random_seed=0
    status = solver.solve(model);name = solver.status_name(status)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return Proposal(name,**common,requested=requested)
    final = dict(current);chosen = {}
    for key,rows in domains.items():
        slot,assignments = next(row for i,row in enumerate(rows) if solver.boolean_value(variables[key][i]))
        chosen[key]=slot;final.update(assignments)
    failures = list(validate(plan.base,final)) + list(pattern_errors(plan,final))
    changed = tuple(sorted(k for k in current if final[k] != current[k]))
    failures.extend(Violation('locked',(k,)) for k in changed if k in state.locked)
    if failures:
        return Proposal('MODEL_INVALID',**common,requested=requested,detail='Independent full-calendar audit rejected the solver result')
    moved_series = tuple(sorted(s.id for s in plan.series if chosen[s.id] != originals[s.id]))
    moves = tuple(Move(key,final[key].start,final[key].rooms) for key in changed)
    if not moves:
        key=next(iter(current));moves=(Move(key,current[key].start,current[key].rooms),)
    req=Request('move',moves=moves)
    preview=Preview(state.revision,state.input_revision,req,changed,(),tuple(sorted(final.items())))
    return Proposal(name,**common,request=req,preview=preview,requested=requested,
                    additional=tuple(k for k in moved_series if k not in forced),
                    minimum_proven=status==cp_model.OPTIMAL,objective=solver.objective_value,best_bound=solver.best_objective_bound)
