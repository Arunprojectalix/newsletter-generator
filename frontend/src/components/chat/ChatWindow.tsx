import { useState, useRef, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, Loader2 } from 'lucide-react'
import { useStore } from '@/store/useStore'
import { conversationApi } from '@/services/api'
import ChatMessage from './ChatMessage'

export default function ChatWindow() {
  const [message, setMessage] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()
  
  const {
    currentConversation,
    setCurrentConversation,
    currentNewsletter,
    isGenerating,
    isChatDisabled,
  } = useStore()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [currentConversation?.messages])

  // Chat mutation - sends message and gets AI response with full context
  const chatMutation = useMutation({
    mutationFn: async (content: string) => {
      if (!currentConversation) return

      // Send message to AI and get response (this handles both user message and AI response)
      const aiResponse = await conversationApi.chat(currentConversation._id, content)
      
      // Fetch updated conversation to get both user message and AI response
      const updatedConversation = await conversationApi.get(currentConversation._id)
      setCurrentConversation(updatedConversation)
      
      // Invalidate conversations query to refresh the list
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      
      return aiResponse
    },
    onError: (error) => {
      console.error('Chat error:', error)
      // You could show a toast notification here
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !chatMutation.isPending) {
      chatMutation.mutate(message)
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
        <div className="text-center">
          <p>Select a conversation to start chatting</p>
          <p className="text-sm mt-2">Or create a new neighborhood to begin</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h2 className="text-lg font-semibold text-gray-900">Newsletter Chat</h2>
        <p className="text-sm text-gray-500">
          Chat with AI to customize your newsletter and get help
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {currentConversation.messages
          .filter(msg => msg.role !== 'system') // Hide system messages from UI
          .map((msg, index) => (
            <ChatMessage key={index} message={msg} />
          ))}
        
        {chatMutation.isPending && (
          <div className="flex items-center space-x-2 text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">AI is thinking...</span>
          </div>
        )}
        
        {chatMutation.error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-sm text-red-600">
              Sorry, I encountered an error. Please try again.
            </p>
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
            disabled={isDisabled || chatMutation.isPending}
            placeholder={
              isDisabled 
                ? 'Chat is disabled' 
                : chatMutation.isPending 
                  ? 'AI is responding...'
                  : 'Ask me anything about your newsletter...'
            }
            className="flex-1 input-field"
          />
          <button
            type="submit"
            disabled={isDisabled || !message.trim() || chatMutation.isPending}
            className="btn-primary px-6"
          >
            {chatMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </form>
        
        {/* Helpful suggestions */}
        {currentConversation.messages.length <= 1 && (
          <div className="mt-3 text-xs text-gray-500">
            <p className="mb-1">💡 Try asking:</p>
            <div className="flex flex-wrap gap-2">
              {[
                "Can you add more family events?",
                "Make the tone more friendly",
                "Add a section about local services",
                "What events are happening this week?"
              ].map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => setMessage(suggestion)}
                  className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded transition-colors"
                  disabled={chatMutation.isPending}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
