<template>
  <div class="page-narrow" style="max-width: 900px">
    <h2>Аналитика</h2>
    <p class="page-lead">Сводка по группе, сложные вопросы и динамика студентов.</p>

    <div class="ui-card ui-card--muted">
      <label class="ui-label">Группа</label>
      <select v-model="groupId" class="ui-select" style="max-width: 400px" @change="load">
        <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
      </select>
    </div>

    <div v-if="data" class="analytics-grid">
      <div class="ui-card">
        <h3 style="margin-top: 0">Сводка</h3>
        <p class="stat-big">{{ data.sessions_count }}</p>
        <p class="ui-meta" style="margin: 0">активных сессий в выборке</p>
      </div>
      <div class="ui-card span-2">
        <h3 style="margin-top: 0">Сложные вопросы</h3>
        <ul class="plain-list">
          <li v-for="q in data.hardest_questions" :key="q.question_id">
            {{ q.text }} — средний <strong>{{ q.avg_score }}</strong>, верных {{ q.percent_correct }}%
          </li>
        </ul>
      </div>
      <div class="ui-card span-2">
        <h3 style="margin-top: 0">Студенты</h3>
        <div v-for="s in data.student_cards" :key="s.student_id" class="student-row">
          <div>
            <strong>{{ s.name }}</strong>
            <p class="spark">{{ s.results_timeline.map((x) => x.score ?? '—').join(' → ') }}</p>
          </div>
          <button type="button" class="ui-btn ui-btn--ghost" @click="loadStudent(s.student_id)">Подробнее</button>
        </div>
      </div>
    </div>

    <div v-if="studentDetail" class="ui-card">
      <h3 style="margin-top: 0">{{ studentDetail.name }}</h3>
      <ul class="plain-list">
        <li v-for="(t, i) in studentDetail.timeline" :key="i">
          {{ t.date }} · {{ t.topic || '—' }} · {{ t.score ?? '—' }} / {{ t.max_score ?? '—' }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const groups = ref([])
const groupId = ref('')
const data = ref(null)
const studentDetail = ref(null)

const load = async () => {
  studentDetail.value = null
  if (!groupId.value) return
  const res = await api.get('/analytics/group', { params: { group_id: groupId.value } })
  data.value = res.data
}

const loadStudent = async (id) => {
  const res = await api.get(`/analytics/student/${id}`)
  studentDetail.value = res.data
}

onMounted(async () => {
  const res = await api.get('/groups')
  groups.value = res.data
  if (res.data.length) {
    groupId.value = res.data[0].id
    await load()
  }
})
</script>

<style scoped>
.analytics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
@media (max-width: 700px) {
  .analytics-grid {
    grid-template-columns: 1fr;
  }
}
.span-2 {
  grid-column: span 2;
}
@media (max-width: 700px) {
  .span-2 {
    grid-column: span 1;
  }
}
.stat-big {
  font-size: 2.5rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--accent);
  margin: 0.25rem 0;
}
.plain-list {
  margin: 0;
  padding-left: 1.2rem;
  color: var(--text-muted);
  line-height: 1.6;
}
.student-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border);
}
.student-row:last-child {
  border-bottom: none;
}
.spark {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0.25rem 0 0;
}
</style>
