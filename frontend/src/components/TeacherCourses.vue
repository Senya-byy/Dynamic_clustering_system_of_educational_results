<template>
  <div class="page-narrow" style="max-width: 760px">
    <h2>Предметы</h2>
    <p class="page-lead">Создавайте предметы и выбирайте группы, которые по ним обучаются.</p>

    <div class="ui-card">
      <h3 style="margin-top: 0">Новый предмет</h3>
      <div class="ui-row">
        <input v-model="newName" class="ui-input ui-grow" placeholder="Например: ТРПО" />
        <button type="button" class="ui-btn ui-btn--primary" @click="createCourse">Создать</button>
      </div>
      <p v-if="error" class="ui-alert ui-alert--error">{{ error }}</p>
    </div>

    <div class="ui-card">
      <h3 style="margin-top: 0">Мои предметы</h3>
      <div class="ui-row" style="align-items: flex-end">
        <div class="ui-grow">
          <label class="ui-label">Предмет</label>
          <select v-model.number="selectedCourseId" class="ui-select" @change="loadCourseGroups">
            <option disabled :value="0">Выберите</option>
            <option v-for="c in courses" :key="c.id" :value="c.id">
              {{ c.name }}<template v-if="c.archived"> (архив)</template>
            </option>
          </select>
        </div>
        <button v-if="selectedCourse" type="button" class="ui-btn ui-btn--ghost" @click="toggleArchived">
          {{ selectedCourse.archived ? 'Вернуть из архива' : 'Архивировать' }}
        </button>
      </div>

      <div v-if="selectedCourseId" style="margin-top: 1rem">
        <h4 style="margin: 0 0 0.5rem">Группы предмета</h4>
        <p class="ui-meta" style="margin: 0 0 0.75rem">
          Можно выбрать только группы, к которым у вас есть доступ. Выбранные отображаются цветными метками сверху.
        </p>
        <GroupCheckboxList v-model="selectedGroupIds" :options="courseGroupOptions" />
        <div class="ui-actions">
          <button type="button" class="ui-btn ui-btn--secondary" @click="saveGroups">Сохранить группы</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../api'
import GroupCheckboxList from './GroupCheckboxList.vue'

const courses = ref([])
const selectedCourseId = ref(0)
const courseGroups = ref([])
const selectedGroupIds = ref([])
const newName = ref('')
const error = ref('')

const courseGroupOptions = computed(() =>
  courseGroups.value.map((g) => ({ id: Number(g.id), name: g.name }))
)

const selectedCourse = computed(() => courses.value.find((c) => c.id === selectedCourseId.value) || null)

const loadCourses = async () => {
  const res = await api.get('/courses', { params: { include_archived: true } })
  courses.value = res.data || []
  if (!selectedCourseId.value && courses.value.length) {
    selectedCourseId.value = courses.value[0].id
    await loadCourseGroups()
  }
}

const loadCourseGroups = async () => {
  if (!selectedCourseId.value) return
  const res = await api.get(`/courses/${selectedCourseId.value}/groups`)
  courseGroups.value = res.data?.groups || []
  selectedGroupIds.value = courseGroups.value.filter((g) => g.selected).map((g) => Number(g.id))
}

const createCourse = async () => {
  error.value = ''
  const name = newName.value.trim()
  if (!name) {
    error.value = 'Укажите название'
    return
  }
  try {
    await api.post('/courses', { name })
    newName.value = ''
    await loadCourses()
  } catch (e) {
    error.value = e.response?.data?.error || 'Не удалось создать предмет'
  }
}

const saveGroups = async () => {
  const ids = selectedGroupIds.value.map((x) => Number(x)).filter((n) => n > 0)
  try {
    await api.put(`/courses/${selectedCourseId.value}/groups`, { group_ids: ids })
    await loadCourseGroups()
  } catch (e) {
    alert(e.response?.data?.error || 'Не удалось сохранить')
  }
}

const toggleArchived = async () => {
  if (!selectedCourse.value) return
  try {
    await api.patch(`/courses/${selectedCourseId.value}`, { archived: !selectedCourse.value.archived })
    await loadCourses()
  } catch (e) {
    alert(e.response?.data?.error || 'Не удалось сохранить')
  }
}

onMounted(() => loadCourses())
</script>

