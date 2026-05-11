<template>
  <div class="page-narrow" style="max-width: 880px">
    <h2>Рейтинг группы</h2>

    <div v-if="isTeacherLike" class="ui-card ui-card--muted">
      <label class="ui-label">Группа</label>
      <select v-model="selectedGroupId" class="ui-select" style="max-width: 400px" @change="load">
        <option disabled value="">Выберите</option>
        <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
      </select>
      <p v-if="isTeacherLike && selectedGroupLabel" class="pick-summary" style="margin-top: 0.65rem">
        <span class="pick-summary__label">Группа</span>
        <span class="pick-summary__pill">{{ selectedGroupLabel }}</span>
      </p>
    </div>

    <div class="ui-card ui-card--muted">
      <label class="ui-label">Предмет</label>
      <select v-model="selectedCourseId" class="ui-select" style="max-width: 400px" @change="load">
        <option disabled value="">Выберите</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <p v-if="selectedCourseLabel" class="pick-summary" style="margin-top: 0.65rem">
        <span class="pick-summary__label">Предмет</span>
        <span class="pick-summary__pill pick-summary__pill--muted">{{ selectedCourseLabel }}</span>
      </p>
    </div>

    <div class="ui-card">
      <div class="ui-table-wrap">
        <table class="ui-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Студент</th>
              <th>Сумма баллов</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rating" :key="row.user_id" :class="{ 'row-self': row.is_self }">
              <td>{{ row.rank }}</td>
              <td>
                {{ row.name }}
                <span v-if="row.is_self" class="ui-badge">вы</span>
              </td>
              <td><strong>{{ row.total_score }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../api'
import { useAuthStore } from '../store/auth'

const authStore = useAuthStore()
const rating = ref([])
const groups = ref([])
const selectedGroupId = ref('')
const courses = ref([])
const selectedCourseId = ref('')

const isTeacherLike = computed(
  () => authStore.role === 'teacher' || authStore.role === 'admin'
)

const selectedGroupLabel = computed(() => {
  if (!isTeacherLike.value) return ''
  const g = groups.value.find((x) => String(x.id) === String(selectedGroupId.value))
  return g?.name || ''
})

const selectedCourseLabel = computed(() => {
  const c = courses.value.find((x) => String(x.id) === String(selectedCourseId.value))
  return c?.name || ''
})

const load = async () => {
  const gid = selectedGroupId.value || authStore.groupId
  const cid = selectedCourseId.value
  if (!gid || !cid) return
  const res = await api.get('/rating/group', { params: { group_id: gid, course_id: cid } })
  rating.value = res.data
}

onMounted(async () => {
  if (isTeacherLike.value) {
    const res = await api.get('/groups')
    groups.value = res.data
    if (res.data.length) {
      selectedGroupId.value = res.data[0].id
    }
    const cr = await api.get('/courses')
    courses.value = (cr.data || []).filter((c) => !c.archived)
    if (courses.value.length) {
      selectedCourseId.value = courses.value[0].id
    }
  } else {
    selectedGroupId.value = authStore.groupId || ''
    const cr = await api.get('/my/courses')
    courses.value = cr.data || []
    if (courses.value.length) {
      selectedCourseId.value = courses.value[0].id
    }
  }
  await load()
})

watch(selectedGroupId, load)
watch(selectedCourseId, load)
</script>

<style scoped>
.row-self td {
  background: #eef2ff;
}
.pick-summary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.pick-summary__label {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 600;
}
.pick-summary__pill {
  font-size: 0.88rem;
  font-weight: 700;
  padding: 0.28rem 0.75rem;
  border-radius: 999px;
  background: var(--accent, #6366f1);
  color: #fff;
}
.pick-summary__pill--muted {
  background: #64748b;
}
</style>
