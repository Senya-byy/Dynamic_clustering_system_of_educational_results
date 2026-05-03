<template>
  <div class="page-narrow">
    <h2>Ответ на паре</h2>
    <p class="page-lead">Войдите по QR или по коду и паролю от преподавателя.</p>

    <div v-if="!sessionInfo" class="ui-card">
      <div class="join-mode-row">
        <button
          type="button"
          class="ui-btn"
          :class="joinMode === 'qr' ? 'ui-btn--primary' : 'ui-btn--ghost'"
          @click="joinMode = 'qr'"
        >
          Из QR
        </button>
        <button
          type="button"
          class="ui-btn"
          :class="joinMode === 'manual' ? 'ui-btn--primary' : 'ui-btn--ghost'"
          @click="joinMode = 'manual'"
        >
          Код и пароль
        </button>
      </div>

      <template v-if="joinMode === 'qr'">
        <label class="ui-label" for="code">Код пары</label>
        <input id="code" v-model="sessionCode" class="ui-input" placeholder="Например AB12CD" />

        <label class="ui-label" for="nonce">Nonce</label>
        <input id="nonce" v-model="nonce" class="ui-input" placeholder="Из ссылки после сканирования QR" />

        <div class="ui-actions">
          <button type="button" class="ui-btn ui-btn--primary" @click="verifyTicket">Получить вопрос</button>
        </div>
      </template>

      <template v-else>
        <label class="ui-label" for="mcode">Код пары</label>
        <input id="mcode" v-model="manualCode" class="ui-input" placeholder="Как у преподавателя" />

        <label class="ui-label" for="mpin">Пароль пары (6 цифр)</label>
        <input
          id="mpin"
          v-model="manualPin"
          class="ui-input"
          inputmode="numeric"
          maxlength="12"
          placeholder="000000"
          autocomplete="one-time-code"
        />

        <div class="ui-actions">
          <button type="button" class="ui-btn ui-btn--primary" @click="verifyManual">Получить вопрос</button>
        </div>
      </template>

      <p v-if="verifyError" class="ui-alert ui-alert--error">{{ verifyError }}</p>
    </div>

    <div v-else-if="!answerSubmitted" class="ui-card">
      <h3>{{ sessionInfo.question.text }}</h3>
      <p class="ui-meta">
        Тема: <strong>{{ sessionInfo.question.topic || '—' }}</strong> · Сложность:
        <span class="ui-badge ui-badge--accent">{{ sessionInfo.question.difficulty || '—' }}</span>
        · Макс. баллов: <strong>{{ sessionInfo.question.max_score }}</strong>
      </p>
      <label class="ui-label" for="ans">Ваш ответ</label>
      <textarea id="ans" v-model="answerText" class="ui-textarea" rows="6" placeholder="Введите развёрнутый ответ" />
      <div class="ui-actions">
        <button type="button" class="ui-btn ui-btn--primary" @click="submitAnswer">Отправить</button>
      </div>
      <p v-if="submitError" class="ui-alert ui-alert--error">{{ submitError }}</p>
      <div v-if="sessionInfo.timer_seconds" class="ui-timer">Таймер пары: {{ timerDisplay }}</div>
    </div>

    <div v-else class="ui-card ui-card--success">
      <p style="margin: 0 0 1rem">Ответ отправлен, посещение зафиксировано. Дождитесь проверки.</p>
      <button type="button" class="ui-btn ui-btn--secondary" @click="goAnswers">Мои ответы и обратная связь</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import api from '../api'
import { getDeviceId } from '../utils/deviceId'
import { useRouter, useRoute } from 'vue-router'

const joinMode = ref('qr')
const sessionCode = ref('')
const nonce = ref('')
const manualCode = ref('')
const manualPin = ref('')
const sessionInfo = ref(null)
const answerText = ref('')
const answerSubmitted = ref(false)
const verifyError = ref('')
const submitError = ref('')
const timerSeconds = ref(0)
let timerInterval = null
const router = useRouter()
const route = useRoute()

const loadFromJoin = () => {
  const raw = sessionStorage.getItem('active_session_payload')
  if (!raw) return false
  try {
    sessionInfo.value = JSON.parse(raw)
    sessionCode.value = sessionInfo.value.code
    sessionStorage.removeItem('active_session_payload')
    if (sessionInfo.value.timer_seconds) {
      timerSeconds.value = sessionInfo.value.timer_seconds
      startTimer()
    }
    return true
  } catch {
    return false
  }
}

onMounted(() => {
  if (route.query.from === 'join' && loadFromJoin()) {
    return
  }
})

watch(
  () => route.fullPath,
  () => {
    if (route.query.from === 'join' && loadFromJoin()) {
      verifyError.value = ''
    }
  }
)

const verifyTicket = async () => {
  verifyError.value = ''
  const code = sessionCode.value.trim()
  const n = nonce.value.trim()
  if (!code || !n) {
    verifyError.value = 'Введите код пары и nonce из ссылки'
    return
  }
  try {
    const res = await api.post('/sessions/verify-ticket', {
      code,
      nonce: n,
      device_id: getDeviceId()
    })
    applySessionPayload(res.data)
  } catch (e) {
    verifyError.value = e.response?.data?.error || 'Ошибка'
  }
}

const applySessionPayload = (data) => {
  sessionInfo.value = data
  sessionCode.value = data.code
  if (data.timer_seconds) {
    timerSeconds.value = data.timer_seconds
    startTimer()
  }
}

const verifyManual = async () => {
  verifyError.value = ''
  const code = manualCode.value.trim()
  const pin = manualPin.value.trim().replace(/\D/g, '')
  if (!code) {
    verifyError.value = 'Введите код пары'
    return
  }
  if (pin.length !== 6) {
    verifyError.value = 'Пароль — ровно 6 цифр'
    return
  }
  try {
    const res = await api.post('/sessions/verify-pin', {
      code,
      join_pin: pin,
      device_id: getDeviceId()
    })
    applySessionPayload(res.data)
  } catch (e) {
    verifyError.value = e.response?.data?.error || 'Ошибка'
  }
}

const startTimer = () => {
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    if (timerSeconds.value > 0) timerSeconds.value--
  }, 1000)
}

const submitAnswer = async () => {
  const text = answerText.value.trim()
  if (!text) {
    submitError.value = 'Введите текст ответа'
    return
  }
  submitError.value = ''
  try {
    await api.post('/answers/submit', {
      session_code: sessionCode.value.trim(),
      text,
      device_id: getDeviceId()
    })
    answerSubmitted.value = true
    if (timerInterval) clearInterval(timerInterval)
  } catch (e) {
    submitError.value = e.response?.data?.error || 'Не удалось отправить ответ'
  }
}

const goAnswers = () => {
  router.push('/my-answers')
}

const timerDisplay = computed(() => {
  const t = timerSeconds.value
  const min = Math.floor(t / 60)
  const sec = t % 60
  return `${min}:${sec < 10 ? '0' : ''}${sec}`
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})
</script>

<style scoped>
.join-mode-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
</style>
