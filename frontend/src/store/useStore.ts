import { create } from 'zustand'
import type { Neighborhood, Newsletter, Conversation } from '@/types'

interface AppState {
  // Neighborhood
  currentNeighborhood: Neighborhood | null
  setCurrentNeighborhood: (neighborhood: Neighborhood | null) => void
  
  // Newsletter
  currentNewsletter: Newsletter | null
  setCurrentNewsletter: (newsletter: Newsletter | null) => void
  
  // Conversation
  currentConversation: Conversation | null
  setCurrentConversation: (conversation: Conversation | null) => void
  conversations: Conversation[]
  setConversations: (conversations: Conversation[]) => void
  
  // UI State
  isChatDisabled: boolean
  setIsChatDisabled: (disabled: boolean) => void
  isGenerating: boolean
  setIsGenerating: (generating: boolean) => void
}

export const useStore = create<AppState>((set) => ({
  // Neighborhood
  currentNeighborhood: null,
  setCurrentNeighborhood: (neighborhood) => set({ currentNeighborhood: neighborhood }),
  
  // Newsletter
  currentNewsletter: null,
  setCurrentNewsletter: (newsletter) => set({ currentNewsletter: newsletter }),
  
  // Conversation
  currentConversation: null,
  setCurrentConversation: (conversation) => set({ currentConversation: conversation }),
  conversations: [],
  setConversations: (conversations) => set({ conversations }),
  
  // UI State
  isChatDisabled: false,
  setIsChatDisabled: (disabled) => set({ isChatDisabled: disabled }),
  isGenerating: false,
  setIsGenerating: (generating) => set({ isGenerating: generating }),
}))
