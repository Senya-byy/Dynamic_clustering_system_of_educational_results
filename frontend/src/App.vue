<template>
  <div id="app" class="app-root">
    <nav
      v-if="authStore.token"
      class="topnav"
      :class="{ 'topnav--menu-open': navMenuOpen }"
    >
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
          @click="navMenuOpen = false"
        >ClassQR</router-link>

        <button
          type="button"
          class="topnav__burger"
          :aria-expanded="navMenuOpen"
          aria-controls="topnav-menu"
          aria-label="Открыть меню"
          @click="navMenuOpen = !navMenuOpen"
        >
          <span />
          <span />
          <span />
        </button>

        <div class="topnav__backdrop" aria-hidden="true" @click="navMenuOpen = false" />

        <div id="topnav-menu" class="topnav__menu" role="navigation">
          <router-link v-if="authStore.role === 'admin'" to="/admin" @click="navMenuOpen = false">Админ</router-link>

          <template v-if="authStore.role === 'teacher' || authStore.role === 'admin'">
            <router-link to="/teacher/questions" @click="navMenuOpen = false">Вопросы</router-link>
            <router-link to="/teacher/sessions" @click="navMenuOpen = false">Пары и QR</router-link>
            <router-link to="/teacher/check" @click="navMenuOpen = false">Проверка</router-link>
            <router-link to="/teacher/schedule" @click="navMenuOpen = false">Расписание</router-link>
            <router-link to="/teacher/analytics" @click="navMenuOpen = false">Аналитика</router-link>
          </template>

          <template v-if="authStore.role === 'student'">
            <router-link to="/student/quiz" @click="navMenuOpen = false">Ответ</router-link>
            <router-link to="/my-answers" @click="navMenuOpen = false">Мои ответы</router-link>
          </template>

          <router-link to="/rating" @click="navMenuOpen = false">Рейтинг</router-link>
          <router-link to="/profile" @click="navMenuOpen = false">Профиль</router-link>

          <span class="topnav__spacer" />
          <button type="button" class="btn-logout" @click="logoutAndClose">Выйти</button>
        </div>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>

    <YandexMetrika />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAuthStore } from './store/auth'
import { useRouter, useRoute } from 'vue-router'
import YandexMetrika from './components/YandexMetrika.vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const navMenuOpen = ref(false)

watch(
  () => route.fullPath,
  () => {
    navMenuOpen.value = false
  }
)

const logout = () => {
  authStore.logout()
  router.push('/login')
}

const logoutAndClose = () => {
  navMenuOpen.value = false
  logout()
}
</script>
