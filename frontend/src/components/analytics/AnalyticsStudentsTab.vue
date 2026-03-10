<template>
  <div>
    <div v-if="!groupId" class="ui-card ui-card--muted">
      <p class="ui-meta" style="margin: 0">Выберите группу.</p>
    </div>
    <template v-else-if="data">
      <div class="ui-card ui-card--muted" style="margin-bottom: 1rem">
        <span class="ui-meta">Сессий группы в системе: <strong>{{ data.sessions_count }}</strong></span>
      </div>
      <div class="ui-card">
        <h3 style="margin-top: 0">Список студентов группы</h3>
        <div class="ui-table-wrap">
          <table class="ui-table">
            <thead>
              <tr>
                <th>Студент</th>
                <th>Сумма баллов</th>
                <th>Средний балл</th>
                <th>Ответов</th>
                <th>Опозданий</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in data.students" :key="s.student_id">
                <td>{{ s.name }}</td>
                <td><strong>{{ formatNum(s.total_score) }}</strong></td>
                <td>{{ s.avg_score }}</td>
                <td>{{ s.answers_count }}</td>
                <td>{{ s.late_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../../api'

const props = defineProps({
  groupId: { type: [String, Number], default: '' },
})

const data = ref(null)

const formatNum = (x) => (Number.isInteger(x) ? x : Number(x).toFixed(2))

const load = async () => {
  if (!props.groupId) {
    data.value = null
    return
  }
  const res = await api.get(`/analytics/group/${props.groupId}/students`)
  data.value = res.data
}

watch(
  () => props.groupId,
  () => load(),
  { immediate: true }
)
</script>
