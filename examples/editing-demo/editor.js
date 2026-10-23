'use strict';
const $=id=>document.getElementById(id);
const years={1:['#4D65D9','#f0f2fd'],2:['#875CC7','#f5f0fc'],3:['#25857B','#edf7f5'],4:['#BA8025','#fbf5e9']};
let data,selected='A',mode='time_only',view='calendar',action='swap',pending=null,loadSequence=0,proposalSequence=0;
const labels=['الأولى','الثانية','الثالثة','الرابعة'];
const weekName=e=>e.week_pattern==='odd'?'الأسابيع الفردية':e.week_pattern==='even'?'الأسابيع الزوجية':'كل الأسابيع';
const time=t=>`${String(9+Math.floor(t/60)).padStart(2,'0')}:${String(t%60).padStart(2,'0')}`;
const event=id=>data.events.find(e=>e.id===id);
const when=p=>`⁦${time(p.start)}–${time(p.end)}⁩ · ${p.rooms.map(r=>data.rooms[r]).join(' + ')}`;
function element(tag,text,className){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n;}
function toast(text,error=false){$('toast').textContent=text;$('toast').classList.toggle('error',error);$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,4500);}
async function api(path,body){const response=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const result=await response.json();if(!response.ok){const err=new Error(result.message||result.error);err.status=response.status;err.result=result;throw err;}return result;}
async function load(){const seq=++loadSequence;const result=await api(`/api/state?selected=${encodeURIComponent(selected)}&mode=${mode}`);if(seq!==loadSequence)return;const previousSource=data?.swaps.selected;data=result;if(previousSource!==selected){$('move-time').value=time(event(selected).start);}if(pending&&(pending.stamp.revision!==data.revision||pending.stamp.input_revision!==data.input_revision)){pending=null;proposalSequence++;}render();}
function target(id){return data.swaps.targets.find(t=>t.occurrence===id);}
function reasons(violations){return [...new Set(violations.map(v=>{
 const other=v.occurrences.filter(id=>id!==selected).map(id=>event(id)?.label||'موعد محفوظ').join('، ');
 const staff=data.professors[v.resource]||'المدرس';const room=data.rooms[v.resource]||'المكان';
 return ({professor_overlap:`${staff} لديه حصة أخرى: ${other}.`,student_overlap:`طلاب مشتركون مع ${other}.`,room_overlap:`${room} محجوزة لحصة أخرى: ${other}.`,locked:'هذه الحصة مثبتة؛ ألغِ تثبيتها أولاً.',calendar:'الحصة لا تتسع داخل الأيام والساعات المحددة.',professor_availability:`${staff} غير متاح في الموعد الجديد.`,room_availability:`${room} غير متاحة طوال مدة الحصة.`,room_closure:`${room} مغلقة في الموعد الجديد.`,room_type:'نوع المكان لا يناسب هذه الحصة.',room_group:'هذا الاختيار لا يناسب احتياجات المكان للحصة.',capacity:'سعة المكان لا تكفي جميع الطلاب.',student_coverage:'لم يتم تخصيص مكان لكل الطلاب.',start_domain:'الموعد خارج الخيارات المسموح بها.',duration:'مدة الحصة لا يجوز تغييرها أثناء التبديل.',coverage:'بعض الحصص المطلوبة غير مخصصة.',weekly_pattern:'التغيير لا يحافظ على النمط الأسبوعي في كل التكرارات.',weekly_target:'اختر موعداً محلياً صالحاً للنمط الأسبوعي.',requested_target:'الاقتراح لا يحقق التغيير الذي طلبته.'})[v.code]||'هذا التعديل يخالف أحد القيود المدخلة.';
 }))];}
