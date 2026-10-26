import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { readCaption, saveCaption, validatePoster, MAX_IMAGE_BYTES } from '../src/contentDraft.ts'
afterEach(() => { delete globalThis.localStorage })
test('captions persist separately per review without altering campaign metadata', () => {
  const data = new Map()
  globalThis.localStorage = { getItem: key => data.get(key) ?? null, setItem: (key, value) => data.set(key, value) }
  saveCaption('one', 'Actual marketing copy')
  assert.equal(readCaption('one'), 'Actual marketing copy')
  assert.equal(readCaption('two'), '')
  saveCaption('one', '')
  assert.equal(readCaption('one'), '')
  assert.throws(() => saveCaption('one', 'x'.repeat(10001)), /exceeds/)
})
test('caption storage and corrupt data failures are not successful saves', () => {
  globalThis.localStorage = { getItem: () => '{}', setItem: () => { throw new Error('quota') } }
  assert.throws(() => readCaption('one'), /unreadable/)
  assert.throws(() => saveCaption('one', 'Draft'), /quota/)
})
test('poster validation accepts PNG and JPEG signatures', async () => {
  await validatePoster(new File([new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10])], 'poster.png', { type: 'image/png' }))
  await validatePoster(new File([new Uint8Array([255, 216, 255, 224])], 'poster.jpg', { type: 'image/jpeg' }))
})
test('poster validation rejects unsupported, empty, oversized and disguised files', async () => {
  await assert.rejects(validatePoster(new File(['svg'], 'poster.svg', { type: 'image/svg+xml' })), /PNG or JPEG/)
  await assert.rejects(validatePoster(new File([], 'empty.png', { type: 'image/png' })), /empty/)
  await assert.rejects(validatePoster(new File([new Uint8Array(MAX_IMAGE_BYTES + 1)], 'large.png', { type: 'image/png' })), /5 MB/)
  await assert.rejects(validatePoster(new File(['not an image'], 'fake.png', { type: 'image/png' })), /valid PNG or JPEG/)
})
