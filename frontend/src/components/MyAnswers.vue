<template>
  <div class="page-narrow">
    <h2>Мои ответы</h2>
    <p class="page-lead">Баллы и комментарии появляются после проверки.</p>

    <div v-for="ans in answers" :key="ans.id" class="ui-card">
      <p class="block-title">Вопрос</p>
      <p>{{ ans.question_text }}</p>
      <p class="block-title">Мой ответ</p>
      <p class="answer-body">{{ ans.student_answer }}</p>
      <p class="ui-meta">
        Баллы:
        <strong>{{ ans.score !== null ? ans.score : 'не проверено' }}</strong>
        / {{ ans.max_score }}
      </p>
      <p v-if="ans.is_correct !== null && ans.is_correct !== undefined" class="ui-meta">
        Быстрая оценка:
        <span class="ui-badge ui-badge--accent">{{ ans.is_correct ? 'верно' : 'неверно' }}</span>
      </p>
      <p class="block-title">Комментарий</p>
      <p>{{ ans.comment || '—' }}</p>
      <p class="block-title">Эталон / критерии</p>
      <p class="muted-block">{{ ans.correct_answer || '—' }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const answers = ref([])

onMounted(async () => {
  const res = await api.get('/answers/my')
  answers.value = res.data
})
</script>

<style scoped>
.block-title {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
  margin: 1rem 0 0.35rem;
}
.block-title:first-child {
  margin-top: 0;
}
.answer-body {
  white-space: pre-wrap;
  line-height: 1.55;
  margin: 0;
}
.muted-block {
  color: var(--text-muted);
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0;
}
</style>
