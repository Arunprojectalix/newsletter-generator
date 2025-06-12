import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, Loader2 } from 'lucide-react'
import { useStore } from '@/store/useStore'
import { conversationApi, newsletterApi } from '@/services/api'
import ChatMessage from './ChatMessage'

export default function ChatWindow() {
  const [message, setMessage] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const {
    currentConversation,
    setCurrentConversation,
    currentNewsletter,
    setCurrentNewsletter,
    isGenerating,
    isChatDisabled,
  } = useStore()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [currentConversation?.messages])

  // Add message mutation
  const addMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      if (!currentConversation || !currentNewsletter) return

      // Add user message
      const userMessage = await conversationApi.addMessage(currentConversation._id, content)
      
      // Update local conversation
      const updatedConversation = {
        ...currentConversation,
        messages: [...currentConversation.messages, userMessage],
      }
      setCurrentConversation(updatedConversation)

      // Update newsletter
      const updatedNewsletter = await newsletterApi.update(currentNewsletter._id, content)
      setCurrentNewsletter(updatedNewsletter)

      // Add AI response to conversation
      const aiMessage = {
        role: 'assistant' as const,
        content: 'Newsletter has been updated based on your request.',
        timestamp: new Date().toISOString(),
      }
      
      setCurrentConversation({
        ...updatedConversation,
        messages: [...updatedConversation.messages, userMessage, aiMessage],
      })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !addMessageMutation.isPending) {
      addMessageMutation.mutate(message)
      setMessage('')
    }
  }

  const isDisabled = 
    isChatDisabled || 
    isGenerating || 
    currentConversation?.status === 'closed' ||
    currentNewsletter?.status === 'accepted' ||
    currentNewsletter?.status === 'rejected'

  if (!currentConversation) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        Select a conversation to start chatting
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h2 className="text-lg font-semibold text-gray-900">Newsletter Chat</h2>
        <p className="text-sm text-gray-500">
          Chat with AI to customize your newsletter
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {currentConversation.messages.map((msg, index) => (
          <ChatMessage key={index} message={msg} />
        ))}
        
        {addMessageMutation.isPending && (
          <div className="flex items-center space-x-2 text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">AI is updating the newsletter...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white px-6 py-4">
        {isDisabled && (
          <div className="mb-2 text-sm text-gray-500 text-center">
            {currentConversation.status === 'closed' && 'This conversation is closed'}
            {currentNewsletter?.status === 'accepted' && 'Newsletter has been accepted'}
            {currentNewsletter?.status === 'rejected' && 'Newsletter has been rejected'}
            {isGenerating && 'Please wait while newsletter is being generated...'}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={isDisabled}
            placeholder={isDisabled ? 'Chat is disabled' : 'Type your message...'}
            className="flex-1 input-field"
          />
          <button
            type="submit"
            disabled={isDisabled || !message.trim()}
            className="btn-primary px-6"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  )
}
