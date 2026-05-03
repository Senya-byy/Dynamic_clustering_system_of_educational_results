<template>
  <div class="page-narrow analytics-shell" style="max-width: 1000px">
    <h2>Аналитика</h2>
    <p class="page-lead">Выберите группу — данные на вкладках ниже.</p>

    <div class="ui-card ui-card--muted">
      <label class="ui-label">Группа</label>
      <select v-model="groupId" class="ui-select" style="max-width: 400px" @change="onGroupChange">
        <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
      </select>
    </div>

    <nav class="analytics-tabs" aria-label="Разделы аналитики">
      <router-link
        v-for="t in tabs"
        :key="t.to"
        :to="t.to"
        class="analytics-tab"
        active-class="analytics-tab--active"
      >
        {{ t.label }}
      </router-link>
    </nav>

    <router-view v-slot="{ Component }">
      <component :is="Component" :group-id="groupId" :groups="groups" />
    </router-view>
  </div>
</template>

<script setup>
import { ref, provide, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()
const groups = ref([])
const groupId = ref('')
const transitionsKey = ref(0)

const tabs = [
  { to: '/teacher/analytics/students', label: 'Студенты' },
  { to: '/teacher/analytics/clustering', label: 'Кластеризация' },
  { to: '/teacher/analytics/clusters', label: 'Состав кластеров' },
  { to: '/teacher/analytics/transitions', label: 'Переходы' },
]

const bumpTransitions = () => {
  transitionsKey.value += 1
}

provide('analyticsTransitionsKey', transitionsKey)
provide('refreshAnalyticsTransitions', bumpTransitions)

const onGroupChange = () => {
  bumpTransitions()
}

onMounted(async () => {
  const res = await api.get('/groups')
  groups.value = res.data
  if (res.data.length) {
    groupId.value = res.data[0].id
  }
  if (router.currentRoute.value.path === '/teacher/analytics') {
    router.replace('/teacher/analytics/students')
  }
})

watch(groupId, () => bumpTransitions())
</script>

<style scoped>
.analytics-shell {
  padding-bottom: 2rem;
}
.analytics-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 1rem 0 1.25rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.5rem;
}
.analytics-tab {
  padding: 0.45rem 0.85rem;
  border-radius: 8px;
  font-size: 0.9rem;
  color: var(--text-muted);
  text-decoration: none;
  border: 1px solid transparent;
}
.analytics-tab:hover {
  color: var(--text);
  background: rgba(99, 102, 241, 0.08);
}
.analytics-tab--active {
  color: var(--accent);
  font-weight: 600;
  border-color: var(--accent);
  background: rgba(99, 102, 241, 0.1);
}
</style>
