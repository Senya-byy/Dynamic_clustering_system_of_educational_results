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

const isTeacherLike = computed(
  () => authStore.role === 'teacher' || authStore.role === 'admin'
)

const load = async () => {
  const gid = selectedGroupId.value || authStore.groupId
  if (!gid) return
  const res = await api.get('/rating/group', { params: { group_id: gid } })
  rating.value = res.data
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
.row-self td {
  background: #eef2ff;
}
</style>
