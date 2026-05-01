<template>
  <div class="page-narrow" style="padding-top: 1rem">
    <div class="ui-card">
      <h2 style="margin-top: 0">Вход по QR</h2>
      <p v-if="loading" class="ui-meta">Проверка билета…</p>
      <p v-else-if="err" class="ui-alert ui-alert--error">{{ err }}</p>
      <template v-else>
        <p class="page-lead" style="margin-bottom: 1rem">
          В ссылке нет параметров <code class="ui-badge">code</code> и
          <code class="ui-badge">nonce</code>. Отсканируйте актуальный QR у преподавателя (ссылка из QR действует несколько секунд).
        </p>
        <router-link to="/student/quiz" class="ui-btn ui-btn--secondary" style="display: inline-block; text-decoration: none">Ручной ввод кода</router-link>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { getDeviceId } from '../utils/deviceId'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const err = ref('')

onMounted(async () => {
  const code = route.query.code
  const nonce = route.query.nonce
  if (!code || !nonce) {
    loading.value = false
    return
  }
  try {
    const res = await api.post('/sessions/verify-ticket', {
      code,
      nonce,
      device_id: getDeviceId()
    })
    sessionStorage.setItem('active_session_payload', JSON.stringify(res.data))
    router.replace({ path: '/student/quiz', query: { from: 'join' } })
  } catch (e) {
    err.value = e.response?.data?.error || 'Не удалось войти'
    loading.value = false
  }
})
</script>
