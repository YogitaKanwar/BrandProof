export interface Box { x: number; y: number; width: number; height: number }
export interface PosterOut {
  id: string; campaign_id: string; content_revision: number; mime: 'image/png'; sha256: string; width: number; height: number; created_at: string
  ocr: {engine: 'tesseract'; status: 'completed' | 'partial' | 'unavailable'; reason: string | null; text: string; words: (Box & {text: string; confidence: number; start: number; end: number})[]}
}
export function overlayBox(box: Box, width: number, height: number) {
  if (![box.x,box.y,box.width,box.height,width,height].every(Number.isFinite) || width <= 0 || height <= 0 || box.x < 0 || box.y < 0 || box.width <= 0 || box.height <= 0 || box.x + box.width > width || box.y + box.height > height) return null
  return { left: `${box.x/width*100}%`, top: `${box.y/height*100}%`, width: `${box.width/width*100}%`, height: `${box.height/height*100}%` }
}
