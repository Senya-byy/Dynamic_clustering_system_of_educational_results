<template>
  <div>
    <div v-if="!groupId" class="ui-card ui-card--muted">
      <p class="ui-meta" style="margin: 0">Выберите группу.</p>
    </div>
    <template v-else-if="transitions">
      <div class="ui-card ui-card--muted compare-row">
        <div>
          <label class="ui-label">Сравнить студента A</label>
          <select v-model="cmpA" class="ui-select">
            <option value="">—</option>
            <option v-for="(sid, i) in heatmap.student_ids" :key="'a' + sid" :value="String(i)">
              {{ heatmap.student_labels[i] }}
            </option>
          </select>
        </div>
        <div>
          <label class="ui-label">Сравнить студента B</label>
          <select v-model="cmpB" class="ui-select">
            <option value="">—</option>
            <option v-for="(sid, i) in heatmap.student_ids" :key="'b' + sid" :value="String(i)">
              {{ heatmap.student_labels[i] }}
            </option>
          </select>
        </div>
      </div>

      <div v-if="compareRows.length" class="ui-card">
        <h3 style="margin-top: 0">Траектории выбранных студентов</h3>
        <div class="ui-table-wrap">
          <table class="ui-table ui-table--compact">
            <thead>
              <tr>
                <th>Студент</th>
                <th v-for="rid in heatmap.run_ids" :key="'h' + rid">{{ shortDate(rid) }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in compareRows" :key="row.name">
                <td>{{ row.name }}</td>
                <td v-for="(cell, j) in row.cells" :key="j">{{ cell ?? '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="transitionRuns.length" class="ui-card">
        <h3 style="margin-top: 0">Доля студентов по кластерам (по запускам)</h3>
        <div class="stacked-legend">
          <span v-for="lab in allLabels" :key="'lg' + lab" class="lg-item">
            <i class="dot" :style="{ background: colorFor(lab) }" /> Кластер {{ lab }}
          </span>
        </div>
        <div v-for="r in transitionRuns" :key="r.id" class="stacked-row">
          <span class="stacked-date">{{ formatRunDate(r.created_at) }}</span>
          <div class="stacked-bar">
            <div
              v-for="seg in stackedSegments(r)"
              :key="seg.label"
              class="stacked-seg"
              :style="{ width: seg.pct + '%', background: colorFor(Number(seg.label)) }"
              :title="`Кластер ${seg.label}: ${seg.count}`"
            />
          </div>
        </div>
      </div>

      <div v-if="heatmap.run_ids?.length" class="ui-card">
        <h3 style="margin-top: 0">Heatmap: студент × запуск</h3>
        <p class="ui-meta">Ячейка — номер кластера в данном запуске.</p>
        <div class="heatmap-wrap">
          <table class="heatmap">
            <thead>
              <tr>
                <th class="heatmap-sticky">Студент</th>
                <th v-for="rid in heatmap.run_ids" :key="rid" class="heatmap-run">
                  {{ shortDate(rid) }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(sid, i) in heatmap.student_ids"
                :key="sid"
                :class="rowHighlightClass(i)"
              >
                <td class="heatmap-sticky">{{ heatmap.student_labels[i] }}</td>
                <td
                  v-for="(cell, j) in heatmap.matrix[i]"
                  :key="j"
                  class="heatmap-cell"
                  :class="cell === null || cell === undefined ? 'heatmap-cell--empty' : 'heatmap-cell--fill'"
                  :style="heatmapCellStyle(cell)"
                  :title="'Кластер ' + cell"
                >
                  {{ cell === null || cell === undefined ? '—' : cell }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, inject } from 'vue'
import api from '../../api'
import { colorForClusterLabel } from '../../utils/clusterColors'

const colorFor = (lab) => colorForClusterLabel(lab)

const props = defineProps({
  groupId: { type: [String, Number], default: '' },
})

const transitionsKey = inject('analyticsTransitionsKey', ref(0))
const transitions = ref(null)
const cmpA = ref('')
const cmpB = ref('')

const transitionRuns = computed(() => transitions.value?.runs ?? [])
const heatmap = computed(() => transitions.value?.heatmap ?? { run_ids: [], student_ids: [], matrix: [] })

const runDateById = computed(() => {
  const m = {}
  for (const r of transitionRuns.value) m[r.id] = r.created_at
  return m
})

const allLabels = computed(() => {
  const s = new Set()
  for (const r of transitionRuns.value) {
    Object.keys(r.distribution || {}).forEach((k) => s.add(Number(k)))
  }
  return Array.from(s).sort((a, b) => a - b)
})

const compareRows = computed(() => {
  const rows = []
  const hi = (idx) => {
    if (idx === '' || idx === null) return null
    const i = Number(idx)
    if (!heatmap.value.matrix[i]) return null
    return {
      name: heatmap.value.student_labels[i],
      cells: heatmap.value.matrix[i],
    }
  }
  const a = hi(cmpA.value)
  const b = hi(cmpB.value)
  if (a) rows.push(a)
  if (b && (!a || cmpA.value !== cmpB.value)) rows.push(b)
  return rows
})

const formatRunDate = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })
}

const shortDate = (rid) => {
  const iso = runDateById.value[rid]
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d.getTime()) ? '—' : d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
}

