#!/usr/bin/env python3
"""Build the simplified, native FigCraft proposal and a three-page review."""
import json
import subprocess
from pathlib import Path
from figcraft_api import Builder, HeadlessSession, ROOT, COLORS
from editing_artifacts import build as build_editing_artifacts, clock
from editing_frames import add as add_editing_frames

YEARS = ['السنة الأولى', 'السنة الثانية', 'السنة الثالثة', 'السنة الرابعة']
SETUP = [('المواد', '06-courses'), ('المدرسون', '07-professors'),
         ('القاعات', '08-rooms'), ('الأيام والساعات', '09-calendar')]


class SimpleDesign(Builder):
    def __init__(self, session):
        super().__init__(session)
        self.active = None
        self.hops = []
        self.tabs = []
        self.timed = []
        self.primary = ['01-students', '02-generate', '03-schedule']

    def link(self, node, dest, label):
        self.hops.append({'from': self.active, 'node': node, 'destination': dest, 'label': label})

    def button(self, parent, x, y, label, dest=None, variant='primary'):
        node = super().button(parent, x, y, label, None, variant)
        if dest:
            self.link(node, dest, label)
        return node

    def textlink(self, parent, x, y, w, label, dest, color='action'):
        node = self.layer(parent, x, y, w, 44, 'surface', name='Link / '+label, radius=8)
        self.text(node, 8, 7, w-16, label, 15, color, height=30)
        self.link(node, dest, label)
        return node

    def boot(self):
        self.cmd('file.new', name='G6 / Simple college scheduler')
        collection=self.cmd('variable.createCollection', name='G6 / Simple tokens', modes=['Light'])['id']
        for name, color in COLORS.items():
            self.variables[name]=self.cmd('variable.create', collection=collection,
                                         name='color/'+name, type='color', value=color)['id']
        board=self.cmd('frame.create', name='Components / implementation reference',
                       x=0, y=50000, width=760, height=220, props={'fill':COLORS['canvas']})['id']
        for i, (variant,bg,fg,stroke) in enumerate([
            ('primary','action','surface',None), ('secondary','surface','ink','border'),
            ('disabled','border','secondary',None)]):
            b=self.layer(board, 24+i*244, 64, 180, 48, bg,
                         name='Button / '+variant, radius=10, stroke=stroke)
            label=self.text(b, 8, 7, 164, 'إجراء', 16, fg, 'center', 34)
            component=self.cmd('component.create', ids=[b])['id']
            self.cmd('component.addProperty', id=component, name='Label', type='text', layer=label, default='إجراء')
            self.buttons[variant]=component
            self.text(board, 24+i*244, 130, 180, variant, 13, 'secondary', 'left')

    def frame(self, key, step=None, title=None, sub=None, setup=False, width=1280, height=900):
        idx=len(self.frames)
        n=self.cmd('frame.create', name=key, x=0, y=idx*1000,
                   width=width, height=height, props={'fill':COLORS['canvas'],'clip':True})['id']
        self.frames[key]=n
        self.active=key
        self.layer(n, 0, 0, width, 80, 'surface', name='Header')
        self.text(n, width-220, 13, 100, 'جدول', 27, bold=True, height=50)
        if setup:
            self.textlink(n, 120, 18, 180, 'العودة للطلاب', '01-students')
        else:
            self.textlink(n, 120, 18, 110, 'الإعدادات', '06-courses', 'secondary')
        if step:
            labels=['الطلاب','إنشاء الجدول','تعديل وتحميل']
            for i, label in enumerate(labels):
                xx=870-i*320
                color='action' if step==i+1 else 'secondary'
                self.text(n, xx, 105, 190, f'{i+1}  {label}', 17, color, 'center', 44, step==i+1)
                if i<2:
                    self.layer(n, xx-72, 126, 64, 1, 'border', name='Step connector')
        if title:
            self.text(n, 120, 177 if step else 112, width-240, title, 32, bold=True, height=62)
        if sub:
            self.text(n, 120, 240 if step else 174, width-240, sub, 16, 'secondary', height=36)
        self.text(n, 120, height-42, width-240, 'نموذج واجهة · البيانات المعروضة أمثلة فقط', 11, 'secondary', height=28)
        return n

    def years(self, parent, y, selected=0, prefix=None, counts=False):
        for i, label in enumerate(YEARS):
            x=912-i*264
            node=self.layer(parent, x, y, 248, 60, 'subtle' if i==selected else 'surface',
                            name='Year / '+label, radius=10, stroke='action' if i==selected else 'border')
            self.text(node, 12, 12, 224, label+(' · 3 طلاب' if counts else ''), 16,
                      'action' if i==selected else 'ink', 'center', 36, i==selected)
            if prefix:
                target=prefix[i]
                if target != self.active:
                    self.link(node, target, label)

    def field(self, parent, x, y, w, label, value):
        self.text(parent, x, y, w, label, 15, 'secondary', height=30)
        box=self.layer(parent, x, y+34, w, 48, 'surface', radius=8,
                       stroke='controlBorder', name='Input / '+label)
        self.text(box, 12, 7, w-24, value, 16, height=34)
        return box

    def rows(self, parent, x, y, columns, rows, rowheight=72, editable=False):
        width=sum(w for _,w in columns)
        table=self.layer(parent, x, y, width, 48+len(rows)*rowheight,
                         'surface', name='Readable table', radius=12, stroke='border')
        self.layer(table, 1, 1, width-2, 47, 'canvas', name='Table header')
        edge=width
        for name,w in columns:
            edge-=w
            self.text(table, edge+16, 8, w-32, name, 14, 'secondary', height=32)
        for i, values in enumerate(rows):
            top=48+i*rowheight
            if i:
                self.layer(table, 16, top, width-32, 1, 'border', name='Row divider')
            edge=width
            for value,(_,w) in zip(values,columns):
                edge-=w
                if editable:
                    self.layer(table, edge+10, top+10, w-20, rowheight-20, 'surface',
                               name='Editable value / '+value, radius=6, stroke='controlBorder')
                self.text(table, edge+16, top+16, w-32, value, 16, height=rowheight-20)
        return table

    def students(self, empty=False):
        key='14-empty-students' if empty else '01-students'
        n=self.frame(key, 1, 'أضف الطلاب', 'اختر السنة، ثم أضف طالباً أو ارفع ملف CSV.')
        self.years(n, 304, counts=not empty)
        if empty:
            panel=self.card(n, 120, 396, 1040, 338)
            self.text(panel, 24, 48, 992, 'لم تضف طلاباً لهذه السنة بعد', 23, align='center', bold=True, height=50)
            self.text(panel, 24, 108, 992, 'كل ما تحتاجه: المواد المسجلة لكل طالب.', 17, 'secondary', 'center')
            self.button(panel, 540, 194, 'إضافة طالب', '04-add-student')
            self.button(panel, 320, 194, 'رفع ملف CSV', '05-csv-preview', 'secondary')
            self.button(n, 120, 790, 'التالي', variant='disabled')
        else:
            self.button(n, 980, 396, 'إضافة طالب', '04-add-student', 'secondary')
            self.button(n, 780, 396, 'رفع ملف CSV', '05-csv-preview', 'secondary')
            self.rows(n, 120, 468, [('الطالب',200),('المواد المسجلة',840)],
                      [('طالب 1','برمجة 1، رياضيات 1'),('طالب 2','برمجة 1'),('طالب 3','برمجة 1، رياضيات 1')], 72)
            self.button(n, 120, 790, 'التالي', '02-generate')
        return n

    def generation(self, key='02-generate', missing=False):
        n=self.frame(key, 2, 'أنشئ الجدول', 'سنرتب الجداول لكل السنوات الأربع معاً.')
        c=self.card(n, 280, 318, 720, 414)
        self.field(c, 392, 40, 288, 'الفصل الدراسي', 'الفصل الأول')
        self.field(c, 40, 40, 312, 'نوع الجدول', 'محاضرات وسكاشن ومعامل')
        if missing:
            err=self.layer(c, 40, 158, 640, 120, 'errorSurface', radius=8, name='Missing duration')
            self.text(err, 16, 12, 608, 'أدخل مدة معمل برمجة 1 أولاً.', 18, 'error', height=42)
            self.textlink(err, 400, 64, 224, 'تحديد المدة', '06-courses', 'error')
            self.button(c, 270, 318, 'إنشاء الجدول', variant='disabled')
        else:
            self.text(c, 40, 177, 640, 'يشمل طلاب السنوات الأولى والثانية والثالثة والرابعة.', 18,
                      align='center', height=50)
            self.text(c, 40, 236, 640, 'باستخدام المواد والمدرسين والقاعات التي أدخلتها.', 16,
                      'secondary', 'center', height=40)
            self.button(c, 270, 318, 'إنشاء الجدول', '11-running')
        self.textlink(n, 120, 786, 180, 'رجوع للطلاب', '01-students', 'secondary')
        return n

    def result(self, year=0):
        keys=['03-schedule','13-schedule-year2','13-schedule-year3','13-schedule-year4']
        n=self.frame(keys[year], 3, 'راجع الجدول ثم حمّله', 'عرض يوم من المثال · يمكنك تعديل المواعيد قبل التحميل.')
        self.years(n, 304, year, keys)
        snapshot=self.editing_data['baseline']
        schedules=[]
        for e in snapshot['events']:
            if year+1 not in e['years']:continue
            schedules.append(('السبت',clock(e['start'])+'–'+clock(e['end']),
                              e['label']+' · '+e['kind']+(' · فردي' if e['week_pattern']=='odd' else ' · زوجي' if e['week_pattern']=='even' else ''),
                              '، '.join(snapshot['professors'][p] for p in e['professors']),
                              ' + '.join(snapshot['rooms'][r] for r in e['rooms'])))
        self.rows(n, 120, 402, [('اليوم',132),('الوقت',184),('المادة',356),('المدرس',184),('المكان',184)], schedules, 78)
        self.button(n, 120, 790, 'تحميل الجدول', '10-download')
        self.button(n, 320, 790, 'تعديل الجدول', '17-edit-calendar', 'secondary')
        self.textlink(n, 920, 790, 240, 'تعديل البيانات', '01-students', 'secondary')
        return n

    def modal(self, key, step, title, w=720, h=570):
        n=self.frame(key, step)
        veil=self.layer(n, 0, 80, 1280, 820, '#202939', name='Dialog backdrop')
        self.set(veil, opacity=.12)
        box=self.layer(n, (1280-w)/2, (900-h)/2, w, h, 'surface', name=title, radius=16, stroke='border')
        self.text(box, 32, 24, w-64, title, 27, bold=True, height=60)
        return n,box

    def checkbox(self, parent, x, y, w, label, checked=False):
        cell=self.layer(parent, x, y, w, 60, 'subtle' if checked else 'surface',
                        name='Course choice / '+label, radius=8, stroke='border')
        square=self.layer(cell, w-44, 18, 24, 24, 'action' if checked else 'surface', radius=4, stroke='action' if checked else 'border')
        if checked:
            self.text(square, 0, -3, 24, '✓', 18, 'surface', 'center', 30)
        self.text(cell, 20, 13, w-80, label, 17, height=40)
        return cell

    def add_student(self):
        keys=['04-add-student','04-selected-first','04-selected-two']
        for state,key in enumerate(keys):
            _,box=self.modal(key, 1, 'إضافة طالب · السنة الأولى')
            self.text(box, 32, 92, 656, 'حدد المواد المسجلة لهذا الطالب فقط.', 17, 'secondary')
            for i,label in enumerate(['برمجة 1','رياضيات 1','قواعد بيانات']):
                choice=self.checkbox(box, 32, 158+i*78, 656, label, state>i)
                if state==0 and i==0:
                    self.link(choice,keys[1],'اختيار برمجة 1')
                if state==1 and i==1:
                    self.link(choice,keys[2],'اختيار رياضيات 1')
            if state:
                self.button(box, 508, 478, 'حفظ الطالب', '01-students')
            else:
                self.button(box, 508, 478, 'حفظ الطالب', variant='disabled')
            self.button(box, 308, 478, 'إلغاء', '01-students', 'secondary')

    def csv(self):
        _,box=self.modal('05-csv-preview', 1, 'إضافة طلاب من ملف', h=570)
        self.text(box, 32, 94, 656, 'السنة الأولى · كل صف في الملف يمثل طالباً واحداً.', 17, 'secondary')
        file=self.layer(box, 32, 142, 656, 48, 'canvas', name='Selected CSV', radius=8, stroke='border')
        self.text(file, 20, 7, 616, 'students-year-1.csv', 16, align='left', height=36)
        self.rows(box, 32, 216, [('الصف',92),('المواد',564)],
                  [('1','C001 | C002'),('2','C001'),('3','C001 | C002')], 48)
        self.text(box, 32, 422, 656, 'ستضاف 3 سجلات. أسماء الطلاب غير مطلوبة.', 16, 'secondary')
        self.button(box, 508, 478, 'إضافة الطلاب', '01-students')
        self.button(box, 308, 478, 'إلغاء', '01-students', 'secondary')

    def setup_header(self, key, selected):
        n=self.frame(key, title='إعدادات الجدول', setup=True,
                     sub='أدخل هذه البيانات يدوياً، ثم استخدمها عند إنشاء الجداول.')
        for i,(label,target) in enumerate(SETUP):
            tab=self.layer(n, 912-i*264, 236, 248, 56, 'subtle' if i==selected else 'surface',
                           name='Setup tab / '+label, radius=10, stroke='action' if i==selected else 'border')
            self.text(tab, 12, 10, 224, label, 17, 'action' if i==selected else 'ink', 'center', 38)
            if key!=target:
                self.link(tab,target,label)
        return n

    def courses(self):
        n=self.setup_header('06-courses',0)
        c=self.card(n, 120, 328, 1040, 452)
        self.field(c, 584, 24, 420, 'اسم المادة', 'برمجة 1')
        self.text(c, 32, 66, 480, 'رمز الملف: C001', 15, 'secondary', 'left')
        self.text(c, 32, 136, 976, 'حدد تفاصيل كل جزء من المادة', 20, bold=True, height=42)
        columns=[('الجزء',220),('المدة بالدقائق',180),('مرات في الأسبوع',256),('المدرس المعيّن',320)]
        self.rows(c, 32, 192, columns,
                  [('محاضرة','120','2','مدرس أ'),
                   ('معمل','60','1','مدرس ب')], 66, editable=True)
        self.text(c, 32, 384, 976, '+ إضافة محاضرة أو سكشن أو معمل أو امتحان', 16, 'action')
        self.button(n, 120, 798, 'حفظ والعودة', '02-generate')
        self.text(n, 520, 800, 640, 'المدرس والتكرار والمدة تحددهم أنت لكل جزء.', 16, 'secondary')

    def professors(self):
        n=self.setup_header('07-professors',1)
        c=self.card(n, 120, 328, 1040, 452)
        self.field(c, 584, 24, 420, 'اسم المدرس', 'مدرس أ')
        self.text(c, 32, 142, 976, 'أوقات إتاحته', 20, bold=True)
        self.rows(c, 32, 198, [('الأيام',456),('من',260),('إلى',260)],
                  [('السبت إلى الخميس','09:00','17:00')], 72, editable=True)
        self.text(c, 32, 352, 976, '+ إضافة فترة إتاحة', 16, 'action')
        self.button(n, 120, 798, 'حفظ والعودة', '02-generate')

    def rooms(self):
        n=self.setup_header('08-rooms',2)
        c=self.card(n, 120, 328, 1040, 452)
        self.field(c, 680, 24, 324, 'اسم القاعة أو المعمل', 'معمل 1')
        self.field(c, 344, 24, 300, 'النوع', 'معمل حاسبات')
        self.field(c, 32, 24, 276, 'السعة', '30 طالباً')
        self.text(c, 32, 142, 976, 'أوقات إتاحة المكان', 20, bold=True)
        self.rows(c, 32, 198, [('الأيام',456),('من',260),('إلى',260)],
                  [('السبت إلى الخميس','09:00','17:00')], 72, editable=True)
        self.text(c, 32, 352, 976, 'بيانات الموقع: مبنى / طابق عند الحاجة.', 15, 'secondary')
        self.button(n, 120, 798, 'حفظ والعودة', '02-generate')

    def calendar(self):
        n=self.setup_header('09-calendar',3)
        c=self.card(n, 120, 328, 1040, 452)
        self.field(c, 680, 24, 324, 'الفصل الدراسي', 'الفصل الأول')
        self.field(c, 344, 24, 300, 'من تاريخ', '01 / 10 / 2026')
        self.field(c, 32, 24, 276, 'إلى تاريخ', '31 / 12 / 2026')
        self.text(c, 32, 142, 976, 'الأيام والساعات المسموح بها', 20, bold=True)
        self.rows(c, 32, 198, [('الأيام',456),('من',260),('إلى',260)],
                  [('السبت إلى الخميس','09:00','17:00')], 72, editable=True)
        self.text(c, 32, 352, 976, 'يمكن تحديد أيام الامتحانات والاستثناءات داخل الفصل.', 15, 'secondary')
        self.button(n, 120, 798, 'حفظ والعودة', '02-generate')

    def download(self):
        _,box=self.modal('10-download', 3, 'تحميل الجدول', h=570)
        self.field(box, 32, 100, 656, 'السنوات المطلوبة', 'كل السنوات')
        self.text(box, 32, 218, 656, 'اختر نوع الملف', 17, 'secondary')
        for i,label in enumerate(['PDF','PNG','JPG']):
            x=480-i*224
            choice=self.layer(box, x, 268, 208, 64, 'subtle' if i==0 else 'surface',
                              name='Format / '+label, radius=10, stroke='action' if i==0 else 'border')
            self.text(choice, 12, 14, 184, label, 21, 'action' if i==0 else 'ink', 'center', 40, True)
        self.text(box, 32, 378, 656, 'سيحتوي الملف على الجداول فقط.', 16, 'secondary')
        self.button(box, 508, 478, 'تحميل', '16-download-done')
        self.button(box, 308, 478, 'إلغاء', '03-schedule', 'secondary')

    def running(self):
        n,box=self.modal('11-running', 2, 'جارٍ إنشاء الجدول…', w=640, h=360)
        self.text(box, 32, 114, 576, 'نرتب مواعيد السنوات الأربع دون تداخل.', 19, 'secondary', 'center', 54)
        self.button(box, 230, 242, 'إلغاء', '02-generate', 'secondary')
        self.timed.append({'from':'11-running','to':'03-schedule','ms':1300})

    def done(self):
        _,box=self.modal('16-download-done', 3, 'الملف جاهز للتحميل', w=640,h=350)
        self.text(box, 32, 112, 576, 'جداول السنوات الأربع · PDF', 20, align='center', height=60)
        self.button(box, 230, 236, 'العودة للجدول', '03-schedule')

    def mobile(self):
        key='15-mobile-schedule'
        idx=len(self.frames)
        n=self.cmd('frame.create', name=key, x=0, y=idx*1000, width=390, height=844,
                   props={'fill':COLORS['canvas'],'clip':True})['id']
        self.frames[key]=n;self.active=key
        self.layer(n,0,0,390,80,'surface',name='Mobile header')
        self.text(n,20,14,350,'جدول',26,bold=True,height=50)
        self.text(n,20,114,350,'جدولك جاهز',29,bold=True,height=60)
        self.field(n,20,194,350,'السنة','السنة الأولى')
        for i,(time,course,where) in enumerate([
            ('09:00–11:00','برمجة 1 · محاضرة','مدرس أ · قاعة 1'),
            ('11:00–12:00','برمجة 1 · معمل','مدرس ب · معمل 1')]):
            c=self.card(n,20,316+i*154,350,132)
            self.text(c,16,10,318,'السبت · '+time,15,'secondary',height=34)
            self.text(c,16,48,318,course,19,bold=True,height=42)
            self.text(c,16,90,318,where,15,'secondary')
        self.button(n,190,672,'تحميل الجدول','10-download')
        self.text(n,20,786,350,'نموذج واجهة · بيانات تجريبية',11,'secondary')

    def save(self):
        for hop in self.hops:
            # Use explicit page-relative hit areas over the visible controls. Bounds
            # come from FigCraft, including nested dialog/component coordinates.
            source=self.frames[hop['from']]
            bounds=self.cmd('node.get',id=hop['node'])['absoluteBounds']
            root=self.cmd('node.get',id=source)['absoluteBounds']
            hotspot=self.layer(source,bounds['x']-root['x'],bounds['y']-root['y'],
                               bounds['width'],bounds['height'],'#FFFFFF00',
                               name='Hotspot / '+hop['label'])
            hop['visualNode']=hop['node']
            hop['node']=hotspot
            self.cmd('proto.interaction.add',id=hotspot,dest=self.frames[hop['destination']])
        for item in self.timed:
            self.cmd('proto.interaction.add',id=self.frames[item['from']],
                     trigger={'type':'afterDelay','ms':item['ms']},
                     action={'type':'navigate','dest':self.frames[item['to']]})
        self.cmd('proto.flow.add',start=self.frames['14-empty-students'],name='Students → Generate → Edit and download')
        self.cmd('proto.flow.add',start=self.frames['06-courses'],name='Manual setup')
        self.cmd('proto.flow.add',start=self.frames['17-edit-calendar'],name='Constrained editing and calculated swap graph')
        native=ROOT/'g6-timetabling.figcraft'
        self.cmd('file.save',path=str(native))
        self.cmd('variable.export',format='css',path=str(ROOT/'tokens.css'))
        for name,node in self.frames.items():
            self.cmd('file.export',ids=[node],format='png',path=str(ROOT/'previews'/f'{name}.png'))
        pdfs=[]
        for name in self.primary:
            p=ROOT/'.work'/f'{name}.pdf'
            self.cmd('file.export',ids=[self.frames[name]],format='pdf',path=str(p))
            pdfs.append(str(p))
        subprocess.run(['pdfunite',*pdfs,str(ROOT/'g6-ui-review.pdf')],check=True)
        editing_pdfs=[]
        for name in ['17-edit-calendar','18-swap-graph','19-swap-preview','20-swap-blocked','22-broader-preview']:
            p=ROOT/'.work'/f'{name}.pdf'
            self.cmd('file.export',ids=[self.frames[name]],format='pdf',path=str(p))
            editing_pdfs.append(str(p))
        subprocess.run(['pdfunite',*editing_pdfs,str(ROOT/'g6-editing-review.pdf')],check=True)
        manifest={
            'status':'simplified proposal; synthetic data; navigation-only prototype',
            'native':native.name,'primaryScreens':self.primary,'frames':self.frames,
            'components':self.buttons,'variables':len(self.variables),
            'links':self.hops,'timedTransitions':self.timed,
            'editingFrames':['17-edit-calendar','18-swap-graph','19-swap-preview','20-swap-blocked','21-edit-applied','22-broader-preview','23-broader-applied'],
            'editingEvidence':'assets/editing-evidence.json',
            'inputContract':{'studentFields':['registered_courses'],
                             'year':'selected list context','recordId':'generated metadata',
                             'professorAssignments':'setter only',
                             'durationAndFrequency':'manual, per course component'},
        }
        (ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        (ROOT/'tokens.json').write_text(json.dumps({
            'color':COLORS,'font':{'arabic':'Noto Sans Arabic','latin':'Noto Sans'},
            'spacing':[4,8,12,16,24,32,40], 'radius':{'control':10,'panel':12,'dialog':16},
            'viewport':{'desktop':[1280,900],'mobile':[390,844]},'controlHeight':48,
        },ensure_ascii=False,indent=2)+'\n')
        print('Saved native FigCraft, three-page PDF, and previews.',flush=True)


def main():
    (ROOT/'previews').mkdir(exist_ok=True)
    with HeadlessSession() as session:
        b=SimpleDesign(session); b.editing_data=build_editing_artifacts(); b.boot()
        b.students(); b.generation(); b.result()
        for fn in [b.add_student,b.csv,b.courses,b.professors,b.rooms,b.calendar,
                   b.download,b.running,b.done,b.mobile]:
            fn()
        b.generation('12-fix-input',missing=True)
        b.students(empty=True)
        for year in [1,2,3]: b.result(year)
        add_editing_frames(b,b.editing_data)
        b.save()


if __name__=='__main__':
    main()
