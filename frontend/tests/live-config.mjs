export const apiBase = (process.env.BRANDPROOF_TEST_API_URL || 'http://127.0.0.1:8001/api/v1').replace(/\/$/, '')

export async function verifyBackend() {
  const contractUrl = new URL('/openapi.json', apiBase)
  let response
  try {
    response = await fetch(contractUrl, { signal: AbortSignal.timeout(5000) })
  } catch {
    throw new Error(`BrandProof integration blocked: cannot reach ${contractUrl}. Start the authorised backend before testing.`)
  }
  if (!response.ok) throw new Error(`BrandProof integration blocked: OpenAPI returned HTTP ${response.status}.`)
  const contract = await response.json()
  if (contract.info?.title !== 'BrandProof API' || !contract.paths?.['/api/v1/demo-sessions']) {
    throw new Error('BrandProof integration blocked: target is not the BrandProof API. No test session was created.')
  }
}
