import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

const YANDEX_METRIKA_ID = '109024733'
const YANDEX_TAG_SRC = `https://mc.yandex.ru/metrika/tag.js?id=${YANDEX_METRIKA_ID}`

/** В production-сборке добавляет в index.html теги, которые видит проверка Метрики без выполнения Vue. */
function yandexMetrikaStaticHtml() {
  return {
    name: 'yandex-metrika-static-html',
    transformIndexHtml(html) {
      const inject = `
  <!-- Yandex.Metrika counter -->
  <script type="text/javascript">
      (function(m,e,t,r,i,k,a){
          m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
          m[i].l=1*new Date();
          for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
          k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
      })(window, document,'script','${YANDEX_TAG_SRC}', 'ym');

      ym(${YANDEX_METRIKA_ID}, 'init', {
          ssr: true,
          webvisor: true,
          clickmap: true,
          ecommerce: "dataLayer",
          referrer: document.referrer,
          url: location.href,
          accurateTrackBounce: true,
          trackLinks: true
      });

      // SPA (Vue Router): track virtual pageviews
      (function () {
          var lastUrl = location.href;
          function hit() {
              if (location.href === lastUrl) return;
              lastUrl = location.href;
              if (typeof ym === 'function') {
                  ym(${YANDEX_METRIKA_ID}, 'hit', lastUrl);
              }
          }
          try {
              var pushState = history.pushState;
              history.pushState = function () { pushState.apply(this, arguments); hit(); };
              var replaceState = history.replaceState;
              history.replaceState = function () { replaceState.apply(this, arguments); hit(); };
          } catch (e) {}
          window.addEventListener('popstate', hit);
      })();
  </script>
  <noscript><div><img src="https://mc.yandex.ru/watch/${YANDEX_METRIKA_ID}" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
  <!-- /Yandex.Metrika counter -->
`
      // ближе к началу страницы: сразу после открытия <body>
      return html.replace('<body>', `<body>${inject}`)
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
