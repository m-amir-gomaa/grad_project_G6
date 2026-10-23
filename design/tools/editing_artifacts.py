"""Generate native-design evidence from the actual editing engine's fixture."""
import json
import sys
from dataclasses import asdict
from pathlib import Path
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
from timetabling.patterns import Intent
from timetabling.editing_demo import make_editor,payload,json_default,preview_payload

POSITIONS={'A':(715,305),'C':(210,90),'B':(480,95),'D':(190,285),
           'E':(465,305),'F':(190,510),'G':(460,535),'H':(750,530)}
YEAR_COLORS={1:'#4D65D9',2:'#875CC7',3:'#25857B',4:'#BA8025'}


def clock(t):return f'{9+t//60:02d}:{t%60:02d}'
def svg_graph(data,path):
    events={e['id']:e for e in data['events']}
    states={t['occurrence']:t['status'] for t in data['swaps']['targets']}
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="640" viewBox="0 0 960 640">',
         '<rect width="960" height="640" fill="#FFFFFF"/>']
    sx,sy=POSITIONS['A']
    for key,status in states.items():
        x,y=POSITIONS[key];locked=key in data['locked']
        color='#23986F' if status=='valid' else '#B4BDCD' if locked else '#D5A3AC'
        dash='' if status=='valid' else ' stroke-dasharray="5 7"'
        width='3' if status=='valid' else '1.5'
        out.append(f'<path d="M {sx-95} {sy} C {sx-225} {sy} {x+205} {y} {x+95} {y}" fill="none" stroke="{color}" stroke-width="{width}"{dash}/>')
    for key in ['C','B','D','E','F','G','H','A']:
        e=events[key];x,y=POSITIONS[key];selected=key=='A';valid=states.get(key)=='valid';locked=key in data['locked']
        stroke='#315DF5' if selected else '#67B498' if valid else '#B9C4D3' if locked else '#E6C5CD'
        fill='#F0F4FF' if selected else '#F7FCF9' if valid else '#FFFFFF'
        out.append(f'<g id="graph-node-{key}"><rect x="{x-95}" y="{y-49}" width="190" height="98" rx="15" fill="{fill}" stroke="{stroke}" stroke-width="{2 if selected else 1.2}"/>')
        out.append(f'<rect x="{x+77}" y="{y-30}" width="3" height="60" rx="1.5" fill="{YEAR_COLORS[e["year"]]}"/>')
        status='الحصة المختارة' if selected else 'مثبتة' if locked else 'يمكن التبديل' if valid else 'عرض السبب'
        color='#315DF5' if selected else '#73819A' if locked else '#187B59' if valid else '#A65C6C'
        timing='\u2066'+clock(e['start'])+'–'+clock(e['end'])+'\u2069 · '+data['rooms'][e['rooms'][0]]
        weeks='أسابيع فردية' if e['week_pattern']=='odd' else 'أسابيع زوجية' if e['week_pattern']=='even' else 'كل الأسابيع'
        for text,dy,size,col in [(e['label'],-17,16,'#202939'),(timing,5,11,'#627087'),(weeks,23,10,'#627087'),(status,42,12,color)]:
            out.append(f'<text x="{x}" y="{y+dy}" text-anchor="middle" direction="rtl" font-family="Noto Sans Arabic" font-size="{size}" fill="{col}">{escape(text)}</text>')
        out.append('</g>')
    out.append('</svg>')
    path.write_text('\n'.join(out)+'\n',encoding='utf-8')


def build():
    dest=ROOT/'assets';dest.mkdir(exist_ok=True)
    editor=make_editor();baseline=payload(editor)
    state=editor.state();request=Intent('swap','A','C',mode='time_only')
    good=editor.preview_intent(request,state.revision,state.input_revision)
    blocked=editor.preview_intent(Intent('swap','A','B'),state.revision,state.input_revision)
    good_view=preview_payload(editor,good);bad_view=preview_payload(editor,blocked)
    editor.commit_intent(request,state.revision,state.input_revision);after=payload(editor)
    other=make_editor();old=other.state()
    proposal=other.propose(Intent('swap','A','B'),old.revision,old.input_revision,seconds=6)
    if proposal.preview is None or not proposal.minimum_proven:
        raise RuntimeError('No proven minimum whole-pattern rearrangement for the design fixture: '+proposal.status)
    broad_view=preview_payload(other,proposal.preview)
    other.apply_proposal(proposal);broad_after=payload(other)
    data={'baseline':baseline,'validPreview':good_view,'blockedPreview':bad_view,'after':after,
          'broader':{'status':proposal.status,'minimum_proven':proposal.minimum_proven,
                     'requested':proposal.requested,'additional':proposal.additional,
                     'preview':broad_view,'after':broad_after}}
    (dest/'editing-evidence.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,default=json_default)+'\n')
    svg_graph(baseline,dest/'swap-neighborhood.svg')
    return data


if __name__=='__main__':build()
