// Lightweight API client for the SAWA backend.
const API_BASE_URL = 'https://sawa-ai-backend.vercel.app/api/v1'

const TOKEN_KEY = 'sawa_token'
const BUSINESS_KEY = 'sawa_business_id'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export function getStoredBusinessId(): string | null {
  return localStorage.getItem(BUSINESS_KEY)
}

export function setStoredBusinessId(id: string | null) {
  if (id) localStorage.setItem(BUSINESS_KEY, id)
  else localStorage.removeItem(BUSINESS_KEY)
}

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

interface ApiFetchOptions {
  method?: string
  headers?: Record<string, string>
  body?: unknown
}

export async function apiFetch<T = unknown>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  }

  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const businessId = getStoredBusinessId()
  if (businessId) headers['X-Business-ID'] = businessId

  let body: BodyInit | null | undefined
  if (options.body !== undefined) {
    if (
      options.body instanceof URLSearchParams ||
      options.body instanceof FormData
    ) {
      body = options.body
    } else {
      headers['Content-Type'] = 'application/json'
      body = JSON.stringify(options.body)
    }
  }

  const init: RequestInit = {
    ...options,
    headers,
    body,
  }

  const resp = await fetch(`${API_BASE_URL}${path}`, init)

  if (resp.status === 401) {
    // Clear expired token and send to login.
    setToken(null)
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    throw new ApiError(401, 'Not authenticated')
  }

  let data: unknown = null
  const text = await resp.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = null
    }
  }

  if (!resp.ok) {
    const detail =
      data && typeof data === 'object' && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : resp.statusText
    throw new ApiError(resp.status, detail)
  }

  return data as T
}

// ---------------------------------------------------------------------------
// Auth API
// ---------------------------------------------------------------------------

export interface UserOut {
  id: number
  email: string
  full_name: string
  phone: string
  is_platform_admin: boolean
  is_active: boolean
  created_at: string | null
}

export interface BusinessOut {
  id: number
  name: string
  business_type: string
  description: string
  location: string
  phone: string
  email: string
  website: string
  primary_language: string
  currency: string
  timezone: string
  status: string
  onboarding_completed: boolean
  created_at: string | null
}

export interface BusinessMembershipOut {
  business: BusinessOut
  role: string
  permissions: string[]
}

export interface MeResponse {
  user: UserOut
  memberships: BusinessMembershipOut[]
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface RegisterRequest {
  email: string
  full_name: string
  password: string
  phone?: string
  business_name?: string | null
}

export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<TokenResponse>('/auth/login', {
      method: 'POST',
      // OAuth2 form-encoded
      body: new URLSearchParams({ username: email, password }),
    }),

  register: (data: RegisterRequest) =>
    apiFetch<TokenResponse>('/auth/register', {
      method: 'POST',
      body: data,
    }),

  me: () => apiFetch<MeResponse>('/auth/me'),
}

// ---------------------------------------------------------------------------
// Businesses API
// ---------------------------------------------------------------------------

export const businessesApi = {
  list: () => apiFetch<BusinessOut[]>('/businesses/'),
  create: (data: { name: string }) =>
    apiFetch<BusinessOut>('/businesses/', {
      method: 'POST',
      body: data,
    }),
}

// ---------------------------------------------------------------------------
// SMS API
// ---------------------------------------------------------------------------

export interface SMSSendRequest {
  phone: string
  message: string
}

export interface SMSSendResponse {
  success: boolean
  provider: string
  message_id: string
  error: string
}

