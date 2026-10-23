"""Synthetic whole-pattern editor and explicit broader-rearrangement demo."""
import argparse
from collections import OrderedDict
from dataclasses import asdict,is_dataclass
from datetime import date,timedelta
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
from threading import RLock
from urllib.parse import parse_qs,urlsplit
from uuid import uuid4

from .editing import (Interval,Occurrence,Problem,Professor,Request,Room,RejectedEdit,StaleEdit,placement)
from .patterns import Intent,Member,PatternEditor,Plan,Series,Slot,civil,local_minute,series_slot

ASSETS=Path(__file__).resolve().parents[1]/'examples'/'editing-demo'
META={
 'A':{'label':'برمجة 1','kind':'محاضرة','year':1},
 'B':{'label':'هياكل بيانات','kind':'محاضرة','year':2},
 'C':{'label':'قواعد بيانات','kind':'محاضرة','year':3},
 'D':{'label':'ذكاء اصطناعي','kind':'معمل','year':4},
 'E':{'label':'رياضيات حاسوبية','kind':'محاضرة','year':2},
 'F':{'label':'قواعد بيانات','kind':'معمل','year':3},
 'G':{'label':'برمجة 1','kind':'معمل','year':1},
 'H':{'label':'شبكات متقدمة','kind':'محاضرة','year':4},
}
ROOM_LABELS={'h1':'قاعة 1','h2':'قاعة 2','l1':'معمل 1'}
PROFESSOR_LABELS={'p1':'مدرس أ','p2':'مدرس ب','p3':'مدرس ج'}
ZONE='Africa/Cairo'
WEEKS=(date(2026,10,12),date(2026,10,19),date(2026,10,26))


def demo_plan():
    # Explicit synthetic availability; no college default is inferred.
    windows=tuple(Interval(local_minute(w+timedelta(days=5),540,ZONE),
                           local_minute(w+timedelta(days=5),1140,ZONE)) for w in WEEKS)
    rooms=(Room('h1','hall',30,windows),Room('h2','hall',30,windows),Room('l1','lab',20,windows))
    staff=tuple(Professor(p,windows) for p in PROFESSOR_LABELS)
    cohorts={y:frozenset(f'y{y}-{i}' for i in range(1,4)) for y in range(1,5)}
    rows=[('A',0,120,'p1','h1'),('B',120,60,'p2','h2'),('C',240,90,'p1','h2'),
          ('D',120,60,'p3','l1'),('E',180,60,'p1','h2'),('F',330,60,'p2','l1'),
          ('G',390,60,'p3','l1'),('H',420,60,'p1','h2')]
    occurrences=[];patterns=[];initial={};domains=[]
    for key,start,duration,prof,room in rows:
        row=META[key];participants=cohorts[row['year']];years=frozenset({row['year']})
        if key=='B':participants=participants|{'y1-1'};years=years|{1}
        week_pattern='even' if key=='C' else 'odd' if key=='D' else 'all'
        kind='lab' if room=='l1' else 'hall';course={'G':'A','F':'C'}.get(key,key)
        options=(('l1',),) if kind=='lab' else (('h1',),('h2',))
        members=[]
        for number,week in enumerate(WEEKS,1):
            if week_pattern=='odd' and not number%2:continue
            if week_pattern=='even' and number%2:continue
            eid=f'{key}:{number}'
            occurrences.append(Occurrence(eid,course,row['kind'],duration,participants,frozenset({prof}),
                windows,frozenset({kind}),options,years=years))
            members.append(Member(eid,week,number));initial[eid]=(local_minute(week+timedelta(days=5),540+start,ZONE),(room,))
        patterns.append(Series(key,ZONE,tuple(members),week_pattern=week_pattern))
        domains.append((key,tuple(Slot(5,540+t,group) for t in (0,60,120,180,240,300,330,360,390,420,480,540) for group in options)))
    base=Problem(tuple(occurrences),rooms,staff)
    baseline={key:placement(base,key,t,group) for key,(t,group) in initial.items()}
    return Plan(base,tuple(patterns),tuple(domains)),baseline


def make_editor():
    plan,baseline=demo_plan();editor=PatternEditor(plan,baseline)
    editor.set_series_locked({'H'},True,0,0)
    return editor


