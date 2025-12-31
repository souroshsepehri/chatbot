'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'

// Force dynamic rendering (no static generation)
export const dynamic = 'force-dynamic'

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await api.login({ username, password })
      router.push('/admin')
    } catch (err: any) {
      console.error('Login error:', err)
      const errorMsg = err.message || 'اطلاعات ورود نامعتبر است'
      setError(errorMsg.includes('Invalid credentials') ? 'نام کاربری یا رمز عبور اشتباه است' : errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background" dir="rtl">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl text-primary">ورود به پنل مدیریت</CardTitle>
          <CardDescription>
            لطفا اطلاعات کاربری خود را وارد کنید
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm">
                {error.includes('HTTP 500') ? 'خطای سرور: لطفا مطمئن شوید که پایگاه داده و سرویس‌ها در حال اجرا هستند' : error}
              </div>
            )}
            <div>
              <label className="text-sm font-medium mb-2 block">نام کاربری</label>
              <Input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                dir="ltr"
                className="text-left"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">رمز عبور</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                dir="ltr"
                className="text-left"
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'در حال ورود...' : 'ورود'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

