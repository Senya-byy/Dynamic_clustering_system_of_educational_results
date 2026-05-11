<template>
  <div>
    <div v-if="!groupId" class="ui-card ui-card--muted">
      <p class="ui-meta" style="margin: 0">Выберите группу.</p>
    </div>
    <div v-else class="ui-card">
      <h3 style="margin-top: 0">Кластеризация (k-means)</h3>
      <div class="ui-row" style="margin: 0.5rem 0 0.25rem">
        <div class="ui-grow">
          <label class="ui-label">Предмет</label>
          <select v-model.number="selectedCourseId" class="ui-select" @change="loadLatest">
            <option disabled :value="0">Выберите предмет</option>
            <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
      </div>
      <div class="cluster-actions">
        <button type="button" class="ui-btn" :disabled="busy" @click="run">
          {{ busy ? 'Считаем…' : 'Запустить кластеризацию' }}
        </button>
        <span v-if="err" class="cluster-err">{{ err }}</span>
      </div>

      <template v-if="display">
        <p class="run-meta">
          <strong>k</strong> = {{ display.n_clusters }} (не менее 3) ·
          <strong>Силуэт</strong> =
          {{ display.silhouette_score !== null && display.silhouette_score !== undefined ? display.silhouette_score : '—' }}
        </p>
        <p v-if="display.summary_ru" class="ui-meta">{{ display.summary_ru }}</p>

        <div class="viz-grid">
          <div class="viz-card">
            <h4 class="viz-title">Доли кластеров</h4>
            <div class="doughnut-wrap">
              <Doughnut v-if="doughnutData" :data="doughnutData" :options="doughnutOptions" />
            </div>
          </div>
          <div class="viz-card viz-card--grow">
            <h4 class="viz-title">Средние по признаку</h4>
            <div v-if="display.feature_keys?.length" class="feature-pick">
              <label class="ui-label">Признак</label>
              <select v-model="barFeatureKey" class="ui-select">
                <option v-for="key in display.feature_keys" :key="key" :value="key">
                  {{ display.feature_labels[key] || key }}
                </option>
              </select>
            </div>
            <div class="bar-wrap">
              <Bar v-if="barData" :data="barData" :options="barOptions" />
            </div>
          </div>
        </div>

        <div class="legend-card">
          <h4 class="viz-title">Карта: кто в каком кластере</h4>
          <p class="ui-meta legend-hint">
            Цвет совпадает с диаграммами. Имена — в том же кластере, что и сегмент кольца / столбец.
          </p>
          <div
            v-for="c in display.cluster_summaries"
            :key="'leg' + c.label"
            class="legend-block"
          >
            <div class="legend-head">
              <span class="swatch" :style="{ background: colorFor(c.label) }" />
              <strong>Кластер {{ c.label }}</strong>
              <span class="ui-meta">({{ c.size }} чел.)</span>
            </div>
            <div v-if="namesFor(c).length" class="name-chips">
              <span
                v-for="(name, idx) in namesFor(c)"
                :key="idx"
                class="name-chip"
                :style="{ borderColor: colorFor(c.label), color: colorFor(c.label) }"
              >
                {{ name }}
              </span>
            </div>
            <p v-else class="ui-meta">Состав откройте на вкладке «Состав кластеров» для выбранного запуска.</p>
          </div>
        </div>

        <div v-for="c in display.cluster_summaries" :key="c.label" class="cluster-block">
          <p class="cluster-title">
            <span class="swatch swatch--inline" :style="{ background: colorFor(c.label) }" />
            Кластер {{ c.label }}
            <span class="ui-meta">({{ c.size }} чел.)</span>
          </p>
          <div class="ui-table-wrap">
            <table class="ui-table ui-table--compact">
              <tbody>
                <tr v-for="key in display.feature_keys" :key="key">
                  <td>{{ display.feature_labels[key] || key }}</td>
                  <td><strong>{{ c.mean_features[key] }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
      <p v-else class="ui-meta">Запустите кластеризацию — после первого запуска здесь появится последний срез.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, inject } from 'vue'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
} from 'chart.js'
import { Doughnut, Bar } from 'vue-chartjs'
import api from '../../api'
import { colorForClusterLabel } from '../../utils/clusterColors'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement)

const props = defineProps({
  groupId: { type: [String, Number], default: '' },
})

const transitionsKey = inject('analyticsTransitionsKey', ref(0))
const refreshTransitions = inject('refreshAnalyticsTransitions', () => {})

const busy = ref(false)
const err = ref('')
const posted = ref(null)
const loaded = ref(null)
const courses = ref([])
const selectedCourseId = ref(0)
const barFeatureKey = ref('')

const colorFor = (label) => colorForClusterLabel(label)

const fetchCourses = async () => {
  const res = await api.get('/courses')
  courses.value = res.data || []
  if (selectedCourseId.value && !courses.value.some((c) => c.id === selectedCourseId.value)) {
    selectedCourseId.value = courses.value.length ? courses.value[0].id : 0
  }
  if (!selectedCourseId.value && courses.value.length) {
    selectedCourseId.value = courses.value[0].id
  }
}

const display = computed(() => {
  if (posted.value && Number(posted.value.gid) === Number(props.groupId)) {
    return posted.value.payload
  }
  return loaded.value
})

