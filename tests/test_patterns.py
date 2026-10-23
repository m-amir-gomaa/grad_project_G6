"""Whole-pattern and repair regressions, including an exhaustive optimum oracle."""
from dataclasses import replace
from datetime import date,timedelta
from itertools import product
import unittest
from zoneinfo import ZoneInfo
from timetabling.editing import (Interval,Move,Occurrence,Problem,Professor,Request,Reservation,
                                Room,RejectedEdit,StaleEdit,placement,validate)
from timetabling.patterns import (Intent,Member,PatternEditor,Plan,Series,Slot,local_minute,
                                 civil,series_slot,series_moves)
from test_editing import minute_oracle


def fixture(weeks=None,starts=(540,542,544),extra_b=False):
    weeks=weeks or (date(2027,1,4),date(2027,1,11))
    windows=tuple(Interval(local_minute(w,0,'UTC'),local_minute(w+timedelta(days=7),0,'UTC')) for w in weeks)
    rooms=(Room('h1','hall',30,windows),Room('h2','hall',30,windows))
    professors=(Professor('p',windows),)
    events=[];series=[];baseline={};domains=[]
    for index,start in enumerate(starts):
        key=chr(65+index);members=[]
        for number,week in enumerate(weeks,1):
            eid=f'{key}:{number}'
            events.append(Occurrence(eid,key,'lecture',2,frozenset({f's{index}'}),frozenset({'p'}),windows,
                                    frozenset({'hall'}),(('h1',),('h2',)),years=frozenset({[1,2,4][index%3]})))
            members.append(Member(eid,week,number))
        series.append(Series(key,'UTC',tuple(members)))
        values={0:(540,),1:(542,544,546) if extra_b else (542,544),2:(544,540)}[index]
        domains.append((key,tuple(Slot(0,t,('h1',)) for t in values)))
    base=Problem(tuple(events),rooms,professors)
    for s,start in zip(series,starts):
        for member in s.members:baseline[member.occurrence]=placement(base,member.occurrence,local_minute(member.week,start,'UTC'),('h1',))
    return Plan(base,tuple(series),tuple(domains)),baseline


def preview(editor,intent):
    s=editor.state();return editor.preview_intent(intent,s.revision,s.input_revision)


def commit(editor,intent):
    s=editor.state();return editor.commit_intent(intent,s.revision,s.input_revision)


def propose(editor,intent,seconds=4):
    s=editor.state();return editor.propose(intent,s.revision,s.input_revision,seconds)


