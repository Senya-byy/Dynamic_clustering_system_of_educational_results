<template>
  <div class="page-narrow" style="max-width: 800px">
    <h2>Проверка ответов</h2>
    <p class="page-lead">Выберите сессию и выставьте баллы или воспользуйтесь быстрой оценкой.</p>

    <div class="ui-card ui-card--muted">
      <label class="ui-label">Сессия</label>
      <select v-model="selectedSessionId" class="ui-select" @change="loadAnswers">
        <option disabled value="">Выберите сессию</option>
        <option v-for="s in sessions" :key="s.id" :value="s.id">
          {{ s.display_title || s.code }} · {{ s.code }}
        </option>
      </select>
    </div>

    <div v-if="selectedSessionId" class="ui-card ui-card--muted" style="margin-bottom: 1rem">
      <div class="ui-actions" style="justify-content: space-between; gap: 0.75rem; flex-wrap: wrap">
        <div class="ui-meta" style="margin: 0">
          Непроверено: <strong>{{ pendingAnswers.length }}</strong>
          · Проверено: <strong>{{ reviewedAnswers.length }}</strong>
        </div>
        <div class="ui-actions" style="margin: 0; gap: 0.5rem">
          <button
            type="button"
            class="ui-btn"
            :class="tab === 'pending' ? 'ui-btn--primary' : ''"
            @click="tab = 'pending'"
          >
            Непроверено
          </button>
          <button
            type="button"
            class="ui-btn"
            :class="tab === 'reviewed' ? 'ui-btn--primary' : ''"
            @click="tab = 'reviewed'"
          >
            Проверено
          </button>
        </div>
      </div>
    </div>

    <div v-for="ans in visibleAnswers" :key="ans.id" class="ui-card answer-card">
      <p class="head-line">
        <strong>{{ ans.student_name }}</strong>
        <span class="ui-meta" style="margin: 0"> · {{ ans.submitted_at }}</span>
        <span v-if="ans.is_late" class="ui-badge" style="margin-left: 0.5rem">Опоздание</span>
        <span v-if="ans.checked_at || ans._justReviewed" class="ui-badge" style="margin-left: 0.5rem">Проверено</span>
      </p>

      <div class="question-block">
        <p class="q-label">Вопрос</p>
        <p class="q-text">{{ ans.question_text || '—' }}</p>
        <p class="q-meta">
          Тема: <strong>{{ ans.question_topic || '—' }}</strong>
          · Сложность: <strong>{{ ans.question_difficulty || '—' }}</strong>
          · Макс. балл: <strong>{{ ans.question_max_score ?? ans.max_score }}</strong>
        </p>
      </div>

      <p class="ans-label">Ответ студента</p>
      <p class="body">{{ ans.text }}</p>
      <div class="quick">
        <span class="ui-meta" style="margin: 0">Быстро:</span>
        <button type="button" class="ui-btn ok-btn" @click="quickGrade(ans, true)">Верно (макс.)</button>
        <button type="button" class="ui-btn bad-btn" @click="quickGrade(ans, false)">Неверно (0)</button>
      </div>
      <label class="ui-label">Баллы (макс. {{ ans.max_score }})</label>
      <input v-model.number="ans.score" class="ui-input" type="number" :min="0" :max="ans.max_score" />
      <label class="ui-label">Комментарий</label>
      <textarea v-model="ans.comment" class="ui-textarea" rows="3" placeholder="Комментарий для студента" />
      <div class="ui-actions">
        <button type="button" class="ui-btn ui-btn--primary" @click="gradeAnswer(ans)">Сохранить</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'

const sessions = ref([])
const selectedSessionId = ref('')
const answers = ref([])
const tab = ref('pending')

const fetchSessions = async () => {
  const res = await api.get('/sessions/teacher')
  sessions.value = res.data
}

const loadAnswers = async () => {
  if (!selectedSessionId.value) return
  const res = await api.get(`/sessions/${selectedSessionId.value}/answers`)
  answers.value = res.data
  tab.value = 'pending'
}

const isReviewed = (ans) => Boolean(ans.checked_at || ans._justReviewed)

const pendingAnswers = computed(() => answers.value.filter((a) => !isReviewed(a)))
const reviewedAnswers = computed(() => answers.value.filter((a) => isReviewed(a)))

const visibleAnswers = computed(() => {
  return tab.value === 'reviewed' ? reviewedAnswers.value : pendingAnswers.value
})

const gradeAnswer = async (ans) => {
  const mx = Number(ans.max_score ?? ans.question_max_score ?? 0)
  let sc = Number(ans.score)
  if (!Number.isFinite(sc)) {
    alert('Укажите баллы числом')
    return
  }
  sc = Math.round(sc)
  if (sc < 0 || sc > mx) {
    alert(`Баллы должны быть от 0 до ${mx}`)
    return
  }
  try {
    const res = await api.post(`/answers/${ans.id}/grade`, {
      score: sc,
      comment: (ans.comment || '').trim(),
      is_correct: ans.is_correct
    })
    ans.score = sc
    // UX: сразу убираем из "Непроверено" в "Проверено" без перезагрузки списка
    ans._justReviewed = true
    if (res?.data?.checked_at) {
      ans.checked_at = res.data.checked_at
    }
  } catch (e) {
    alert(e.response?.data?.error || 'Не удалось сохранить оценку')
  }
}

const quickGrade = async (ans, ok) => {
  ans.score = ok ? ans.max_score : 0
  ans.is_correct = ok
  if (!ans.comment) {
    ans.comment = ok ? 'Верно (быстрая оценка)' : 'Неверно (быстрая оценка)'
  }
  await gradeAnswer(ans)
}

onMounted(fetchSessions)
</script>

<style scoped>
.question-block {
  margin: 0.75rem 0 1rem;
  padding: 0.85rem 1rem;
  background: rgba(99, 102, 241, 0.06);
  border: 1px solid var(--border);
  border-radius: 10px;
}
.q-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--accent);
  font-weight: 700;
  margin: 0 0 0.35rem;
}
.q-text {
  margin: 0 0 0.5rem;
  line-height: 1.5;
  white-space: pre-wrap;
}
.q-meta {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.45;
}
.ans-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  margin: 0 0 0.25rem;
}
.body {
  white-space: pre-wrap;
  line-height: 1.55;
  margin: 0.5rem 0 1rem;
}
.quick {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.75rem;
}
.ok-btn {
  background: #059669;
  color: #fff;
  font-size: 0.8125rem;
  padding: 0.45rem 0.9rem;
}
.ok-btn:hover {
  background: #047857;
}
.bad-btn {
  background: #e11d48;
  color: #fff;
  font-size: 0.8125rem;
  padding: 0.45rem 0.9rem;
}
.bad-btn:hover {
  background: #be123c;
}
.head-line {
  margin: 0 0 0.25rem;
}
</style>
