<template>
  <noscript v-if="isProd">
    <div>
      <img
        src="https://mc.yandex.ru/watch/109012791"
        style="position: absolute; left: -9999px"
        alt=""
      />
    </div>
  </noscript>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import router from '../router'

const isProd = import.meta.env.PROD

const COUNTER_ID = 109012791
const TAG_SRC = 'https://mc.yandex.ru/metrika/tag.js?ids=109012791'

let removeAfterEach = null

onMounted(() => {
  if (!isProd || typeof document === 'undefined') return

  const w = window
  const d = document
  const i = 'ym'

  for (let j = 0; j < d.scripts.length; j++) {
    if (d.scripts[j].src === TAG_SRC) return
  }

  w[i] =
    w[i] ||
    function () {
      ;(w[i].a = w[i].a || []).push(arguments)
    }
  w[i].l = Date.now()

  const anchor = d.getElementsByTagName('script')[0]
  const s = d.createElement('script')
  s.type = 'text/javascript'
  s.async = true
  s.src = TAG_SRC

  s.onload = () => {
    if (typeof w[i] !== 'function') return

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
  }

  const parent = anchor?.parentNode || d.head || d.body
  if (anchor) {
    parent.insertBefore(s, anchor)
  } else {
    parent.appendChild(s)
  }
})

onBeforeUnmount(() => {
  removeAfterEach?.()
  removeAfterEach = null
})
</script>
