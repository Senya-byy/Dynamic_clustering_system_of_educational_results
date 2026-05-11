<template>
  <div class="page-narrow" style="max-width: 720px">
    <h2>Расписание</h2>
    <p class="page-lead">Расписание и импорт CSV.</p>

    <div class="ui-card ui-card--muted">
      <div class="ui-row">
        <div class="ui-grow">
          <label class="ui-label">Группа</label>
          <select v-model="groupId" class="ui-select" @change="load">
            <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
          </select>
          <p v-if="selectedGroupName" class="pick-summary" style="margin-top: 0.65rem">
            <span class="pick-summary__label">Выбрано</span>
            <span class="pick-summary__pill">{{ selectedGroupName }}</span>
          </p>
        </div>
        <button type="button" class="ui-btn ui-btn--secondary" @click="loadCurrent">Сейчас пара?</button>
      </div>
      <p v-if="currentMsg" class="ui-alert ui-alert--ok" style="margin-top: 1rem; margin-bottom: 0">{{ currentMsg }}</p>
    </div>

    <form class="ui-card" @submit.prevent="addSlot">
      <h3 style="margin-top: 0">Новый слот</h3>
      <label class="ui-label">День недели (0 = пн)</label>
      <input v-model.number="form.weekday" class="ui-input" type="number" min="0" max="6" required />
      <label class="ui-label">Начало HH:MM</label>
      <input v-model="form.start_time" class="ui-input" required placeholder="09:00" />
      <label class="ui-label">Конец HH:MM</label>
      <input v-model="form.end_time" class="ui-input" required placeholder="10:30" />
      <label class="ui-label">Название</label>
      <input v-model="form.title" class="ui-input" placeholder="Лекция" />
      <div class="ui-actions">
        <button type="submit" class="ui-btn ui-btn--primary">Добавить</button>
      </div>
    </form>

    <div class="ui-card">
      <h3 style="margin-top: 0">Слоты</h3>
      <ul class="ui-list">
        <li v-for="s in slots" :key="s.id">
          <span>
            <span class="ui-badge">День {{ s.weekday }}</span>
            {{ s.start_time }}–{{ s.end_time }} {{ s.title || '' }}
          </span>
          <button type="button" class="ui-btn ui-btn--danger" @click="remove(s.id)">Удалить</button>
        </li>
      </ul>
    </div>

    <div class="ui-card">
      <h3 style="margin-top: 0">Импорт CSV</h3>
      <p class="page-lead" style="margin-bottom: 0.75rem">Колонки: group_id, weekday, start_time, end_time, title</p>
      <input type="file" accept=".csv" class="ui-input" style="padding: 0.5rem" @change="onFile" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'

const groups = ref([])
const groupId = ref('')
const slots = ref([])
const currentMsg = ref('')
const form = ref({ weekday: 0, start_time: '09:00', end_time: '10:30', title: '' })

const selectedGroupName = computed(() => {
  const id = groupId.value
  const g = groups.value.find((x) => String(x.id) === String(id))
  return g?.name || ''
})

const load = async () => {
  if (!groupId.value) return
  const res = await api.get(`/groups/${groupId.value}/schedule`)
  slots.value = res.data
}

const loadCurrent = async () => {
  if (!groupId.value) return
  const res = await api.get(`/groups/${groupId.value}/schedule/current`)
  if (res.data.is_now) {
    currentMsg.value = `Сейчас: ${res.data.title || 'Пара'} ${res.data.start_time}–${res.data.end_time}`
  } else {
    currentMsg.value = res.data.message || 'Нет пары'
  }
}

const timeRe = /^\s*(\d{1,2}):(\d{2})\s*$/

const addSlot = async () => {
  const st = (form.value.start_time || '').trim()
  const et = (form.value.end_time || '').trim()
  const m1 = st.match(timeRe)
  const m2 = et.match(timeRe)
  if (!m1 || !m2) {
    alert('Время начала и конца укажите в формате ЧЧ:ММ (например 09:00)')
    return
  }
  const toNorm = (m) => {
    const h = parseInt(m[1], 10)
    const mi = parseInt(m[2], 10)
    if (h < 0 || h > 23 || mi < 0 || mi > 59) return null
    return `${String(h).padStart(2, '0')}:${String(mi).padStart(2, '0')}`
  }
  const ns = toNorm(m1)
  const ne = toNorm(m2)
  if (!ns || !ne) {
    alert('Некорректное время')
    return
  }
  if (ns >= ne) {
    alert('Время окончания должно быть позже начала')
    return
  }
  const titleRaw = (form.value.title || '').trim()
  try {
    await api.post('/schedule', {
      group_id: Number(groupId.value),
      weekday: form.value.weekday,
      start_time: ns,
      end_time: ne,
      title: titleRaw || null
    })
    await load()
  } catch (e) {
    alert(e.response?.data?.error || 'Не удалось добавить слот')
  }
}

const remove = async (id) => {
  await api.delete(`/schedule/slots/${id}`)
  await load()
}

const onFile = async (e) => {
  const f = e.target.files?.[0]
  if (!f) return
  const fd = new FormData()
  fd.append('file', f)
  await api.post('/import/schedule', fd, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  await load()
}

onMounted(async () => {
  const res = await api.get('/groups')
  groups.value = res.data
  if (res.data.length) {
    groupId.value = res.data[0].id
    await load()
  }
})
</script>

<style scoped>
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
.ui-list li {
  justify-content: space-between;
}
</style>
