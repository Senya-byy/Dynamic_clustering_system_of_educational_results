import { defineStore } from 'pinia'
import api from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('access_token'),
    role: localStorage.getItem('role'),
    userId: localStorage.getItem('user_id'),
    groupId: localStorage.getItem('group_id')
  }),
  actions: {
    async login(login, password) {
      try {
        const lo = String(login || '').trim()
        if (!lo || !password) {
          return false
        }
        const res = await api.post('/auth/login', { login: lo, password })
        await this.applyAuthPayload(res.data)
        return true
      } catch (e) {
        console.error(e)
        return false
      }
    },
    async applyAuthPayload(payload) {
      this.token = payload.access_token
      this.role = payload.role
      this.userId = String(payload.user_id)
      this.groupId = payload.group_id != null ? String(payload.group_id) : null
      localStorage.setItem('access_token', this.token)
      localStorage.setItem('role', this.role)
      localStorage.setItem('user_id', this.userId)
      if (this.groupId) {
        localStorage.setItem('group_id', this.groupId)
      } else {
        localStorage.removeItem('group_id')
      }
      await this.fetchProfile()
    },
    async fetchProfile() {
      try {
        const res = await api.get('/auth/profile')
        this.user = res.data
        if (res.data.group_id != null) {
          this.groupId = String(res.data.group_id)
          localStorage.setItem('group_id', this.groupId)
        }
      } catch (e) {
        console.error(e)
      }
    },
    logout() {
      this.token = null
      this.role = null
      this.userId = null
      this.groupId = null
      this.user = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('role')
      localStorage.removeItem('user_id')
      localStorage.removeItem('group_id')
    }
  }
})