const stackedSegments = (r) => {
  const d = r.distribution || {}
  const entries = Object.keys(d).map((k) => ({ label: k, count: d[k] }))
  const total = entries.reduce((s, e) => s + e.count, 0) || 1
  return entries.map((e) => ({
    label: e.label,
    count: e.count,
    pct: (100 * e.count) / total,
  }))
}

const heatmapCellStyle = (cell) => {
  if (cell === null || cell === undefined) return {}
  const hex = colorForClusterLabel(cell)
  return {
    background: `${hex}40`,
    color: '#0f172a',
    fontWeight: '700',
    borderBottom: `2px solid ${hex}`,
  }
}

const rowHighlightClass = (i) => {
  const a = cmpA.value !== '' && Number(cmpA.value) === i
  const b = cmpB.value !== '' && Number(cmpB.value) === i
  if (a || b) return 'heatmap-row--hl'
  return ''
}

const load = async () => {
  if (!props.groupId) {
    transitions.value = null
    return
  }
  const res = await api.get(`/analytics/cluster/${props.groupId}/transitions`)
  transitions.value = res.data
}

watch(
  () => [props.groupId, transitionsKey.value],
  () => load(),
  { immediate: true }
)
</script>

<style scoped>
.compare-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}
.ui-table--compact td {
  padding: 0.35rem 0.5rem;
  font-size: 0.88rem;
}
.stacked-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}
.stacked-date {
  flex: 0 0 110px;
  font-size: 0.8rem;
  color: var(--text-muted);
}
.stacked-bar {
  flex: 1;
  display: flex;
  height: 18px;
  border-radius: 6px;
  overflow: hidden;
  background: #e2e8f0;
}
.stacked-seg {
  min-width: 2px;
  height: 100%;
}
.stacked-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  font-size: 0.8rem;
}
.lg-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  display: inline-block;
}
.heatmap-cell--fill {
  transition: background 0.15s ease;
}
.heatmap-wrap {
  overflow-x: auto;
  margin-top: 0.5rem;
}
.heatmap {
  border-collapse: collapse;
  font-size: 0.8rem;
  min-width: 100%;
}
.heatmap th,
.heatmap td {
  border: 1px solid var(--border);
  padding: 0.35rem 0.5rem;
  text-align: center;
}
.heatmap-sticky {
  text-align: left !important;
  position: sticky;
  left: 0;
  background: var(--card-bg, #fff);
  z-index: 1;
  white-space: nowrap;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.heatmap-run {
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  max-width: 2rem;
  font-size: 0.7rem;
  color: var(--text-muted);
}
.heatmap-cell--empty {
  background: #f8fafc;
  color: #94a3b8;
}
:deep(tr.heatmap-row--hl) td {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}
</style>
