import { apiBase, verifyBackend } from './live-config.mjs'
await verifyBackend()
import assert from 'node:assert/strict'
import { createBackendClient } from '../src/api/backend.ts'
import { requestJson } from '../src/api/client.ts'
const client = createBackendClient(apiBase)
const initial = await client.connect()
assert.equal(initial.data.reviews.length, 0)
const saved = await client.create({ title: 'Y01 HTTP integration', publicationDate: '2026-11-12', brand: '', brief: '' })
const id = saved.data.reviews[0].id
assert.equal((await client.list()).data.reviews[0].id, id)
const loaded = (await client.get(id)).data.reviews[0].backendCampaign
assert.equal(loaded.publication_date, '2026-11-12')
assert.equal(loaded.content_revision, 1)
assert.equal(loaded.source_revision, 0)
await assert.rejects(client.create({ title: 'Invalid', publicationDate: 'bad', brand: '', brief: '' }), error => error.status === 422 && error.code === 'validation_error')
await assert.rejects(client.get('does-not-exist'), error => error.status === 404)
await assert.rejects(createBackendClient(apiBase).get(id), error => error.status === 401)
await assert.rejects(requestJson(`${apiBase}/campaigns`), error => error.status === 401 && error.code === 'unauthenticated')
const separate = await requestJson(`${apiBase}/demo-sessions`, { method: 'POST' })
await assert.rejects(requestJson(`${apiBase}/campaigns`, { method: 'POST', headers: { Authorization: `Bearer ${separate.actors.reviewer.access_token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({name:'Denied',publication_date:'2026-11-12'}) }), error => error.status === 403)
await assert.rejects(requestJson(`${apiBase}/campaigns/${id}`, { headers: { Authorization: `Bearer ${separate.actors.creator.access_token}` } }), error => error.status === 404)
assert.equal((await client.list()).data.reviews[0].id, id)
console.log('PASS real HTTP session, campaign persistence/list/get/revisions, 401/403/404/422, workspace isolation and memory-only refresh boundary (no tokens logged)')
