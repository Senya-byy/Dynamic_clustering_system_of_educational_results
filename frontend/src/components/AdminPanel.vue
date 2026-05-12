<template>
  <div class="page-narrow" style="max-width: 920px">
    <h1>Администрирование</h1>
    <p class="page-lead">
      Создание групп, преподавателей и учеников. Доступ только для роли
      <code class="ui-badge ui-badge--accent" style="font-family: inherit">admin</code>.
    </p>

    <section class="ui-card">
      <h2>Группы</h2>
      <form class="ui-row" @submit.prevent="createGroup">
        <div class="ui-grow">
          <label class="ui-label">Название</label>
          <input v-model="newGroup.name" class="ui-input" placeholder="Например ИТ-252" required />
        </div>
        <div class="ui-grow">
          <label class="ui-label">Преподаватель</label>
          <select v-model.number="newGroup.teacher_id" class="ui-select" required>
            <option disabled :value="0">Выберите</option>
            <option v-for="t in teachers" :key="t.id" :value="t.id">
              {{ t.login }}<template v-if="t.full_name"> — {{ t.full_name }}</template>
            </option>
          </select>
        </div>
        <button type="submit" class="ui-btn ui-btn--primary">Создать группу</button>
      </form>
      <p
        v-if="msg.group"
        class="ui-alert"
        :class="msg.group.ok ? 'ui-alert--ok' : 'ui-alert--error'"
      >
        {{ msg.group.text }}
      </p>
      <div class="ui-table-wrap">
        <table class="ui-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Название</th>
              <th>Преподаватель</th>
              <th>Логин</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="g in groups" :key="g.id">
              <td>{{ g.id }}</td>
              <td><strong>{{ g.name }}</strong></td>
              <td>{{ g.teacher_id }}</td>
              <td>{{ g.teacher_login }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="ui-card">
      <h2>Новый преподаватель</h2>
      <form @submit.prevent="createTeacher">
        <label class="ui-label">Логин</label>
        <input v-model="newTeacher.login" class="ui-input" required autocomplete="off" />
        <label class="ui-label">Пароль</label>
        <input v-model="newTeacher.password" class="ui-input" type="password" required />
        <label class="ui-label">ФИО</label>
        <input v-model="newTeacher.full_name" class="ui-input" placeholder="Необязательно" />
        <div class="ui-actions">
          <button type="submit" class="ui-btn ui-btn--primary">Создать</button>
        </div>
      </form>
      <p
        v-if="msg.teacher"
        class="ui-alert"
        :class="msg.teacher.ok ? 'ui-alert--ok' : 'ui-alert--error'"
      >
        {{ msg.teacher.text }}
      </p>
    </section>

    <section class="ui-card">
      <h2>Новый ученик</h2>
      <form @submit.prevent="createStudent">
        <label class="ui-label">Логин</label>
        <input v-model="newStudent.login" class="ui-input" required autocomplete="off" />
        <label class="ui-label">Пароль</label>
        <input v-model="newStudent.password" class="ui-input" type="password" required />
        <label class="ui-label">ФИО</label>
        <input v-model="newStudent.full_name" class="ui-input" placeholder="Необязательно" />
        <label class="ui-label">Группа</label>
        <select v-model.number="newStudent.group_id" class="ui-select">
          <option :value="null">Без группы</option>
          <option v-for="g in groups" :key="'sg' + g.id" :value="g.id">{{ g.name }}</option>
        </select>
        <div class="ui-actions">
          <button type="submit" class="ui-btn ui-btn--primary">Создать</button>
        </div>
      </form>
      <p
        v-if="msg.student"
        class="ui-alert"
        :class="msg.student.ok ? 'ui-alert--ok' : 'ui-alert--error'"
      >
        {{ msg.student.text }}
      </p>
    </section>

    <section class="ui-card">
      <h2>Пользователи</h2>
      <button type="button" class="ui-btn ui-btn--secondary" @click="loadUsers">Обновить список</button>
      <div class="ui-table-wrap">
        <table class="ui-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Логин</th>
              <th>Роль</th>
              <th>ФИО</th>
              <th>Группа</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.id }}</td>
              <td><strong>{{ u.login }}</strong></td>
              <td><span class="ui-badge ui-badge--accent">{{ u.role }}</span></td>
              <td>{{ u.full_name || '—' }}</td>
              <td>{{ u.group_id ?? '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import api from '../api'

const groups = ref([])
const teachers = ref([])
const users = ref([])

const newGroup = ref({ name: '', teacher_id: 0 })
const newTeacher = ref({ login: '', password: '', full_name: '' })
const newStudent = ref({ login: '', password: '', full_name: '', group_id: null })

const msg = reactive({
  group: null,
  teacher: null,
  student: null
})

const loadTeachers = async () => {
  const res = await api.get('/admin/teachers')
  teachers.value = res.data
  if (teachers.value.length && !newGroup.value.teacher_id) {
    newGroup.value.teacher_id = teachers.value[0].id
  }
}

const loadGroups = async () => {
  const res = await api.get('/admin/groups')
  groups.value = res.data
}

const loadUsers = async () => {
  const res = await api.get('/admin/users')
  users.value = res.data
}

const createGroup = async () => {
  msg.group = null
  try {
    await api.post('/admin/groups', {
      name: newGroup.value.name,
      teacher_id: newGroup.value.teacher_id
    })
    newGroup.value.name = ''
    msg.group = { ok: true, text: 'Группа создана' }
    await loadGroups()
    await loadUsers()
  } catch (e) {
    msg.group = { ok: false, text: e.response?.data?.error || 'Ошибка' }
  }
}

const createTeacher = async () => {
  msg.teacher = null
  try {
    await api.post('/admin/users', {
      login: newTeacher.value.login,
      password: newTeacher.value.password,
      role: 'teacher',
      full_name: newTeacher.value.full_name || null
    })
    newTeacher.value = { login: '', password: '', full_name: '' }
    msg.teacher = { ok: true, text: 'Преподаватель создан' }
    await loadTeachers()
    await loadUsers()
  } catch (e) {
    msg.teacher = { ok: false, text: e.response?.data?.error || 'Ошибка' }
  }
}

const createStudent = async () => {
  msg.student = null
  try {
    const body = {
      login: newStudent.value.login,
      password: newStudent.value.password,
      role: 'student',
      full_name: newStudent.value.full_name || null,
      group_id: newStudent.value.group_id
    }
    await api.post('/admin/users', body)
    newStudent.value = { login: '', password: '', full_name: '', group_id: null }
    msg.student = { ok: true, text: 'Ученик создан' }
    await loadUsers()
  } catch (e) {
    msg.student = { ok: false, text: e.response?.data?.error || 'Ошибка' }
  }
}

onMounted(async () => {
  await loadTeachers()
  await loadGroups()
  await loadUsers()
})
</script>
