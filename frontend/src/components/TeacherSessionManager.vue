<template>
  <div class="page-narrow">
    <h2>Пары и динамический QR</h2>
    <p class="page-lead">
      QR обновляется каждую секунду, nonce одноразовый. Для ссылки в QR используется заголовок
      <code class="ui-badge">X-Frontend-Origin</code> (ставится автоматически).
    </p>

    <form class="ui-card" @submit.prevent="startSession">
      <label class="ui-label">Группа</label>
      <select v-model="selectedGroupId" class="ui-select" required>
        <option disabled value="">Выберите группу</option>
        <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
      </select>

      <label class="ui-label">Один вопрос</label>
      <select v-model="selectedQuestionId" class="ui-select">
        <option value="">—</option>
        <option v-for="q in questions" :key="q.id" :value="q.id">{{ q.text.slice(0, 72) }}…</option>
      </select>

      <label class="ui-label">Пул вопросов (случайный)</label>
      <select v-model="poolSelected" multiple class="ui-select ui-select--multi">
        <option v-for="q in questions" :key="'p' + q.id" :value="q.id">{{ q.id }}: {{ q.text.slice(0, 48) }}…</option>
      </select>

      <label class="ui-label">Таймер (сек), опционально</label>
      <input v-model="timerSeconds" class="ui-input" type="number" min="0" placeholder="300" />

      <div class="ui-actions">
        <button type="submit" class="ui-btn ui-btn--primary">Создать сессию</button>
      </div>
    </form>

    <div v-if="activeSessionId" class="ui-card qr-panel">
      <h3>Живой QR</h3>
      <img v-if="liveQr" :src="liveQr" alt="QR" class="qr-img" />
      <p class="mono">Код: <strong>{{ sessionCode }}</strong></p>
      <p class="page-lead" style="margin-bottom: 0.75rem">Студент входит по ссылке из QR (роль student).</p>
      <button type="button" class="ui-btn ui-btn--secondary" @click="stopLive">Остановить обновление</button>
    </div>

    <div class="ui-card">
      <h3>Мои сессии</h3>
      <ul class="ui-list">
        <li v-for="s in mySessions" :key="s.id">
          <span>
            <span class="ui-badge ui-badge--accent">{{ s.code }}</span>
            {{ s.is_active ? 'активна' : 'закрыта' }} · {{ s.start_time }}
          </span>
          <span class="li-actions">
            <button v-if="s.is_active" type="button" class="ui-btn ui-btn--ghost" @click="goLive(s)">QR</button>
            <button v-if="s.is_active" type="button" class="ui-btn ui-btn--danger" @click="closeSession(s.id)">Закрыть</button>
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '../api'

const groups = ref([])
const questions = ref([])
const selectedGroupId = ref('')
const selectedQuestionId = ref('')
const poolSelected = ref([])
const timerSeconds = ref('')
const liveQr = ref('')
const sessionCode = ref('')
const activeSessionId = ref(null)
const mySessions = ref([])
let pollTimer = null

const fetchGroups = async () => {
  const res = await api.get('/groups')
  groups.value = res.data
}
const fetchQuestions = async () => {
  const res = await api.get('/questions')
  questions.value = res.data
}
const fetchSessions = async () => {
  const res = await api.get('/sessions/teacher')
  mySessions.value = res.data
}

const pollQr = async () => {
  if (!activeSessionId.value) return
  const res = await api.get(`/sessions/${activeSessionId.value}/live-qr`, {
    headers: { 'X-Frontend-Origin': window.location.origin }
  })
  liveQr.value = res.data.qr_code
  sessionCode.value = res.data.code
}

const startSession = async () => {
  const body = {
    group_id: Number(selectedGroupId.value),
    timer_seconds: timerSeconds.value ? parseInt(timerSeconds.value, 10) : null
  }
  const pool = poolSelected.value.map((x) => parseInt(x, 10)).filter(Boolean)
  if (pool.length) {
    body.question_ids = pool
  } else if (selectedQuestionId.value) {
    body.question_id = parseInt(selectedQuestionId.value, 10)
  } else {
    alert('Выберите вопрос или пул')
    return
  }
  const res = await api.post('/sessions', body)
  activeSessionId.value = res.data.id
  sessionCode.value = res.data.code
  await fetchSessions()
  stopLive()
  pollTimer = setInterval(pollQr, 1000)
  await pollQr()
}

const goLive = (s) => {
  activeSessionId.value = s.id
  sessionCode.value = s.code
  stopLive()
  pollTimer = setInterval(pollQr, 1000)
  pollQr()
}

const stopLive = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const closeSession = async (id) => {
  await api.post(`/sessions/${id}/close`)
  if (activeSessionId.value === id) {
    activeSessionId.value = null
    liveQr.value = ''
    stopLive()
  }
  await fetchSessions()
}

onMounted(() => {
  fetchGroups()
  fetchQuestions()
  fetchSessions()
})

onUnmounted(() => stopLive())
</script>

<style scoped>
.qr-panel {
  text-align: center;
}
.qr-img {
  max-width: 280px;
  display: block;
  margin: 1rem auto;
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
}
.mono {
  font-family: ui-monospace, monospace;
  font-size: 0.95rem;
}
.li-actions {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
  margin-left: auto;
}
.ui-list li {
  justify-content: space-between;
}
</style>
