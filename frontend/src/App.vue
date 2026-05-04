<template>
  <div id="app" class="app-root">
    <nav v-if="authStore.token" class="topnav">
      <div class="topnav__inner">
        <router-link
          class="topnav__brand"
          :to="
            authStore.role === 'student'
              ? '/student/quiz'
              : authStore.role === 'admin'
                ? '/admin'
                : '/teacher/sessions'
          "
        >ClassQR</router-link>

        <router-link v-if="authStore.role === 'admin'" to="/admin">Админ</router-link>

        <template v-if="authStore.role === 'teacher' || authStore.role === 'admin'">
          <router-link to="/teacher/questions">Вопросы</router-link>
          <router-link to="/teacher/sessions">Пары и QR</router-link>
          <router-link to="/teacher/check">Проверка</router-link>
          <router-link to="/teacher/schedule">Расписание</router-link>
          <router-link to="/teacher/analytics">Аналитика</router-link>
        </template>

        <template v-if="authStore.role === 'student'">
          <router-link to="/student/quiz">Ответ</router-link>
          <router-link to="/my-answers">Мои ответы</router-link>
        </template>

        <router-link to="/rating">Рейтинг</router-link>
        <router-link to="/profile">Профиль</router-link>

        <span class="topnav__spacer" />
        <button type="button" class="btn-logout" @click="logout">Выйти</button>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useAuthStore } from './store/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>
