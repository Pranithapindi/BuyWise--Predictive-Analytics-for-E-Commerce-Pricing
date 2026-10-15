import axios from 'axios'
import toast from 'react-hot-toast'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor: attach Bearer token ───────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── Response interceptor: handle 401 with refresh ─────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }

    // Show error toast for non-401 errors
    const message = error.response?.data?.detail || error.message || 'Something went wrong'
    if (error.response?.status !== 401) {
      toast.error(message)
    }

    return Promise.reject(error)
  }
)

// ── API helper functions ──────────────────────────────────────────────────────
export const productsAPI = {
  track: (url, scrape_interval = 60) => api.post('/products/track', { url, scrape_interval }),
  list: (skip = 0, limit = 50) => api.get('/products', { params: { skip, limit } }),
  get: (id) => api.get(`/products/${id}`),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`),
  scrapeNow: (id) => api.post(`/products/${id}/scrape`),
  supportedWebsites: () => api.get('/products/supported-websites'),
}

export const analyticsAPI = {
  summary: (productId) => api.get(`/analytics/${productId}/summary`),
  history: (productId, limit = 200) => api.get(`/analytics/${productId}/history`, { params: { limit } }),
  stats: (productId) => api.get(`/analytics/${productId}/stats`),
  trends: (productId) => api.get(`/analytics/${productId}/trends`),
  chart: (productId) => api.get(`/analytics/${productId}/chart`),
  heatmap: (productId) => api.get(`/analytics/${productId}/heatmap`),
  monthly: (productId) => api.get(`/analytics/${productId}/monthly`),
}

export const mlAPI = {
  predict: (productId, days = 30) => api.get(`/ml/${productId}/predict`, { params: { days } }),
  recommend: (productId) => api.get(`/ml/${productId}/recommendation`),
  train: (productId) => api.post(`/ml/${productId}/train`),
}

export const alertsAPI = {
  create: (data) => api.post('/alerts', data),
  list: () => api.get('/alerts'),
  update: (id, data) => api.put(`/alerts/${id}`, data),
  delete: (id) => api.delete(`/alerts/${id}`),
}

export const searchAPI = {
  search: (params) => api.get('/search', { params }),
}

export const exportAPI = {
  export: (productId, format) => api.get(`/export/${productId}`, {
    params: { format },
    responseType: 'blob',
  }),
}

export const adminAPI = {
  stats: () => api.get('/admin/stats'),
  users: (skip = 0, limit = 100) => api.get('/admin/users', { params: { skip, limit } }),
  logs: (limit = 100, status_filter) => api.get('/admin/logs', { params: { limit, status_filter } }),
  deactivateUser: (userId) => api.put(`/admin/users/${userId}/deactivate`),
}
