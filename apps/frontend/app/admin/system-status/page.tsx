'use client'

import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api, type HealthResponse } from '@/lib/api'

// Force dynamic rendering (no static generation)
export const dynamic = 'force-dynamic'

export default function SystemStatusPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const loadHealth = async () => {
    setLoading(true)
    try {
      const h = await api.getHealth()
      setHealth(h)
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHealth()
    const interval = setInterval(loadHealth, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const StatusBadge = ({ status, message }: { status: string; message?: string }) => (
    <div className="flex items-center gap-2">
      <div className={`h-3 w-3 rounded-full ${
        status === 'ok' ? 'bg-green-500' : 'bg-red-500'
      }`} />
      <span className="font-medium">{status === 'ok' ? 'OK' : 'ERROR'}</span>
      {message && <span className="text-sm text-muted-foreground">({message})</span>}
    </div>
  )

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">System Status</h1>
        <Button onClick={loadHealth} disabled={loading}>
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Backend</CardTitle>
          </CardHeader>
          <CardContent>
            {health ? (
              <StatusBadge status={health.backend.status} message={health.backend.message} />
            ) : (
              <p>Loading...</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Database</CardTitle>
          </CardHeader>
          <CardContent>
            {health ? (
              <StatusBadge status={health.db.status} message={health.db.message} />
            ) : (
              <p>Loading...</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>OpenAI</CardTitle>
          </CardHeader>
          <CardContent>
            {health ? (
              <StatusBadge status={health.openai.status} message={health.openai.message} />
            ) : (
              <p>Loading...</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Website Crawler</CardTitle>
          </CardHeader>
          <CardContent>
            {health ? (
              <StatusBadge status={health.website_crawler.status} message={health.website_crawler.message} />
            ) : (
              <p>Loading...</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

