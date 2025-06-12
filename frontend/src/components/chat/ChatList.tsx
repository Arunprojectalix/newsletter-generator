import { Plus, MessageSquare } from 'lucide-react'
import type { Conversation } from '@/types'

interface ChatListProps {
  conversations: Conversation[]
  currentConversationId?: string
  onSelectConversation: (id: string) => void
  onNewChat: () => void
}

export default function ChatList({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewChat,
}: ChatListProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={onNewChat}
          className="w-full btn-primary flex items-center justify-center"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-2 space-y-1">
          {conversations.map((conversation) => {
            const isActive = conversation._id === currentConversationId
            const lastMessage = conversation.messages[conversation.messages.length - 1]
            
            return (
              <button
                key={conversation._id}
                onClick={() => onSelectConversation(conversation._id)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-50 border-primary-200 border'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <MessageSquare className="h-5 w-5 text-gray-400 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      Newsletter Chat
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {lastMessage?.content || 'No messages yet'}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {formatDate(conversation.created_at)}
                    </p>
                  </div>
                  {conversation.status === 'closed' && (
                    <span className="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded">
                      Closed
                    </span>
                  )}
                </div>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
