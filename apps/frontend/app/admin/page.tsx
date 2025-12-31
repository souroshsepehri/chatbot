'use client'

import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api, type HealthResponse, type KBQA, type WebsiteSource, type ChatLog } from '@/lib/api'
import Link from 'next/link'
import { BookOpen, Globe, FileText, Activity, Plus, ArrowRight } from 'lucide-react'

// Force dynamic rendering (no static generation)
export const dynamic = 'force-dynamic'

export default function AdminDashboard() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [kbItems, setKbItems] = useState<KBQA[]>([])
  const [websiteSources, setWebsiteSources] = useState<WebsiteSource[]>([])
  const [recentLogs, setRecentLogs] = useState<ChatLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [healthData, kbData, websiteData, logsData] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getKBQA().catch(() => []),
        api.getWebsiteSources().catch(() => []),
        api.getLogs({ limit: 5 }).catch(() => ({ logs: [], total: 0, limit: 5, offset: 0 }))
      ])

      setHealth(healthData)
      setKbItems(kbData)
      setWebsiteSources(websiteData)
      setRecentLogs(logsData.logs || [])
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const StatusBadge = ({ status }: { status: string }) => {
    const isOk = status === 'ok'
    const statusText = isOk ? 'موجود' : status === 'error' ? 'خطا' : 'نامشخص'
    return (
      <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        isOk ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
      }`}>
        <span className={`w-1.5 h-1.5 rounded-full ml-1.5 ${isOk ? 'bg-green-500' : 'bg-red-500'}`}></span>
        {statusText}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]" dir="rtl">
        <div className="text-muted-foreground">در حال بارگذاری داشبورد...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6" dir="rtl">
      <div>
        <h1 className="text-3xl font-bold">داشبورد</h1>
        <p className="text-muted-foreground mt-1">نمای کلی سیستم چت‌بات</p>
      </div>

      {/* System Health */}
      <div>
        <h2 className="text-xl font-semibold mb-4">وضعیت سیستم</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">بک‌اند</CardTitle>
            </CardHeader>
            <CardContent>
              {health ? (
                <StatusBadge status={health.backend.status} />
              ) : (
                <span className="text-muted-foreground text-sm">نامشخص</span>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">پایگاه داده</CardTitle>
            </CardHeader>
            <CardContent>
              {health ? (
                <StatusBadge status={health.db.status} />
              ) : (
                <span className="text-muted-foreground text-sm">نامشخص</span>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">OpenAI</CardTitle>
            </CardHeader>
            <CardContent>
              {health ? (
                <StatusBadge status={health.openai.status} />
              ) : (
                <span className="text-muted-foreground text-sm">نامشخص</span>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">خزنده وب</CardTitle>
            </CardHeader>
            <CardContent>
              {health ? (
                <StatusBadge status={health.website_crawler.status} />
              ) : (
                <span className="text-muted-foreground text-sm">نامشخص</span>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Statistics */}
      <div>
        <h2 className="text-xl font-semibold mb-4">آمار</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <BookOpen className="h-4 w-4" />
                پایگاه دانش
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{kbItems.length}</div>
              <p className="text-xs text-muted-foreground mt-1">آیتم سوال-پاسخ</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Globe className="h-4 w-4" />
                منابع وب‌سایت
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{websiteSources.length}</div>
              <p className="text-xs text-muted-foreground mt-1">منابع پیکربندی شده</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <FileText className="h-4 w-4" />
                لاگ‌های چت
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{recentLogs.length}</div>
              <p className="text-xs text-muted-foreground mt-1">مکالمات اخیر</p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold mb-4">عملیات سریع</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card className="hover:shadow-md transition-shadow">
            <CardHeader>
              <CardTitle className="text-base">افزودن آیتم پایگاه دانش</CardTitle>
              <CardDescription>ایجاد یک جفت سوال-پاسخ جدید</CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/admin/kb">
                <Button variant="outline" className="w-full">
                  <Plus className="h-4 w-4 ml-2" />
                  افزودن آیتم
                </Button>
              </Link>
            </CardContent>
          </Card>
          <Card className="hover:shadow-md transition-shadow">
            <CardHeader>
              <CardTitle className="text-base">افزودن منبع وب‌سایت</CardTitle>
              <CardDescription>پیکربندی وب‌سایت جدید برای خزیدن</CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/admin/website">
                <Button variant="outline" className="w-full">
                  <Plus className="h-4 w-4 ml-2" />
                  افزودن وب‌سایت
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recent Activity */}
      {recentLogs.length > 0 && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">لاگ‌های چت اخیر</h2>
            <Link href="/admin/logs">
              <Button variant="ghost" size="sm">
                مشاهده همه
                <ArrowRight className="h-4 w-4 mr-2" />
              </Button>
            </Link>
          </div>
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                {recentLogs.map((log) => (
                  <div key={log.id} className="border-b last:border-0 pb-4 last:pb-0">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="font-medium text-sm">{log.user_message}</p>
                        <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                          {log.bot_message}
                        </p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                          <span>{new Date(log.created_at).toLocaleString('fa-IR')}</span>
                          {log.refused && (
                            <span className="text-orange-600 font-medium">رد شده</span>
                          )}
                          {log.sources_json && (
                            <span>
                              {((log.sources_json.kb_ids?.length || 0) + (log.sources_json.website_page_ids?.length || 0))} منبع
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Quick Links */}
      <div>
        <h2 className="text-xl font-semibold mb-4">لینک‌های سریع</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link href="/admin/kb">
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  پایگاه دانش
                </CardTitle>
                <CardDescription>مدیریت آیتم‌های سوال-پاسخ</CardDescription>
              </CardHeader>
            </Card>
          </Link>
          <Link href="/admin/logs">
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  لاگ‌های چت
                </CardTitle>
                <CardDescription>مشاهده تاریخچه مکالمات</CardDescription>
              </CardHeader>
            </Card>
          </Link>
          <Link href="/admin/website">
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  منابع وب‌سایت
                </CardTitle>
                <CardDescription>مدیریت خزیدن وب‌سایت</CardDescription>
              </CardHeader>
            </Card>
          </Link>
          <Link href="/admin/system-status">
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  وضعیت سیستم
                </CardTitle>
                <CardDescription>اطلاعات تفصیلی سلامت سیستم</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        </div>
      </div>
    </div>
  )
}

