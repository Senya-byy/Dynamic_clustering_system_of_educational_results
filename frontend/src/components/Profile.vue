<template>
  <div class="page-narrow">
    <h2>Профиль</h2>

    <div v-if="profile" class="ui-card">
      <p class="ui-meta"><strong>Логин:</strong> {{ profile.login }}</p>
      <p class="ui-meta"><strong>Роль:</strong> <span class="ui-badge ui-badge--accent">{{ profile.role }}</span></p>
      <p v-if="isStudent" class="ui-meta">
        <strong>Группа:</strong> {{ studentGroupName || '—' }}
      </p>

      <label class="ui-label" for="fn">Полное имя</label>
      <input id="fn" v-model="profile.full_name" class="ui-input" />

      <p class="ui-label" style="margin-top: 1rem">Приватность в рейтинге</p>
      <label class="radio-line"><input v-model="profile.privacy_mode" type="radio" :value="true" /> Скрыть имя («Студент N»)</label>
      <label class="radio-line"><input v-model="profile.privacy_mode" type="radio" :value="false" /> Показывать имя</label>

      <div class="ui-actions">
        <button type="button" class="ui-btn ui-btn--primary" @click="saveProfile">Сохранить</button>
      </div>
    </div>

    <div v-if="isTeacher" class="ui-card">
      <h3>Мои группы</h3>
      <p class="page-lead" style="margin: 0 0 0.75rem; font-size: 0.9rem">
        Группы создаёт администратор. Вы можете только привязать к себе существующую группу.
      </p>
      <ul v-if="myGroups.length" class="ui-list profile-groups">
        <li v-for="g in myGroups" :key="g.id">
          <span>{{ g.name }}</span>
          <button type="button" class="ui-btn ui-btn--ghost ui-btn--small" @click="detachGroup(g)">
            Отвязать
          </button>
        </li>
      </ul>
      <p v-else class="ui-meta" style="margin: 0">Пока нет групп</p>

      <div class="profile-add-group">
        <select v-model.number="attachGroupId" class="ui-select ui-grow">
          <option disabled :value="0">Выберите группу…</option>
          <option v-for="g in allGroups" :key="'ag' + g.id" :value="g.id">{{ g.name }}</option>
        </select>
        <button type="button" class="ui-btn ui-btn--secondary" @click="attachGroup">Привязать</button>
      </div>
      <p v-if="groupMsg" class="ui-alert" :class="groupErr ? 'ui-alert--error' : 'ui-alert--ok'">{{ groupMsg }}</p>
    </div>

    <div class="ui-card">
      <h3>Смена пароля</h3>
      <label class="ui-label">Текущий пароль</label>
      <input v-model="pwd.old" class="ui-input" type="password" autocomplete="current-password" />
      <label class="ui-label">Новый пароль</label>
      <input v-model="pwd.new" class="ui-input" type="password" autocomplete="new-password" />
      <div class="ui-actions">
        <button type="button" class="ui-btn ui-btn--secondary" @click="changePassword">Обновить пароль</button>
      </div>
      <p v-if="pwdMsg" class="ui-alert" :class="pwdErr ? 'ui-alert--error' : 'ui-alert--ok'">{{ pwdMsg }}</p>
    </div>

    <div class="ui-card">
      <h3>Обратная связь</h3>
      <p style="margin: 0">
        <a class="profile-feedback-link" :href="feedbackFormUrl" target="_blank" rel="noopener noreferrer">
          Форма Class-QR
        </a>
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import api from '../api'
import { useAuthStore } from '../store/auth'
import { FEEDBACK_FORM_URL } from '../config/feedback'

const feedbackFormUrl = FEEDBACK_FORM_URL

const authStore = useAuthStore()
const isTeacher = computed(() => authStore.role === 'teacher')
const isStudent = computed(() => authStore.role === 'student')

const profile = ref(null)
const pwd = ref({ old: '', new: '' })
const pwdMsg = ref('')
const pwdErr = ref(false)

const myGroups = ref([])
const allGroups = ref([])
const attachGroupId = ref(0)
const groupMsg = ref('')
const groupErr = ref(false)

const studentGroupName = ref('')

