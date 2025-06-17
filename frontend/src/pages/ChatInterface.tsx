import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useStore } from '@/store/useStore'
import ChatList from '@/components/chat/ChatList'
import ChatWindow from '@/components/chat/ChatWindow'
import NewsletterPreview from '@/components/newsletter/NewsletterPreview'
import { neighborhoodApi, conversationApi, newsletterApi } from '@/services/api'
import { Loader2 } from 'lucide-react'

export default function ChatInterface() {
  const { neighborhoodId } = useParams<{ neighborhoodId: string }>()
  const navigate = useNavigate()
  const [newsletterVersion, setNewsletterVersion] = useState(0)
  
  const {
    setCurrentNeighborhood,
    currentConversation,
    setCurrentConversation,
    setCurrentNewsletter,
    conversations,
    setConversations,
    setIsGenerating,
  } = useStore()

  // Fetch neighborhood
  const { data: neighborhood, isLoading: neighborhoodLoading } = useQuery({
    queryKey: ['neighborhood', neighborhoodId],
    queryFn: () => neighborhoodApi.get(neighborhoodId!),
    enabled: !!neighborhoodId,
  })

  // Fetch conversations
  const { data: conversationsList } = useQuery({
    queryKey: ['conversations', neighborhoodId],
    queryFn: () => conversationApi.listByNeighborhood(neighborhoodId!),
    enabled: !!neighborhoodId,
  })

  // Fetch newsletters for this neighborhood
  const { data: allNewsletters } = useQuery({
    queryKey: ['newsletters'],
    queryFn: newsletterApi.list,
  })

  // Create conversation mutation
  const createConversationMutation = useMutation({
    mutationFn: () => conversationApi.create(neighborhoodId!),
    onSuccess: async (conversation) => {
      setCurrentConversation(conversation)
      
      // Generate newsletter
      setIsGenerating(true)
      const newsletter = await newsletterApi.generate(neighborhoodId!, conversation._id)
      setCurrentNewsletter(newsletter)
      
      // Start polling for newsletter status
      pollNewsletterStatus(newsletter._id)
    },
  })

  // Poll newsletter status
  const pollNewsletterStatus = (newsletterId: string) => {
    const interval = setInterval(async () => {
      try {
        const newsletter = await newsletterApi.get(newsletterId)
        setCurrentNewsletter(newsletter)
        
        if (newsletter.status !== 'generating') {
          clearInterval(interval)
          setIsGenerating(false)
          setNewsletterVersion((v) => v + 1)
        }
      } catch (error) {
        clearInterval(interval)
        setIsGenerating(false)
      }
    }, 2000)
  }

  // Helper function to find newsletter by conversation ID
  const findNewsletterByConversationId = (conversationId: string) => {
    return allNewsletters?.find(newsletter => newsletter.conversation_id === conversationId)
  }

  // Helper function to find latest newsletter for neighborhood
  const findLatestNewsletterForNeighborhood = () => {
    return allNewsletters?.find(newsletter => newsletter.neighborhood_id === neighborhoodId)
  }

  // Initialize
  useEffect(() => {
    if (neighborhood) {
      setCurrentNeighborhood(neighborhood)
    }
  }, [neighborhood, setCurrentNeighborhood])

  useEffect(() => {
    if (conversationsList && allNewsletters) {
      setConversations(conversationsList)
      
      // Auto-create conversation if none exist
      if (conversationsList.length === 0) {
        createConversationMutation.mutate()
      } else {
        // Load the most recent conversation
        const latestConversation = conversationsList[0]
        setCurrentConversation(latestConversation)
        
        // Find associated newsletter by conversation_id
        const associatedNewsletter = findNewsletterByConversationId(latestConversation._id)
        if (associatedNewsletter) {
          setCurrentNewsletter(associatedNewsletter)
          setNewsletterVersion((v) => v + 1)
        } else {
          // If no newsletter for this conversation, try to find the latest newsletter for this neighborhood
          const latestNewsletter = findLatestNewsletterForNeighborhood()
          if (latestNewsletter) {
            setCurrentNewsletter(latestNewsletter)
            setNewsletterVersion((v) => v + 1)
          }
        }
      }
    }
  }, [conversationsList, allNewsletters, setConversations])

  if (neighborhoodLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (!neighborhood) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Neighborhood not found</p>
          <button onClick={() => navigate('/new')} className="btn-primary">
            Create New Neighborhood
          </button>
        </div>
      </div>
    )
  }

  const handleNewChat = () => {
    navigate('/new')
  }

  const handleSelectConversation = async (conversationId: string) => {
    const conversation = conversations.find((c) => c._id === conversationId)
    if (conversation) {
      setCurrentConversation(conversation)
      
      // Find associated newsletter by conversation_id
      const associatedNewsletter = findNewsletterByConversationId(conversationId)
      if (associatedNewsletter) {
        setCurrentNewsletter(associatedNewsletter)
        setNewsletterVersion((v) => v + 1)
      } else {
        // If no newsletter for this conversation, try to find the latest newsletter for this neighborhood
        const latestNewsletter = findLatestNewsletterForNeighborhood()
        if (latestNewsletter) {
          setCurrentNewsletter(latestNewsletter)
          setNewsletterVersion((v) => v + 1)
        }
      }
    }
  }

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Left Column - Chat List */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <ChatList
          conversations={conversations}
          currentConversationId={currentConversation?._id}
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
        />
      </div>

      {/* Middle Column - Chat Window */}
      <div className="flex-1 flex flex-col">
        <ChatWindow />
      </div>

      {/* Right Column - Newsletter Preview */}
      <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
        <NewsletterPreview key={newsletterVersion} />
      </div>
    </div>
  )
}
