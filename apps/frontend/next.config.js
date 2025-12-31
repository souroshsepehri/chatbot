/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Get backend URL from environment variable
    // Default: 8000 for production, 8001 for dev mode
    // Dev mode detection: if running on port 3001, use backend port 8001
    // Also check if we're running via 'npm run dev' (which sets NODE_ENV=development)
    const isDev = process.env.NODE_ENV === 'development' || process.env.PORT === '3001' || !process.env.NODE_ENV || process.env.NODE_ENV === ''
    // Force dev mode to use port 8001 (backend dev server)
    const defaultPort = '8001'  // Always use 8001 for now (dev mode)
    const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL || `http://127.0.0.1:${defaultPort}`
    
    // Remove trailing slash if present
    const cleanBackendUrl = backendUrl.replace(/\/$/, '')
    
    // Log in development mode only
    if (process.env.NODE_ENV !== 'production') {
      console.log(`[Next.js] API rewrites: /api/* -> ${cleanBackendUrl}/*`)
    }
    
    return [
      {
        source: '/api/:path*',
        destination: `${cleanBackendUrl}/:path*`,
      },
    ]
  },
}

module.exports = nextConfig