def request_from_json(editor,body):
    kind=body.get('kind')
    if kind in {'undo','redo'}:return Request(kind)
    if kind=='swap':
        if 'mode' not in body:raise ValueError('Choose the swap mode explicitly')
        pair=body['pair']
        if len(pair)!=2:raise ValueError('Choose two patterns')
        return Intent('swap',pair[0],pair[1],mode=body['mode'])
    if kind=='move':
        rows=body['moves']
        if len(rows)!=1:raise ValueError('Choose one whole pattern; batches require a reviewed proposal')
        row=rows[0];s=editor.plan.get(row['occurrence'])
        current=series_slot(s,dict(editor.state().placements))
        return Intent('move',s.id,target=Slot(row.get('day',current.day),540+row['start'],tuple(row['rooms'])))
    raise ValueError('Unknown pattern operation')


def projected(editor,placements):
    plan=editor.plan;events={o.id:o for o in plan.base.occurrences};result=[]
    for s in plan.series:
        slot=series_slot(s,placements);o=events[s.members[0].occurrence]
        result.append(dict(id=s.id,**META[s.id],start=slot.minute-540,end=slot.minute-540+o.duration,
            rooms=slot.rooms,duration=o.duration,years=sorted(o.years),professors=sorted(o.professors),
            room_options=o.room_options,day=slot.day,week_pattern=s.week_pattern,
            occurrence_count=len(s.members),occurrence_ids=[m.occurrence for m in s.members]))
    return result


def payload(editor,selected='A',mode='time_only'):
    with editor._mutex:
        state,swaps=editor.inspect_patterns(selected,mode);positions=dict(state.placements)
        events=projected(editor,positions);owners={m.occurrence:s for s in editor.plan.series for m in s.members}
        locked=[s.id for s in editor.plan.series if any(m.occurrence in state.locked for m in s.members)]
        return dict(synthetic=True,scope='whole_weekly_pattern',timezone=ZONE,
            revision=state.revision,input_revision=state.input_revision,valid=state.valid,locked=locked,
            can_undo=state.can_undo,can_redo=state.can_redo,events=events,rooms=ROOM_LABELS,professors=PROFESSOR_LABELS,
            swaps=map_swaps(editor,swaps),
            occurrences=[dict(id=key,pattern=owners[key].id,start=p.start,end=p.end,rooms=p.rooms,
                local=civil(p.start,owners[key].timezone).isoformat(),allocation=p.allocation) for key,p in state.placements])


def map_violations(editor,violations):
    mapping={m.occurrence:(s.id,m.teaching_week) for s in editor.plan.series for m in s.members}
    result=[];seen=set()
    for v in violations:
        ids=tuple(sorted({mapping.get(key,(key,None))[0] for key in v.occurrences}))
        identity=(v.code,ids,v.resource,v.detail)
        if identity in seen:continue
        seen.add(identity)
        result.append(dict(code=v.code,occurrences=ids,resource=v.resource,detail=v.detail))
    return result


def map_swaps(editor,data):
    return {**data,'targets':[{**t,'reasons':map_violations(editor,t['reasons'])} for t in data['targets']]}


def preview_payload(editor,preview):
    owners={m.occurrence:s.id for s in editor.plan.series for m in s.members}
    changed=sorted({owners[key] for key in preview.changed if key in owners})
    return dict(revision=preview.revision,input_revision=preview.input_revision,scope='whole_weekly_pattern',
        changed=changed,changed_occurrences=list(preview.changed),affected_occurrences=len(preview.changed),
        violations=map_violations(editor,preview.violations),
        placements=[[row['id'],row] for row in projected(editor,dict(preview.placements))])


def json_default(value):
    if is_dataclass(value):return asdict(value)
    if isinstance(value,(set,frozenset)):return sorted(value)
    if isinstance(value,date):return value.isoformat()
    raise TypeError(type(value).__name__)


def snapshot_file(path):
    Path(path).write_text(json.dumps(payload(make_editor()),ensure_ascii=False,indent=2,default=json_default)+'\n',encoding='utf-8')


