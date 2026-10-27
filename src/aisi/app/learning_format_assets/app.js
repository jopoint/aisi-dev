(() => {
  'use strict';
  let settings = JSON.parse(document.getElementById('ui-state').textContent);
  let latestStatus = null;
  let saveChain = Promise.resolve();
  let saving = 0;
  let polling = false;
  const byId = id => document.getElementById(id);
  const names = {input:'Input', groupwork:'Groupwork', discussion:'Discussion'};
  function text(id, value) { if (byId(id).textContent !== value) byId(id).textContent = value; }
  function renderSettings() {
    document.querySelectorAll('[name="learning_format"]').forEach(button => button.setAttribute('aria-pressed', String(button.value === settings.learning_format)));
    for (const key of ['participants','number_of_groups','presentation_side']) {
      if (document.activeElement !== byId(key)) byId(key).value = settings[key] ?? '';
    }
    byId('groupwork-parameters').hidden = settings.learning_format !== 'groupwork';
    byId('input-parameters').hidden = settings.learning_format !== 'input';
    for (const kind of ['chairs','persons']) {
      const enabled = Boolean(settings['show_'+kind]);
      document.querySelector('[name="toggle"][value="'+kind+'"]').setAttribute('aria-pressed', String(enabled));
      text(kind+'-label', enabled ? 'An' : 'Aus');
    }
    byId('adaptive_layout_preview').checked = Boolean(settings.adaptive_layout_preview);
  }
  function renderStatus(s) {
    latestStatus = s;
    const count = s.observed_ids.length;
    byId('connection').dataset.online = String(Boolean(s.camera_fresh));
    text('connection-label', s.camera_fresh ? 'Raum verbunden' : 'Tracking unterbrochen');
    text('table-count', s.camera_fresh ? count+' '+(count===1?'Tisch erkannt':'Tische erkannt') : 'Keine aktuellen Tische');
    let title, description, tone = 'neutral';
    const rejected = (s.message || '').startsWith('Kein neuer Vorschlag:');
    if (s.error) {
      title = 'Verbindung prüfen'; description = 'Die Raumsteuerung meldet einen Fehler.'; tone = 'error';
    } else if (!s.camera_fresh) {
      title = 'Warte auf Tracking'; description = 'Die Ausgabe bleibt bis zur Wiederverbindung aus.'; tone = 'error';
    } else if (!count) {
      title = 'Kein Tisch erkannt'; description = 'Tische im Kamerabild sichtbar machen.';
    } else if (s.busy) {
      title = 'Vorschlag wird berechnet'; description = 'Das bisherige Layout bleibt erhalten.';
    } else if (rejected) {
      title = 'Vorschlag nicht möglich'; description = s.message.replace(/^Kein neuer Vorschlag:\s*/, ''); tone = 'error';
    } else if (s.requires_activation || !s.active_format) {
      title = 'Bereit für dein Layout'; description = 'Lernformat wählen und Vorschlag aktivieren.';
    } else if (s.missing_active_ids.length) {
      title = 'Tischmenge hat sich geändert'; description = 'Einen neuen Vorschlag aktivieren.'; tone = 'pending';
    } else if (s.pending_settings) {
      title = 'Änderungen bereit'; description = 'Aktiv: '+names[s.active_format]+'.'; tone = 'pending';
    } else if (!s.td_approved) {
      title = 'Ausgabe wird geprüft'; description = 'Das Layout wird nach erfolgreicher Prüfung eingeblendet.';
    } else {
      title = 'Layout aktiv'; description = names[s.active_format]+' · '+s.chairs+' '+(s.chairs===1?'Stuhl':'Stühle'); tone = 'active';
    }
    if (saving) { title='Wird gespeichert'; description='Einstellungen werden übernommen.'; }
    text('status-title', title); text('status-description', description);
    document.querySelector('.activation-panel').dataset.tone = tone;
    byId('motion-activate').disabled = Boolean(saving || s.busy || !s.camera_fresh || !count);
    text('activation-label', s.active_format && s.pending_settings ? 'Änderungen aktivieren' : 'Vorschlag aktivieren');
    const rows = [['Kamera',s.camera_reason],['Tisch-IDs',s.observed_ids.join(', ')||'—'],['Sitzung / Revision',s.session+' / '+s.revision],['Berechnung',s.planning_seconds == null ? '—' : s.planning_seconds.toFixed(2)+' s'],['TD-Ausgabe',s.td_approval],['Motion',s.message],['Fehler',s.error||'—']];
    const dl = byId('diagnostics-data'); dl.replaceChildren();
    for (const [name,value] of rows) { const dt=document.createElement('dt'), dd=document.createElement('dd'); dt.textContent=name; dd.textContent=String(value); dl.append(dt,dd); }
  }
  function showError(error) { byId('request-error').hidden=false; text('request-error',error.message || 'Änderung konnte nicht gespeichert werden. Bitte erneut versuchen.'); }
  function dataFor(form, submitter) {
    const data = new FormData(form);
    if (submitter && submitter.name) data.set(submitter.name,submitter.value);
    for (const key of ['participants','number_of_groups','presentation_side']) data.set(key,byId(key).value);
    data.set('adaptive_layout_preview',byId('adaptive_layout_preview').checked?'on':'off');
    return new URLSearchParams(data);
  }
  function save(data) {
    saving++;
    byId('motion-activate').disabled=true;
    let succeeded = false;
    const result = saveChain.then(async () => {
      const response = await fetch('/set',{method:'POST',body:data,headers:{Accept:'application/json'}});
      if (!response.ok) throw new Error('Änderung konnte nicht gespeichert werden. Bitte erneut versuchen.');
      const payload = await response.json();
      settings=payload.settings; renderSettings();
      latestStatus=payload.motion;
      succeeded=true; byId('request-error').hidden=true;
    });
    saveChain = result.catch(showError).finally(() => {
      saving--;
      if (latestStatus) renderStatus(latestStatus);
      if (!succeeded) byId('motion-activate').disabled=true;
    });
    return saveChain;
  }
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit',event => { event.preventDefault(); save(dataFor(form,event.submitter)); });
    if (form.id === 'settings-form' || form.id === 'advanced-form') form.addEventListener('change',() => save(dataFor(form)));
  });
  document.querySelectorAll('[data-step]').forEach(button => button.addEventListener('click',() => {
    const field=byId(button.dataset.for), minimum=Number(field.min)||1, maximum=Number(field.max)||99;
    field.value=String(Math.max(minimum,Math.min(maximum,(Number(field.value)||minimum)+Number(button.dataset.step))));
    field.dispatchEvent(new Event('change',{bubbles:true}));
  }));
  async function poll() {
    if (polling || saving) return;
    polling=true;
    try {
      const response=await fetch('/motion-status',{cache:'no-store'});
      if (!response.ok) throw new Error('Status nicht erreichbar');
      const status=await response.json();
      if (!saving) renderStatus(status);
    } catch (error) {
      text('connection-label','Verbindung unterbrochen'); byId('connection').dataset.online='false';
      text('status-title','Server nicht erreichbar'); text('status-description','Verbindung wird erneut versucht.');
      byId('motion-activate').disabled=true;
    } finally { polling=false; }
  }
  renderSettings(); poll(); setInterval(poll,1000);
})();
