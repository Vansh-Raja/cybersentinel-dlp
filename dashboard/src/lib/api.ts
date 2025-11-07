import axios from 'axios'
import { useAuthStore } from './store/auth'

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token && config.headers) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// Handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = useAuthStore.getState().refreshToken
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
        const response = await axios.post(
          `${apiUrl}/auth/refresh`,
          { refresh_token: refreshToken }
        )

        const { access_token, refresh_token } = response.data
        useAuthStore.getState().setTokens(access_token, refresh_token)

        if (originalRequest.headers) {
          originalRequest.headers['Authorization'] = `Bearer ${access_token}`
        }
        return apiClient(originalRequest)
      } catch (refreshError) {
        useAuthStore.getState().logout()
        window.location.href = '/'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export const api = {
  // Dashboard
  getDashboardOverview: async () => {
    const { data } = await apiClient.get('/dashboard/overview')
    return data
  },

  getEventTimeline: async (hours: number = 24) => {
    const { data } = await apiClient.get('/dashboard/timeline', {
      params: { hours },
    })
    return data
  },

  getAgentsStats: async () => {
    const { data } = await apiClient.get('/dashboard/stats/agents')
    return data
  },

  getClassificationStats: async () => {
    const { data } = await apiClient.get('/dashboard/stats/classification')
    return data
  },

  // Agents
  getAgents: async (params?: any) => {
    const { data } = await apiClient.get('/agents/', { params })
    return data
  },

  getAgent: async (agentId: string) => {
    const { data } = await apiClient.get(`/agents/${agentId}`)
    return data
  },

  createAgent: async (agent: any) => {
    const { data } = await apiClient.post('/agents', agent)
    return data
  },

  deleteAgent: async (agentId: string) => {
    const { data } = await apiClient.delete(`/agents/${agentId}`)
    return data
  },

  getAgentsSummary: async () => {
    const { data} = await apiClient.get('/agents/stats/summary')
    return data
  },

  // Events
  getEvents: async (params?: any) => {
    const { data } = await apiClient.get('/events/', { params })  // Use trailing slash
    return data
  },

  getEvent: async (eventId: string) => {
    const { data } = await apiClient.get(`/events/${eventId}`)
    return data
  },

  getEventStats: async () => {
    const { data } = await apiClient.get('/events/stats/summary')
    return data
  },

  // Classification
  getClassifiedFiles: async (params?: any) => {
    const { data } = await apiClient.get('/classification/files', { params })
    return data
  },

  getClassifiedFile: async (fileId: string) => {
    const { data } = await apiClient.get(`/classification/files/${fileId}`)
    return data
  },

  getClassificationSummary: async () => {
    const { data } = await apiClient.get('/classification/stats/summary')
    return data
  },

  getClassificationByType: async () => {
    const { data } = await apiClient.get('/classification/stats/by-type')
    return data
  },

  getDetectionPatterns: async () => {
    const { data } = await apiClient.get('/classification/patterns')
    return data
  },

  // Policies
  getPolicies: async (params?: any) => {
    const { data } = await apiClient.get('/policies', { params })
    return data
  },

  getPolicy: async (policyId: string) => {
    const { data } = await apiClient.get(`/policies/${policyId}`)
    return data
  },

  createPolicy: async (policy: any) => {
    const { data } = await apiClient.post('/policies', policy)
    return data
  },

  updatePolicy: async (policyId: string, policy: any) => {
    const { data } = await apiClient.put(`/policies/${policyId}`, policy)
    return data
  },

  deletePolicy: async (policyId: string) => {
    const { data } = await apiClient.delete(`/policies/${policyId}`)
    return data
  },

  getPolicyStats: async () => {
    const { data } = await apiClient.get('/policies/stats/summary')
    return data
  },

  // Users
  getCurrentUser: async () => {
    const { data } = await apiClient.get('/users/me')
    return data
  },

  getUsers: async (params?: any) => {
    const { data } = await apiClient.get('/users', { params })
    return data
  },

  getUser: async (userId: string) => {
    const { data } = await apiClient.get(`/users/${userId}`)
    return data
  },

  getUserStats: async () => {
    const { data } = await apiClient.get('/users/stats/summary')
    return data
  },

  // Alerts
  getAlerts: async () => {
    const { data } = await apiClient.get('/alerts')
    return data
  },

  acknowledgeAlert: async (alertId: string) => {
    const { data } = await apiClient.post(`/alerts/${alertId}/acknowledge`)
    return data
  },
}

export default apiClient
