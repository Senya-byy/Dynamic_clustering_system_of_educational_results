<template>
  <span class="ym-app-hook" aria-hidden="true" />
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import router from '../router'

const isProd = import.meta.env.PROD

const COUNTER_ID = 109012791
const TAG_SRC = 'https://mc.yandex.ru/metrika/tag.js?ids=109012791'

let removeAfterEach = null

function findTagScript() {
  if (typeof document === 'undefined') return null
  for (let j = 0; j < document.scripts.length; j++) {
    if (document.scripts[j].src === TAG_SRC) return document.scripts[j]
  }
  return null
}

function ensureYmStub(w) {
  const i = 'ym'
  w[i] =
    w[i] ||
    function () {
      ;(w[i].a = w[i].a || []).push(arguments)
    }
  w[i].l = Date.now()
}

onMounted(() => {
  if (!isProd || typeof document === 'undefined') return

  const w = window
  const d = document
  const i = 'ym'

  ensureYmStub(w)

  if (!findTagScript()) {
    const anchor = d.getElementsByTagName('script')[0]
    const s = d.createElement('script')
    s.type = 'text/javascript'
    s.async = true
    s.src = TAG_SRC
    const parent = anchor?.parentNode || d.head || d.body
    if (anchor) parent.insertBefore(s, anchor)
    else parent.appendChild(s)
  }

  if (w.__ymClassqrInited) return
  w.__ymClassqrInited = true

  let lastTrackedUrl = w.location.href

  w[i](COUNTER_ID, 'init', {
    ssr: true,
    webvisor: true,
    clickmap: true,
    ecommerce: 'dataLayer',
    referrer: d.referrer,
    url: w.location.href,
    accurateTrackBounce: true,
    trackLinks: true,
  })

  removeAfterEach = router.afterEach(() => {
    const href = w.location.href
    if (href === lastTrackedUrl) return
    lastTrackedUrl = href
    w[i](COUNTER_ID, 'hit', href)
  })
})

onBeforeUnmount(() => {
  removeAfterEach?.()
  removeAfterEach = null
})
</script>

<style scoped>
.ym-app-hook {
  display: none;
}
</style>
