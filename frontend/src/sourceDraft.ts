export const emptySource = {
  name: '', owner: '', applicability: '', version: '', validFrom: '', validUntil: '',
  guidelines: '', price: '', offerDates: '', mandatoryTerms: '', prohibitedClaims: '',
  term: '', preferred: '',
}
export type SourceInput = typeof emptySource
export interface PendingSource { input: SourceInput; status: 'pending'; origin: 'local-draft' }
function validate(input: SourceInput): SourceInput {
  const clean = { ...emptySource }
  for (const field of Object.keys(emptySource) as (keyof SourceInput)[]) {
    if (typeof input[field] !== 'string') throw new Error('Source draft is unreadable.')
    const limit = field === 'guidelines' ? 10000 : 2000
    if (input[field].length > limit) throw new Error('Source details exceed the field limits.')
    clean[field] = input[field]
  }
  for (const date of [clean.validFrom, clean.validUntil]) {
    if (date && (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !Number.isFinite(Date.parse(date)) || new Date(date).toISOString().slice(0, 10) !== date)) throw new Error('Enter a valid source date.')
  }
  if (clean.validFrom && clean.validUntil && clean.validFrom > clean.validUntil) throw new Error('Valid until must be on or after valid from.')
  return clean
}
export function readSource(reviewId: string): PendingSource {
  const raw = localStorage.getItem(`brandproof.development.source.${reviewId}`)
  if (!raw) return { input: { ...emptySource }, status: 'pending', origin: 'local-draft' }
  const parsed = JSON.parse(raw) as PendingSource
  if (!parsed || parsed.status !== 'pending' || parsed.origin !== 'local-draft' || !parsed.input) throw new Error('Source draft is unreadable. Existing data has been preserved.')
  // Older local drafts predate the optional owner field.
  return { input: validate(Object.assign({}, emptySource, parsed.input)), status: 'pending', origin: 'local-draft' }
}
export function saveSource(reviewId: string, input: SourceInput): PendingSource {
  const source: PendingSource = { input: validate(input), status: 'pending', origin: 'local-draft' }
  localStorage.setItem(`brandproof.development.source.${reviewId}`, JSON.stringify(source))
  return source
}
