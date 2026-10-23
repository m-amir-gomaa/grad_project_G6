"""Regression cases plus exhaustive checks against a minute-occupancy oracle."""
import itertools
import threading
import unittest
from dataclasses import replace

from timetabling.editing import (Editor, Interval, Move, Occurrence, Placement, Problem,
    Professor, RejectedEdit, Request, Reservation, Room, StaleEdit, placement, validate)


def fixture(durations=(2, 1), starts=(0, 4)):
    window=(Interval(0, 12),)
    rooms=(Room('h1','hall',4,window),Room('h2','hall',4,window))
    professors=(Professor('p1',window),Professor('p2',window))
    events=tuple(Occurrence(chr(65+i),'course'+str(i),'lecture',duration,
        frozenset({'student'+str(i)}),frozenset({'p'+str(i%2+1)}),window,
        frozenset({'hall'}),(('h1',),('h2',)),years=frozenset({i%4+1}))
        for i,duration in enumerate(durations))
    p=Problem(events,rooms,professors)
    assignments={event.id:placement(p,event.id,start,('h1',)) for event,start in zip(events,starts)}
    return p,assignments


def preview(editor,request):
    state=editor.state()
    return editor.preview(request,state.revision,state.input_revision)


def commit(editor,request):
    state=editor.state()
    return editor.commit(request,state.revision,state.input_revision)


def minute_oracle(problem,schedule):
    """Different implementation: enumerate occupied integer minutes, not intervals."""
    occurrences={o.id:o for o in problem.occurrences}
    rooms={r.id:r for r in problem.rooms}
    professors={p.id:p for p in problem.professors}
    if set(schedule)!=set(occurrences): return False
    busy=set()
    for key,o in occurrences.items():
        a=schedule[key]
        if a.end-a.start!=o.duration:return False
        if o.starts is not None and a.start not in o.starts:return False
        if set(a.rooms) not in [set(v) for v in o.room_options]:return False
        if len(a.rooms)!=len(set(a.rooms)):return False
        if {s for s,_ in a.allocation}!=o.students or len(a.allocation)!=len(o.students):return False
        for r in a.rooms:
            if r not in rooms or rooms[r].kind not in o.room_kinds:return False
            if sum(q==r for _,q in a.allocation)>rooms[r].capacity:return False
        if any(r not in a.rooms for _,r in a.allocation):return False
        for t in range(a.start,a.end):
            if not any(w.start<=t<w.end for w in o.windows):return False
            for kind,ids in [('room',a.rooms),('professor',o.professors),('student',o.students)]:
                for resource in ids:
                    marker=(kind,resource,t)
                    if marker in busy:return False
                    busy.add(marker)
                    if kind=='room':
                        room=rooms[resource]
                        if not any(w.start<=t<w.end for w in room.openings):return False
                        if any(w.start<=t<w.end for w in room.closures):return False
                    if kind=='professor' and not any(w.start<=t<w.end for w in professors[resource].openings):return False
    for reserved in problem.reservations:
        for kind,ids in [('room',reserved.rooms),('professor',reserved.professors),('student',reserved.students)]:
            for resource in ids:
                if any((kind,resource,t) in busy for t in range(reserved.window.start,reserved.window.end)):
                    return False
    return True


