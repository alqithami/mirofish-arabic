import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const isGitHubPages = process.env.GITHUB_ACTIONS === 'true'

export default defineConfig({
  base: isGitHubPages ? '/mirofish-arabic/' : '/',
  plugins: [vue()],
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