function render(){
 $('calendar-view').hidden=view!=='calendar';$('graph-view').hidden=view!=='graph';
 $('calendar-tab').setAttribute('aria-pressed',view==='calendar');$('graph-tab').setAttribute('aria-pressed',view==='graph');
 $('swap-tab').setAttribute('aria-pressed',action==='swap');$('move-tab').setAttribute('aria-pressed',action==='move');
 $('swap-controls').hidden=action!=='swap';$('move-controls').hidden=action!=='move';
 $('undo').disabled=!data.can_undo;$('redo').disabled=!data.can_redo;
 const current=event(selected);$('selected-course').replaceChildren();for(const item of data.events){const o=element('option',item.label+' · '+item.kind);o.value=item.id;$('selected-course').append(o);}$('selected-course').value=selected;
 $('selected-detail').textContent=`${current.kind} · ${current.duration} دقيقة · ${current.professors.map(p=>data.professors[p]).join('، ')}`;
 $('selected-when').textContent=when(current);$('pattern-scope').textContent=`تكرارات في الفصل: ${current.occurrence_count} · ${weekName(current)}.`;$('pin').textContent=data.locked.includes(selected)?'إلغاء التثبيت':'تثبيت';
 $('move-room').replaceChildren();for(const group of current.room_options){const option=element('option',group.map(r=>data.rooms[r]).join(' + '));option.value=group.join('|');$('move-room').append(option);}$('move-room').value=current.rooms.join('|');
 $('health').textContent=data.valid?'الجدول مستوفٍ للقيود':'الجدول يحتاج تصحيحاً';
 $('time-axis').replaceChildren(...Array.from({length:11},(_,i)=>element('span',`${9+i}:00`)));
 $('calendar').replaceChildren();
 for(let year=1;year<=4;year++){
  const row=element('div',undefined,'year-row');row.append(element('div',labels[year-1],'year-name'));const lane=element('div',undefined,'lane');
  for(const item of data.events.filter(e=>e.year===year&&(e.week_pattern==='all'||e.week_pattern===$('week-view').value))){
   const b=element('button',undefined,'event');b.dataset.event=item.id;b.style.right=`${item.start/600*100}%`;b.style.width=`${item.duration/600*100}%`;b.style.setProperty('--year',years[year][0]);b.style.setProperty('--tint',years[year][1]);
   b.classList.toggle('is-selected',item.id===selected);const status=target(item.id)?.status;
   if(action==='swap'&&item.id!==selected)b.classList.add(data.locked.includes(item.id)?'is-locked':status==='valid'?'is-valid':status==='blocked'?'is-blocked':'is-neutral');
   b.title=`${item.label} · ${when(item)} · ${data.locked.includes(item.id)?'مثبتة':status==='valid'?'يمكن تبديلها':'انقر لفحص التبديل'}`;
   b.setAttribute('aria-label',b.title);b.append(element('span',item.label,'course'),element('span',`${time(item.start)}–${time(item.end)}`,'time'));
   b.onclick=()=>{if(item.id===selected)return;if(action==='swap')showSwap(item.id);else select(item.id);};
   b.ondblclick=()=>select(item.id);lane.append(b);
  }
  row.append(lane);$('calendar').append(row);
 }
 renderPreview();
}
function svg(tag,attrs={}){const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);return n;}
function renderGraph(){
 const g=$('graph');g.replaceChildren();
 const valid=data.swaps.targets.filter(t=>t.status==='valid').length;
 $('target-summary').textContent=`${valid} بديل متاح · ${data.swaps.targets.length} مفحوصة`;
 const source={x:690,y:310};const positions=[{x:220,y:90},{x:475,y:95},{x:195,y:265},{x:435,y:300},{x:205,y:465},{x:480,y:510},{x:745,y:520}];
 const sorted=[...data.swaps.targets].sort((a,b)=>'CBDEFGHA'.indexOf(a.occurrence)-'CBDEFGHA'.indexOf(b.occurrence));
 sorted.forEach((t,i)=>{
  const point=positions[i],locked=data.locked.includes(t.occurrence);const path=svg('path',{d:`M${source.x-80},${source.y} C${source.x-210},${source.y} ${point.x+170},${point.y} ${point.x+82},${point.y}`,class:`graph-link ${pending?.result.proposal_id&&pending.result.changed.includes(t.occurrence)?'proposed':locked?'locked':t.status==='valid'?'valid':''}`,'data-edge':t.occurrence});g.append(path);
 });
 function node(item,point,status){
  const broad=pending?.result.proposal_id&&pending.result.changed.includes(item.id);const extra=broad&&pending.result.additional.includes(item.id);
  const group=svg('g',{class:`node ${status} ${broad?'proposed':''} ${extra?'additional':''}`,'data-node':item.id,transform:`translate(${point.x},${point.y})`,role:'button',tabindex:'0','aria-label':`${item.label}، ${status==='selected'?'الحصة المختارة':status==='valid'?'يمكن التبديل':'عرض سبب التعذر'}`});
  group.append(svg('rect',{x:-95,y:-48,width:190,height:96,rx:14,class:'node-card'}));
  const strip=svg('rect',{x:77,y:-30,width:3,height:56,rx:2,fill:years[item.year][0]});group.append(strip);
  for(let [text,y,size,color,weight] of [[item.label,-11,15,'#202939',650],[`⁦${time(item.start)}–${time(item.end)}⁩ · ${data.rooms[item.rooms[0]]}`,15,10,'#69758b',400],
    [status==='selected'?'الحصة المختارة':status==='locked'?'مثبتة':status==='unchanged'?'بلا تغيير':status==='unchecked'?'لم يُفحص بعد':status==='valid'?'✓ يمكن التبديل':'× عرض السبب',36,11,status==='selected'?'#315df5':status==='valid'?'#187b59':['locked','unchanged','unchecked'].includes(status)?'#718096':'#a55a66',500]]){
    if(broad&&y===36){text=extra?'تغيير إضافي مقترح':'ضمن التبديل المطلوب';color='#7850b6';}
    const label=svg('text',{x:0,y,'text-anchor':'middle',direction:'rtl','font-size':size,fill:color,'font-weight':weight});label.textContent=text;group.append(label);
  }
  if(status!=='selected'){
   const activate=()=>showSwap(item.id);group.onclick=activate;group.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate();}};
  }
  g.append(group);
 }
 sorted.forEach((t,i)=>node(event(t.occurrence),positions[i],data.locked.includes(t.occurrence)?'locked':t.status));node(event(selected),source,'selected');
}
async function select(id){proposalSequence++;selected=id;pending=null;await load();}
async function propose(request){
 const serial=++proposalSequence;const chosen=selected;const stamp={revision:data.revision,input_revision:data.input_revision};pending=null;renderPreview();
 try{
  const q=await api('/api/preview',{...request,...stamp});
  if(serial!==proposalSequence||chosen!==selected||q.revision!==data.revision||q.input_revision!==data.input_revision)return;
  pending={request,stamp,result:q};renderPreview();
 }catch(err){if(serial!==proposalSequence)return;toast(err.status===409?'تغيّر الجدول؛ افحص التعديل من جديد.':'تعذر فحص هذا الاختيار.',true);pending=null;await load();}
}
async function showSwap(id){await propose({kind:'swap',pair:[selected,id],mode});}
function renderPreview(){
 renderGraph();
 const box=$('proposal');box.replaceChildren();$('apply').disabled=true;$('cancel').hidden=!pending;$('rearrange').hidden=!pending||pending.result.violations.length===0;$('rearrange').disabled=!!pending?.searching;$('rearrange').textContent=pending?.searching?'جارٍ البحث عن ترتيب…':'اقترح ترتيباً أوسع';
 if(!pending){box.className='proposal empty';box.append(element('span','اختر بديلاً لعرض النتيجة هنا.'));return;}
 const q=pending.result,valid=q.violations.length===0;
 box.className=`proposal ${valid?'good':'bad'}`;box.append(element('h3',valid?(q.changed.length?'يمكن تطبيق هذا التعديل':'لا يوجد تغيير في هذا الاختيار'):'لا يمكن تطبيق هذا الاختيار'));
 if(!valid){const ul=element('ul');for(const reason of reasons(q.violations))ul.append(element('li',reason));box.append(ul);return;}
 for(const id of q.changed){const before=event(id);const after=q.placements.find(row=>row[0]===id)[1];const row=element('div',undefined,'change');if(q.additional?.includes(id)){row.classList.add('additional');row.append(element('span','تغيير إضافي','additional-label'));}row.append(element('strong',before.label),element('span',when(before),'from'),element('span',when(after),'to'));box.append(row);}
 box.append(element('p',`أنماط متغيرة: ${q.changed.length} · مواعيد متأثرة: ${q.affected_occurrences}.`));
 if(q.proposal_id){box.classList.add('broader');box.append(element('p',`تغييرات إضافية: ${q.additional.length}. راجعها قبل التطبيق.`));box.append(element('p',q.minimum_proven?'أقل عدد تغييرات إضافية ضمن خيارات البحث.':'اقتراح صالح؛ لم يُثبت أنه الأقل تغييراً.','hint'));}$('apply').disabled=q.changed.length===0;
}
async function apply(){if(!pending)return;const p=pending;$('apply').disabled=true;
 try{await api('/api/apply',p.result.proposal_id?{proposal_id:p.result.proposal_id,...p.stamp}:{...p.request,...p.stamp});pending=null;await load();toast('تم التعديل. جميع القيود مستوفاة.');}
 catch(err){pending=null;await load();toast(err.status===409?'تغيّر الجدول. أعد فحص التعديل.':'رُفض التعديل ولم تتغير أي حصة.',true);}
}
async function broaden(){
 if(!pending||pending.searching||!pending.result.violations.length)return;
 const previous=pending,serial=++proposalSequence;pending={...previous,searching:true};renderPreview();
 try{
  const result=await api('/api/rearrange',{...previous.request,...previous.stamp});
  if(serial!==proposalSequence)return;
  if(result.proposal_id){pending={request:previous.request,stamp:previous.stamp,result};}
  else{pending=previous;toast(result.status==='UNKNOWN'?'انتهى وقت البحث؛ جرّب مرة أخرى.':'لم نجد ترتيباً ضمن الخيارات الحالية والحصص المثبتة.',true);}
  renderPreview();
 }catch(err){if(serial!==proposalSequence)return;pending=null;await load();toast(err.status===409?'تغيّر الجدول؛ أعد الحساب.':'تعذر إعداد اقتراح أوسع.',true);}
}
async function history(kind){try{await api('/api/apply',{kind,revision:data.revision,input_revision:data.input_revision});pending=null;await load();toast(kind==='undo'?'تم التراجع.':'تمت الإعادة.');}catch(err){toast('تعذر التغيير ضمن القيود الحالية.',true);}}
$('calendar-tab').onclick=()=>{view='calendar';render();};$('graph-tab').onclick=()=>{view='graph';action='swap';render();};
$('swap-tab').onclick=()=>{proposalSequence++;action='swap';pending=null;render();};$('move-tab').onclick=()=>{proposalSequence++;action='move';view='calendar';pending=null;render();};
$('swap-mode').onchange=async e=>{proposalSequence++;mode=e.target.value;pending=null;await load();};
$('pin').onclick=async()=>{await api('/api/lock',{ids:[selected],locked:!data.locked.includes(selected),revision:data.revision,input_revision:data.input_revision});pending=null;await load();};
$('move-controls').onsubmit=async e=>{e.preventDefault();const [h,m]=$('move-time').value.split(':').map(Number);await propose({kind:'move',moves:[{occurrence:selected,start:(h-9)*60+m,rooms:$('move-room').value.split('|')}]});};
for(const id of ['move-time','move-room'])$(id).oninput=()=>{proposalSequence++;pending=null;renderPreview();};
$('apply').onclick=apply;$('cancel').onclick=()=>{proposalSequence++;pending=null;renderPreview();};$('undo').onclick=()=>history('undo');$('redo').onclick=()=>history('redo');
$('rearrange').onclick=broaden;$('week-view').onchange=()=>render();
$('selected-course').onchange=e=>select(e.target.value);
load().catch(err=>toast('تعذر تحميل المثال المحلي.',true));
