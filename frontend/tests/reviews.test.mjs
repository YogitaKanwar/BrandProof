import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { createReviewClient, localReviewAdapter } from '../src/api/reviews.ts'
import { ApiError } from '../src/api/client.ts'

afterEach(() => { delete globalThis.localStorage })
function storage() {
  const values = new Map()
  globalThis.localStorage = { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) }
  return values
}
test('title alone creates a linked campaign and review that survive a fresh client', async () => {
  storage()
  const first = await createReviewClient().create({ title: ' Launch ', brand: '', brief: '' })
  assert.equal(first.mode, 'local')
  assert.equal(first.data.reviews[0].title, 'Launch')
  assert.equal(first.data.reviews[0].status, 'draft')
  assert.equal(first.data.reviews[0].campaignId, first.data.campaigns[0].id)
  assert.deepEqual((await createReviewClient().list()).data, first.data)
  await createReviewClient().create({ title: 'Second', brand: '', brief: '' })
  assert.equal((await createReviewClient().list()).data.reviews.length, 2)
})
test('blank titles are generated without losing campaign identity; oversized details rejected', async () => {
  const values = storage()
  await assert.rejects(localReviewAdapter.create({ title: 'A'.repeat(121), brand: '', brief: '' }), /shorten/)
  assert.equal(values.size, 0)
  const first = await localReviewAdapter.create({ title: ' ', brand: '', brief: '' })
  const second = await localReviewAdapter.create({ title: '', brand: '', brief: '' })
  assert.equal(first.reviews[0].title, 'Untitled review')
  assert.notEqual(first.reviews[0].id, second.reviews[0].id)
  assert.notEqual(first.reviews[0].campaignId, second.reviews[0].campaignId)
})
test('storage failure does not return successful draft or partial campaign', async () => {
  storage()
  globalThis.localStorage.setItem = () => { throw new Error('quota exceeded') }
  await assert.rejects(localReviewAdapter.create({ title: 'Launch', brand: '', brief: '' }), /quota/)
  assert.deepEqual(await localReviewAdapter.list(), { campaigns: [], reviews: [] })
})
test('corrupt review data is preserved rather than overwritten', async () => {
  const values = storage()
  values.set('brandproof.development.reviews.v1', '{broken')
  await assert.rejects(localReviewAdapter.create({ title: 'Launch', brand: '', brief: '' }))
  assert.equal(values.get('brandproof.development.reviews.v1'), '{broken')
})
test('offline backend switches to labelled separate local drafts and stays local', async () => {
  storage()
  let calls = 0
  const offline = async () => { calls++; throw new ApiError('Offline', 0) }
  const client = createReviewClient({ list: offline, create: offline })
  const loaded = await client.list()
  assert.equal(loaded.mode, 'local')
  assert.match(loaded.notice, /nothing is synced/)
  const saved = await client.create({ title: 'Offline draft', brand: '', brief: '' })
  assert.equal(saved.mode, 'local')
  assert.equal(calls, 1)
})
test('server unavailability falls back; permission and validation errors do not', async () => {
  storage()
  for (const status of [502, 503, 504]) {
    const fail = async () => { throw new ApiError('Unavailable', status) }
    assert.equal((await createReviewClient({ list: fail, create: fail }).list()).mode, 'local')
  }
  for (const status of [400, 401, 403, 409, 422]) {
    const fail = async () => { throw new ApiError('Rejected', status) }
    await assert.rejects(createReviewClient({ list: fail, create: fail }).create({ title: 'No', brand: '', brief: '' }), error => error.status === status)
  }
  assert.equal((await localReviewAdapter.list()).reviews.length, 0)
})
test('connected adapter uses backend data without touching local storage', async () => {
  const data = { campaigns: [], reviews: [] }
  const remote = { list: async () => data, create: async () => data }
  const result = await createReviewClient(remote).list()
  assert.equal(result.mode, 'backend')
  assert.deepEqual(result.data, data)
})
