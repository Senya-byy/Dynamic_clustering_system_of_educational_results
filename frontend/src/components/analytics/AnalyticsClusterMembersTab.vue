<template>
  <div>
    <div v-if="!groupId" class="ui-card ui-card--muted">
      <p class="ui-meta" style="margin: 0">Выберите группу.</p>
    </div>
    <template v-else>
      <div class="ui-card ui-card--muted">
        <label class="ui-label">Запуск кластеризации</label>
        <select v-model="runId" class="ui-select" style="max-width: 420px" @change="loadDetail">
          <option disabled value="">Выберите запуск</option>
          <option v-for="r in runs" :key="r.id" :value="r.id">
            {{ formatRunDate(r.created_at) }} · k={{ r.n_clusters }}
          </option>
        </select>
        <button
          v-if="detail"
          type="button"
          class="ui-btn ui-btn--ghost"
          style="margin-left: 0.75rem"
          @click="exportCsv"
        >
          Экспорт CSV
        </button>
      </div>

      <div v-if="detail" class="ui-card">
        <h3 style="margin-top: 0">Состав кластеров</h3>
        <p class="ui-meta legend-hint">
          Цвет заголовка и меток совпадает с вкладкой «Кластеризация».
        </p>
        <div v-for="c in detail.clusters" :key="c.label" class="block">
          <p class="title">
            <span class="swatch" :style="{ background: colorFor(c.label) }" />
            Кластер {{ c.label }} <span class="ui-meta">({{ c.size }})</span>
          </p>
          <div class="name-chips">
            <span
              v-for="(name, idx) in c.student_names"
              :key="idx"
              class="name-chip"
              :style="{ borderColor: colorFor(c.label), color: colorFor(c.label) }"
            >
              {{ name }}
            </span>
          </div>
        </div>
      </div>
      <p v-else-if="runs.length === 0" class="ui-meta">Пока нет запусков — выполните кластеризацию.</p>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, inject } from 'vue'
import api from '../../api'
import { colorForClusterLabel } from '../../utils/clusterColors'

const colorFor = (label) => colorForClusterLabel(label)

const props = defineProps({
  groupId: { type: [String, Number], default: '' },
})

const transitionsKey = inject('analyticsTransitionsKey', ref(0))
const runs = ref([])
const runId = ref('')
const detail = ref(null)

const formatRunDate = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })
}

const loadRuns = async () => {
  runId.value = ''
  detail.value = null
  if (!props.groupId) {
    runs.value = []
    return
  }
  try {
    const res = await api.get(`/analytics/cluster/${props.groupId}/runs`)
    runs.value = res.data || []
    if (runs.value.length) {
      runId.value = runs.value[runs.value.length - 1].id
      await loadDetail()
    }
  } catch {
    runs.value = []
  }
}

const loadDetail = async () => {
  if (!runId.value || !props.groupId) {
    detail.value = null
    return
  }
  const res = await api.get(`/analytics/cluster/${props.groupId}/runs/${runId.value}`)
  detail.value = res.data
}

const exportCsv = () => {
  if (!detail.value?.clusters) return
  const lines = ['cluster_label;student_id;student_name']
  for (const c of detail.value.clusters) {
    c.student_ids.forEach((sid, i) => {
      const name = (c.student_names[i] || '').replace(/"/g, '""')
      lines.push(`${c.label};${sid};"${name}"`)
    })
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `clusters_run_${runId.value}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}

watch(
  () => props.groupId,
  () => loadRuns(),
  { immediate: true }
)

watch(
  () => transitionsKey.value,
  () => loadRuns()
)
</script>

<style scoped>
.block {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}
.block:last-child {
  border-bottom: none;
}
.title {
  margin: 0 0 0.35rem;
  font-weight: 700;
}
.names {
  margin: 0;
  line-height: 1.5;
  color: var(--text-muted);
}
.legend-hint {
  margin: 0 0 0.75rem;
}
.swatch {
  display: inline-block;
  width: 0.85rem;
  height: 0.85rem;
  border-radius: 4px;
  margin-right: 0.4rem;
  vertical-align: middle;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.08);
}
.name-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.name-chip {
  font-size: 0.82rem;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 2px solid;
  background: #fff;
  font-weight: 600;
}
</style>
