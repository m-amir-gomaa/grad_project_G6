/* Uses the installed Playwright package and Chromium; no dependency download. */
const { chromium }=require('playwright');
const {spawn,execFileSync}=require('child_process');
const {createInterface}=require('readline');
const fs=require('fs');const path=require('path');const assert=require('assert/strict');
(async()=>{
 const root=path.resolve(__dirname,'../..');const work=path.join(root,'design/.work');fs.mkdirSync(work,{recursive:true});
 const python=process.env.EDITOR_PYTHON||(fs.existsSync(path.join(root,'.venv/bin/python'))?path.join(root,'.venv/bin/python'):'python3');
 const server=spawn(python,['-m','timetabling.editing_demo','--port','0'],{cwd:root,stdio:['ignore','pipe','pipe']});
 const url=await new Promise((resolve,reject)=>{createInterface({input:server.stdout}).once('line',resolve);server.once('error',reject);server.once('exit',code=>reject(new Error('Demo exited '+code)));});
 let browser;
 try{
  browser=await chromium.launch({headless:true,executablePath:execFileSync('which',['chromium'],{encoding:'utf8'}).trim(),args:['--no-sandbox']});
  const page=await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',error=>errors.push(String(error)));
  await page.goto(url);await page.locator('[data-event="A"]').waitFor();
  async function state(){return (await page.request.get(url+'/api/state')).json();}
  async function until(check){for(let n=0;n<70;n++){const s=await state();if(check(s))return s;await page.waitForTimeout(40);}throw new Error('State did not settle');}
  const initial=await state();assert(initial.valid);assert.equal(initial.events.length,8);assert.equal(initial.occurrences.length,21);
  assert.equal(await page.locator('[data-event="C"]').count(),0);
  assert.equal(await page.locator('[data-event="D"]').count(),1);
  await page.locator('#week-view').selectOption('even');
  assert.equal(await page.locator('[data-event="C"]').count(),1);
  assert.equal(await page.locator('[data-event="D"]').count(),0);
  await page.locator('#week-view').selectOption('odd');
  await page.locator('#graph-tab').click();await page.locator('#graph-view').waitFor({state:'visible'});
  assert.equal(await page.locator('#graph .node.valid').count(),initial.swaps.targets.filter(t=>t.status==='valid').length);
  await page.locator('[data-node="B"]').click();await page.locator('.proposal.bad').waitFor();assert(await page.locator('#apply').isDisabled());
  assert.match(await page.locator('#proposal').innerText(),/مدرس أ/);
  // Direct backend request remains rejected, even if a client ignores disabled UI.
  let rejected=await page.request.post(url+'/api/apply',{data:{kind:'swap',pair:['A','B'],mode:'time_only',revision:initial.revision,input_revision:initial.input_revision}});
  assert.equal(rejected.status(),422);assert.equal((await state()).revision,initial.revision);
  await page.locator('#rearrange').click();await page.locator('.proposal.broader').waitFor();
  assert.match(await page.locator('#proposal').innerText(),/تغيير إضافي/);
  assert.equal((await state()).revision,initial.revision);
  assert.equal(await page.locator('#graph .node.additional').count(),1);
  await page.screenshot({path:path.join(work,'editing-broader.png'),fullPage:true});
  await page.locator('#apply').click();const rearranged=await until(s=>s.revision===initial.revision+1);
  assert(rearranged.valid);assert.equal(rearranged.events.find(e=>e.id==='A').start,120);
  assert.equal(rearranged.events.find(e=>e.id==='B').start,0);
  assert.equal(rearranged.events.find(e=>e.id==='E').start,60);
  assert.deepEqual(rearranged.events.find(e=>e.id==='H'),initial.events.find(e=>e.id==='H'));
  assert.equal(rearranged.occurrences.filter((o,i)=>JSON.stringify(o)!==JSON.stringify(initial.occurrences[i])).length,9);
  await page.locator('#undo').click();const baseline=await until(s=>s.revision===rearranged.revision+1);
  assert.deepEqual(baseline.occurrences,initial.occurrences);
  // A stored broader proposal is invalidated by a later pin change.
  const broad=await(await page.request.post(url+'/api/rearrange',{data:{kind:'swap',pair:['A','B'],mode:'time_only',revision:baseline.revision,input_revision:baseline.input_revision}})).json();
  assert.equal(broad.status,'OPTIMAL');assert.deepEqual(broad.additional,['E']);assert.equal(broad.affected_occurrences,9);
  const pinned=await(await page.request.post(url+'/api/lock',{data:{ids:['C'],locked:true,revision:baseline.revision,input_revision:baseline.input_revision}})).json();
  const staleBroad=await page.request.post(url+'/api/apply',{data:{proposal_id:broad.proposal_id,revision:baseline.revision,input_revision:baseline.input_revision}});
  assert.equal(staleBroad.status(),409);assert.deepEqual((await state()).occurrences,initial.occurrences);
  const live=await state();await page.request.post(url+'/api/lock',{data:{ids:['C'],locked:false,revision:live.revision,input_revision:live.input_revision}});
  await page.reload();await page.locator('[data-event="A"]').waitFor();await page.locator('#graph-tab').click();
  const beforeDirect=await state();
  await page.locator('#selected-course').selectOption('D');
  await page.waitForFunction(()=>document.querySelector('#graph [data-node="B"]')?.classList.contains('unchanged'));
  await page.locator('[data-node="B"]').click();await page.locator('.proposal.good').waitFor();assert(await page.locator('#apply').isDisabled());
  assert.match(await page.locator('#proposal').innerText(),/لا يوجد تغيير/);
  await page.locator('#selected-course').selectOption('A');
  await page.waitForFunction(()=>document.querySelector('#graph .node.selected')?.getAttribute('data-node')==='A');
  // An older blocked response must not replace a newer valid proposal.
  await page.route('**/api/preview',async route=>{if(route.request().postDataJSON().pair?.[1]==='B')await new Promise(r=>setTimeout(r,350));await route.continue();});
  await page.locator('[data-node="B"]').click();await page.locator('[data-node="C"]').click();
  await page.locator('.proposal.good').waitFor();await page.waitForTimeout(450);
  assert(await page.locator('#apply').isEnabled());assert.match(await page.locator('#proposal').innerText(),/قواعد بيانات/);
  await page.unroute('**/api/preview');
  await page.screenshot({path:path.join(work,'editing-graph.png'),fullPage:true});
  await page.locator('#apply').click();const changed=await until(s=>s.revision===beforeDirect.revision+1);
  const a=changed.events.find(e=>e.id==='A'),c=changed.events.find(e=>e.id==='C');
  assert.equal(a.start,240);assert.equal(a.end,360);assert.equal(c.start,0);assert.equal(c.end,90);
  assert.equal(changed.occurrences.filter(o=>o.id.startsWith('A:')).length,3);
  for(const o of changed.occurrences.filter(o=>o.id.startsWith('A:')))assert.equal(o.end-o.start,120);
  assert.equal(changed.occurrences.filter((o,i)=>JSON.stringify(o)!==JSON.stringify(initial.occurrences[i])).length,4);
  assert(changed.valid);assert.deepEqual(changed.events.find(e=>e.id==='B'),initial.events.find(e=>e.id==='B'));
  await page.locator('#undo').click();await until(s=>s.revision===changed.revision+1);
  assert.deepEqual((await state()).events,initial.events);
  await page.locator('#redo').click();await until(s=>s.revision===changed.revision+2);
  await page.locator('#undo').click();await until(s=>s.revision===changed.revision+3);
  await page.locator('#calendar-tab').click();await page.locator('#move-tab').click();
  await page.locator('#move-time').fill('17:00');await page.locator('#move-room').selectOption('h1');
  await page.locator('#move-controls button[type=submit]').click();await page.locator('.proposal.good').waitFor();
  await page.locator('#apply').click();const moved=await until(s=>s.events.find(e=>e.id==='A').start===480);assert(moved.valid);
  // A previously valid preview cannot be committed after pins/inputs/schedule change.
  const old={kind:'move',moves:[{occurrence:'A',start:0,rooms:['h1']}],revision:moved.revision,input_revision:moved.input_revision};
  const validPreview=await page.request.post(url+'/api/preview',{data:old});assert.equal(validPreview.status(),200);
  await page.request.post(url+'/api/lock',{data:{ids:['C'],locked:true,revision:moved.revision,input_revision:moved.input_revision}});
  const stale=await page.request.post(url+'/api/apply',{data:old});assert.equal(stale.status(),409);
  assert.equal((await state()).events.find(e=>e.id==='A').start,480);
  await page.reload();await page.locator('[data-event="A"]').waitFor();
  await page.screenshot({path:path.join(work,'editing-calendar.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(work,'editing-mobile.png'),fullPage:true});
  assert.equal(await page.locator('#move-tab').count(),1);assert.deepEqual(errors,[]);
  const result={result:'passed',fixtures:'synthetic; 8 weekly patterns, 21 dated occurrences; academic odd/even weeks; all four years; cross-year registration',
   checks:['graph colours from same-revision engine results','blocked preview and server rejection','unequal-duration atomic swap',
           'whole-pattern expansion','odd/even calendar views','broader proposal does not mutate before Apply','minimal additional pattern highlighted',
           'nine dated changes committed atomically','pinned pattern preserved','whole proposal undone in one step','stored stale proposal rejected',
           'unchanged unrelated classes','undo and redo','validated move','stale edit rejected','unchanged targets stay neutral','out-of-order preview ignored','mobile layout capture','no browser runtime errors'],
   screenshots:['editing-graph.png','editing-calendar.png','editing-mobile.png','editing-broader.png']};
  fs.writeFileSync(path.join(root,'examples/editing-demo/browser-verification.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result,null,2));
 }finally{if(browser)await browser.close();server.kill('SIGTERM');}
})().catch(error=>{console.error(error);process.exitCode=1;});
