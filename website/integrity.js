// Independent browser integrity reader. Does not evaluate policy or grant authority.
const encoder = new TextEncoder();
const decoder = new TextDecoder('utf-8', {fatal: true});
const hashPattern = /^sha256:[0-9a-f]{64}$/;
const tables = ['blobs', 'events', 'manifest', 'objects'];
export function requireValue(ok, message) { if (!ok) throw new Error(message); }
export function decode64(text) {
  requireValue(typeof text === 'string' && text.length <= 12 * 1024 * 1024 && /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(text), 'Invalid or oversized base64 body');
  return Uint8Array.from(atob(text), c => c.charCodeAt(0));
}
export async function digest(raw, prefix = '') {
  requireValue(globalThis.crypto?.subtle, 'Integrity checks require HTTPS or localhost and Web Crypto support.');
  const pre = encoder.encode(prefix);
  const all = new Uint8Array(pre.length + raw.length);
  all.set(pre); all.set(raw, pre.length);
  const hash = new Uint8Array(await crypto.subtle.digest('SHA-256', all));
  return 'sha256:' + Array.from(hash, n => n.toString(16).padStart(2, '0')).join('');
}
function canonical(value) {
  if (value === null || typeof value === 'boolean' || typeof value === 'string') return JSON.stringify(value);
  if (typeof value === 'number') { requireValue(Number.isSafeInteger(value), 'Unsupported canonical number'); return String(value); }
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  requireValue(typeof value === 'object', 'Unsupported canonical value');
  return '{' + Object.keys(value).sort().map(k => {
    requireValue(/^[\x00-\x7F]*$/.test(k), 'Non-ASCII canonical key');
    return JSON.stringify(k) + ':' + canonical(value[k]);
  }).join(',') + '}';
}
function parseBody(raw) {
  const text = decoder.decode(raw);
  const body = JSON.parse(text);
  requireValue(canonical(body) === text, 'Noncanonical or duplicate-key record body');
  return body;
}
function key(row, length) {
  requireValue(row && Array.isArray(row.keys) && row.keys.length === length && Object.keys(row).sort().join(',') === 'body,keys', 'Invalid snapshot row');
  return row.keys;
}
export async function inspectSnapshot(snapshot, anchor = null) {
  requireValue(snapshot?.profile === 'gptfs-browser-snapshot-1' && snapshot.source_profile === 'gptfs-0.1-directory-1', 'Unsupported snapshot profile');
  requireValue(snapshot.tables && Object.keys(snapshot.tables).sort().join(',') === tables.join(','), 'Unsupported table set');
  let total = 0;
  for (const table of tables) {
    requireValue(Array.isArray(snapshot.tables[table]) && snapshot.tables[table].length <= 10000, 'Invalid or oversized record collection');
    for (const row of snapshot.tables[table]) {
      requireValue(typeof row.body === 'string', 'Missing record bytes');
      total += row.body.length;
    }
  }
  requireValue(total <= 32 * 1024 * 1024, 'Snapshot exceeds the 32 MiB browser limit');
  requireValue(snapshot.tables.manifest.length === 1, 'Expected one manifest');
  const mr = snapshot.tables.manifest[0];
  requireValue(key(mr, 1)[0] === 1, 'Invalid manifest identity');
  const manifestRaw = decode64(mr.body), manifest = parseBody(manifestRaw);
  requireValue(manifest.format === 'GPTFS' && manifest.format_version === '0.1.0' && manifest.schema_version === 1 && manifest.hash === 'sha256' && manifest.canonicalization === 'gptfs-json-1', 'Unsupported GPTFS identity profile');
  const blobs = new Map(), objects = new Map(), events = [];
  for (const row of snapshot.tables.blobs) {
    const [id] = key(row, 1), raw = decode64(row.body);
    requireValue(typeof id === 'string' && hashPattern.test(id) && !blobs.has(id) && await digest(raw) === id, 'Blob digest mismatch or duplicate identity');
    blobs.set(id, raw);
  }
  for (const row of snapshot.tables.objects) {
    const [id] = key(row, 1), raw = decode64(row.body);
    requireValue(typeof id === 'string' && hashPattern.test(id) && !objects.has(id) && await digest(raw, 'GPTFS:object:1\0') === id, 'Object digest mismatch or duplicate identity');
    const body = parseBody(raw);
    requireValue(blobs.has(body.blob) && Number.isSafeInteger(body.size) && body.size === blobs.get(body.blob).length && Array.isArray(body.parents) && body.parents.every(p => typeof p === 'string'), 'Missing blob, wrong size, or invalid relationships');
    objects.set(id, {id, body, raw});
  }
  for (const object of objects.values()) requireValue(object.body.parents.every(id => objects.has(id)), 'Missing relationship target');
  let previous = null;
  const ids = new Set();
  for (const row of snapshot.tables.events) {
    const [seq, id] = key(row, 2), raw = decode64(row.body), body = parseBody(raw);
    requireValue(seq === events.length + 1 && seq === body.seq && body.previous === previous, 'Broken ledger order or ancestry');
    requireValue(!ids.has(id) && hashPattern.test(id) && await digest(raw, 'GPTFS:event:1\0') === id, 'Event digest mismatch or duplicate identity');
    if (seq === 1) requireValue(body.kind === 'genesis' && body.data?.manifest === await digest(manifestRaw), 'Genesis does not bind this manifest');
    events.push({id, ...body}); ids.add(id); previous = id;
  }
  requireValue(events.length > 0, 'Empty ledger');
  const cp = anchor ?? snapshot.checkpoint;
  if (cp) {
    requireValue(cp.project_id === manifest.project_id && cp.manifest === await digest(manifestRaw), 'Checkpoint project mismatch');
    requireValue(Number.isSafeInteger(cp.seq) && cp.seq > 0 && events[cp.seq - 1]?.id === cp.head, 'Checkpoint history mismatch');
  }
  return {manifest, manifestRaw, blobs, objects, events, head: previous,
    checkpoint: anchor ? 'external-match' : cp ? 'bundled-match' : 'absent',
    policy: 'not-evaluated', requiredExtensions: manifest.required_extensions ?? []};
}

export function contentText(bytes) {
  try { return decoder.decode(bytes); } catch { return null; }
}