class PatternTests(unittest.TestCase):
    def test_move_changes_all_repeated_weeks_and_preserves_room_duration_roster(self):
        plan,baseline=fixture(starts=(540,));editor=PatternEditor(plan,baseline)
        out=commit(editor,Intent('move','A',target=Slot(1,600,('h2',))))
        self.assertTrue(out.valid)
        for member in plan.series[0].members:
            p=dict(out.placements)[member.occurrence];local=civil(p.start,'UTC')
            self.assertEqual((local.weekday(),local.hour,local.minute),(1,10,0))
            self.assertEqual(p.end-p.start,2);self.assertEqual(p.rooms,('h2',))
        self.assertEqual(len(out.placements),len(baseline))

    def test_one_bad_week_rejects_entire_pattern_and_one_date_bypass_is_blocked(self):
        plan,baseline=fixture(starts=(540,));week=plan.series[0].members[1].week
        closed=Interval(local_minute(week,600,'UTC'),local_minute(week,602,'UTC'))
        plan=replace(plan,base=replace(plan.base,rooms=(replace(plan.base.rooms[0],closures=(closed,)),plan.base.rooms[1])))
        editor=PatternEditor(plan,baseline);before=editor.state()
        req=Intent('move','A',target=Slot(0,600,('h1',)))
        self.assertFalse(preview(editor,req).valid)
        with self.assertRaises(RejectedEdit):commit(editor,req)
        m=plan.series[0].members[0]
        with self.assertRaises(RejectedEdit):editor.commit(Request('move',moves=(Move(m.occurrence,local_minute(m.week,600,'UTC'),('h1',)),)),0,0)
        self.assertEqual(editor.state(),before)

    def test_odd_even_uses_entered_academic_numbers_and_does_not_add_inactive_weeks(self):
        weeks=(date(2027,1,11),date(2027,1,25),date(2027,2,8))
        plan,baseline=fixture(weeks,starts=(540,))
        s=replace(plan.series[0],members=tuple(replace(m,teaching_week=n) for m,n in zip(plan.series[0].members,(1,3,5))),week_pattern='odd')
        # Academic week 1 here is ISO week 2: parity must not come from ISO dates.
        self.assertEqual(s.members[0].week.isocalendar().week%2,0)
        plan=replace(plan,series=(s,));editor=PatternEditor(plan,baseline)
        state=commit(editor,Intent('move','A',target=Slot(2,600,('h1',))))
        self.assertEqual(len(state.placements),3)
        self.assertEqual({civil(p.start,'UTC').date()-timedelta(days=2) for _,p in state.placements},set(weeks))
        with self.assertRaises(ValueError):replace(s,week_pattern='even')

    def test_swap_different_active_week_counts_keeps_each_series_own_weeks(self):
        plan,baseline=fixture((date(2027,1,4),date(2027,1,18),date(2027,2,1)),starts=(540,542))
        a=replace(plan.series[0],members=tuple(replace(m,teaching_week=n) for m,n in zip(plan.series[0].members,(1,3,5))),week_pattern='odd')
        b=replace(plan.series[1],members=tuple(replace(m,teaching_week=n) for m,n in zip(plan.series[1].members[:2],(1,3))),week_pattern='odd')
        keep={m.occurrence for s in (a,b) for m in s.members}
        plan=replace(plan,base=replace(plan.base,occurrences=tuple(o for o in plan.base.occurrences if o.id in keep)),series=(a,b))
        baseline={k:v for k,v in baseline.items() if k in keep};editor=PatternEditor(plan,baseline)
        state=commit(editor,Intent('swap','A','B'))
        self.assertEqual(len(state.placements),5);self.assertTrue(state.valid)
        self.assertEqual(series_slot(a,dict(state.placements)).minute,542)
        self.assertEqual(series_slot(b,dict(state.placements)).minute,540)

    def test_dst_preserves_local_weekday_hour_not_a_constant_utc_shift(self):
        weeks=(date(2026,10,26),date(2026,11,2));zone='America/New_York'
        windows=tuple(Interval(local_minute(w,0,zone),local_minute(w+timedelta(days=7),0,zone)) for w in weeks)
        rooms=(Room('r','hall',10,windows),);staff=(Professor('p',windows),)
        events=tuple(Occurrence(str(i),'A','lecture',60,frozenset({'s'}),frozenset({'p'}),windows,frozenset({'hall'}),(('r',),)) for i in range(2))
        base=Problem(events,rooms,staff);s=Series('A',zone,tuple(Member(str(i),w,i+1) for i,w in enumerate(weeks)))
        old={str(i):placement(base,str(i),local_minute(w,540,zone),('r',)) for i,w in enumerate(weeks)}
        editor=PatternEditor(Plan(base,(s,)),old);state=commit(editor,Intent('move','A',target=Slot(6,540,('r',))))
        deltas=[]
        for key,p in state.placements:
            d=civil(p.start,zone);self.assertEqual((d.weekday(),d.hour),(6,9));deltas.append(p.start-old[key].start)
        self.assertEqual(abs(deltas[0]-deltas[1]),60)

    def test_dst_gaps_and_unresolved_folds_are_never_guessed(self):
        with self.assertRaises(ValueError):local_minute(date(2027,3,14),150,'America/New_York')
        with self.assertRaises(ValueError):local_minute(date(2026,11,1),90,'America/New_York')

    def test_broader_rearrangement_can_require_a_three_pattern_chain(self):
        plan,baseline=fixture();editor=PatternEditor(plan,baseline)
        intent=Intent('move','A',target=Slot(0,542,('h1',)))
        self.assertFalse(preview(editor,intent).valid)
        solution=propose(editor,intent)
        self.assertEqual(solution.status,'OPTIMAL');self.assertTrue(solution.minimum_proven)
        self.assertEqual(solution.additional,('B','C'));self.assertEqual(len(solution.preview.changed),6)
        self.assertEqual(editor.state().revision,0)  # Searching never applies anything.
        state=editor.apply_proposal(solution);self.assertTrue(state.valid)
        self.assertEqual(series_slot(plan.get('A'),dict(state.placements)).minute,542)
        self.assertEqual(series_slot(plan.get('B'),dict(state.placements)).minute,544)
        self.assertEqual(series_slot(plan.get('C'),dict(state.placements)).minute,540)
        state=editor.commit(Request('undo'),state.revision,state.input_revision)
        self.assertEqual(dict(state.placements),baseline)

    def test_search_prefers_one_extra_pattern_over_two(self):
        plan,baseline=fixture(extra_b=True);editor=PatternEditor(plan,baseline)
        solution=propose(editor,Intent('move','A',target=Slot(0,542,('h1',))))
        self.assertEqual(solution.status,'OPTIMAL');self.assertEqual(solution.additional,('B',))
        self.assertEqual(series_slot(plan.get('B'),dict(solution.preview.placements)).minute,546)

    def test_pin_applies_to_whole_pattern_and_cannot_be_relaxed_by_search(self):
        plan,baseline=fixture();editor=PatternEditor(plan,baseline)
        editor.set_series_locked({'C'},True,0,0)
        self.assertEqual(len(editor.state().locked),2)
        before=editor.state();solution=propose(editor,Intent('move','A',target=Slot(0,542,('h1',))))
        self.assertEqual(solution.status,'INFEASIBLE');self.assertEqual(editor.state(),before)

    def test_fixed_nonpattern_booking_is_included_in_broader_solver(self):
        plan,baseline=fixture(extra_b=True)
        windows=plan.base.rooms[0].openings
        o=Occurrence('outside','X','lecture',2,frozenset({'other'}),frozenset({'p'}),windows,frozenset({'hall'}),(('h1',),),years=frozenset({3}))
        base=replace(plan.base,occurrences=(*plan.base.occurrences,o));plan=replace(plan,base=base)
        baseline['outside']=placement(base,'outside',local_minute(date(2027,1,4),546,'UTC'),('h1',))
        editor=PatternEditor(plan,baseline)
        solution=propose(editor,Intent('move','A',target=Slot(0,542,('h1',))))
        self.assertEqual(solution.additional,('B','C'))
        self.assertEqual(dict(solution.preview.placements)['outside'],baseline['outside'])

    def test_proposal_rejects_stale_schedule_input_or_changed_pins(self):
        plan,baseline=fixture();editor=PatternEditor(plan,baseline);intent=Intent('move','A',target=Slot(0,542,('h1',)))
        solution=propose(editor,intent);editor.set_series_locked({'C'},True,0,0)
        with self.assertRaises(StaleEdit):editor.apply_proposal(solution)
        editor=PatternEditor(plan,baseline);solution=propose(editor,intent);editor.replace_plan(plan,0,0)
        with self.assertRaises(StaleEdit):editor.apply_proposal(solution)

    def test_tiny_budget_is_unknown_not_infeasible_and_has_no_side_effect(self):
        plan,baseline=fixture();editor=PatternEditor(plan,baseline);before=editor.state()
        solution=propose(editor,Intent('move','A',target=Slot(0,542,('h1',))),seconds=1e-9)
        self.assertEqual(solution.status,'UNKNOWN');self.assertFalse(solution.minimum_proven)
        self.assertIsNone(solution.preview);self.assertEqual(editor.state(),before)

    def test_forged_legal_solution_that_ignores_requested_target_is_rejected(self):
        plan,baseline=fixture();editor=PatternEditor(plan,baseline)
        solution=propose(editor,Intent('move','A',target=Slot(0,542,('h1',))))
        identity=Request('move',moves=(Move('A:1',baseline['A:1'].start,('h1',)),))
        with self.assertRaises(RejectedEdit):editor.apply_proposal(replace(solution,request=identity))
        self.assertEqual(dict(editor.state().placements),baseline)

    def test_exhaustive_optimum_matches_independent_minute_oracle(self):
        checked=0
        for extra in (False,True):
            plan,baseline=fixture(extra_b=extra);editor=PatternEditor(plan,baseline)
            intent=Intent('move','A',target=Slot(0,542,('h1',)))
            choices={k:v for k,v in plan.domains};choices['A']=(intent.target,)
            best=None
            for slots in product(*(choices[s.id] for s in plan.series)):
                candidate={}
                for s,slot in zip(plan.series,slots):
                    # Independent expansion; fixture uses UTC Mondays and 2-minute lessons.
                    for m in s.members:
                        t=int(datetime_stamp(m.week))+slot.minute
                        candidate[m.occurrence]=placement(plan.base,m.occurrence,t,slot.rooms)
                if not minute_oracle(plan.base,candidate):continue
                additional=sum(slot.minute!=old for s,slot,old in zip(plan.series,slots,(540,542,544)) if s.id!='A')
                copies=sum(candidate[m.occurrence]!=baseline[m.occurrence] for s in plan.series if s.id!='A' for m in s.members)
                score=(additional,copies);best=score if best is None else min(best,score);checked+=1
            actual=propose(editor,intent)
            self.assertEqual(actual.status,'OPTIMAL')
            got=(len(actual.additional),sum(k in actual.preview.changed for s in plan.series if s.id in actual.additional for k in [m.occurrence for m in s.members]))
            self.assertEqual(got,best)
        self.assertGreaterEqual(checked,2)


def datetime_stamp(day):
    from datetime import datetime,timezone
    return datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()//60


if __name__=='__main__':unittest.main()
