import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { emptySource, readSource, saveSource } from '../src/sourceDraft.ts'
afterEach(() => { delete globalThis.localStorage })
function storage() {
  const values = new Map()
  globalThis.localStorage = { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) }
  return values
}
test('guidelines, facts and source metadata persist per review as pending only', () => {
  storage()
  const input = { ...emptySource, name: 'Workshop policy', applicability: 'India workshop', version: '2', guidelines: 'Use confirmed facts only.', price: 'INR 499', offerDates: 'October', mandatoryTerms: 'Terms apply', prohibitedClaims: 'Placement guarantee', validFrom: '2026-10-01', validUntil: '2026-10-31' }
  const saved = saveSource('one', input)
  assert.deepEqual(readSource('one'), saved)
  assert.equal(saved.status, 'pending')
  assert.equal(saved.origin, 'local-draft')
  assert.equal(readSource('two').input.guidelines, '')
})
test('invalid dates and oversize text are rejected before writing', () => {
  const values = storage()
  assert.throws(() => saveSource('one', { ...emptySource, validFrom: '2026-11-01', validUntil: '2026-10-01' }), /on or after/)
  assert.throws(() => saveSource('one', { ...emptySource, validFrom: '2026-02-30' }), /valid source date/)
  assert.throws(() => saveSource('one', { ...emptySource, guidelines: 'x'.repeat(10001) }), /limits/)
  assert.equal(values.size, 0)
})
test('local records cannot become owner-confirmed approvals', () => {
  const values = storage()
  values.set('brandproof.development.source.one', JSON.stringify({ input: emptySource, status: 'approved', origin: 'backend' }))
  assert.throws(() => readSource('one'), /unreadable/)
  assert.match(values.get('brandproof.development.source.one'), /approved/)
  assert.equal(saveSource('two', { ...emptySource, status: 'approved' }).status, 'pending')
})
test('storage failure propagates rather than reporting source save success', () => {
  storage()
  globalThis.localStorage.setItem = () => { throw new Error('quota') }
  assert.throws(() => saveSource('one', emptySource), /quota/)
})
test('older source drafts retain facts when optional owner is added', () => {
  const values = storage()
  const input = { ...emptySource, price: 'INR 499' }
  delete input.owner
  values.set('brandproof.development.source.old', JSON.stringify({ input, status: 'pending', origin: 'local-draft' }))
  assert.equal(readSource('old').input.owner, '')
  assert.equal(readSource('old').input.price, 'INR 499')
})
