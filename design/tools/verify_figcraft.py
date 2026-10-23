#!/usr/bin/env python3
"""Reopen the simplified FigCraft file and exercise observed prototype hotspots."""
import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session-helper',type=Path,required=True)
    args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('artcraft_session',args.session_helper)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    manifest=json.loads((ROOT/'manifest.json').read_text())
    frames=manifest['frames']; observed=[]
    with mod.Session('figcraft',ROOT/'.work') as s:
        def cmd(command,**params):
            return s.call('engine.execute',{'command':command,'params':params})

        def state(expected,hotspots=False,timeout=5):
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                current=s.call('ui.inspect').get('presenter')
                if current and current['current']==frames[expected] and (not hotspots or current['hotspots']):
                    return current
                time.sleep(.03)
            s.call('ui.screenshot',{'path':str(ROOT/'.work'/'verification-failure.png')})
            raise AssertionError(('Expected prototype state',expected,current))

        def click(source,label,dest):
            state(source,True)
            time.sleep(.12)
            before=state(source,True)
            item=next(v for v in manifest['links'] if v['from']==source and v['label']==label and v['destination']==dest)
            target=next(v for v in before['hotspots'] if v['id']==item['node'])
            x0,y0,x1,y1=target['rect'];at=[(x0+x1)/2,(y0+y1)/2]
            s.call('ui.input',{'events':[{'move':at},{'down':at}]})
            s.call('ui.inspect')
            time.sleep(.04)
            s.call('ui.input',{'events':[{'up':at}]})
            after=state(dest)
            time.sleep(.08)
            observed.append({'from':source,'to':dest,'action':label,'node':item['node'],
                             'observedRect':target['rect'],'verifiedFrame':after['current']})
            print('Verified',source,'→',dest,flush=True)

        cmd('file.open',path=str(ROOT/manifest['native']))
        cmd('view.set',zoom=.5,cx=640,cy=450)
        for name,node in frames.items():
            item=s.call('node.get',{'id':node,'depth':0})
            assert item['name']==name
            assert item['width']>0 and item['height']>0
        components=cmd('component.list')
        assert len(components)==len(manifest['components'])
        assert all(c['instances']>0 for c in components)
        doc=s.call('document.inspect',{'depth':1})
        assert doc.get('variables',0)>=manifest['variables']
        cmd('proto.presentOptions',scale='fit',deviceFrame=False)
        cmd('proto.present',start=frames['14-empty-students'])
        for hop in [
            ('14-empty-students','إضافة طالب','04-add-student'),
            ('04-add-student','اختيار برمجة 1','04-selected-first'),
            ('04-selected-first','اختيار رياضيات 1','04-selected-two'),
            ('04-selected-two','حفظ الطالب','01-students'),
            ('01-students','رفع ملف CSV','05-csv-preview'),
            ('05-csv-preview','إضافة الطلاب','01-students'),
            ('01-students','التالي','02-generate'),
            ('02-generate','إنشاء الجدول','11-running'),
        ]: click(*hop)
        after=state('03-schedule',timeout=5)
        observed.append({'from':'11-running','to':'03-schedule','trigger':'afterDelay',
                         'verifiedFrame':after['current'],'syntheticNavigationOnly':True})
        print('Verified simulated loading transition',flush=True)
        for hop in [
            ('03-schedule','السنة الثانية','13-schedule-year2'),
            ('13-schedule-year2','السنة الثالثة','13-schedule-year3'),
            ('13-schedule-year3','السنة الرابعة','13-schedule-year4'),
            ('13-schedule-year4','السنة الأولى','03-schedule'),
            ('03-schedule','تحميل الجدول','10-download'),
            ('10-download','تحميل','16-download-done'),
            ('16-download-done','العودة للجدول','03-schedule'),
            ('03-schedule','الإعدادات','06-courses'),
            ('06-courses','المدرسون','07-professors'),
            ('07-professors','القاعات','08-rooms'),
            ('08-rooms','الأيام والساعات','09-calendar'),
            ('09-calendar','حفظ والعودة','02-generate'),
            ('02-generate','إنشاء الجدول','11-running'),
            ('11-running','إلغاء','02-generate'),
        ]: click(*hop)
        cmd('proto.present',start=frames['12-fix-input'])
        click('12-fix-input','تحديد المدة','06-courses')
        click('06-courses','حفظ والعودة','02-generate')
        click('02-generate','إنشاء الجدول','11-running')
        state('03-schedule',timeout=5)
        for hop in [
            ('03-schedule','تعديل الجدول','17-edit-calendar'),
            ('17-edit-calendar','بدائل التبديل','18-swap-graph'),
            ('18-swap-graph','عرض سبب هياكل البيانات','20-swap-blocked'),
            ('20-swap-blocked','اقتراح ترتيب أوسع','22-broader-preview'),
            ('22-broader-preview','إلغاء الاقتراح','20-swap-blocked'),
            ('20-swap-blocked','اقتراح ترتيب أوسع','22-broader-preview'),
            ('22-broader-preview','تطبيق كل التغييرات','23-broader-applied'),
            ('23-broader-applied','تراجع عن الترتيب','17-edit-calendar'),
            ('17-edit-calendar','بدائل التبديل','18-swap-graph'),
            ('18-swap-graph','عرض سبب هياكل البيانات','20-swap-blocked'),
            ('20-swap-blocked','بدائل التبديل','18-swap-graph'),
            ('18-swap-graph','اختيار قواعد البيانات','19-swap-preview'),
            ('19-swap-preview','تطبيق التبديل','21-edit-applied'),
            ('21-edit-applied','تراجع عن التبديل','17-edit-calendar'),
            ('17-edit-calendar','معاينة تبديل قواعد البيانات','19-swap-preview'),
            ('19-swap-preview','تطبيق التبديل','21-edit-applied'),
            ('21-edit-applied','تحميل الجدول','10-download'),
        ]: click(*hop)
        s.call('ui.screenshot',{'path':str(ROOT/'.work'/'simplified-prototype.png')})
    result={
        'result':'passed','savedNativeReopened':True,
        'nativeSha256':hashlib.sha256((ROOT/manifest['native']).read_bytes()).hexdigest(),
        'primaryScreens':manifest['primaryScreens'],'supportingFrames':len(frames)-3,
        'components':len(components),'colorVariables':manifest['variables'],
        'observedTransitions':observed,
        'limits':['Native navigation prototype; editing calculations are supplied by the separate tested engine.',
                  'The local browser demonstrator executes actual previews/commits; native links navigate prepared states.',
                  'The three primary screens are the everyday flow; other frames are setup/dialog/state examples.',
                  'Native visual/navigation checks do not establish browser responsiveness or accessibility conformance.'],
    }
    (ROOT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__': main()
