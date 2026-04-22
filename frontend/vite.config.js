import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "/security/",
  server: {
    port: 3004,      
    strictPort: true 
  }
})
