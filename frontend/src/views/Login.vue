<template>
  <div class="login-container">
    <h2>Вход в систему</h2>
    <form @submit.prevent="handleLogin">
      <input v-model="login" type="text" placeholder="Логин" required />
      <input v-model="password" type="password" placeholder="Пароль" required />
      <button type="submit">Войти</button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const login = ref('')
const password = ref('')
const router = useRouter()

const handleLogin = async () => {
  try {
    const response = await axios.post('/api/auth/login', {
      login: login.value,
      password: password.value
    })
    localStorage.setItem('token', response.data.access_token)
    localStorage.setItem('user', JSON.stringify(response.data.user))
    
    // Редирект в зависимости от роли
    if (response.data.user.role === 'teacher') {
      router.push('/teacher/dashboard')
    } else if (response.data.user.role === 'student') {
      router.push('/student/quiz')
    } else if (response.data.user.role === 'admin') {
      router.push('/admin/users')
    }
  } catch (error) {
    alert('Ошибка авторизации: ' + error.response?.data?.error || 'Неизвестная ошибка')
  }
}
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 100px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
}
</style>
