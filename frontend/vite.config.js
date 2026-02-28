import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',  // Listen on all interfaces
    strictPort: false,
  },
  // Force localhost API even in production build
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify('http://localhost:8000')
  }
})
