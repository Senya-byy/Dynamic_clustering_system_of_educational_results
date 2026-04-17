import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (typeof window !== 'undefined') {
    const h = window.location.hostname
    if (h !== 'localhost' && h !== '127.0.0.1') {
      config.headers['X-Frontend-Origin'] = window.location.origin
    }
  }
  return config
})

export default api
