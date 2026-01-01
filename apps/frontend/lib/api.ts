// API base URL - always use relative /api path
// Next.js rewrite rule will proxy /api/* to backend
// This works both in development (via Next.js rewrite) and production (via nginx)
function getApiUrl(): string {
  // Always use relative /api path
  // Next.js will handle the rewrite to backend
  return '/api'
}

export interface ChatRequest {
  session_id?: string
  message: string
}

export interface SourceInfo {
  type: 'kb' | 'website'
  id: number
  title?: string
  url?: string
}

export interface ChatResponse {
  session_id: string
  answer: string
  sources: SourceInfo[]
  refused: boolean
  openai_called: boolean
  missing_info?: any
  // Debug fields - only present in development
  debug?: {
    llm_called: boolean
    retrieval_hits: {
      kb: number
      website: number
    }
  }
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  ok: boolean
}

export interface UserInfo {
  username: string
}

export interface Category {
  id: number
  title: string
  created_at: string
}

export interface KBQA {
  id: number
  category_id?: number
  question: string
  answer: string
  created_at: string
  updated_at: string
}

export interface ChatLog {
  id: number
  session_id: string
  user_message: string
  bot_message: string
  sources_json?: {
    kb_ids?: number[]
    website_page_ids?: number[]
  }
  refused: boolean
  intent?: string | null
  created_at: string
}

export interface WebsiteSource {
  id: number
  base_url: string
  enabled: boolean
  created_at: string
  last_crawled_at?: string
  crawl_status: string
  pages_count?: number
}

export interface Greeting {
  id: number
  message: string
  enabled: boolean
  priority: number
  created_at: string
  updated_at: string
}

export interface Intent {
  id: number
  name: string
  keywords: string
  response: string
  enabled: boolean
  priority: number
  created_at: string
  updated_at: string
}

export interface HealthResponse {
  backend: { status: string; message?: string }
  db: { status: string; message?: string }
  openai: { status: string; message?: string }
  website_crawler: { status: string; message?: string }
}

class ApiClient {
  private baseUrl: string

