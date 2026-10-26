import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { campaignService } from '../src/api/campaigns.ts'
import { requestJson, ApiError } from '../src/api/client.ts'

const originalFetch = globalThis.fetch
afterEach(() => { globalThis.fetch = originalFetch; delete globalThis.localStorage })

test('development campaigns persist, trim fields and reject blank names', async () => {
  const values = new Map()
  globalThis.localStorage = { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) }
  assert.deepEqual(await campaignService.list(), [])
  const saved = await campaignService.create({ name: ' Launch ', brand: ' Brand ', description: ' Brief ' })
  assert.equal(saved.name, 'Launch')
  assert.equal(saved.brand, 'Brand')
  assert.deepEqual(await campaignService.list(), [saved])
  await assert.rejects(campaignService.create({ name: ' ', brand: 'Brand', description: '' }), /required/)
})

test('storage failure does not report a successful save', async () => {
  globalThis.localStorage = { getItem: () => null, setItem: () => { throw new Error('Storage denied') } }
  await assert.rejects(campaignService.create({ name: 'Launch', brand: 'Brand', description: '' }), /Storage denied/)
})

test('corrupt fixture records are rejected', async () => {
  globalThis.localStorage = { getItem: () => '[{"name":"Incomplete"}]' }
  await assert.rejects(campaignService.list(), /unreadable/)
})

test('HTTP failure, network failure and malformed JSON are errors', async () => {
  globalThis.fetch = async () => new Response('{}', { status: 403 })
  await assert.rejects(requestJson('https://fixture.invalid'), error => error instanceof ApiError && error.status === 403)
  globalThis.fetch = async () => { throw new TypeError('offline') }
  await assert.rejects(requestJson('https://fixture.invalid'), /Cannot reach/)
  globalThis.fetch = async () => new Response('not json')
  await assert.rejects(requestJson('https://fixture.invalid'), /unreadable/)
})

test('transport forwards options and returns actual JSON', async () => {
  globalThis.fetch = async (_url, options) => {
    assert.equal(options.method, 'POST')
    assert.equal(options.headers.get('Content-Type'), 'application/json')
    assert.equal(options.headers.get('Accept'), 'application/json')
    return Response.json({ id: 'server-record' })
  }
  assert.deepEqual(await requestJson('https://fixture.invalid', { method: 'POST', headers: new Headers({ 'Content-Type': 'application/json' }), body: '{}' }), { id: 'server-record' })
})
