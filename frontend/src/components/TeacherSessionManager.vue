<template>
  <div class="page-narrow">
    <h2>Пары и динамический QR</h2>
    <p class="page-lead">
      QR обновляется каждую секунду; каждый код в ссылке действует около 5 секунд, за это время могут войти несколько студентов. Ссылка в QR должна вести на адрес
      <strong>вашего ноутбука в Wi‑Fi</strong>, а не на <code class="ui-badge">localhost</code> — иначе телефон
      откроет страницу у себя.
    </p>
    <p v-if="isLocalHostPage && qrFrontendOrigin" class="ui-alert" style="margin-top: 0.75rem">
      Для QR используется адрес ноутбука в сети:
      <strong>{{ qrFrontendOrigin }}</strong>
      (запрос к API подставил его вместо localhost).
    </p>
    <p
      v-else-if="isLocalHostPage && !qrFrontendOrigin"
      class="ui-alert ui-alert--error"
      style="margin-top: 0.75rem"
    >
      Не удалось получить IP для QR. Откройте эту вкладку как
      <code class="ui-badge">http://&lt;IP-ноутбука&gt;:5173</code>
      или задайте в <code class="ui-badge">.env</code> переменную
      <code class="ui-badge">VITE_QR_ORIGIN=http://IP:5173</code>
      и перезапустите Vite.
    </p>

    <form class="ui-card" @submit.prevent="startSession">
      <label class="ui-label">Группа</label>
      <select v-model="selectedGroupId" class="ui-select" required>
        <option disabled value="">Выберите группу</option>
        <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
      </select>

      <label class="ui-label">Один вопрос (фиксированный)</label>
      <select v-model="selectedQuestionId" class="ui-select">
        <option value="">—</option>
        <option v-for="q in questions" :key="q.id" :value="q.id">{{ q.text.slice(0, 72) }}…</option>
      </select>

      <label class="ui-label">Пул по темам каталога</label>
      <p class="page-lead" style="margin: 0 0 0.5rem; font-size: 0.9rem">
        Учитываются только вопросы с «Темой из каталога». Каждому студенту при первом входе по QR выдаётся
        <strong>свой</strong> вопрос из пула (по возможности разные; если вопросов мало — повторения). Вопрос
        закрепляется до отправки ответа. После ответа повторный вход по QR невозможен.
      </p>
      <select v-model="poolTopicIds" multiple class="ui-select ui-select--multi">
        <option v-for="t in topics" :key="'tp' + t.id" :value="t.id">
          {{ t.name }} ({{ questionCountByTopic[t.id] || 0 }} вопр.)
        </option>
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
        <li v-for="s in mySessions" :key="s.id" class="session-row">
          <div class="session-info">
            <span class="ui-badge ui-badge--accent">{{ s.code }}</span>
            <template v-if="editingTitleId !== s.id">
              <span class="session-title-text">{{ sessionDisplayTitle(s) }}</span>
              <span class="ui-meta">{{ s.is_active ? 'активна' : 'закрыта' }}</span>
            </template>
            <template v-else>
              <input
                v-model="titleDraft"
                class="ui-input session-title-input"
                maxlength="250"
                placeholder="Название занятия"
              />
              <span class="title-edit-actions">
                <button type="button" class="ui-btn ui-btn--primary" @click="saveSessionTitle(s)">Сохранить</button>
                <button type="button" class="ui-btn ui-btn--ghost" @click="cancelEditTitle">Отмена</button>
              </span>
            </template>
          </div>
          <span class="li-actions">
            <button
              v-if="editingTitleId !== s.id"
              type="button"
              class="ui-btn ui-btn--ghost"
              @click="beginEditTitle(s)"
            >
              Название
            </button>
            <button v-if="s.is_active" type="button" class="ui-btn ui-btn--ghost" @click="goLive(s)">QR</button>
            <button v-if="s.is_active" type="button" class="ui-btn ui-btn--danger" @click="closeSession(s.id)">Закрыть</button>
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../api'

const isLocalHostPage = computed(() => {
  if (typeof window === 'undefined') return false
  const h = window.location.hostname
  return h === 'localhost' || h === '127.0.0.1'
})

const qrFrontendOrigin = ref('')

