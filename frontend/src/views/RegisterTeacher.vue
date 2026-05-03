<template>
  <div class="login-page">
    <div class="login-card login-card--wide">
      <div class="login-card__logo" aria-hidden="true">▣</div>
      <h2>Регистрация: преподаватель</h2>
      <p class="subtitle">
        Логин, пароль, ФИО и хотя бы одна группа (названия не должны совпадать с уже существующими в системе)
      </p>

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

        <label class="ui-label" for="rt-groups">Группы (по одному названию на строку)</label>
        <textarea
          id="rt-groups"
          v-model="groupLines"
          class="ui-input ui-textarea"
          rows="5"
          required
          placeholder="ИТ-251&#10;ИТ-252"
        />

        <div class="ui-actions">
          <button type="submit" class="ui-btn ui-btn--primary" :disabled="loading">
            {{ loading ? '…' : 'Зарегистрироваться' }}
          </button>
        </div>
      </form>

      <p class="hint">После входа дополнительные группы можно создать на странице «Пары и QR».</p>
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const authStore = useAuthStore()

const login = ref('')
const password = ref('')
const password2 = ref('')
const fullName = ref('')
const groupLines = ref('')
const error = ref('')
const loading = ref(false)

const parseGroupNames = () => {
  const raw = String(groupLines.value || '')
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter(Boolean)
  const out = []
  const seen = new Set()
  for (const s of raw) {
    const k = s.toLowerCase()
    if (seen.has(k)) continue
    seen.add(k)
    out.push(s)
  }
  return out
}

const submit = async () => {
  error.value = ''
  if (password.value !== password2.value) {
    error.value = 'Пароли не совпадают'
    return
  }
  const names = parseGroupNames()
  if (!names.length) {
    error.value = 'Укажите хотя бы одно название группы'
    return
  }
  loading.value = true
  try {
    const res = await api.post('/register/teacher', {
      login: login.value,
      password: password.value,
      full_name: fullName.value,
      new_group_names: names,
    })
    await authStore.applyAuthPayload(res.data)
    router.push('/teacher/sessions')
  } catch (e) {
    error.value = e.response?.data?.error || 'Ошибка регистрации'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.ui-textarea {
  resize: vertical;
  min-height: 6rem;
  font-family: inherit;
}
</style>
