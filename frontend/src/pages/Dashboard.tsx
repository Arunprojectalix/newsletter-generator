import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Plus, Calendar, MapPin, FileText, Eye, Trash2 } from 'lucide-react'
import { newsletterApi, neighborhoodApi } from '@/services/api'
import type { Newsletter } from '@/types'

export default function Dashboard() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Fetch all newsletters
  const { data: newsletters, isLoading } = useQuery({
    queryKey: ['newsletters'],
    queryFn: newsletterApi.list,
  })

  // Fetch neighborhoods to get neighborhood details
  const { data: neighborhoods } = useQuery({
    queryKey: ['neighborhoods'],
    queryFn: neighborhoodApi.list,
  })

  // Delete newsletter mutation
  const deleteMutation = useMutation({
    mutationFn: newsletterApi.delete,
    onSuccess: () => {
      // Invalidate and refetch newsletters
      queryClient.invalidateQueries({ queryKey: ['newsletters'] })
    },
  })

  const getNeighborhoodById = (id: string) => {
    return neighborhoods?.find((n) => n._id === id)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'generated':
        return 'bg-green-100 text-green-800'
      case 'generating':
        return 'bg-blue-100 text-blue-800'
      case 'accepted':
        return 'bg-emerald-100 text-emerald-800'
      case 'rejected':
        return 'bg-red-100 text-red-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  }

  const handleCardClick = (newsletter: Newsletter) => {
    navigate(`/chat/${newsletter.neighborhood_id}`)
  }

  const handlePreviewNewsletter = (e: React.MouseEvent, newsletter: Newsletter) => {
    e.stopPropagation()
    window.open(`/api/v1/preview/${newsletter._id}`, '_blank')
  }

  const handleDeleteNewsletter = (e: React.MouseEvent, newsletter: Newsletter) => {
    e.stopPropagation()
    if (window.confirm('Are you sure you want to delete this newsletter? This action cannot be undone.')) {
      deleteMutation.mutate(newsletter._id)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading newsletters...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Newsletter Dashboard</h1>
            <p className="mt-2 text-gray-600">
              Manage and view all your community newsletters
            </p>
          </div>
          <button
            onClick={() => navigate('/new')}
            className="btn-primary flex items-center"
          >
            <Plus className="h-5 w-5 mr-2" />
            Create New Newsletter
          </button>
        </div>

        {/* Stats */}
        {newsletters && newsletters.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <FileText className="h-8 w-8 text-primary-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Newsletters</p>
                  <p className="text-2xl font-semibold text-gray-900">{newsletters.length}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                  <div className="h-4 w-4 bg-green-600 rounded-full"></div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Generated</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {newsletters.filter((n) => n.status === 'generated' || n.status === 'accepted').length}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <div className="h-4 w-4 bg-blue-600 rounded-full animate-pulse"></div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">In Progress</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {newsletters.filter((n) => n.status === 'generating').length}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="h-8 w-8 bg-emerald-100 rounded-full flex items-center justify-center">
                  <div className="h-4 w-4 bg-emerald-600 rounded-full"></div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Accepted</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {newsletters.filter((n) => n.status === 'accepted').length}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Newsletters Grid */}
        {newsletters && newsletters.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {newsletters.map((newsletter) => {
              const neighborhood = getNeighborhoodById(newsletter.neighborhood_id)
              return (
                <div
                  key={newsletter._id}
                  onClick={() => handleCardClick(newsletter)}
                  className="bg-white rounded-lg shadow hover:shadow-lg transition-all cursor-pointer transform hover:scale-105"
                >
                  <div className="p-6">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                          {neighborhood?.title || newsletter.newsletter_metadata.location}
                        </h3>
                        <div className="flex items-center text-sm text-gray-500 mb-2">
                          <MapPin className="h-4 w-4 mr-1" />
                          {newsletter.newsletter_metadata.postcode}
                        </div>
                      </div>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                          newsletter.status
                        )}`}
                      >
                        {newsletter.status}
                      </span>
                    </div>

                    {/* Content Preview */}
                    <div className="mb-4">
                      <p className="text-sm text-gray-600 line-clamp-3">
                        {newsletter.content.main_channel?.welcome_message ||
                          `Newsletter for ${newsletter.newsletter_metadata.location} community`}
                      </p>
                    </div>

                    {/* Events Count */}
                    <div className="flex items-center text-sm text-gray-500 mb-4">
                      <Calendar className="h-4 w-4 mr-1" />
                      {newsletter.content.events?.length || 0} events
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                      <span className="text-sm text-gray-500">
                        {formatDate(newsletter.created_at)}
                      </span>
                      <div className="flex space-x-2">
                        <button
                          onClick={(e) => handlePreviewNewsletter(e, newsletter)}
                          className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded"
                          title="Preview newsletter"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={(e) => handleDeleteNewsletter(e, newsletter)}
                          disabled={deleteMutation.isPending}
                          className="text-red-400 hover:text-red-600 transition-colors p-1 rounded disabled:opacity-50"
                          title="Delete newsletter"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-semibold text-gray-900">No newsletters yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating your first community newsletter.
            </p>
            <div className="mt-6">
              <button
                onClick={() => navigate('/new')}
                className="btn-primary flex items-center mx-auto"
              >
                <Plus className="h-5 w-5 mr-2" />
                Create Your First Newsletter
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 