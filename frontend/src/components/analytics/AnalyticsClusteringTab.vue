<template>
  <div>
    <div v-if="!groupId" class="ui-card ui-card--muted">
      <p class="ui-meta" style="margin: 0">Выберите группу.</p>
    </div>
    <div v-else class="ui-card">
      <h3 style="margin-top: 0">Кластеризация (k-means)</h3>
      <p class="ui-meta">
        Признаки: сумма и средний балл, максимум за ответ, ответы &gt;50% от max, опоздания, доля зачтённых
        (&gt;70% или верно), задачи по сложности. Комментарии не учитываются.
      </p>
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

        <div v-for="c in display.cluster_summaries" :key="c.label" class="cluster-block">
          <p class="cluster-title">
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
import api from '../../api'

const props = defineProps({
  groupId: { type: [String, Number], default: '' },
})

const transitionsKey = inject('analyticsTransitionsKey', ref(0))
const refreshTransitions = inject('refreshAnalyticsTransitions', () => {})

const busy = ref(false)
const err = ref('')
const posted = ref(null)
const loaded = ref(null)

const display = computed(() => {
  if (posted.value && Number(posted.value.gid) === Number(props.groupId)) {
    return posted.value.payload
  }
  return loaded.value
})

const loadLatest = async () => {
  if (!props.groupId) {
    loaded.value = null
    return
  }
  try {
    const tr = await api.get(`/analytics/cluster/${props.groupId}/transitions`)
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
    const res = await api.post(`/analytics/cluster/${props.groupId}`)
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
