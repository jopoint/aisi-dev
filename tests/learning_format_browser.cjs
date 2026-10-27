// Run against generated HTML in an isolated headless browser; no lab endpoints.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');

(async () => {
  const directory = process.argv[2];
  assert(directory, 'Pass the generated preview directory');
  const html = fs.readFileSync(path.join(directory, 'index.html'), 'utf8');
  const browser = await chromium.launch({ headless: true, channel: 'msedge' });
  const page = await browser.newPage({ viewport: { width: 1200, height: 1000 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const posts = [];
  const settings = {learning_format:'input',participants:3,number_of_groups:2,presentation_side:null,
    show_persons:false,show_chairs:true,adaptive_layout_preview:true,transformation_strength:1,layout_revision:1};
  const status = {camera_fresh:true,camera_reason:'receiving',observed_ids:['table_00'],
    missing_active_ids:[],session:100,revision:2,active_format:'input',chairs:3,
    pending_settings:false,busy:false,error:null,sending:true,requires_activation:false,
    td_approved:true,td_approval:'TD-Ausgabe automatisch geprüft und freigegeben.',message:'Vorschlag aktiviert.'};
  await page.route('http://aisi-preview.local/**', async route => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    if (pathname === '/set') {
      const data = new URLSearchParams(request.postData());
      posts.push(Object.fromEntries(data));
      if (data.has('learning_format')) settings.learning_format = data.get('learning_format');
      if (data.has('participants')) settings.participants = Number(data.get('participants'));
      if (data.has('number_of_groups')) settings.number_of_groups = Number(data.get('number_of_groups'));
      if (data.has('presentation_side')) settings.presentation_side = data.get('presentation_side') || null;
      if (data.has('adaptive_layout_preview')) settings.adaptive_layout_preview = data.get('adaptive_layout_preview') === 'on';
      if (data.has('toggle')) settings['show_'+data.get('toggle')] = !settings['show_'+data.get('toggle')];
      status.pending_settings = true;
      if (data.get('action') === 'activate_motion') {
        status.active_format = settings.learning_format;
        status.pending_settings = false;
        status.revision++;
      }
      await route.fulfill({json:{settings,motion:status}});
    } else if (pathname === '/motion-status') {
      await route.fulfill({json:status});
    } else {
      await route.fulfill({contentType:'text/html; charset=utf-8',body:html});
    }
  });
  try {
    await page.goto('http://aisi-preview.local/');
    await page.getByText('Layout aktiv',{exact:true}).waitFor();
    assert.equal(await page.locator('details').evaluate(node=>node.open),false);
    assert.equal(await page.locator('[name=transformation_strength]').count(),0);
    assert.equal(await page.locator('#groupwork-parameters').isVisible(),false);
    await page.screenshot({path:path.join(directory,'desktop.png'),fullPage:true});
    await page.locator('button[value=groupwork]').click();
    await page.waitForFunction(()=>document.querySelector('button[value=groupwork]').getAttribute('aria-pressed')==='true');
    assert.equal(status.revision,2);
    assert.equal(await page.locator('#groupwork-parameters').isVisible(),true);
    assert.equal(await page.locator('#input-parameters').isVisible(),false);
    await page.locator('[data-for=number_of_groups][data-step="1"]').click();
    await page.waitForFunction(()=>document.querySelector('#number_of_groups').value==='3');
    await page.waitForTimeout(100);
    assert.equal(posts.filter(data=>data.action==='activate_motion').length,0);
    assert.equal(settings.adaptive_layout_preview,true);
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(directory,'mobile.png'),fullPage:true});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.locator('#motion-activate').click();
    await page.getByText('Layout aktiv',{exact:true}).waitFor();
    assert.equal(posts.filter(data=>data.action==='activate_motion').length,1);
    assert.equal(status.revision,3);
    status.camera_fresh=false;
    await page.getByText('Warte auf Tracking',{exact:true}).waitFor();
    assert.equal(await page.locator('#motion-activate').isDisabled(),true);
    await page.locator('summary').click();
    assert.equal(await page.locator('#diagnostics-data').isVisible(),true);
    assert.deepEqual(errors,[]);
    console.log('BROWSER OK: responsive layout, format/settings without activation, preserved planner, one explicit activation, tracking loss, diagnostics');
  } finally {
    await browser.close();
  }
})().catch(error=>{ console.error(error); process.exitCode=1; });
