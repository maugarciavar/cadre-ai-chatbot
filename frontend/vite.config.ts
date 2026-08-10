import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  preview: {
    // Railway serves this behind a dynamic *.up.railway.app host.
    host: true,
    allowedHosts: true,
  },
})
