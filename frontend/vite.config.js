import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // 5000 часто занят AirPlay на macOS; бэкенд по умолчанию для локальной разработки — 5001
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:5001'
  return {
    plugins: [vue()],
    server: {
      host: true,
      port: 5173,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true
        }
      }
    }
  }
})
