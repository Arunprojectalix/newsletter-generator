import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { neighborhoodApi } from '@/services/api'
import { Loader2 } from 'lucide-react'

export default function NeighborhoodForm() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    title: '',
    postcode: '',
    frequency: 'Weekly' as 'Weekly' | 'Monthly',
    info: '',
    manager: {
      email: '',
      whatsapp: '',
    },
    radius: 2,
    branding: {
      company_name: '',
      footer_description: '',
      primary_color: '#1E40AF',
      logo_url: '',
    },
  })

  const createMutation = useMutation({
    mutationFn: neighborhoodApi.create,
    onSuccess: (data) => {
      navigate(`/chat/${data._id}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData)
  }

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    
    if (name.includes('.')) {
      const [parent, child] = name.split('.')
      setFormData((prev) => {
        if (parent === 'manager') {
          return {
            ...prev,
            manager: {
              ...prev.manager,
              [child]: value,
            },
          }
        } else if (parent === 'branding') {
          return {
            ...prev,
            branding: {
              ...prev.branding,
              [child]: value,
            },
          }
        }
        return prev
      })
    } else {
      setFormData((prev) => ({
        ...prev,
        [name]: name === 'radius' ? parseFloat(value) : value,
      }))
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white shadow-xl rounded-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Create New Neighborhood</h1>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-800">Basic Information</h2>
              
              <div>
                <label htmlFor="title" className="form-label">
                  Title *
                </label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  required
                  className="input-field"
                  placeholder="Tower Hamlets Community"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="postcode" className="form-label">
                    Postcode *
                  </label>
                  <input
                    type="text"
                    id="postcode"
                    name="postcode"
                    value={formData.postcode}
                    onChange={handleInputChange}
                    required
                    className="input-field"
                    placeholder="E1 6LF"
                  />
                </div>
                
                <div>
                  <label htmlFor="frequency" className="form-label">
                    Frequency *
                  </label>
                  <select
                    id="frequency"
                    name="frequency"
                    value={formData.frequency}
                    onChange={handleInputChange}
                    className="input-field"
                  >
                    <option value="Weekly">Weekly</option>
                    <option value="Monthly">Monthly</option>
                  </select>
                </div>
              </div>
              
              <div>
                <label htmlFor="radius" className="form-label">
                  Search Radius (miles) *
                </label>
                <input
                  type="number"
                  id="radius"
                  name="radius"
                  value={formData.radius}
                  onChange={handleInputChange}
                  required
                  min="0.5"
                  max="50"
                  step="0.5"
                  className="input-field"
                />
              </div>
              
              <div>
                <label htmlFor="info" className="form-label">
                  Additional Information
                </label>
                <textarea
                  id="info"
                  name="info"
                  value={formData.info}
                  onChange={handleInputChange}
                  rows={3}
                  className="input-field"
                  placeholder="Family-friendly community newsletter with focus on free activities..."
                />
              </div>
            </div>
            
            {/* Manager Information */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-800">Manager Information</h2>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="manager.email" className="form-label">
                    Email *
                  </label>
                  <input
                    type="email"
                    id="manager.email"
                    name="manager.email"
                    value={formData.manager.email}
                    onChange={handleInputChange}
                    required
                    className="input-field"
                    placeholder="manager@example.com"
                  />
                </div>
                
                <div>
                  <label htmlFor="manager.whatsapp" className="form-label">
                    WhatsApp (optional)
                  </label>
                  <input
                    type="tel"
                    id="manager.whatsapp"
                    name="manager.whatsapp"
                    value={formData.manager.whatsapp}
                    onChange={handleInputChange}
                    className="input-field"
                    placeholder="+447123456789"
                  />
                </div>
              </div>
            </div>
            
            {/* Branding */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-800">Branding</h2>
              
              <div>
                <label htmlFor="branding.company_name" className="form-label">
                  Company Name *
                </label>
                <input
                  type="text"
                  id="branding.company_name"
                  name="branding.company_name"
                  value={formData.branding.company_name}
                  onChange={handleInputChange}
                  required
                  className="input-field"
                  placeholder="Community Housing"
                />
              </div>
              
              <div>
                <label htmlFor="branding.footer_description" className="form-label">
                  Footer Description *
                </label>
                <input
                  type="text"
                  id="branding.footer_description"
                  name="branding.footer_description"
                  value={formData.branding.footer_description}
                  onChange={handleInputChange}
                  required
                  className="input-field"
                  placeholder="Building stronger communities together"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="branding.primary_color" className="form-label">
                    Primary Color
                  </label>
                  <input
                    type="color"
                    id="branding.primary_color"
                    name="branding.primary_color"
                    value={formData.branding.primary_color}
                    onChange={handleInputChange}
                    className="input-field h-10"
                  />
                </div>
                
                <div>
                  <label htmlFor="branding.logo_url" className="form-label">
                    Logo URL (optional)
                  </label>
                  <input
                    type="url"
                    id="branding.logo_url"
                    name="branding.logo_url"
                    value={formData.branding.logo_url}
                    onChange={handleInputChange}
                    className="input-field"
                    placeholder="https://example.com/logo.png"
                  />
                </div>
              </div>
            </div>
            
            {/* Submit Button */}
            <div className="pt-6">
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="w-full btn-primary flex items-center justify-center"
              >
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5" />
                    Creating...
                  </>
                ) : (
                  'Create Neighborhood'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
