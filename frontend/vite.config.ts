import react from '@vitejs/plugin-react'
import { defineConfig,loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({mode}) => {
  const target=loadEnv(mode,process.cwd(),'').BRANDPROOF_API_TARGET || 'http://127.0.0.1:8000'
  return {
  plugins: [react()],
  server: { proxy: { '/api': target } },
  preview: { proxy: { '/api': target } },
}})
