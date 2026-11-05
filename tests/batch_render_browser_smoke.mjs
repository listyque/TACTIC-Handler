import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
const {chromium}=await import(process.env.BATCH_PLAYWRIGHT || 'playwright');
const url=new URL(process.env.BATCH_WEB_URL), token=url.searchParams.get('token');
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:920},deviceScaleFactor:1});
const errors=[];page.on('pageerror',error=>errors.push(error.message));
page.on('console',message=>{if(message.type()==='error')errors.push(message.text().replaceAll(token,'[redacted]'));});
async function request(route,body) {
  return page.evaluate(async ({route,body,token})=>{
    const response=await fetch(route+(route.includes('?')?'&':'?')+'token='+token,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});
    const result=await response.json();if(!response.ok)throw Error(result.error);return result;
  },{route,body,token});
}
const state=()=>request('/api/state');
const action=(action,values={})=>request('/api/action',{action,...values});
const row=id=>page.locator(`[data-select="${id}"]`);
try {
  await page.goto(url.href);await page.locator('[data-select="episode-5"]').waitFor();
  // A row and its grip retain their DOM identity across polling.
  await page.evaluate(()=>{window.savedRow=document.querySelector('[data-select="episode-2"]');window.savedGrip=window.savedRow.querySelector('[data-drag]');});
  await page.waitForTimeout(1200);
  assert(await page.evaluate(()=>window.savedRow===document.querySelector('[data-select="episode-2"]') && window.savedGrip===window.savedRow.querySelector('[data-drag]')));
  await row('episode-1').locator('.queue-copy').click();
  await row('episode-3').locator('.queue-copy').click({modifiers:['Shift']});
  await page.waitForFunction(()=>document.querySelectorAll('.queue-row.child.selected').length===3);
  assert.equal((await state()).selectionCount,3);
  await row('episode-2').locator('[data-action="include"]').click();
  await page.waitForFunction(()=>[1,2,3].every(i=>!document.querySelector(`[data-select="episode-${i}"] input`).checked));
  assert((await state()).queue[0].shots.slice(1,4).every(job=>job.state==='skipped'));
  await row('episode').locator('[data-action="include-all"]').click();
  await page.waitForFunction(()=>document.querySelectorAll('.queue-row.child input:checked').length>=11);
  assert.equal((await state()).queue[0].shots[0].state,'completed');
  await row('episode-5').locator('[data-action="include"]').click();
  await page.waitForFunction(()=>!document.querySelector('[data-select="episode-5"] input').checked);
  // An authentic HTML5 grip drag crosses at least one polling interval.
  const grip=row('episode-5').locator('[data-drag]');
  await grip.scrollIntoViewIfNeeded();
  const from=await grip.boundingBox();
  await page.mouse.move(from.x+from.width/2,from.y+from.height/2);await page.mouse.down();
  await page.mouse.move(from.x+from.width/2+10,from.y+from.height/2,{steps:5});
  await page.waitForTimeout(1200);
  await row('episode-2').scrollIntoViewIfNeeded();const target=await row('episode-2').boundingBox();
  await page.mouse.move(target.x+30,target.y+target.height/2,{steps:12});await page.mouse.up();
  await page.waitForFunction(()=>[...document.querySelectorAll('[data-parent="episode"]')].findIndex(row=>row.dataset.select==='episode-5')===2);
  assert.equal((await state()).queue[0].shots[2].jobId,'episode-5');
  // Selecting an already visible row never changes either scroll position.
  await page.locator('#queue').evaluate(node=>node.scrollTop=300);
  await page.locator('#catalog').evaluate(node=>node.scrollTop=400);
  const scroll=()=>page.evaluate(()=>[document.querySelector('#queue').scrollTop,document.querySelector('#catalog').scrollTop]);
  const before=await scroll();
  const visible=await page.locator('#queue .queue-row').evaluateAll(nodes=>nodes.find(node=>{const r=node.getBoundingClientRect(),p=node.parentElement.getBoundingClientRect();return r.top>p.top&&r.bottom<p.bottom;})?.dataset.select);
  await row(visible).locator('.queue-copy').click();await page.waitForTimeout(1200);
  assert.deepEqual(await scroll(),before);
  const measurements={};
  for(const language of ['en','ru'])for(const width of [950,1440]) {
    await page.setViewportSize({width,height:920});
    const native=await action('fixture-view',{language,width,height:920});
    await page.waitForFunction(lang=>document.documentElement.lang===lang,language);
    await page.locator('#queue').evaluate(node=>node.scrollTop=0);
    await page.locator('#catalog').evaluate(node=>node.scrollTop=0);
    await page.screenshot({path:path.join(process.env.BATCH_EVIDENCE,`web-${language}-${width}.png`)});
    const web=await page.evaluate(()=>{
      const measure=selector=>{const node=document.querySelector(selector),r=node.getBoundingClientRect(),css=getComputedStyle(node);return {x:r.x,y:r.y,width:r.width,height:r.height,font:css.fontSize,color:css.backgroundColor};};
      return {catalog:measure('.catalog-card'),catalogPreview:measure('.catalog-card .thumb'),episode:measure('[data-select="episode"]'),shot:measure('[data-select="episode-0"]'),queuePreview:measure('[data-select="episode"] .thumb')};
    });
    assert.equal(web.catalog.height+8,88);assert.equal(web.catalogPreview.width,48);
    assert.equal(web.episode.height+8,88);assert.equal(web.shot.height+8,80);assert.equal(web.queuePreview.width,44);
    assert.equal(native.native.batchQueueRow_0.height,88);assert.equal(native.native.batchQueueRow_1.height,80);
    assert.equal(native.native.batchQueuePreview_0.width,web.queuePreview.width);
    assert.equal(await page.locator('#search').getAttribute('placeholder'),language==='ru'?'Найти эпизод':'Search episodes');
    assert.equal((await page.locator('[data-action="settings-open"]').getAttribute('title')),language==='ru'?'Настройки рендера':'Render settings');
    measurements[`${language}-${width}`]={web,native:native.native};
  }
  assert.deepEqual(errors,[]);
  await fs.writeFile(path.join(process.env.BATCH_EVIDENCE,'browser-geometry.json'),JSON.stringify(measurements,null,2));
  console.log('PASS: browser mouse/Shift/bulk inclusion, grip drag across polling, scroll retention, EN/RU, narrow/wide native/browser geometry; no JavaScript or QML errors');
} finally {await browser.close();}