export interface SMSMessageOut {
  id: number
  business_id: number
  to_phone: string
  body: string
  provider: string
  status: string
  provider_message_id: string
  error_message: string
  created_at: string | null
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export const smsApi = {
  send: (data: SMSSendRequest) =>
    apiFetch<SMSSendResponse>('/sms/send', {
      method: 'POST',
      body: data,
    }),
  history: (page = 1, page_size = 20) =>
    apiFetch<Paginated<SMSMessageOut>>(
      `/sms/history?page=${page}&page_size=${page_size}`,
    ),
}

// ---------------------------------------------------------------------------
// Campaigns API
// ---------------------------------------------------------------------------

export interface CampaignOut {
  id: number
  business_id: number
  name: string
  channel: string
  audience: Record<string, unknown>
  message: string
  language: string
  schedule_at: string | null
  status: string
  is_ai_generated: boolean
  ai_prompt: string
  approved: boolean
  created_at: string | null
  updated_at: string | null
}

export interface CampaignList {
  items: CampaignOut[]
  total: number
}

export interface CampaignCreateRequest {
  name: string
  channel: string
  audience: Record<string, unknown>
  message: string
  language?: string
}

export interface CampaignExecuteOut {
  campaign_id: number
  total: number
  sent: number
  failed: number
  status: string
}

export const campaignsApi = {
  list: () => apiFetch<CampaignList>('/campaigns/'),
  create: (data: CampaignCreateRequest) =>
    apiFetch<CampaignOut>('/campaigns/', {
      method: 'POST',
      body: data,
    }),
  execute: (id: number) =>
    apiFetch<CampaignExecuteOut>(`/campaigns/${id}/execute`, {
      method: 'POST',
    }),
}

// ---------------------------------------------------------------------------
// Automations API
// ---------------------------------------------------------------------------

export type AutomationTrigger =
  | 'whatsapp_message_received'
  | 'new_lead_created'
  | 'scheduled_time'

export interface AutomationStepCreate {
  step_type: 'action' | 'condition' | 'delay'
  action_type?: string
  config: Record<string, unknown>
  order_index: number
}

export interface AutomationCreateRequest {
  name: string
  is_active: boolean
  trigger_type: AutomationTrigger
  steps: AutomationStepCreate[]
}

export interface AutomationOut {
  id: number
  business_id: number
  name: string
  description: string
  trigger_type: string
  trigger_config: Record<string, unknown>
  is_active: boolean
  created_at: string | null
  updated_at: string | null
}

export interface AutomationList {
  items: AutomationOut[]
  total: number
}

const TRIGGER_LABELS: Record<AutomationTrigger, string> = {
  whatsapp_message_received: 'WhatsApp message received',
  new_lead_created: 'New lead created',
  scheduled_time: 'Scheduled time',
}

export function triggerLabel(trigger: string): string {
  return (
    TRIGGER_LABELS[trigger as AutomationTrigger] ?? trigger.replaceAll('_', ' ')
  )
}

export const automationsApi = {
  list: () => apiFetch<AutomationList>('/automations/'),
  create: (data: AutomationCreateRequest) =>
    apiFetch<AutomationOut>('/automations/', {
      method: 'POST',
      body: data,
    }),
  update: (
    id: number,
    data: {
      is_active?: boolean
      name?: string
      steps?: AutomationStepCreate[]
    },
  ) =>
    apiFetch<AutomationOut>(`/automations/${id}`, {
      method: 'PATCH',
      body: data,
    }),
  remove: (id: number) =>
    apiFetch<null>(`/automations/${id}`, { method: 'DELETE' }),
}

// ---------------------------------------------------------------------------
// Analytics API (Phase 11)
// ---------------------------------------------------------------------------

export interface MessageVolumePoint {
  date: string
  whatsapp: number
  sms: number
}

export interface LeadFunnelStage {
  stage: string
  count: number
}

export interface CampaignPerformance {
  total_campaigns: number
  total_sent: number
  total_delivered: number
  total_failed: number
}

export interface AiVsHuman {
  ai_handled: number
  human_handled: number
}

export interface DashboardQuickStats {
  total_messages_30d: number
  active_automations: number
  won_leads: number
  campaign_delivery_rate: number
}

export interface DashboardResponse {
  message_volume: MessageVolumePoint[]
  lead_funnel: LeadFunnelStage[]
  campaign_performance: CampaignPerformance
  ai_vs_human: AiVsHuman
  stats: DashboardQuickStats
}

export const analyticsApi = {
  dashboard: () => apiFetch<DashboardResponse>('/analytics/dashboard'),
}