<template>
  <div class="page-narrow" style="max-width: 880px">
    <h2>Рейтинг группы</h2>

    <div v-if="isTeacherLike" class="ui-card ui-card--muted">
      <label class="ui-label">Группа</label>
      <select v-model="selectedGroupId" class="ui-select" style="max-width: 400px" @change="load">
        <option disabled value="">Выберите</option>
        <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
      </select>
    </div>

    <div v-if="histogram.length" class="ui-card chart-card">
      <h3>Распределение баллов</h3>
      <div class="bars">
        <div v-for="row in histogram" :key="row.score" class="bar-wrap">
          <div class="bar" :style="{ height: row.pct + '%' }" :title="String(row.count)" />
          <span class="lbl">{{ row.score }}</span>
          <span class="cnt">{{ row.count }}</span>
        </div>
      </div>
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
const histData = ref({})

const isTeacherLike = computed(
  () => authStore.role === 'teacher' || authStore.role === 'admin'
)

const histogram = computed(() => {
  const h = histData.value || {}
  const entries = Object.keys(h).map((k) => ({ score: Number(k), count: h[k] }))
  const maxC = Math.max(1, ...entries.map((e) => e.count))
  return entries
    .sort((a, b) => a.score - b.score)
    .map((e) => ({ ...e, pct: Math.round((e.count / maxC) * 100) }))
})

const loadRating = async (groupId) => {
  if (!groupId) return
  const res = await api.get('/rating/group', { params: { group_id: groupId } })
  rating.value = res.data
}

const loadHist = async (groupId) => {
  if (!groupId || !isTeacherLike.value) {
    histData.value = {}
    return
  }
  try {
    const res = await api.get('/analytics/group', { params: { group_id: groupId } })
    histData.value = res.data.score_histogram || {}
  } catch {
    histData.value = {}
  }
}

const load = async () => {
  const gid = selectedGroupId.value || authStore.groupId
  if (!gid) return
  await loadRating(gid)
  await loadHist(gid)
}

onMounted(async () => {
  if (isTeacherLike.value) {
    const res = await api.get('/groups')
    groups.value = res.data
    if (res.data.length) {
      selectedGroupId.value = res.data[0].id
    }
  } else {
    selectedGroupId.value = authStore.groupId || ''
  }
  await load()
})

watch(selectedGroupId, load)
</script>

<style scoped>
.chart-card h3 {
  margin-bottom: 0.5rem;
}
.bars {
  display: flex;
  align-items: flex-end;
  gap: 0.65rem;
  min-height: 160px;
  padding: 0.5rem 0 0;
}
.bar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-width: 0;
}
.bar {
  width: 100%;
  max-width: 40px;
  background: linear-gradient(180deg, #818cf8 0%, var(--accent) 100%);
  border-radius: 8px 8px 2px 2px;
  min-height: 6px;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);
}
.lbl {
  font-size: 0.75rem;
  margin-top: 0.35rem;
  color: var(--text-muted);
  font-weight: 600;
}
.cnt {
  font-size: 0.68rem;
  color: #94a3b8;
}
.row-self td {
  background: #eef2ff;
}
</style>
