import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

const YANDEX_METRIKA_ID = '109012791'
const YANDEX_TAG_SRC = `https://mc.yandex.ru/metrika/tag.js?ids=${YANDEX_METRIKA_ID}`

/** В production-сборке добавляет в index.html теги, которые видит проверка Метрики без выполнения Vue. */
function yandexMetrikaStaticHtml() {
  return {
    name: 'yandex-metrika-static-html',
    transformIndexHtml(html) {
      const inject = `
  <script async src="${YANDEX_TAG_SRC}"></script>
  <noscript><div><img src="https://mc.yandex.ru/watch/${YANDEX_METRIKA_ID}" style="position:absolute;left:-9999px" alt="" /></div></noscript>
`
      return html.replace('</body>', `${inject}</body>`)
    },
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // 5000 часто занят AirPlay на macOS; бэкенд по умолчанию для локальной разработки — 5001
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:5001'
  return {
    plugins: [vue(), ...(mode === 'production' ? [yandexMetrikaStaticHtml()] : [])],
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
