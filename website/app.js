import {inspectSnapshot, decode64, contentText} from './integrity.js';
const $ = id => document.getElementById(id);
let current = null, model = null, selected = null, external = null, lastReport = null, generation = 0;
function node(tag, text, className) { const el = document.createElement(tag); if (text !== undefined) el.textContent = text; if (className) el.className = className; return el; }
function short(id) { return id ? id.slice(7, 19) : '—'; }
function label(object) {
  const origin = object.body.origin ?? '';
  if (origin.includes('original-observation')) return 'Original observation';
  if (origin.includes('derived-note')) return 'Derived note';
  if (object.body.type === 'evidence') return 'Measurement evidence';
  if (origin.startsWith('claude-plugin:/')) return origin.split('/').filter(Boolean).slice(-2).join('/');
  if (object.body.type === 'bundle') return 'Original plugin archive';
  return `${object.body.type ?? 'Object'} · ${short(object.id)}`;
}
function download(name, bytes, type = 'application/octet-stream') {
  const url = URL.createObjectURL(new Blob([bytes], {type}));
  const a = node('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function selectObject(id) { selected = id; renderObjects(); renderDetail(); renderLedger(); }
function renderObjects() {
  $('object-list').replaceChildren();
  if (!model) return;
  const filter = $('object-search').value.toLowerCase();
  for (const object of model.objects.values()) {
    if (![label(object), object.id, object.body.type, object.body.origin].join(' ').toLowerCase().includes(filter)) continue;
    const button = node('button', undefined, 'object-button'); button.type = 'button'; button.setAttribute('aria-pressed', String(object.id === selected));
    button.append(node('strong', label(object)), node('small', `${object.body.type} / ${object.body.size} bytes`));
    button.addEventListener('click', () => selectObject(object.id)); $('object-list').append(button);
  }
}
function renderDetail() {
  const object = model?.objects.get(selected);
  if (!object) return;
  $('object-title').textContent = label(object); $('object-type').textContent = object.body.type;
  $('object-origin').textContent = object.body.origin;
  $('object-meta').replaceChildren();
  for (const [term, value] of [['Identity', object.id], ['Blob', object.body.blob], ['Authority', object.body.authority ?? 'unspecified'], ['Trust', object.body.trust ?? 'unspecified']]) {
    const pair = node('div'); pair.append(node('dt', term), node('dd', value)); $('object-meta').append(pair);
  }
  const bytes = model.blobs.get(object.body.blob), text = contentText(bytes);
  $('object-content').textContent = text === null ? `Binary content · ${bytes.length} bytes\n\n${Array.from(bytes.slice(0, 160), n => n.toString(16).padStart(2, '0')).join(' ')}${bytes.length > 160 ? '\n…' : ''}` : text.slice(0, 20000) + (text.length > 20000 ? '\n[Preview truncated; download preserves original bytes.]' : '');
  $('relationships').replaceChildren();
  const related = [...object.body.parents.map(id => ['Parent', id]), ...[...model.objects.values()].filter(o => o.body.parents.includes(object.id)).map(o => ['Child', o.id])];
  for (const [relation, id] of related) { const button = node('button', `${relation} → ${label(model.objects.get(id))}`); button.addEventListener('click', () => selectObject(id)); $('relationships').append(button); }
  if (!related.length) $('relationships').append(node('span', 'No parent or child objects in this snapshot.'));
}
function renderLedger() {
  $('ledger').replaceChildren();
  if (!model) return;
  for (const event of model.events) {
    const data = event.data ?? {}, status = data.status ?? data.decision;
    const el = node('article', undefined, `event ${status === 'deny' || status === 'denied' ? 'denied' : status === 'completed' ? 'completed' : ''} ${data.object === selected || data.evidence === selected ? 'focused' : ''}`);
    const heading = node('div', undefined, 'event-heading'); heading.append(node('strong', event.kind + (status ? ` · ${status}` : '')), node('small', String(event.seq).padStart(2, '0'))); el.append(heading);
    const description = data.code ?? data.text ?? (event.kind === 'import' ? 'Inert plugin import · no authority granted' : event.kind === 'custody' ? data.origin : event.kind === 'genesis' ? 'Manifest bound to history' : event.actor);
    el.append(node('p', description));
    if (data.capability) el.append(node('p', `Capability: ${data.capability}`));
    $('ledger').append(el);
  }
}
async function load(snapshot, description) {
  const ticket = ++generation;
  current = snapshot; model = null; selected = null;
  $('load-status').textContent = description;
  $('verification').classList.remove('failed'); $('verify-title').textContent = 'Checking original bytes and history…';
  $('object-list').replaceChildren(); $('ledger').replaceChildren(); $('object-meta').replaceChildren(); $('relationships').replaceChildren();
  $('object-title').textContent = 'No verified object selected'; $('object-origin').textContent = ''; $('object-content').textContent = 'Content appears after integrity checks pass.';
  $('object-count').textContent = '—'; $('event-count').textContent = '—'; $('object-type').textContent = 'DATA';
  try {
    const verified = await inspectSnapshot(snapshot, external);
    if (ticket !== generation) return;
    model = verified;
    $('verification').querySelector('.verify-symbol').textContent = '✓';
    $('verify-title').textContent = 'Integrity checks passed';
    const cp = model.checkpoint === 'external-match' ? 'External checkpoint matches.' : model.checkpoint === 'bundled-match' ? 'Bundled checkpoint matches; external trust is not established.' : 'No checkpoint supplied.';
    $('verify-detail').textContent = `${model.blobs.size} blob hashes · ${model.objects.size} object identities · ${model.events.length} chained events. ${cp} Policy: not evaluated.${model.requiredExtensions.length ? ' Required extensions are unsupported; execution must remain blocked.' : ''}`;
    $('object-count').textContent = String(model.objects.size); $('event-count').textContent = String(model.events.length);
    lastReport = {integrity:'valid',policy:'not-evaluated',project_id:model.manifest.project_id,head:model.head,checkpoint:model.checkpoint,required_extensions:model.requiredExtensions,objects:model.objects.size,blobs:model.blobs.size,events:model.events.length};
    selectObject([...model.objects.values()].find(o => o.body.origin === 'demo:original-observation')?.id ?? model.objects.keys().next().value);
  } catch (error) {
    if (ticket !== generation) return;
    $('verification').classList.add('failed'); $('verification').querySelector('.verify-symbol').textContent = '!';
    $('verify-title').textContent = 'Integrity check failed'; $('verify-detail').textContent = error.message;
    lastReport = {integrity:'invalid',policy:'not-evaluated',error:error.message};
  }
}
async function demo() {
  external = null; $('object-search').value = '';
  try { const response = await fetch('data/demo.snapshot.json'); if (!response.ok) throw new Error('Demo could not be loaded.'); await load(await response.json(), 'Synthetic demo · created for this project · original bytes retained'); }
  catch (error) { $('load-status').textContent = error.message; }
}
async function readFile(input, max) {
  const file = input.files[0]; if (!file) return null;
  if (file.size > max) throw new Error('File exceeds the supported size limit.');
  return {value:JSON.parse(await file.text()), name:file.name};
}
$('load-demo').addEventListener('click', demo);
$('snapshot-file').addEventListener('change', async event => {
  try { const file = await readFile(event.target, 32*1024*1024); if (file) { external = null; $('object-search').value = ''; await load(file.value, `Local snapshot: ${file.name} · read in this tab only`); } }
  catch (error) {
    await load(null, `Could not open file: ${error.message}`);
    $('verify-detail').textContent = error.message; lastReport.error = error.message;
  }
  event.target.value = '';
});
$('checkpoint-file').addEventListener('change', async event => {
  try { const file = await readFile(event.target, 64*1024); if (file && current) { external = file.value; await load(current, `External checkpoint: ${file.name} · trust depends on how you retained it`); } }
  catch (error) {
    await load(null, `Could not open checkpoint: ${error.message}`);
    $('verify-detail').textContent = error.message; lastReport.error = error.message;
  }
  event.target.value = '';
});
$('object-search').addEventListener('input', renderObjects);
$('tamper').addEventListener('click', async () => {
  if (!current) return;
  const copy = structuredClone(current), row = copy.tables?.blobs?.[0];
  if (!row) return;
  const raw = decode64(row.body); if (!raw.length) return;
  raw[0] ^= 1;
  let binary = '';
  for (let offset = 0; offset < raw.length; offset += 32768) binary += String.fromCharCode(...raw.subarray(offset, offset + 32768));
  row.body = btoa(binary);
  await load(copy, 'Tamper experiment · one blob byte changed; its claimed identity was retained. Reset demo to restore.');
});
document.querySelectorAll('[data-step]').forEach(button => button.addEventListener('click', () => {
  if (!model) { $('load-status').textContent = 'Reset the demo to explore verified objects.'; return; }
  const step = button.dataset.step;
  if (step === 'denial') {
    const skill = [...model.objects.values()].find(o => o.body.type === 'skill'); if (skill) selectObject(skill.id);
    const denial = $('ledger').querySelector('.denied'); if (denial) denial.scrollIntoView({block:'nearest',behavior:'smooth'});
    $('load-status').textContent = 'The skill is data. Its admission is denied by type scope; shell.exec is denied by the capability ceiling.';
  } else {
    const obj = [...model.objects.values()].find(o => step === 'source' ? o.body.type === 'source' : o.body.type === 'note');
    if (obj) selectObject(obj.id);
    $('load-status').textContent = step === 'source' ? 'Original observation · exact bytes have their own identity.' : 'Derived note · use the Parent relationship to return to the original source.';
  }
}));
$('download-object').addEventListener('click', () => { const obj = model?.objects.get(selected); if (obj) download(`gptfs-${obj.body.type}-${short(obj.id)}.bin`, model.blobs.get(obj.body.blob)); });
$('download-report').addEventListener('click', () => { if (lastReport) download('gptfs-integrity-report.json', JSON.stringify(lastReport, null, 2), 'application/json'); });
$('copy-quickstart').addEventListener('click', async () => { try { await navigator.clipboard.writeText($('quickstart-code').textContent); $('copy-quickstart').textContent = 'Copied'; } catch { $('copy-quickstart').textContent = 'Select commands to copy'; } });
demo();
