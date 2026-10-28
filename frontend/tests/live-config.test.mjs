import test from 'node:test'
import assert from 'node:assert/strict'
import { apiBase, verifyBackend } from './live-config.mjs'

test('live preflight rejects another service before creating a session', async t => {
  const requests = []
  t.mock.method(globalThis, 'fetch', async url => {
    requests.push(String(url))
    return Response.json({ info: { title: 'SpeakEZ API' }, paths: {} })
  })
  await assert.rejects(verifyBackend(), /not the BrandProof API/)
  assert.deepEqual(requests, [new URL('/openapi.json', apiBase).href])
})

test('live preflight accepts the expected API contract', async t => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({
    info: { title: 'BrandProof API' }, paths: { '/api/v1/demo-sessions': {} },
  }))
  await verifyBackend()
})

test('live preflight reports an unreachable runtime as blocked', async t => {
  t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('fetch failed') })
  await assert.rejects(verifyBackend(), /integration blocked: cannot reach/)
})
