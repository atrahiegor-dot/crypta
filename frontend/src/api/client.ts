import axios from 'axios'

// In production (Vercel): /api/* → proxy → Render backend
// In dev: Vite proxies /api to localhost:8000
const BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
})

// Inject JWT token from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('tasker_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth endpoints (no token needed)
export async function authTelegram(initData: string): Promise<string> {
  const res = await api.post<{ access_token: string }>('/auth/telegram', {
    init_data: initData,
  })
  return res.data.access_token
}

export default api
