<template>
  <div class="page-narrow">
    <h2>Профиль</h2>

    <div v-if="profile" class="ui-card">
      <p class="ui-meta"><strong>Логин:</strong> {{ profile.login }}</p>
      <p class="ui-meta"><strong>Роль:</strong> <span class="ui-badge ui-badge--accent">{{ profile.role }}</span></p>

      <label class="ui-label" for="fn">Полное имя</label>
      <input id="fn" v-model="profile.full_name" class="ui-input" />

      <p class="ui-label" style="margin-top: 1rem">Приватность в рейтинге</p>
      <label class="radio-line"><input v-model="profile.privacy_mode" type="radio" :value="true" /> Скрыть имя («Студент N»)</label>
      <label class="radio-line"><input v-model="profile.privacy_mode" type="radio" :value="false" /> Показывать имя</label>

      <div class="ui-actions">
        <button type="button" class="ui-btn ui-btn--primary" @click="saveProfile">Сохранить</button>
      </div>
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
      <p class="ui-meta" style="margin-top: 0">
        Сообщите о проблеме, идее или вопросе через форму Class-QR (Google). Откроется в новой вкладке.
      </p>
      <p style="margin: 0">
        <a
          class="profile-feedback-link"
          :href="feedbackFormUrl"
          target="_blank"
          rel="noopener noreferrer"
        >
          Открыть форму обратной связи
        </a>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { useAuthStore } from '../store/auth'
import { FEEDBACK_FORM_URL } from '../config/feedback'

const feedbackFormUrl = FEEDBACK_FORM_URL

const authStore = useAuthStore()
const profile = ref(null)
const pwd = ref({ old: '', new: '' })
const pwdMsg = ref('')
const pwdErr = ref(false)

const fetchProfile = async () => {
  const res = await api.get('/auth/profile')
  profile.value = res.data
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

onMounted(fetchProfile)
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
</style>
