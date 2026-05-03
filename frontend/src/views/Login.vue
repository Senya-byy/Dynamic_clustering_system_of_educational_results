<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-card__logo">
        <img src="/favicon.png" alt="ClassQR" width="44" height="44" />
      </div>
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
        <div class="ui-actions" style="margin-top: 0.75rem">
          <router-link class="ui-btn ui-btn--secondary" to="/register" style="text-decoration: none; text-align: center">
            Зарегистрироваться
          </router-link>
        </div>
      </form>

      <p class="hint">
        Демо: <strong>teacher</strong> / teacher123 · <strong>student</strong> / student123 ·
        <strong>admin</strong> / admin123
      </p>
      <p class="login-feedback">
        <a class="login-feedback__link" :href="feedbackFormUrl" target="_blank" rel="noopener noreferrer">Обратная связь</a>
      </p>
      <p v-if="error" class="ui-alert ui-alert--error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../store/auth'
import { useRouter, useRoute } from 'vue-router'
import { FEEDBACK_FORM_URL } from '../config/feedback'

const feedbackFormUrl = FEEDBACK_FORM_URL

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
