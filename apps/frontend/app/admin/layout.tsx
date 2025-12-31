'use client'

import { useEffect, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { LogOut, LayoutDashboard, FileText, BookOpen, FolderTree, Globe, Activity } from 'lucide-react'

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const [username, setUsername] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Skip auth check for login page
    if (pathname === '/admin/login') {
      setLoading(false)
      return
    }

    let cancelled = false

    // Check auth on mount for other admin pages
    api.getMe()
      .then(user => {
        if (!cancelled) {
          setUsername(user.username)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          console.error('Auth check failed:', err)
          setLoading(false)
          setUsername(null)
          // API client's handleUnauthorized will redirect, but if it doesn't, we do it here
          // Only redirect if we're not already on login page
          if (pathname !== '/admin/login') {
            router.replace('/admin/login')
          }
        }
      })

    return () => {
      cancelled = true
    }
  }, [router, pathname])

  // No polling needed - token refresh happens automatically on each API call
  // The API client handles 401 and refresh automatically

  const handleLogout = async () => {
    await api.logout()
    router.push('/admin/login')
  }

  // For login page, don't show the admin layout
  if (pathname === '/admin/login') {
    return <>{children}</>
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center" dir="rtl">در حال بارگذاری...</div>
  }

  if (!username) {
    return <div className="min-h-screen flex items-center justify-center" dir="rtl">در حال هدایت به صفحه ورود...</div>
  }

  const navItems = [
    { href: '/admin', label: 'داشبورد', icon: LayoutDashboard },
    { href: '/admin/logs', label: 'گزارشات چت', icon: FileText },
    { href: '/admin/kb', label: 'پایگاه دانش', icon: BookOpen },
    { href: '/admin/website', label: 'منابع وب‌سایت', icon: Globe },
    { href: '/admin/system-status', label: 'وضعیت سیستم', icon: Activity },
  ]

  return (
    <div className="min-h-screen bg-background" dir="rtl">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 border-l bg-card min-h-screen p-4">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-primary">پنل مدیریت</h1>
            <p className="text-sm text-muted-foreground mt-1">خوش آمدید، {username}</p>
          </div>
          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-2 rounded-md transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </Link>
              )
            })}
          </nav>
          <div className="mt-8">
            <Button
              variant="outline"
              onClick={handleLogout}
              className="w-full"
            >
              <LogOut className="h-4 w-4 ml-2" />
              خروج
            </Button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  )
}

