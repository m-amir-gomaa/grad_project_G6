"""Editable FigCraft frames backed by engine-calculated synthetic previews."""
from pathlib import Path
from editing_artifacts import clock,POSITIONS,YEAR_COLORS
from figcraft_api import ROOT


def time_room(row,data):
    return clock(row['start'])+'–'+clock(row['end'])+' · '+ ' + '.join(data['rooms'][r] for r in row['rooms'])


def shell(b,key,title,sub):
    n=b.frame(key,3,title,sub,width=1440,height=1000)
    b.textlink(n,32,244,180,'الجدول','17-edit-calendar')
    b.textlink(n,228,244,220,'بدائل التبديل','18-swap-graph')
    return n


def panel(b,n,data,kind='select'):
    rows={e['id']:e for e in data['baseline']['events']};a=rows['A']
    c=b.card(n,1056,300,352,640)
    b.text(c,20,16,312,'الحصة المختارة',13,'secondary')
    b.text(c,20,49,312,a['label'],24,bold=True,height=50)
    b.text(c,20,101,312,'محاضرة · 120 دقيقة · مدرس أ',14,'secondary')
    b.text(c,20,140,312,time_room(a,data['baseline']),14)
    b.field(c,20,190,312,'أسلوب التبديل','المواعيد فقط · النمط الأسبوعي')
    if kind=='valid':
        notice=b.layer(c,20,312,312,190,'successSurface',radius=10,stroke='border',name='Valid atomic edit')
        b.text(notice,14,10,284,'يمكن تطبيق هذا التبديل',17,'success',bold=True)
        b.text(notice,14,62,284,'برمجة 1: 13:00–15:00\nقواعد بيانات: 09:00–10:30',15,'success',height=84)
        b.text(notice,14,151,284,f"نمطا حصتين · {data['validPreview']['affected_occurrences']} تكرارات.",13,'success')
        b.button(c,152,544,'تطبيق التبديل','21-edit-applied')
    elif kind=='blocked':
        notice=b.layer(c,20,312,312,190,'errorSurface',radius=10,stroke='border',name='Blocked cross-year professor conflict')
        b.text(notice,14,10,284,'التبديل غير متاح',17,'error',bold=True)
        b.text(notice,14,60,284,'مدرس أ لديه رياضيات حاسوبية\nمن 12:00 إلى 13:00.',15,'error',height=84)
        b.text(notice,14,151,284,'لم تتغير أي حصة.',13,'error')
        b.button(c,152,544,'اقتراح ترتيب أوسع','22-broader-preview')
    else:
        notice=b.layer(c,20,312,312,190,'canvas',radius=10,stroke='border',name='Choose a calculated partner')
        b.text(notice,14,24,284,'اختر نمط حصة بديلة.',20,bold=True,height=50)
        b.text(notice,14,90,284,'الأخضر: تبديل تم فحصه.\nالأحمر: اضغط لمعرفة السبب.',14,'secondary',height=82)
        b.button(c,152,544,'تطبيق التبديل',variant='disabled')
    b.text(c,20,600,312,'كل التكرارات · نفس الطلاب والمدرسين.',12,'secondary')
    return c


def board(b,n,data,after=False):
    snapshot=data['after'] if after else data['baseline']
    c=b.card(n,32,300,1000,640)
    states={r['occurrence']:r['status'] for r in snapshot['swaps']['targets']}
    for i in range(11):
        x=20+(10-i)*86
        b.text(c,x-18,24,46,str(9+i)+':00',11,'secondary','center',30)
        if i<10:b.layer(c,x,76,1,472,'border',name='Time guide')
    tint={1:'#F0F2FD',2:'#F5F0FC',3:'#EDF7F5',4:'#FBF5E9'}
    for year in range(1,5):
        y=80+(year-1)*118
        b.layer(c,20,y,860,1,'border',name='Year guide')
        b.text(c,898,y+20,88,['الأولى','الثانية','الثالثة','الرابعة'][year-1],14,'secondary')
        for e in snapshot['events']:
            if e['year']!=year:continue
            x=20+(600-e['end'])/600*860;w=e['duration']/600*860
            stroke='action' if e['id']=='A' else 'success' if states.get(e['id'])=='valid' else 'border'
            card=b.layer(c,x,y+14,w,88,tint[year],radius=9,stroke=stroke,name='Occurrence / '+e['id'])
            b.set(card,clip=True)
            label=b.text(card,7,8,w-14,e['label'],12,height=50,bold=True)
            b.set(label,maxLines=2)
            if e['week_pattern']!='all':
                b.text(card,7,46,w-14,'فردي' if e['week_pattern']=='odd' else 'زوجي',9,'secondary',height=16)
            b.text(card,7,64,w-14,clock(e['start'])+'–'+clock(e['end']),10,'secondary',height=22)
            if not after and e['id']=='C':b.link(card,'19-swap-preview','معاينة تبديل قواعد البيانات')
            if not after and e['id']=='B':b.link(card,'20-swap-blocked','سبب تعذر تبديل هياكل البيانات')
    b.text(c,20,590,960,'العرض يجمع الفردي والزوجي؛ التعديل يشمل كل التكرارات مع الحفاظ على أسابيع كل حصة.',12,'secondary')
    return c


