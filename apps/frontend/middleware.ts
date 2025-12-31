import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname
  
  // Only protect admin routes (except login)
  // Note: We don't check cookies here because:
  // 1. Cookies set by backend (different origin) may not be visible to Next.js middleware
  // 2. Backend will validate authentication and return 401 if needed
  // 3. Frontend API client handles 401 responses and redirects to login
  // This middleware is kept for potential future use but currently just passes through
  
  if (pathname.startsWith('/admin') && pathname !== '/admin/login') {
    // Let the request through - backend will handle auth validation
    // Frontend API client will redirect to login on 401 responses
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: '/admin/:path*',
}

