export interface ManagerInfo {
  email: string
  whatsapp?: string
}

export interface BrandingInfo {
  company_name: string
  footer_description: string
  primary_color?: string
  logo_url?: string
}

export interface Neighborhood {
  _id: string
  title: string
  postcode: string
  frequency: 'Weekly' | 'Monthly'
  info?: string
  manager: ManagerInfo
  radius: number
  branding: BrandingInfo
  created_at: string
  updated_at: string
  is_active: boolean
}

export interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface Conversation {
  _id: string
  neighborhood_id: string
  newsletter_id?: string
  messages: Message[]
  status: 'active' | 'closed'
  created_at: string
  updated_at: string
  closed_at?: string
}

export interface EventDetails {
  event_title: string
  description: string
  location: string
  cost: string
  date: string
  booking_details?: string
  images: string[]
  additional_info?: string
  is_recurring: boolean
  tags: string[]
  source_url?: string
  verified: boolean
}

export interface Newsletter {
  _id: string
  neighborhood_id: string
  conversation_id?: string
  newsletter_metadata: {
    location: string
    postcode: string
    radius: number
    generation_date: string
    template_version: string
    source_count: number
    verification_status: string
  }
  content: {
    header: Record<string, any>
    main_channel: Record<string, any>
    weekly_schedule?: Record<string, any>
    monthly_schedule?: Record<string, any>
    featured_venue?: Record<string, any>
    partner_spotlight?: Record<string, any>
    newsletter_highlights: Array<Record<string, any>>
    events: EventDetails[]
  }
  status: 'generating' | 'generated' | 'accepted' | 'rejected' | 'error'
  error_message?: string
  created_at: string
  updated_at: string
  version: number
}