def add(b,data):
    n=shell(b,'17-edit-calendar','راجع الجدول وعدّل ما تحتاجه','التعديل يشمل كل التكرارات، مع الحفاظ على الأسابيع الفردية والزوجية.')
    board(b,n,data);panel(b,n,data)
    n=shell(b,'18-swap-graph','ما الذي يمكن تبديله؟','بديل متاح واحد في هذا المثال · كل السنوات تدخل في الحساب.')
    b.card(n,32,300,1000,640)
    imported=b.cmd('file.import',path=str(ROOT/'assets'/'swap-neighborhood.svg'))
    node=imported['id'];b.cmd('node.reparent',ids=[node],parent=n)
    b.set(node,x=52,y=300,name='Editable calculated swap graph')
    for key,dest,label in [('C','19-swap-preview','اختيار قواعد البيانات'),('B','20-swap-blocked','عرض سبب هياكل البيانات')]:
        x,y=POSITIONS[key]
        target=b.layer(n,52+x-95,300+y-49,190,98,'#FFFFFF00',name='Graph choice / '+key)
        b.link(target,dest,label)
    panel(b,n,data)
    n=shell(b,'19-swap-preview','راجع الحصتين قبل التطبيق','تحافظ كل حصة على مدتها ومدرسها وطلابها. الحصص الأخرى ثابتة.')
    outer=b.card(n,32,300,1000,640)
    baseline={e['id']:e for e in data['baseline']['events']}
    proposed={e['id']:e for e in data['after']['events']}
    for i,key in enumerate(['A','C']):
        old=baseline[key];new=proposed[key]
        card=b.card(outer,32,40+i*248,936,216)
        b.text(card,24,14,888,old['label'],23,bold=True,height=48)
        b.text(card,24,67,888,str(old['duration'])+' دقيقة · نفس المدرس والطلاب',14,'secondary')
        b.text(card,492,115,420,'الآن',13,'secondary')
        b.text(card,492,150,420,time_room(old,data['baseline']),18,height=48)
        newbox=b.layer(card,24,108,432,88,'successSurface',radius=10)
        b.text(newbox,16,7,400,'بعد التبديل',13,'success')
        b.text(newbox,16,40,400,time_room(new,data['baseline']),18,'success',height=42)
    b.text(outer,32,558,936,f"نمطا حصتين يتغيران · {data['validPreview']['affected_occurrences']} مواعيد في الفصل · جميع القيود مستوفاة.",16,'success')
    panel(b,n,data,'valid')
    n=shell(b,'20-swap-blocked','هذا البديل يتعارض مع حصة أخرى','السبب يظهر لك قبل أن يتغير أي موعد.')
    c=b.card(n,32,300,1000,640)
    b.text(c,32,28,936,'مدرس أ مرتبط بحصتين في الوقت نفسه',23,bold=True,height=50)
    b.text(c,32,94,936,'التبديل المقترح ينقل برمجة 1 إلى 11:00–13:00.',17,'secondary')
    for x,label in [(48,'13:00'),(468,'12:00'),(888,'11:00')]:b.text(c,x,180,64,label,14,'secondary','center')
    a=b.layer(c,64,238,840,86,'subtle',radius=10,name='Proposed Programming 11–13')
    b.text(a,20,18,800,'برمجة 1 · موعد مقترح · السنة الأولى',20,'action',height=48)
    b.layer(c,64,238,420,86,'errorSurface',name='Actual conflicting interval 12–13',radius=10)
    b.text(c,80,264,380,'تعارض من 12:00 إلى 13:00',16,'error')
    e=b.layer(c,64,372,420,86,'errorSurface',radius=10,name='Other year class 12–13')
    b.text(e,16,12,388,'رياضيات حاسوبية · السنة الثانية',17,'error',height=56)
    b.text(c,32,520,936,'يشمل الفحص السنوات الأربع، حتى عندما تعرض جدول سنة واحدة.',16,'secondary')
    panel(b,n,data,'blocked')
    n=shell(b,'21-edit-applied','تم التبديل بنجاح','يمكنك المتابعة في التعديل أو التراجع أو تحميل الجدول.')
    board(b,n,data,after=True)
    p=b.card(n,1056,300,352,640)
    b.text(p,20,32,312,'التعديلات محفوظة',24,bold=True,height=50)
    b.text(p,20,110,312,'برمجة 1: 13:00–15:00\nقواعد بيانات: 09:00–10:30',16,height=90)
    b.text(p,20,242,312,'فُحصت جميع القيود من جديد.\nلم تتغير بقية الحصص.',16,'success',height=90)
    b.button(p,152,444,'تراجع عن التبديل','17-edit-calendar','secondary')
    b.button(p,152,544,'تحميل الجدول','10-download')

    # An explicitly requested broader rearrangement, calculated by CP-SAT.
    n=shell(b,'22-broader-preview','راجع الترتيب الأوسع','طلبك محفوظ. راجع الأنماط الإضافية قبل تطبيق أي تغيير.')
    broad=data['broader'];after={e['id']:e for e in broad['after']['events']}
    before={e['id']:e for e in data['baseline']['events']}
    outer=b.card(n,32,300,1000,640)
    changed=list(broad['requested'])+list(broad['additional'])
    for i,key in enumerate(changed):
        old,new=before[key],after[key];extra=key in broad['additional']
        row=b.layer(outer,32,32+i*172,936,152,'#F6F0FC' if extra else 'canvas',radius=10,stroke='border')
        b.text(row,20,12,896,old['label']+(' · تغيير إضافي' if extra else ' · طلبك'),20,bold=True,height=44)
        b.text(row,490,69,426,'من: '+time_room(old,data['baseline']),16,'secondary',height=40)
        b.text(row,20,69,440,'إلى: '+time_room(new,data['baseline']),16,'success',height=40)
        b.text(row,20,111,896,f"كل التكرارات: {new['occurrence_count']} · {new['duration']} دقيقة · نفس المدرس والطلاب",13,'secondary')
    b.text(outer,32,570,936,f"أنماط متغيرة: {len(changed)} · مواعيد متأثرة: {broad['preview']['affected_occurrences']} · الحصص المثبتة ثابتة.",15,'success')
    p=b.card(n,1056,300,352,640)
    b.text(p,20,26,312,'اقتراح مستوفٍ للقيود',23,bold=True,height=60)
    b.text(p,20,116,312,'يتطلب طلبك تعديل نمط حصة\nإضافية. كل التغييرات ظاهرة هنا.',17,height=96)
    b.text(p,20,246,312,'أقل عدد تغييرات إضافية\nضمن خيارات البحث.',16,'success',height=84)
    b.text(p,20,368,312,'لن يتغير أي موعد حتى التطبيق.',14,'secondary')
    b.button(p,152,484,'إلغاء الاقتراح','20-swap-blocked','secondary')
    b.button(p,152,554,'تطبيق كل التغييرات','23-broader-applied')
    n=shell(b,'23-broader-applied','تم تطبيق الترتيب الأوسع','تغيرت الأنماط كاملة. يمكنك التراجع عن الاقتراح كله بخطوة واحدة.')
    board(b,n,{'baseline':data['baseline'],'after':broad['after']},after=True)
    p=b.card(n,1056,300,352,640)
    b.text(p,20,32,312,'التعديلات محفوظة',24,bold=True,height=60)
    b.text(p,20,126,312,f"{len(changed)} أنماط أسبوعية\n{broad['preview']['affected_occurrences']} مواعيد في الفصل\nجميع القيود مستوفاة.",18,'success',height=150)
    b.text(p,20,320,312,'الحصص المثبتة لم تتحرك.',16,'secondary')
    b.button(p,152,464,'تراجع عن الترتيب','17-edit-calendar','secondary')
    b.button(p,152,554,'تحميل الجدول','10-download')
