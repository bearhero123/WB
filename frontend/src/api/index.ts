import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截: 自动携带 Admin Key
api.interceptors.request.use((config) => {
  const adminKey = localStorage.getItem('adminKey')
  if (adminKey) {
    config.headers['X-Admin-Key'] = adminKey
  }
  return config
})

// 响应拦截
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 401) {
      ElMessage.error(typeof detail === 'object' ? detail.message : '认证失败')
      localStorage.removeItem('adminKey')
      window.location.href = '/login'
    } else if (status === 403) {
      ElMessage.error(typeof detail === 'object' ? detail.message : '权限不足')
    } else if (status === 404) {
      ElMessage.error(typeof detail === 'string' ? detail : '资源不存在')
    } else if (status === 409) {
      ElMessage.error(typeof detail === 'string' ? detail : '资源冲突')
    } else {
      ElMessage.error(`请求失败: ${error.message}`)
    }
    return Promise.reject(error)
  }
)

// ========================
// 账号 API
// ========================
export const accountApi = {
  list: (skip = 0, limit = 50) =>
    api.get('/admin/accounts', { params: { skip, limit } }),
  get: (id: number) => api.get(`/admin/accounts/${id}`),
  create: (data: any) => api.post('/admin/accounts', data),
  update: (id: number, data: any) => api.put(`/admin/accounts/${id}`, data),
  delete: (id: number) => api.delete(`/admin/accounts/${id}`),
}

// ========================
// 密钥 API
// ========================
export const keyApi = {
  list: (skip = 0, limit = 50) =>
    api.get('/admin/keys', { params: { skip, limit } }),
  get: (id: number) => api.get(`/admin/keys/${id}`),
  create: (data: any) => api.post('/admin/keys', data),
  update: (id: number, data: any) => api.put(`/admin/keys/${id}`, data),
  delete: (id: number) => api.delete(`/admin/keys/${id}`),
}

// ========================
// 任务 API
// ========================
export const taskApi = {
  checkin: (accountId: number) =>
    api.post(`/admin/tasks/checkin/${accountId}`),
  checkinAll: () => api.post('/admin/tasks/checkin-all'),
  validateCookie: (accountId: number) =>
    api.post(`/admin/tasks/validate-cookie/${accountId}`),
  applySchedules: () => api.post('/admin/tasks/apply-schedules'),
  applySchedule: (accountId: number) =>
    api.post(`/admin/tasks/apply-schedule/${accountId}`),
  schedulerStatus: () => api.get('/admin/tasks/scheduler-status'),
  logs: (params?: { account_id?: number; event_type?: string; status?: string; skip?: number; limit?: number }) =>
    api.get('/admin/tasks/logs', { params }),
}

// ========================
// 推送 API
// ========================
export const pushApi = {
  test: (sendkey?: string) =>
    api.post('/admin/push/test', null, { params: sendkey ? { sendkey } : {} }),
  testAccount: (accountId: number) =>
    api.post(`/admin/push/test/${accountId}`),
}

// ========================
// 健康检查
// ========================
export const healthApi = {
  check: () => api.get('/health'),
}

export default api