const fetchProfile = async () => {
  const res = await api.get('/auth/profile')
  profile.value = res.data
}

const fetchStudentGroupName = async () => {
  if (!isStudent.value) return
  studentGroupName.value = ''
  const gid = Number(profile.value?.group_id || 0)
  if (!gid) return
  try {
    const res = await api.get('/register/groups')
    const rows = res.data || []
    const g = rows.find((x) => Number(x.id) === gid)
    studentGroupName.value = g ? g.name : ''
  } catch {
    studentGroupName.value = ''
  }
}

const fetchTeacherGroups = async () => {
  if (!isTeacher.value) return
  try {
    const res = await api.get('/groups')
    myGroups.value = res.data || []
  } catch {
    myGroups.value = []
  }
}

const fetchAllGroupsForAttach = async () => {
  if (!isTeacher.value) return
  try {
    const res = await api.get('/register/groups')
    allGroups.value = res.data || []
    if (!attachGroupId.value && allGroups.value.length) {
      attachGroupId.value = allGroups.value[0].id
    }
  } catch {
    allGroups.value = []
  }
}

const saveProfile = async () => {
  const fn = (profile.value.full_name || '').trim()
  if (fn.length > 200) {
    alert('ФИО не длиннее 200 символов')
    return
  }
  try {
    await api.put('/auth/profile', {
      full_name: fn || null,
      privacy_mode: profile.value.privacy_mode
    })
    profile.value.full_name = fn || null
    await authStore.fetchProfile()
    alert('Профиль обновлён')
  } catch (e) {
    alert(e.response?.data?.error || 'Не удалось сохранить')
  }
}

const changePassword = async () => {
  pwdMsg.value = ''
  pwdErr.value = false
  const nw = pwd.value.new
  if (!pwd.value.old || !nw || !String(nw).trim()) {
    pwdErr.value = true
    pwdMsg.value = 'Заполните оба поля пароля'
    return
  }
  if (String(nw).length < 4) {
    pwdErr.value = true
    pwdMsg.value = 'Новый пароль не короче 4 символов'
    return
  }
  try {
    await api.put('/auth/password', {
      old_password: pwd.value.old,
      new_password: nw
    })
    pwdMsg.value = 'Пароль обновлён'
    pwd.value = { old: '', new: '' }
  } catch (e) {
    pwdErr.value = true
    pwdMsg.value = e.response?.data?.error || 'Ошибка'
  }
}

const attachGroup = async () => {
  groupMsg.value = ''
  groupErr.value = false
  if (!attachGroupId.value) return
  try {
    await api.post('/teachers/me/groups', { group_id: attachGroupId.value })
    await fetchTeacherGroups()
    groupMsg.value = 'Группа привязана'
  } catch (e) {
    groupErr.value = true
    groupMsg.value = e.response?.data?.error || 'Ошибка'
  }
}

const detachGroup = async (g) => {
  if (!confirm(`Отвязать группу «${g.name}»?`)) return
  groupMsg.value = ''
  groupErr.value = false
  try {
    await api.delete(`/teachers/me/groups/${g.id}`)
    await fetchTeacherGroups()
    groupMsg.value = 'Группа отвязана'
  } catch (e) {
    groupErr.value = true
    groupMsg.value = e.response?.data?.error || 'Ошибка'
  }
}

onMounted(async () => {
  await fetchProfile()
  await fetchStudentGroupName()
  await fetchTeacherGroups()
  await fetchAllGroupsForAttach()
})
</script>

<style scoped>
.radio-line {
  display: block;
  margin: 0.35rem 0;
  font-size: 0.9rem;
  color: var(--text-muted);
}
.profile-feedback-link {
  font-weight: 600;
  color: var(--accent);
  text-decoration: none;
}
.profile-feedback-link:hover {
  text-decoration: underline;
}
.profile-add-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.75rem;
  align-items: center;
}
.profile-add-group .ui-input {
  flex: 1 1 160px;
  min-width: 0;
}
.profile-groups li {
  justify-content: space-between;
  align-items: center;
}
.ui-btn--small {
  padding: 0.35rem 0.65rem;
  font-size: 0.85rem;
}
</style>
