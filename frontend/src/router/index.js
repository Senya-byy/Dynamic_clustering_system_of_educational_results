import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import TeacherQuestionCreator from '../components/TeacherQuestionCreator.vue'
import TeacherSessionManager from '../components/TeacherSessionManager.vue'
import TeacherCheckPanel from '../components/TeacherCheckPanel.vue'
import StudentQuiz from '../components/StudentQuiz.vue'
import MyAnswers from '../components/MyAnswers.vue'
import Rating from '../components/Rating.vue'
import Profile from '../components/Profile.vue'
import JoinSession from '../components/JoinSession.vue'
import TeacherSchedule from '../components/TeacherSchedule.vue'
import TeacherAnalytics from '../components/TeacherAnalytics.vue'
import AdminPanel from '../components/AdminPanel.vue'

const teacherMeta = { roles: ['teacher', 'admin'] }

const routes = [
  { path: '/login', component: Login },
  { path: '/join', component: JoinSession, meta: { public: true } },
  { path: '/', redirect: '/login' },
  { path: '/admin', component: AdminPanel, meta: { role: 'admin' } },
  { path: '/teacher/questions', component: TeacherQuestionCreator, meta: teacherMeta },
  { path: '/teacher/sessions', component: TeacherSessionManager, meta: teacherMeta },
  { path: '/teacher/check', component: TeacherCheckPanel, meta: teacherMeta },
  { path: '/teacher/schedule', component: TeacherSchedule, meta: teacherMeta },
  { path: '/teacher/analytics', component: TeacherAnalytics, meta: teacherMeta },
  { path: '/student/quiz', component: StudentQuiz, meta: { role: 'student' } },
  { path: '/my-answers', component: MyAnswers, meta: { role: 'student' } },
  { path: '/rating', component: Rating, meta: { roles: ['student', 'teacher', 'admin'] } },
  { path: '/profile', component: Profile, meta: { roles: ['student', 'teacher', 'admin'] } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const role = localStorage.getItem('role')

  if (to.meta?.public && to.path === '/join') {
    if (!token) {
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
    if (role !== 'student') {
      next(role === 'admin' ? '/admin' : '/teacher/sessions')
      return
    }
    next()
    return
  }

  if (!token && to.path !== '/login') {
    next('/login')
    return
  }

  if (to.path === '/login' && token) {
    if (role === 'student') {
      next('/student/quiz')
    } else if (role === 'admin') {
      next('/admin')
    } else {
      next('/teacher/sessions')
    }
    return
  }

  if (to.meta?.role && role !== to.meta.role) {
    next('/login')
    return
  }
  if (to.meta?.roles && !to.meta.roles.includes(role)) {
    next('/login')
    return
  }
  next()
})

export default router
