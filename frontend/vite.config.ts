import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  envDir: '../', // load .env from project root
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true, // This makes the Vite server accessible from outside the container
    port: 5179, // Default Vite dev server port
    watch: {
      usePolling: true, // Needed for hot-reloading to work reliably in Docker containers
    },
  },
})