export const MAX_IMAGE_BYTES = 5 * 1024 * 1024
export const MAX_CAPTION_LENGTH = 10000

export function readCaption(reviewId: string): string {
  const value = localStorage.getItem(`brandproof.development.caption.${reviewId}`)
  if (value === null) return ''
  const parsed: unknown = JSON.parse(value)
  if (typeof parsed !== 'string') throw new Error('Saved caption is unreadable.')
  return parsed
}

export function saveCaption(reviewId: string, caption: string) {
  if (caption.length > MAX_CAPTION_LENGTH) throw new Error('Caption exceeds 10,000 characters.')
  localStorage.setItem(`brandproof.development.caption.${reviewId}`, JSON.stringify(caption))
}

export async function validatePoster(file: File) {
  if (!['image/png', 'image/jpeg'].includes(file.type)) throw new Error('Choose a PNG or JPEG image.')
  if (!file.size) throw new Error('This image is empty. Choose another file.')
  if (file.size > MAX_IMAGE_BYTES) throw new Error('Image must be 5 MB or smaller.')
  const bytes = new Uint8Array(await file.slice(0, 8).arrayBuffer())
  const png = [137, 80, 78, 71, 13, 10, 26, 10].every((byte, index) => bytes[index] === byte)
  const jpeg = bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255
  if ((file.type === 'image/png' && !png) || (file.type === 'image/jpeg' && !jpeg)) {
    throw new Error('This file is not a valid PNG or JPEG image.')
  }
}
