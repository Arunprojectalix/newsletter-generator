import axios from 'axios'
import type { Neighborhood, Newsletter, Conversation, Message } from '@/types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Neighborhoods
export const neighborhoodApi = {
  create: async (data: Omit<Neighborhood, '_id' | 'created_at' | 'updated_at' | 'is_active'>) => {
    const response = await api.post<Neighborhood>('/neighborhoods', data)
    return response.data
  },
  
  get: async (id: string) => {
    const response = await api.get<Neighborhood>(`/neighborhoods/${id}`)
    return response.data
  },
  
  list: async () => {
    const response = await api.get<Neighborhood[]>('/neighborhoods')
    return response.data
  },
  
  delete: async (id: string) => {
    const response = await api.delete(`/neighborhoods/${id}`)
    return response.data
  },
}

// Newsletters
export const newsletterApi = {
  list: async () => {
    const response = await api.get<Newsletter[]>('/newsletters')
    return response.data
  },

  generate: async (neighborhoodId: string, conversationId?: string) => {
    const response = await api.post<Newsletter>('/newsletters/generate', {
      neighborhood_id: neighborhoodId,
      conversation_id: conversationId,
    })
    return response.data
  },
  
  get: async (id: string) => {
    const response = await api.get<Newsletter>(`/newsletters/${id}`)
    return response.data
  },
  
  update: async (id: string, message: string) => {
    const response = await api.put<Newsletter>(`/newsletters/${id}/update`, {
      user_message: message,
    })
    return response.data
  },
  
  action: async (id: string, action: 'accept' | 'reject', feedback?: string) => {
    const response = await api.post(`/newsletters/${id}/action`, {
      action,
      feedback,
    })
    return response.data
  },

  delete: async (id: string) => {
    const response = await api.delete(`/newsletters/${id}`)
    return response.data
  },
}

// Conversations
export const conversationApi = {
  create: async (neighborhoodId: string, newsletterId?: string) => {
    const response = await api.post<Conversation>('/conversations', {
      neighborhood_id: neighborhoodId,
      newsletter_id: newsletterId,
    })
    return response.data
  },
  
  get: async (id: string) => {
    const response = await api.get<Conversation>(`/conversations/${id}`)
    return response.data
  },
  
  addMessage: async (id: string, content: string) => {
    const response = await api.post<Message>(`/conversations/${id}/messages`, {
      content,
      role: 'user',
    })
    return response.data
  },

  chat: async (id: string, content: string) => {
    const response = await api.post<Message>(`/conversations/${id}/chat`, {
      content,
      role: 'user',
    })
    return response.data
  },
  
  listByNeighborhood: async (neighborhoodId: string) => {
    const response = await api.get<Conversation[]>(`/conversations/neighborhood/${neighborhoodId}`)
    return response.data
  },
}

export default api
