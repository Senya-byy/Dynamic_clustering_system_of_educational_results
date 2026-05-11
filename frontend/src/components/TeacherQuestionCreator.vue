<template>
  <div class="page-narrow" style="max-width: 760px">
    <h2>Вопросы</h2>
    <p class="page-lead">Темы и вопросы для пар.</p>

    <div class="ui-card">
      <h3 style="margin-top: 0">Каталог тем</h3>
      <label class="ui-label">Предмет</label>
      <select v-model.number="selectedCourseId" class="ui-select" @change="onCourseChange">
        <option disabled :value="0">Выберите предмет</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <p class="ui-meta" style="margin: 0.5rem 0 0">
        Управление предметами и группами: <router-link to="/teacher/courses">Предметы</router-link>
      </p>
      <ul class="topic-chips">
        <li v-for="t in topics" :key="t.id" class="topic-chip">
          <span class="ui-badge ui-badge--accent">{{ t.name }}</span>
          <button type="button" class="ui-btn ui-btn--danger ui-btn--ghost chip-del" @click="deleteTopic(t)">
            Удалить
          </button>
        </li>
      </ul>
      <div class="ui-row" style="margin-top: 1rem">
        <input v-model="newTopicName" class="ui-input ui-grow" placeholder="Новая тема" />
        <button type="button" class="ui-btn ui-btn--secondary" @click="addTopic">Добавить</button>
      </div>
    </div>

    <form class="ui-card" @submit.prevent="createQuestion">
      <h3 style="margin-top: 0">Новый вопрос</h3>
      <label class="ui-label">Формулировка</label>
      <textarea v-model="newQuestion.text" class="ui-textarea" rows="3" required placeholder="Текст вопроса" />
      <label class="ui-label">Тема (текст)</label>
      <input v-model="newQuestion.topic" class="ui-input" placeholder="Кратко (если не выбрана тема из каталога)" />
      <label class="ui-label">Тема из каталога</label>
      <select v-model.number="newQuestion.topic_id" class="ui-select">
        <option :value="null">—</option>
        <option v-for="t in topics" :key="'sel' + t.id" :value="t.id">{{ t.name }}</option>
      </select>
      <p class="page-lead" style="margin: 0 0 0.75rem; font-size: 0.85rem">Тема из списка или краткий текст — хотя бы одно.</p>
      <label class="ui-label">Сложность</label>
      <select v-model="newQuestion.difficulty" class="ui-select">
        <option value="easy">Лёгкий</option>
        <option value="medium">Средний</option>
        <option value="hard">Сложный</option>
      </select>
      <label class="ui-label">Макс. баллов</label>
      <input v-model="newQuestion.max_score" class="ui-input" type="number" min="1" max="10000" required />
      <label class="ui-label">Эталон / критерии</label>
      <textarea
        v-model="newQuestion.correct_answer"
        class="ui-textarea"
        rows="4"
        placeholder="Критерии оценки (необязательно)"
      />
      <div class="ui-actions">
        <button type="button" class="ui-btn ui-btn--ghost" @click="loadRecommendations">Подсказки</button>
        <button type="submit" class="ui-btn ui-btn--primary">Создать вопрос</button>
      </div>
      <ul v-if="recommendations.length" class="rec-list">
        <li v-for="(r, i) in recommendations" :key="i">
          <button type="button" class="ui-btn ui-btn--ghost" style="margin-right: 0.5rem" @click="applyRec(r)">Взять</button>
          <span>{{ r.text }}</span>
        </li>
      </ul>
    </form>

    <h3>Мои вопросы</h3>
    <div v-for="q in questions" :key="q.id" class="ui-card q-item">
      <p><strong>{{ q.text }}</strong></p>
      <p class="ui-meta">{{ q.max_score }} б. · {{ q.difficulty }}</p>
      <div class="ui-actions">
        <button type="button" class="ui-btn ui-btn--secondary" @click="editQuestion(q)">Изменить</button>
        <button type="button" class="ui-btn ui-btn--danger" @click="deleteQuestion(q.id)">Удалить</button>
      </div>
    </div>

    <div v-if="editing" class="ui-modal-overlay" @click.self="editing = null">
      <div class="ui-modal" @click.stop>
        <h3>Редактирование</h3>
        <label class="ui-label">Текст</label>
        <textarea v-model="editForm.text" class="ui-textarea" rows="3" required />
        <label class="ui-label">Тема</label>
        <input v-model="editForm.topic" class="ui-input" />
        <label class="ui-label">Баллы</label>
        <input v-model="editForm.max_score" class="ui-input" type="number" min="1" max="10000" />
        <label class="ui-label">Эталон</label>
        <textarea v-model="editForm.correct_answer" class="ui-textarea" rows="3" required />
        <div class="ui-actions">
          <button type="button" class="ui-btn ui-btn--primary" @click="updateQuestion">Сохранить</button>
          <button type="button" class="ui-btn ui-btn--secondary" @click="editing = null">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const questions = ref([])
const topics = ref([])
const courses = ref([])
const selectedCourseId = ref(0)
const newTopicName = ref('')
const newQuestion = ref({
  text: '',
  topic: '',
  topic_id: null,
  difficulty: 'medium',
  max_score: 1,
  correct_answer: ''
})
const editing = ref(null)
const editForm = ref({})
const recommendations = ref([])