const resolveQrOrigin = () => {
  const env = (import.meta.env.VITE_QR_ORIGIN || '').trim()
  if (env) return env
  if (qrFrontendOrigin.value) return qrFrontendOrigin.value
  const h = window.location.hostname
  if (h === 'localhost' || h === '127.0.0.1') {
    return ''
  }
  return window.location.origin
}

const frontendDevPort = () => {
  const p = parseInt(window.location.port, 10)
  if (p > 0) return p
  return window.location.protocol === 'https:' ? 443 : 80
}

const groups = ref([])
const questions = ref([])
const topics = ref([])

const questionCountByTopic = computed(() => {
  const m = {}
  for (const q of questions.value) {
    const tid = q.topic_id
    if (tid != null) {
      m[tid] = (m[tid] || 0) + 1
    }
  }
  return m
})

const selectedGroupId = ref('')
const selectedQuestionId = ref('')
const poolTopicIds = ref([])
const timerSeconds = ref('')
const liveQr = ref('')
const sessionCode = ref('')
const activeSessionId = ref(null)
const mySessions = ref([])
const editingTitleId = ref(null)
const titleDraft = ref('')
let pollTimer = null

const formatDefaultTitleFromIso = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const yyyy = d.getFullYear()
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `Занятие - ${dd}.${mm}.${yyyy} в ${hh}:${mi}`
}

const sessionDisplayTitle = (s) => s.display_title || formatDefaultTitleFromIso(s.start_time)

const beginEditTitle = (s) => {
  editingTitleId.value = s.id
  titleDraft.value = sessionDisplayTitle(s)
}

const cancelEditTitle = () => {
  editingTitleId.value = null
  titleDraft.value = ''
}

const saveSessionTitle = async (s) => {
  const t = titleDraft.value.trim()
  try {
    const res = await api.patch(`/sessions/${s.id}/title`, { title: t || null })
    s.display_title = res.data.display_title
    s.title = res.data.title
    cancelEditTitle()
  } catch (e) {
    alert(e.response?.data?.error || 'Не удалось сохранить')
  }
}

const fetchGroups = async () => {
  const res = await api.get('/groups')
  groups.value = res.data
}
const fetchQuestions = async () => {
  const res = await api.get('/questions')
  questions.value = res.data
}
const fetchTopics = async () => {
  const res = await api.get('/topics')
  topics.value = res.data
}
const fetchSessions = async () => {
  const res = await api.get('/sessions/teacher')
  mySessions.value = res.data
}

const pollQr = async () => {
  if (!activeSessionId.value) return
  const res = await api.get(`/sessions/${activeSessionId.value}/live-qr`, {
    params: { port: frontendDevPort() },
    headers: { 'X-Frontend-Origin': resolveQrOrigin() },
  })
  liveQr.value = res.data.qr_code
  sessionCode.value = res.data.code
}

const startSession = async () => {
  const body = {
    group_id: Number(selectedGroupId.value),
    timer_seconds: timerSeconds.value ? parseInt(timerSeconds.value, 10) : null
  }
  const tpool = poolTopicIds.value.map((x) => parseInt(x, 10)).filter(Boolean)
  if (tpool.length) {
    body.topic_ids = tpool
  } else if (selectedQuestionId.value) {
    body.question_id = parseInt(selectedQuestionId.value, 10)
  } else {
    alert('Выберите один вопрос или одну/несколько тем для пула')
    return
  }
  try {
    const res = await api.post('/sessions', body)
    activeSessionId.value = res.data.id
    sessionCode.value = res.data.code
    await fetchSessions()
    stopLive()
    pollTimer = setInterval(pollQr, 1000)
    await pollQr()
  } catch (e) {
    alert(e.response?.data?.error || 'Не удалось создать сессию')
  }
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

onMounted(async () => {
  fetchGroups()
  fetchQuestions()
  fetchTopics()
  fetchSessions()
  if (isLocalHostPage.value) {
    try {
      const port = window.location.port || '5173'
      const res = await api.get('/meta/qr-origin', { params: { port } })
      if (res.data?.origin) {
        qrFrontendOrigin.value = res.data.origin
      }
    } catch {
      /* сеть / бэкенд недоступен — покажем подсказку про IP вручную */
    }
  }
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
.session-row {
  align-items: flex-start;
  gap: 0.75rem;
}
.session-info {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 0;
  flex: 1;
}
.session-title-text {
  font-weight: 600;
  line-height: 1.35;
}
.session-title-input {
  max-width: 100%;
}
.title-edit-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
</style>