class EditingTests(unittest.TestCase):
    def test_unequal_duration_swap_is_simultaneous_and_keeps_own_participants(self):
        p,s=fixture(); e=Editor(p,s)
        out=commit(e,Request('swap',pair=('A','B')))
        a,b=dict(out.placements)['A'],dict(out.placements)['B']
        self.assertEqual((a.start,a.end,b.start,b.end),(4,6,0,1))
        self.assertEqual({x for x,_ in a.allocation},p.occurrences[0].students)
        self.assertTrue(out.valid)

    def test_third_event_and_other_years_are_checked_not_just_the_swapped_pair(self):
        p,s=fixture((2,1,2),(0,2,3));e=Editor(p,s)
        before=e.state();q=preview(e,Request('swap',pair=('A','B')))
        self.assertFalse(q.valid)
        self.assertIn('professor_overlap',{v.code for v in q.violations})
        with self.assertRaises(RejectedEdit):commit(e,q.request)
        self.assertEqual(e.state(),before)

    def test_cross_year_student_collision_blocks_room_only_independent_professors(self):
        p,s=fixture(); events=list(p.occurrences)
        events[1]=replace(events[1],students=events[0].students,years=frozenset({4}))
        p=replace(p,occurrences=events);s['B']=placement(p,'B',4,('h2',));e=Editor(p,s)
        q=preview(e,Request('move',moves=(Move('A',4,('h1',)),)))
        self.assertIn('student_overlap',{v.code for v in q.violations})

    def test_time_and_room_mode_rejects_wrong_type_while_time_only_can_work(self):
        p,s=fixture();rooms=(p.rooms[0],replace(p.rooms[1],kind='lab'))
        events=(replace(p.occurrences[0],room_options=(('h1',),)),
                replace(p.occurrences[1],room_kinds=frozenset({'lab'}),room_options=(('h2',),)))
        p=replace(p,rooms=rooms,occurrences=events);s['B']=placement(p,'B',4,('h2',));e=Editor(p,s)
        self.assertTrue(preview(e,Request('swap',pair=('A','B'),mode='time_only')).valid)
        self.assertFalse(preview(e,Request('swap',pair=('A','B'),mode='time_and_rooms')).valid)

    def test_capacity_is_recomputed_even_if_adapter_supplied_bad_room_option(self):
        p,s=fixture(); rooms=(p.rooms[0],replace(p.rooms[1],capacity=1))
        events=(replace(p.occurrences[0],students=frozenset({'a','b','c'})),p.occurrences[1])
        p=replace(p,rooms=rooms,occurrences=events)
        s={'A':placement(p,'A',0,('h1',)),'B':placement(p,'B',4,('h2',))}
        q=preview(Editor(p,s),Request('swap',pair=('A','B'),mode='time_and_rooms'))
        self.assertFalse(q.valid);self.assertIn('capacity',{v.code for v in q.violations})

    def test_all_availability_and_external_reservations_are_enforced(self):
        p,s=fixture();e=Editor(p,s)
        constraints=[replace(p,rooms=(replace(p.rooms[0],closures=(Interval(6,8),)),p.rooms[1])),
                     replace(p,professors=(replace(p.professors[0],openings=(Interval(0,6),)),p.professors[1])),
                     replace(p,occurrences=(replace(p.occurrences[0],windows=(Interval(0,6),)),p.occurrences[1])),
                     replace(p,reservations=(Reservation('outside',Interval(6,8),rooms=frozenset({'h1'})),))]
        for changed in constraints:
            with self.subTest(problem=changed):
                editor=Editor(changed,s)
                self.assertFalse(preview(editor,Request('move',moves=(Move('A',6,('h1',)),))).valid)

    def test_adjacent_openings_and_back_to_back_events_use_half_open_intervals(self):
        p,s=fixture((2,2),(0,2))
        p=replace(p,rooms=(replace(p.rooms[0],openings=(Interval(0,1),Interval(1,12))),p.rooms[1]))
        self.assertFalse(validate(p,s))
        self.assertTrue(commit(Editor(p,s),Request('swap',pair=('A','B'))).valid)

    def test_multi_room_swap_rebuilds_exact_student_allocation(self):
        p,s=fixture(); rooms=(*p.rooms,Room('h3','hall',4,(Interval(0,12),)))
        events=tuple(replace(o,students=frozenset({str(i) for i in range(4)}),
                            room_options=(('h1','h2'),('h3',))) for o in p.occurrences)
        p=replace(p,rooms=rooms,occurrences=events)
        s={'A':placement(p,'A',0,('h1','h2')),'B':placement(p,'B',4,('h3',))}
        out=commit(Editor(p,s),Request('swap',pair=('A','B'),mode='time_and_rooms'))
        self.assertTrue(out.valid);self.assertEqual(dict(out.placements)['A'].rooms,('h3',))
        self.assertEqual(len(dict(out.placements)['A'].allocation),4)

    def test_explicit_series_move_and_three_cycle_commit_all_or_none(self):
        p,s=fixture((2,2,2),(0,2,4));e=Editor(p,s)
        request=Request('move',moves=(Move('A',2,('h1',)),Move('B',4,('h1',)),Move('C',0,('h1',))))
        after=commit(e,request);self.assertTrue(after.valid)
        self.assertEqual(set(dict(after.placements)),set(s))
        self.assertEqual(dict(commit(e,Request('undo')).placements),s)

    def test_failed_batch_move_leaves_every_event_unchanged(self):
        p,s=fixture();e=Editor(p,s);before=e.state()
        with self.assertRaises(RejectedEdit):
            commit(e,Request('move',moves=(Move('A',6,('h1',)),Move('B',7,('h1',)))))
        self.assertEqual(e.state(),before)

    def test_locks_stale_previews_and_input_revisions(self):
        p,s=fixture();e=Editor(p,s);q=preview(e,Request('swap',pair=('A','B')))
        e.set_locked(frozenset({'A'}),True,0,0)
        with self.assertRaises(StaleEdit):e.commit(q.request,q.revision,q.input_revision)
        self.assertIn('locked',{x.code for x in preview(e,q.request).violations})
        state=e.state();e.replace_inputs(p,state.revision,state.input_revision)
        with self.assertRaises(StaleEdit):e.commit(q.request,state.revision,state.input_revision)

    def test_undo_redo_revalidate_current_constraints_and_preserve_history_on_reject(self):
        p,s=fixture();e=Editor(p,s);request=Request('move',moves=(Move('A',8,('h1',)),))
        commit(e,request);commit(e,Request('undo'));self.assertEqual(dict(e.state().placements),s)
        commit(e,Request('redo'));self.assertEqual(dict(e.state().placements)['A'].start,8)
        st=e.state();changed=replace(p,rooms=(replace(p.rooms[0],closures=(Interval(0,2),)),p.rooms[1]))
        e.replace_inputs(changed,st.revision,st.input_revision)
        with self.assertRaises(RejectedEdit):commit(e,Request('undo'))
        self.assertEqual(dict(e.state().placements)['A'].start,8)
        st=e.state();e.replace_inputs(p,st.revision,st.input_revision)
        self.assertEqual(dict(commit(e,Request('undo')).placements),s)

    def test_new_edit_after_undo_discards_redo_and_pin_blocks_undo(self):
        p,s=fixture();e=Editor(p,s)
        commit(e,Request('move',moves=(Move('A',8,('h1',)),)))
        commit(e,Request('undo'));commit(e,Request('move',moves=(Move('A',6,('h1',)),)))
        with self.assertRaises(ValueError):preview(e,Request('redo'))
        st=e.state();e.set_locked(frozenset({'A'}),True,st.revision,st.input_revision)
        with self.assertRaises(RejectedEdit):commit(e,Request('undo'))

    def test_only_one_concurrent_commit_with_same_revision_can_succeed(self):
        p,s=fixture();e=Editor(p,s);barrier=threading.Barrier(2);out=[]
        def worker(t):
            barrier.wait()
            try:e.commit(Request('move',moves=(Move('A',t,('h2',)),)),0,0);out.append('ok')
            except StaleEdit:out.append('stale')
        workers=[threading.Thread(target=worker,args=(t,)) for t in [6,8]]
        for w in workers:w.start()
        for w in workers:w.join()
        self.assertCountEqual(out,['ok','stale']);self.assertTrue(e.state().valid)

    def test_unchecked_is_neither_blocked_nor_valid_and_unknown_mode_is_rejected(self):
        p,s=fixture((2,1,2),(0,4,8));e=Editor(p,s)
        data=e.swap_options('A','time_only',limit=0)
        self.assertEqual({v['status'] for v in data['targets']},{'unchecked'})
        with self.assertRaises(ValueError):e.swap_options('A','invented')

    def test_validator_rejects_missing_events_forged_duration_and_student_allocations(self):
        p,s=fixture()
        bad=dict(s);bad.pop('B');self.assertTrue(validate(p,bad))
        bad=dict(s);bad['A']=replace(bad['A'],end=bad['A'].end+1);self.assertTrue(validate(p,bad))
        bad=dict(s);bad['A']=replace(bad['A'],allocation=());self.assertTrue(validate(p,bad))
        bad=dict(s);bad['A']=replace(bad['A'],allocation=(('stranger','h1'),));self.assertTrue(validate(p,bad))

    def test_input_containers_and_returned_snapshots_cannot_mutate_editor_state(self):
        p,s=fixture();source=list(p.occurrences);p=replace(p,occurrences=source);e=Editor(p,s)
        source.clear();s.clear();snapshot=dict(e.state().placements);snapshot.clear()
        self.assertEqual(len(e.state().placements),2);self.assertTrue(e.state().valid)

    def test_time_only_preserves_existing_noncanonical_multiroom_allocation(self):
        p,_=fixture((2,),(0,));o=replace(p.occurrences[0],students=frozenset({'a','b'}),room_options=(('h1','h2'),))
        p=replace(p,occurrences=(o,));s={'A':Placement(0,2,('h1','h2'),(('a','h2'),('b','h1')))}
        e=Editor(p,s);after=commit(e,Request('move',moves=(Move('A',4,('h1','h2')),)))
        self.assertEqual(dict(after.placements)['A'].allocation,s['A'].allocation)

    def test_swap_edges_are_not_transitive_and_old_green_edges_expire(self):
        p,s=fixture((1,1,1),(0,2,4));events=tuple(replace(o,starts=frozenset(starts))
            for o,starts in zip(p.occurrences,[(0,2),(0,2,4),(2,4)]))
        p=replace(p,occurrences=events);e=Editor(p,s)
        self.assertTrue(preview(e,Request('swap',pair=('A','B'))).valid)
        old=preview(e,Request('swap',pair=('B','C')));self.assertTrue(old.valid)
        self.assertFalse(preview(e,Request('swap',pair=('A','C'))).valid)
        commit(e,Request('swap',pair=('A','B')))
        with self.assertRaises(StaleEdit):e.commit(old.request,old.revision,old.input_revision)
        self.assertFalse(preview(e,old.request).valid)

    def test_equal_start_time_only_swap_is_unchanged_not_a_green_target(self):
        p,s=fixture((2,1),(0,0));s['B']=placement(p,'B',0,('h2',));e=Editor(p,s)
        q=preview(e,Request('swap',pair=('A','B')))
        self.assertTrue(q.valid);self.assertEqual(q.changed,())
        self.assertEqual(e.swap_options('A','time_only')['targets'][0]['status'],'unchanged')

    def test_exhaustive_small_domain_swap_classification_matches_minute_oracle(self):
        base,_=fixture((2,1,2),(0,2,4));events=list(base.occurrences)
        events[2]=replace(events[2],students=events[0].students,years=frozenset({4}))
        p=replace(base,occurrences=events);baselines=checks=0
        for starts in itertools.product((0,2,4),repeat=3):
            for rooms in itertools.product(('h1','h2'),repeat=3):
                assignments={o.id:placement(p,o.id,t,(r,)) for o,t,r in zip(p.occurrences,starts,rooms)}
                if not minute_oracle(p,assignments):continue
                baselines+=1;e=Editor(p,assignments)
                for a,b in itertools.combinations(assignments,2):
                    for mode in ('time_only','time_and_rooms'):
                        expected=dict(assignments);pa,pb=assignments[a],assignments[b]
                        ra,rb=(pa.rooms,pb.rooms) if mode=='time_only' else (pb.rooms,pa.rooms)
                        # Oracle construction deliberately does not call candidate/placement().
                        for key,t,group in [(a,pb.start,ra),(b,pa.start,rb)]:
                            o=next(o for o in p.occurrences if o.id==key)
                            expected[key]=Placement(t,t+o.duration,group,tuple((s,group[0]) for s in sorted(o.students)))
                        got=preview(e,Request('swap',pair=(a,b),mode=mode))
                        self.assertEqual(got.valid,minute_oracle(p,expected),(starts,rooms,a,b,mode,got.violations))
                        checks+=1
        self.assertGreater(baselines,30);self.assertGreater(checks,200)
        print(f'Exhaustive editing oracle: {baselines} valid baselines, {checks} swaps checked.')


if __name__=='__main__':unittest.main()