def serve(port):
    editor=make_editor();proposals=OrderedDict();proposal_lock=RLock()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def send_json(self,data,status=200):
            raw=json.dumps(data,ensure_ascii=False,default=json_default).encode()
            self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)))
            self.end_headers();self.wfile.write(raw)
        def trusted(self):
            expected=f'127.0.0.1:{self.server.server_port}'
            return self.headers.get('Host','')==expected and self.headers.get('Origin') in (None,'http://'+expected)
        def do_GET(self):
            if not self.trusted():return self.send_json({'error':'Unexpected host/origin'},403)
            url=urlsplit(self.path)
            if url.path=='/api/state':
                args=parse_qs(url.query)
                try:return self.send_json(payload(editor,args.get('selected',['A'])[0],args.get('mode',['time_only'])[0]))
                except ValueError as exc:return self.send_json({'error':str(exc)},400)
            name={'/':'index.html','/editor.js':'editor.js','/style.css':'style.css'}.get(url.path)
            if name is None:return self.send_json({'error':'Not found'},404)
            raw=(ASSETS/name).read_bytes();kind={'html':'text/html','css':'text/css','js':'text/javascript'}[name.rsplit('.',1)[1]]
            self.send_response(200);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('Content-Length',str(len(raw)))
            self.end_headers();self.wfile.write(raw)
        def do_POST(self):
            if not self.trusted():return self.send_json({'error':'Unexpected host/origin'},403)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=20000:raise ValueError('Invalid request size')
                body=json.loads(self.rfile.read(size))
                if not isinstance(body,dict):raise ValueError('Expected request object')
                revision,inputs=body['revision'],body['input_revision']
                if type(revision) is not int or type(inputs) is not int:raise ValueError('Expected integer revision')
                if self.path=='/api/lock':
                    if type(body['locked']) is not bool:raise ValueError('Expected pin state')
                    editor.set_series_locked(body['ids'],body['locked'],revision,inputs)
                    return self.send_json({'ok':True})
                if self.path=='/api/apply' and 'proposal_id' in body:
                    with proposal_lock:proposal=proposals.get(body['proposal_id'])
                    if proposal is None:raise ValueError('Proposal expired; calculate it again')
                    if (revision,inputs)!=(proposal.revision,proposal.input_revision):raise StaleEdit('Proposal revision changed')
                    return self.send_json(asdict(editor.apply_proposal(proposal)))
                intent=request_from_json(editor,body)
                if self.path=='/api/rearrange':
                    if not isinstance(intent,Intent):raise ValueError('A rearrangement needs an explicit pattern target')
                    proposal=editor.propose(intent,revision,inputs,seconds=4)
                    if proposal.preview is None:
                        return self.send_json(dict(status=proposal.status,detail=proposal.detail,minimum_proven=False))
                    key=uuid4().hex
                    with proposal_lock:
                        proposals[key]=proposal
                        while len(proposals)>32:proposals.popitem(last=False)
                    result=preview_payload(editor,proposal.preview)
                    result.update(proposal_id=key,status=proposal.status,requested=proposal.requested,
                                  additional=proposal.additional,minimum_proven=proposal.minimum_proven)
                    return self.send_json(result)
                if self.path=='/api/preview':
                    with editor._mutex:
                        p=(editor.preview_intent(intent,revision,inputs) if isinstance(intent,Intent)
                           else editor.preview(intent,revision,inputs))
                        return self.send_json(preview_payload(editor,p))
                if self.path=='/api/apply':
                    state=(editor.commit_intent(intent,revision,inputs) if isinstance(intent,Intent)
                           else editor.commit(intent,revision,inputs))
                    return self.send_json(asdict(state))
                return self.send_json({'error':'Not found'},404)
            except StaleEdit as exc:return self.send_json({'error':'stale','message':str(exc)},409)
            except RejectedEdit as exc:return self.send_json({'error':'blocked','violations':map_violations(editor,exc.violations)},422)
            except (ValueError,TypeError,KeyError) as exc:return self.send_json({'error':str(exc)},400)
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'http://127.0.0.1:{server.server_port}',flush=True)
    try:server.serve_forever()
    finally:server.server_close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765);parser.add_argument('--snapshot')
    args=parser.parse_args()
    if args.snapshot:snapshot_file(args.snapshot)
    else:serve(args.port)
