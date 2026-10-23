import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {inspectSnapshot, digest, decode64} from '../website/integrity.js';

const fixture = JSON.parse(await readFile(new URL('../website/data/demo.snapshot.json', import.meta.url)));
const clone = () => structuredClone(fixture);
test('synthetic demo verifies independently with bundled checkpoint labeled accurately', async () => {
  const model = await inspectSnapshot(clone());
  assert.equal(model.checkpoint, 'bundled-match');
  assert.equal(model.policy, 'not-evaluated');
  assert.ok([...model.objects.values()].some(o => o.body.type === 'note' && o.body.parents.length === 1));
  assert.ok(model.events.some(e => e.data.status === 'denied' && e.data.capability === 'shell.exec'));
});
test('separately supplied checkpoint is reported separately', async () => {
  assert.equal((await inspectSnapshot(clone(), fixture.checkpoint)).checkpoint, 'external-match');
});
test('one changed blob byte fails original identity', async () => {
  const data = clone();
  const row = data.tables.blobs[0];
  const raw = decode64(row.body); raw[0] ^= 1;
  row.body = Buffer.from(raw).toString('base64');
  await assert.rejects(inspectSnapshot(data), /Blob digest mismatch/);
});
test('duplicate identity is rejected', async () => {
  const data = clone(); data.tables.objects.push(data.tables.objects[0]);
  await assert.rejects(inspectSnapshot(data), /duplicate identity/);
});
test('missing relationship target is rejected even with rehashed body', async () => {
  const data = clone();
  const row = data.tables.objects.find(r => JSON.parse(Buffer.from(r.body,'base64')).parents.length);
  const text = Buffer.from(row.body,'base64').toString().replace(/"parents":\[[^\]]*\]/, '"parents":["missing"]');
  row.body = Buffer.from(text).toString('base64'); row.keys[0] = await digest(new TextEncoder().encode(text), 'GPTFS:object:1\0');
  await assert.rejects(inspectSnapshot(data), /relationship/);
});
test('tail deletion fails retained checkpoint', async () => {
  const data = clone(); data.tables.events.pop();
  await assert.rejects(inspectSnapshot(data), /Checkpoint history/);
});
test('without anchor a valid shorter history is not called authenticated', async () => {
  const data = clone(); data.tables.events.pop(); data.checkpoint = null;
  const model = await inspectSnapshot(data);
  assert.equal(model.checkpoint,'absent'); assert.equal(model.policy,'not-evaluated');
});
test('unknown tables cannot be silently ignored', async () => {
  const data = clone(); data.tables.future = [];
  await assert.rejects(inspectSnapshot(data), /table set/);
});
test('unknown required extensions are surfaced without approval', async () => {
  const data = clone();
  const row = data.tables.manifest[0];
  const body = JSON.parse(Buffer.from(row.body,'base64')); body.required_extensions = ['future.authority'];
  const text = JSON.stringify(body,Object.keys(body).sort());
  row.body = Buffer.from(text).toString('base64');
  const genesis = JSON.parse(Buffer.from(data.tables.events[0].body,'base64'));
  genesis.data.manifest = await digest(new TextEncoder().encode(text));
  const encode = obj => JSON.stringify(obj, (k,v) => v && !Array.isArray(v) && typeof v === 'object' ? Object.fromEntries(Object.keys(v).sort().map(key => [key,v[key]])) : v);
  const raw = new TextEncoder().encode(encode(genesis));
  data.tables.events = [{keys:[1,await digest(raw,'GPTFS:event:1\0')],body:Buffer.from(raw).toString('base64')}];
  data.checkpoint = null;
  const model = await inspectSnapshot(data);
  assert.deepEqual(model.requiredExtensions,['future.authority']); assert.equal(model.policy,'not-evaluated');
});
test('noncanonical duplicate-key body is rejected', async () => {
  const data = clone(); const row = data.tables.manifest[0];
  const text = Buffer.from(row.body,'base64').toString().replace('{','{"name":"duplicate",');
  row.body = Buffer.from(text).toString('base64');
  await assert.rejects(inspectSnapshot(data), /Noncanonical/);
});
test('foreign checkpoint is rejected', async () => {
  const cp = {...fixture.checkpoint, project_id:'other'};
  await assert.rejects(inspectSnapshot(clone(),cp), /Checkpoint project/);
});
test('malformed base64 is rejected', async () => {
  const data = clone(); data.tables.blobs[0].body = 'bad!!!';
  await assert.rejects(inspectSnapshot(data), /base64/);
});
