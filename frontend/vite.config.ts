import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 2000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined

          if (id.includes('react-globe.gl') || id.includes('/three/')) {
            return 'vendor-globe'
          }

          if (id.includes('leaflet') || id.includes('react-leaflet')) {
            return 'vendor-map'
          }

          if (id.includes('jspdf') || id.includes('html2canvas')) {
            return 'vendor-export'
          }

          if (
            id.includes('echarts') ||
            id.includes('recharts') ||
            id.includes('reactflow') ||
            id.includes('@reactflow')
          ) {
            return 'vendor-visuals'
          }

          if (id.includes('react-markdown') || id.includes('remark-gfm')) {
            return 'vendor-markdown'
          }

          if (
            id.includes('/react/') ||
            id.includes('/react-dom/') ||
            id.includes('react-router-dom') ||
            id.includes('@tanstack/react-query') ||
            id.includes('zustand')
          ) {
            return 'vendor-core'
          }

          return 'vendor-misc'
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
