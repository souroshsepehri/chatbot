'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { api, type WebsiteSource } from '@/lib/api'

// Force dynamic rendering (no static generation)
export const dynamic = 'force-dynamic'

export default function WebsitePage() {
  const [sources, setSources] = useState<WebsiteSource[]>([])
  const [loading, setLoading] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [baseUrl, setBaseUrl] = useState('')
  const [enabled, setEnabled] = useState(true)

  const loadSources = async () => {
    setLoading(true)
    try {
      const srcs = await api.getWebsiteSources()
      setSources(srcs)
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSources()
  }, [])

  const handleCreate = () => {
    setBaseUrl('')
    setEnabled(true)
    setIsDialogOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.createWebsiteSource({ base_url: baseUrl, enabled })
      setIsDialogOpen(false)
      loadSources()
    } catch (error) {
      console.error(error)
    }
  }

  const handleToggle = async (id: number, currentEnabled: boolean) => {
    try {
      await api.updateWebsiteSource(id, { enabled: !currentEnabled })
      loadSources()
    } catch (error) {
      console.error(error)
    }
  }

  const handleRecrawl = async (id: number) => {
    try {
      await api.recrawlWebsite(id)
      alert('Crawl started in background. Check status in a few moments.')
      loadSources()
    } catch (error) {
      console.error(error)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this website source?')) return
    try {
      await api.deleteWebsiteSource(id)
      loadSources()
    } catch (error) {
      console.error(error)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Website Sources</h1>
        <Button onClick={handleCreate}>Add Website Source</Button>
      </div>

      <Card>
        <CardContent className="p-6">
          {loading ? (
            <p>Loading...</p>
          ) : (
            <div className="space-y-4">
              {sources.map((source) => (
                <div key={source.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="font-medium">{source.base_url}</p>
                      <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                        <p>Status: {source.crawl_status}</p>
                        <p>Pages: {source.pages_count || 0}</p>
                        <p>Last crawled: {source.last_crawled_at ? new Date(source.last_crawled_at).toLocaleString() : 'Never'}</p>
                        <p>Enabled: {source.enabled ? 'Yes' : 'No'}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggle(source.id, source.enabled)}
                      >
                        {source.enabled ? 'Disable' : 'Enable'}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRecrawl(source.id)}
                      >
                        Re-crawl
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDelete(source.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Website Source</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Base URL</label>
              <Input
                type="url"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="https://example.com"
                required
                autoFocus
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="enabled"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="h-4 w-4"
              />
              <label htmlFor="enabled" className="text-sm font-medium">
                Enabled
              </label>
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Save</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

