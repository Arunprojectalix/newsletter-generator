import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Check, X, Loader2, RefreshCw } from 'lucide-react'
import { useStore } from '@/store/useStore'
import { newsletterApi } from '@/services/api'

export default function NewsletterPreview() {
  const [refreshKey, setRefreshKey] = useState(0)
  const { 
    currentNewsletter, 
    setCurrentNewsletter,
    currentConversation,
    setCurrentConversation,
    setIsChatDisabled,
    isGenerating 
  } = useStore()

  // fetch newsletter
  const { data: _ } = useQuery({
    queryKey: ['newsletter', currentConversation?._id],
    queryFn: async () => {
      if (!currentConversation?.newsletter_id) return null
      const newsletter = await newsletterApi.get(currentConversation.newsletter_id)
      setCurrentNewsletter(newsletter)
      return newsletter
    },
    enabled: !!currentConversation?._id && !currentNewsletter,
  })

  const actionMutation = useMutation({
    mutationFn: async (action: 'accept' | 'reject') => {
      if (!currentNewsletter) return
      
      await newsletterApi.action(currentNewsletter._id, action)
      
      // Update local state
      setCurrentNewsletter({
        ...currentNewsletter,
        status: `${action}ed` as any,
      })
      
      // Close conversation
      if (currentConversation) {
        setCurrentConversation({
          ...currentConversation,
          status: 'closed',
        })
      }
      
      setIsChatDisabled(true)
    },
  })

  const handleRefresh = () => {
    setRefreshKey((k) => k + 1)
  }

  if (!currentNewsletter) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center">
          <p>No newsletter to preview</p>
          <p className="text-sm mt-2">Start a chat to generate a newsletter</p>
        </div>
      </div>
    )
  }

  const canTakeAction = 
    currentNewsletter.status === 'generated' && 
    currentConversation?.status === 'active'

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Newsletter Preview</h2>
          <button
            onClick={handleRefresh}
            className="p-1 hover:bg-gray-100 rounded"
            title="Refresh preview"
          >
            <RefreshCw className="h-4 w-4 text-gray-500" />
          </button>
        </div>
        
        {/* Status */}
        <div className="mt-2">
          {isGenerating && (
            <div className="flex items-center text-sm text-blue-600">
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Generating newsletter...
            </div>
          )}
          
          {currentNewsletter.status === 'error' && (
            <div className="text-sm text-red-600">
              Error: {currentNewsletter.error_message}
            </div>
          )}
          
          {currentNewsletter.status === 'accepted' && (
            <div className="text-sm text-green-600">
              Newsletter accepted
            </div>
          )}
          
          {currentNewsletter.status === 'rejected' && (
            <div className="text-sm text-red-600">
              Newsletter rejected
            </div>
          )}
        </div>
      </div>

      {/* Preview */}
      <div className="flex-1 overflow-hidden">
        {currentNewsletter.status === 'generating' ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary-600 mx-auto mb-4" />
              <p className="text-gray-600">Generating newsletter...</p>
              <p className="text-sm text-gray-500 mt-2">This may take a few moments</p>
            </div>
          </div>
        ) : currentNewsletter.status === 'error' ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-red-600">
              <p className="font-semibold">Failed to generate newsletter</p>
              <p className="text-sm mt-2">{currentNewsletter.error_message}</p>
            </div>
          </div>
        ) : (
          <iframe
            key={refreshKey}
            src={`${import.meta.env.VITE_API_URL}/api/v1/preview/${currentNewsletter._id}?v=${currentNewsletter.version}`}
            className="w-full h-full border-0"
            title="Newsletter Preview"
          />
        )}
      </div>

      {/* Actions */}
      {canTakeAction && (
        <div className="border-t border-gray-200 bg-white px-6 py-4">
          <div className="flex space-x-4">
            <button
              onClick={() => actionMutation.mutate('accept')}
              disabled={actionMutation.isPending}
              className="flex-1 btn-primary flex items-center justify-center"
            >
              {actionMutation.isPending && actionMutation.variables === 'accept' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Accept
                </>
              )}
            </button>
            
            <button
              onClick={() => actionMutation.mutate('reject')}
              disabled={actionMutation.isPending}
              className="flex-1 btn-secondary flex items-center justify-center"
            >
              {actionMutation.isPending && actionMutation.variables === 'reject' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <X className="h-4 w-4 mr-2" />
                  Reject
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