watch(
  () => display.value?.feature_keys,
  (keys) => {
    if (!keys?.length) return
    if (!keys.includes(barFeatureKey.value)) {
      barFeatureKey.value = keys[0]
    }
  },
  { immediate: true }
)

const doughnutData = computed(() => {
  const d = display.value
  if (!d?.cluster_summaries?.length) return null
  const sums = d.cluster_summaries
  return {
    labels: sums.map((c) => `Кластер ${c.label}`),
    datasets: [
      {
        data: sums.map((c) => c.size),
        backgroundColor: sums.map((c) => colorFor(c.label)),
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  }
})

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      position: 'bottom',
      labels: { usePointStyle: true, padding: 12, font: { size: 12 } },
    },
  },
}

const barData = computed(() => {
  const d = display.value
  const key = barFeatureKey.value
  if (!d?.cluster_summaries?.length || !key) return null
  const sums = [...d.cluster_summaries].sort((a, b) => Number(a.label) - Number(b.label))
  return {
    labels: sums.map((c) => `Кластер ${c.label}`),
    datasets: [
      {
        label: d.feature_labels[key] || key,
        data: sums.map((c) => Number(c.mean_features[key]) || 0),
        backgroundColor: sums.map((c) => colorFor(c.label)),
        borderColor: sums.map((c) => colorFor(c.label)),
        borderWidth: 1,
      },
    ],
  }
})

const barOptions = {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    x: {
      beginAtZero: true,
      grid: { color: 'rgba(0,0,0,0.06)' },
    },
    y: {
      grid: { display: false },
    },
  },
}

const namesFor = (c) => (Array.isArray(c.student_names) ? c.student_names : [])

const loadLatest = async () => {
  if (!props.groupId) {
    loaded.value = null
    return
  }
  try {
    const tr = await api.get(`/analytics/cluster/${props.groupId}/transitions`, {
      params: selectedCourseId.value ? { course_id: selectedCourseId.value } : {},
    })
    const det = tr.data?.latest_run_detail
    if (!det?.clusters?.length) {
      loaded.value = null
      return
    }
    loaded.value = {
      n_clusters: det.run.n_clusters,
      silhouette_score: det.silhouette_score ?? null,
      cluster_summaries: det.clusters.map((c) => ({
        label: c.label,
        size: c.size,
        mean_features: c.mean_features,
        student_ids: c.student_ids || [],
        student_names: c.student_names || [],
      })),
      feature_keys: det.feature_keys,
      feature_labels: det.feature_labels,
      summary_ru: '',
    }
  } catch {
    loaded.value = null
  }
}

const run = async () => {
  err.value = ''
  busy.value = true
  try {
    const res = await api.post(
      `/analytics/cluster/${props.groupId}`,
      null,
      { params: selectedCourseId.value ? { course_id: selectedCourseId.value } : {} }
    )
    posted.value = {
      gid: Number(props.groupId),
      payload: {
        n_clusters: res.data.n_clusters,
        silhouette_score: res.data.silhouette_score,
        cluster_summaries: res.data.cluster_summaries || [],
        feature_keys: res.data.feature_keys,
        feature_labels: res.data.feature_labels,
        summary_ru: res.data.summary_ru || '',
      },
    }
    refreshTransitions()
  } catch (e) {
    err.value = e.response?.data?.error || e.message || 'Ошибка'
  } finally {
    busy.value = false
  }
}

watch(
  () => props.groupId,
  () => {
    posted.value = null
    loadLatest()
  },
  { immediate: true }
)

watch(
  () => transitionsKey.value,
  () => {
    if (posted.value && Number(posted.value.gid) === Number(props.groupId)) return
    loadLatest()
  }
)

fetchCourses()
</script>

<style scoped>
.cluster-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin: 0.75rem 0;
}
.cluster-err {
  color: #b91c1c;
  font-size: 0.9rem;
}
.run-meta {
  margin: 0.75rem 0;
  font-size: 0.95rem;
}
.viz-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  margin: 1rem 0 1.5rem;
  align-items: stretch;
}
.viz-card {
  background: var(--surface-muted, #f8fafc);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1rem;
  min-width: 220px;
}
.viz-card--grow {
  flex: 1 1 280px;
  min-height: 260px;
}
.viz-title {
  margin: 0 0 0.75rem;
  font-size: 1rem;
  font-weight: 700;
}
.doughnut-wrap {
  max-width: 280px;
  margin: 0 auto;
}
.bar-wrap {
  height: 220px;
  margin-top: 0.5rem;
}
.feature-pick {
  margin-bottom: 0.5rem;
}
.legend-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1rem 1.1rem;
  margin-bottom: 1.5rem;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.06), rgba(16, 185, 129, 0.05));
}
.legend-hint {
  margin: 0 0 1rem;
}
.legend-block {
  margin-bottom: 1rem;
}
.legend-block:last-child {
  margin-bottom: 0;
}
.legend-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.45rem;
}
.swatch {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border-radius: 4px;
  flex-shrink: 0;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.08);
}
.swatch--inline {
  vertical-align: middle;
  margin-right: 0.35rem;
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
.cluster-block {
  margin-bottom: 1.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}
.cluster-block:last-child {
  border-bottom: none;
}
.cluster-title {
  margin: 0 0 0.5rem;
  font-weight: 700;
}
.ui-table--compact td {
  padding: 0.35rem 0.5rem;
  font-size: 0.88rem;
}
</style>
