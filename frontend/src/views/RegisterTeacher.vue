<template>
  <div class="login-page">
    <div class="login-card login-card--wide">
      <div class="login-card__logo">
        <img src="/favicon.png" alt="ClassQR" width="44" height="44" />
      </div>
      <h2>Регистрация: преподаватель</h2>
      <p class="subtitle">Логин, пароль, ФИО и выбор существующих групп. Новые группы добавляет администратор.</p>

      <form @submit.prevent="submit">
        <label class="ui-label" for="rt-login">Логин</label>
        <input
          id="rt-login"
          v-model="login"
          class="ui-input"
          autocomplete="username"
          required
          maxlength="50"
          placeholder="латиница, цифры, . _ -"
        />

        <label class="ui-label" for="rt-pass">Пароль</label>
        <input
          id="rt-pass"
          v-model="password"
          class="ui-input"
          type="password"
          autocomplete="new-password"
          required
          placeholder="≥ 8 символов, буква и цифра"
        />

        <label class="ui-label" for="rt-pass2">Повтор пароля</label>
        <input
          id="rt-pass2"
          v-model="password2"
          class="ui-input"
          type="password"
          autocomplete="new-password"
          required
        />

        <label class="ui-label" for="rt-fio">ФИО</label>
        <input
          id="rt-fio"
          v-model="fullName"
          class="ui-input"
          required
          maxlength="200"
          placeholder="Иванов Иван Иванович"
        />

        <label class="ui-label" for="rt-existing-groups">Выберите существующие группы (можно несколько)</label>
        <select
          id="rt-existing-groups"
          v-model="selectedGroupIds"
          multiple
          class="ui-select ui-select--multi"
        >
          <option v-for="g in groups" :key="g.id" :value="g.id">
            {{ g.name }} — {{ g.teacher_name || g.teacher_login || 'преподаватель' }}
          </option>
        </select>

        <div class="ui-actions">
          <button type="submit" class="ui-btn ui-btn--primary" :disabled="loading">
            {{ loading ? '…' : 'Зарегистрироваться' }}
          </button>
        </div>
      </form>

      <p class="hint">Если нужной группы нет в списке — попросите администратора добавить её.</p>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const authStore = useAuthStore()

const login = ref('')
const password = ref('')
const password2 = ref('')
const fullName = ref('')
const groups = ref([])
const selectedGroupIds = ref([])
const error = ref('')
const loading = ref(false)

const submit = async () => {
  error.value = ''
  if (password.value !== password2.value) {
    error.value = 'Пароли не совпадают'
    return
  }
  const gids = (selectedGroupIds.value || []).map((x) => parseInt(x, 10)).filter(Boolean)
  if (!gids.length) {
    error.value = 'Выберите хотя бы одну группу'
    return
  }
  loading.value = true
  try {
    const res = await api.post('/register/teacher', {
      login: login.value,
      password: password.value,
      full_name: fullName.value,
      group_ids: gids,
      new_group_names: [],
    })
    await authStore.applyAuthPayload(res.data)
    router.push('/teacher/sessions')
  } catch (e) {
    error.value = e.response?.data?.error || 'Ошибка регистрации'
  } finally {
    loading.value = false
  }
}

const loadGroups = async () => {
  try {
    const res = await api.get('/register/groups')
    groups.value = res.data || []
  } catch {
    groups.value = []
  }
}

onMounted(() => {
  loadGroups()
})
</script>

<style scoped>
.ui-textarea {
  resize: vertical;
  min-height: 6rem;
  font-family: inherit;
}
</style>
