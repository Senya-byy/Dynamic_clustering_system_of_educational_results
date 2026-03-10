<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-card__logo" aria-hidden="true">▣</div>
      <h2>Вход</h2>
      <p class="subtitle">Учёт посещаемости и ответов на парах</p>

      <form @submit.prevent="handleLogin">
        <label class="ui-label" for="login">Логин</label>
        <input
          id="login"
          v-model="login"
          class="ui-input"
          placeholder="Введите логин"
          required
          autocomplete="username"
        />

        <label class="ui-label" for="password">Пароль</label>
        <input
          id="password"
          v-model="password"
          class="ui-input"
          type="password"
          placeholder="••••••••"
          required
          autocomplete="current-password"
        />

        <div class="ui-actions">
          <button type="submit" class="ui-btn ui-btn--primary">Войти</button>
        </div>
      </form>

      <p class="hint">
        Демо: <strong>teacher</strong> / teacher123 · <strong>student</strong> / student123 ·
        <strong>admin</strong> / admin123
      </p>
      <p v-if="error" class="ui-alert ui-alert--error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../store/auth'
import { useRouter, useRoute } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const login = ref('')
const password = ref('')
const error = ref('')

const handleLogin = async () => {
  const success = await authStore.login(login.value, password.value)
  if (success) {
    const role = authStore.role
    const redir = route.query.redirect
    if (typeof redir === 'string' && redir.startsWith('/')) {
      router.push(redir)
      return
    }
    if (role === 'admin') {
      router.push('/admin')
    } else if (role === 'teacher') {
      router.push('/teacher/sessions')
    } else if (role === 'student') {
      router.push('/student/quiz')
    } else {
      router.push('/')
    }
  } else {
    error.value = 'Неверный логин или пароль'
  }
}
</script>
