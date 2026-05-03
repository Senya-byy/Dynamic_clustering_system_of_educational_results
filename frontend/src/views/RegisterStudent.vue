<template>
  <div class="login-page">
    <div class="login-card login-card--wide">
      <div class="login-card__logo" aria-hidden="true">▣</div>
      <h2>Регистрация: студент</h2>
      <p class="subtitle">Логин, пароль, ФИО и выбор своей группы.</p>

      <form @submit.prevent="submit">
        <label class="ui-label" for="rs-login">Логин</label>
        <input
          id="rs-login"
          v-model="login"
          class="ui-input"
          autocomplete="username"
          required
          maxlength="50"
          placeholder="латиница, цифры, . _ -"
        />

        <label class="ui-label" for="rs-pass">Пароль</label>
        <input
          id="rs-pass"
          v-model="password"
          class="ui-input"
          type="password"
          autocomplete="new-password"
          required
          placeholder="≥ 8 символов, буква и цифра"
        />

        <label class="ui-label" for="rs-pass2">Повтор пароля</label>
        <input
          id="rs-pass2"
          v-model="password2"
          class="ui-input"
          type="password"
          autocomplete="new-password"
          required
        />

        <label class="ui-label" for="rs-fio">ФИО</label>
        <input
          id="rs-fio"
          v-model="fullName"
          class="ui-input"
          required
          maxlength="200"
          placeholder="Иванов Иван Иванович"
        />

        <label class="ui-label" for="rs-group">Группа</label>
        <p v-if="groups.length === 0" class="ui-alert">Список групп пуст — попросите преподавателя создать группу.</p>
        <select
          v-else
          id="rs-group"
          v-model.number="groupId"
          class="ui-select"
          required
        >
          <option disabled :value="0">Выберите группу</option>
          <option v-for="g in groups" :key="g.id" :value="g.id">
            {{ g.name }} — {{ g.teacher_name || g.teacher_login || 'преподаватель' }}
          </option>
        </select>

        <div class="ui-actions">
          <button
            type="submit"
            class="ui-btn ui-btn--primary"
            :disabled="loading || groups.length === 0"
          >
            {{ loading ? '…' : 'Зарегистрироваться' }}
          </button>
        </div>
      </form>

      <p class="hint">
        <router-link class="login-feedback__link" to="/register">Назад</router-link>
        ·
        <router-link class="login-feedback__link" to="/login">Вход</router-link>
      </p>
      <p v-if="error" class="ui-alert ui-alert--error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const authStore = useAuthStore()

const login = ref('')
const password = ref('')
const password2 = ref('')
const fullName = ref('')
const groupId = ref(0)
const groups = ref([])
const error = ref('')
const loading = ref(false)

const loadGroups = async () => {
  try {
    const res = await api.get('/register/groups')
    groups.value = res.data || []
    if (groups.value.length && groupId.value === 0) {
      groupId.value = groups.value[0].id
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Не удалось загрузить список групп'
  }
}

onMounted(() => {
  loadGroups()
})

const submit = async () => {
  error.value = ''
  if (password.value !== password2.value) {
    error.value = 'Пароли не совпадают'
    return
  }
  if (!groupId.value) {
    error.value = 'Выберите группу'
    return
  }
  loading.value = true
  try {
    const res = await api.post('/register/student', {
      login: login.value,
      password: password.value,
      full_name: fullName.value,
      group_id: groupId.value,
    })
    await authStore.applyAuthPayload(res.data)
    router.push('/student/quiz')
  } catch (e) {
    error.value = e.response?.data?.error || 'Ошибка регистрации'
  } finally {
    loading.value = false
  }
}
</script>