  constructor() {
    this.baseUrl = getApiUrl()
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryOn401: boolean = true
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    try {
      const response = await fetch(url, {
        ...options,
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      })

      if (!response.ok) {
        if (response.status === 401 && retryOn401 && !endpoint.includes('/auth/refresh') && !endpoint.includes('/auth/login')) {
          // Try to refresh token once (only if not already calling refresh or login endpoint)
          try {
            const refreshResponse = await fetch(`${this.baseUrl}/auth/refresh`, {
              method: 'POST',
              credentials: 'include',
              headers: {
                'Content-Type': 'application/json',
              },
            })
            
            if (refreshResponse.ok) {
              // Token refreshed - cookies are set automatically by browser (httpOnly)
              // Retry original request once
              return this.request<T>(endpoint, options, false)
            }
          } catch (refreshError) {
            // Refresh failed - proceed to handle unauthorized
          }
          
          // Refresh failed or not applicable - handle unauthorized
          this.handleUnauthorized()
          throw new Error('Unauthorized')
        }
        
        if (response.status === 401 && !endpoint.includes('/auth/login')) {
          // Already tried refresh or refresh endpoint itself - handle unauthorized
          // Don't redirect if we're already on login page
          this.handleUnauthorized()
          throw new Error('Unauthorized')
        }
        
        // Try to parse error response
        let errorDetail = 'خطای نامشخص'
        try {
          const errorData = await response.json()
          const detail = errorData.detail || errorData.message || ''
          
          // Translate common errors to Persian
          if (detail.includes('Database connection error') || detail.includes('Database error')) {
            errorDetail = 'خطای اتصال به پایگاه داده. لطفا مطمئن شوید که پایگاه داده راه‌اندازی شده است.'
          } else if (detail.includes('Invalid credentials')) {
            errorDetail = 'نام کاربری یا رمز عبور اشتباه است'
          } else if (detail.includes('Not authenticated')) {
            errorDetail = 'احراز هویت انجام نشده است'
          } else if (detail) {
            errorDetail = detail
          } else {
            errorDetail = `HTTP ${response.status}: ${response.statusText || 'خطای نامشخص'}`
          }
        } catch {
          // If JSON parsing fails, use status text
          if (response.status === 500) {
            errorDetail = 'خطای سرور: لطفا مطمئن شوید که پایگاه داده و سرویس‌ها در حال اجرا هستند'
          } else {
            errorDetail = `HTTP ${response.status}: ${response.statusText || 'خطای نامشخص'}`
          }
        }
        throw new Error(errorDetail)
      }

      return response.json()
    } catch (error: any) {
      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Network error: Could not connect to backend. Please check if the backend is running.')
      }
      // Re-throw if it's already an Error with a message
      if (error instanceof Error) {
        throw error
      }
      // Fallback
      throw new Error(error?.message || 'Unknown error occurred')
    }
  }

  private handleUnauthorized(): void {
    // Only handle in browser environment
    if (typeof window === 'undefined') {
      return
    }

    // If we're in admin area, redirect to login
    if (window.location.pathname.startsWith('/admin')) {
      // Clear any stale state
      this.logout().catch(() => {
        // Ignore logout errors, just redirect
      })
      // Immediate redirect to login
      window.location.href = '/admin/login'
    }
  }

  // Chat
  async chat(data: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Auth
  async login(data: LoginRequest): Promise<LoginResponse> {
    return this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' })
    } catch (error) {
      // Even if logout fails, clear client-side state
      console.warn('Logout request failed, clearing client state')
    }
  }

  async getMe(): Promise<UserInfo> {
    return this.request<UserInfo>('/auth/me')
  }

  // Admin KB
  async getCategories(): Promise<Category[]> {
    return this.request<Category[]>('/admin/kb/categories')
  }

  async createCategory(data: { title: string }): Promise<Category> {
    return this.request<Category>('/admin/kb/categories', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateCategory(id: number, data: { title?: string }): Promise<Category> {
    return this.request<Category>(`/admin/kb/categories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteCategory(id: number): Promise<void> {
    await this.request(`/admin/kb/categories/${id}`, { method: 'DELETE' })
  }

  async getKBQA(): Promise<KBQA[]> {
    return this.request<KBQA[]>('/admin/kb/qa')
  }

  async createKBQA(data: { category_id?: number; question: string; answer: string }): Promise<KBQA> {
    return this.request<KBQA>('/admin/kb/qa', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateKBQA(id: number, data: { category_id?: number; question?: string; answer?: string }): Promise<KBQA> {
    return this.request<KBQA>(`/admin/kb/qa/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteKBQA(id: number): Promise<void> {
    await this.request(`/admin/kb/qa/${id}`, { method: 'DELETE' })
  }

  // Admin Logs
  async getLogs(params?: { limit?: number; offset?: number; search?: string }): Promise<{
    logs: ChatLog[]
    total: number
    limit: number
    offset: number
  }> {
    const query = new URLSearchParams()
    if (params?.limit) query.append('limit', params.limit.toString())
    if (params?.offset) query.append('offset', params.offset.toString())
    if (params?.search) query.append('search', params.search)
    return this.request(`/admin/logs?${query.toString()}`)
  }

  // Admin Website
  async getWebsiteSources(): Promise<WebsiteSource[]> {
    return this.request<WebsiteSource[]>('/admin/website')
  }

  async createWebsiteSource(data: { base_url: string; enabled?: boolean }): Promise<WebsiteSource> {
    return this.request<WebsiteSource>('/admin/website', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateWebsiteSource(id: number, data: { enabled?: boolean }): Promise<WebsiteSource> {
    return this.request<WebsiteSource>(`/admin/website/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteWebsiteSource(id: number): Promise<void> {
    await this.request(`/admin/website/${id}`, { method: 'DELETE' })
  }

  async recrawlWebsite(id: number): Promise<{ status: string; message?: string }> {
    return this.request(`/admin/website/${id}/recrawl`, { method: 'POST' })
  }

  async getWebsiteStatus(id: number): Promise<{
    status: string
    last_crawled_at?: string
    pages_count: number
  }> {
    return this.request(`/admin/website/${id}/status`)
  }

  // Admin Greeting
  async getGreetings(): Promise<Greeting[]> {
    return this.request<Greeting[]>('/admin/greeting')
  }

  async createGreeting(data: { message: string; enabled?: boolean; priority?: number }): Promise<Greeting> {
    return this.request<Greeting>('/admin/greeting', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateGreeting(id: number, data: { message?: string; enabled?: boolean; priority?: number }): Promise<Greeting> {
    return this.request<Greeting>(`/admin/greeting/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteGreeting(id: number): Promise<void> {
    await this.request(`/admin/greeting/${id}`, { method: 'DELETE' })
  }

  // Admin Intent
  async getIntents(): Promise<Intent[]> {
    return this.request<Intent[]>('/admin/intent')
  }

  async createIntent(data: { name: string; keywords: string; response: string; enabled?: boolean; priority?: number }): Promise<Intent> {
    return this.request<Intent>('/admin/intent', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateIntent(id: number, data: { name?: string; keywords?: string; response?: string; enabled?: boolean; priority?: number }): Promise<Intent> {
    return this.request<Intent>(`/admin/intent/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteIntent(id: number): Promise<void> {
    await this.request(`/admin/intent/${id}`, { method: 'DELETE' })
  }

  // Chat Greeting
  async getGreeting(): Promise<{ message: string }> {
    return this.request<{ message: string }>('/chat/greeting')
  }

  // Health
  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health/components')
  }
}

// Lazy instantiation to avoid errors during build time
let apiInstance: ApiClient | null = null

export const api: ApiClient = (() => {
  if (!apiInstance) {
    apiInstance = new ApiClient()
  }
  return apiInstance
})()