const fetchQuestions = async () => {
  if (!selectedCourseId.value) return
  const res = await api.get('/questions', { params: { course_id: selectedCourseId.value, limit: 200, offset: 0 } })
  questions.value = res.data
}

const fetchTopics = async () => {
  if (!selectedCourseId.value) return
  const res = await api.get('/topics', { params: { course_id: selectedCourseId.value } })
  topics.value = res.data
}

const fetchCourses = async () => {
  const res = await api.get('/courses')
  courses.value = res.data || []
  if (!selectedCourseId.value && courses.value.length) {
    selectedCourseId.value = courses.value[0].id
  }
}

const onCourseChange = async () => {
  await fetchTopics()
  await fetchQuestions()
}

const addTopic = async () => {
  const name = newTopicName.value.trim()
  if (!name) {
    alert('Введите название темы')
    return
  }
  if (!selectedCourseId.value) {
    alert('Сначала выберите предмет')
    return
  }
  try {
    await api.post('/topics', { name, course_id: selectedCourseId.value })
    newTopicName.value = ''
    await fetchTopics()
  } catch (e) {
    alert(e.response?.data?.error || 'Не удалось добавить тему')
  }
}

const deleteTopic = async (t) => {
  if (
    !confirm(
      `Удалить тему «${t.name}»? Связь вопросов с этой темой в каталоге будет снята (сами вопросы останутся).`
    )
  ) {
    return
  }
  try {
    await api.delete(`/topics/${t.id}`)
    await fetchTopics()
    await fetchQuestions()
  } catch (e) {
    alert(e.response?.data?.error || 'Не удалось удалить тему')
  }
}

const loadRecommendations = async () => {
  const hint = newQuestion.value.topic || ''
  const res = await api.get('/questions/recommendations', { params: { topic: hint } })
  recommendations.value = res.data
}

const applyRec = (r) => {
  newQuestion.value.text = r.text
  newQuestion.value.correct_answer = r.criteria || ''
  newQuestion.value.difficulty = r.difficulty || 'medium'
}

const createQuestion = async () => {
  if (!selectedCourseId.value) {
    alert('Сначала выберите предмет')
    return
  }
  const q = newQuestion.value
  const text = (q.text || '').trim()
  const topicTxt = (q.topic || '').trim()
  const maxS = Number(q.max_score)
  if (!text) {
    alert('Введите формулировку вопроса')
    return
  }
  if (!Number.isFinite(maxS) || maxS < 1 || maxS > 10000) {
    alert('Максимум баллов — целое число от 1 до 10000')
    return
  }
  const body = {
    course_id: selectedCourseId.value,
    text,
    topic: topicTxt || undefined,
    topic_id: q.topic_id || undefined,
    difficulty: q.difficulty,
    max_score: maxS,
    correct_answer: (q.correct_answer || '').trim() || undefined
  }
  if (!body.topic_id) delete body.topic_id
  if (!body.topic) delete body.topic
  if (!body.correct_answer) delete body.correct_answer
  try {
    await api.post('/questions', body)
    newQuestion.value = {
      text: '',
      topic: '',
      topic_id: null,
      difficulty: 'medium',
      max_score: 1,
      correct_answer: ''
    }
    recommendations.value = []
    await fetchQuestions()
  } catch (e) {
    alert(e.response?.data?.error || 'Не удалось создать вопрос')
  }
}

const deleteQuestion = async (id) => {
  if (
    confirm(
      'Удалить вопрос? Пары (сессии), где он использовался, будут удалены вместе с ответами и билетами QR.'
    )
  ) {
    try {
      await api.delete(`/questions/${id}`)
      await fetchQuestions()
    } catch (e) {
      alert(e.response?.data?.error || 'Не удалось удалить вопрос')
    }
  }
}

const editQuestion = (q) => {
  editing.value = q.id
  editForm.value = { ...q }
}

const updateQuestion = async () => {
  const f = editForm.value
  const text = (f.text || '').trim()
  const maxS = Number(f.max_score)
  if (!text) {
    alert('Текст вопроса не может быть пустым')
    return
  }
  if (!Number.isFinite(maxS) || maxS < 1 || maxS > 10000) {
    alert('Баллы — целое число от 1 до 10000')
    return
  }
  const topicTxt = (f.topic || '').trim()
  const payload = {
    text,
    correct_answer: (f.correct_answer || '').trim() || null,
    max_score: maxS,
    difficulty: f.difficulty,
    topic_id: f.topic_id != null && f.topic_id !== '' ? Number(f.topic_id) : null
  }
  if (topicTxt) {
    payload.topic = topicTxt
  }
  try {
    await api.put(`/questions/${editing.value}`, payload)
    editing.value = null
    await fetchQuestions()
  } catch (e) {
    alert(e.response?.data?.error || 'Не удалось сохранить')
  }
}

onMounted(() => {
  fetchCourses().then(onCourseChange)
})
</script>

<style scoped>
.topic-chips {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}
.topic-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}
.chip-del {
  font-size: 0.8rem;
  padding: 0.15rem 0.5rem;
}
.rec-list {
  margin: 1rem 0 0;
  padding: 0;
  list-style: none;
  font-size: 0.9rem;
}
.rec-list li {
  padding: 0.5rem 0;
  border-top: 1px solid var(--border);
}
.q-item p {
  margin: 0 0 0.35rem;
}
</style>
