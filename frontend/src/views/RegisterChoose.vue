<template>
  <div class="login-page">
    <div class="login-card login-card--wide">
      <div class="login-card__logo">
        <img src="/favicon.png" alt="ClassQR" width="44" height="44" />
      </div>
      <h2>Регистрация</h2>
      <p class="subtitle">Выберите роль.</p>

      <div class="register-choose">
        <router-link class="ui-btn ui-btn--primary register-choose__btn" to="/register/student">
          Студент
        </router-link>
        <router-link class="ui-btn ui-btn--secondary register-choose__btn" to="/register/teacher">
          Преподаватель
        </router-link>
      </div>

      <p class="hint">
        Уже есть аккаунт?
        <router-link class="login-feedback__link" to="/login">Войти</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.register-choose {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.register-choose__btn {
  text-align: center;
  text-decoration: none;
  display: block;
}
</style>
