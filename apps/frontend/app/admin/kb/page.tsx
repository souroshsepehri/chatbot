'use client'

import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { api, type KBQA, type Category } from '@/lib/api'

// Force dynamic rendering (no static generation)
export const dynamic = 'force-dynamic'

export default function KBPage() {
  const [qaItems, setQaItems] = useState<KBQA[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<KBQA | null>(null)
  const [formData, setFormData] = useState({ question: '', answer: '', category_id: '' })

  const loadData = async () => {
    setLoading(true)
    try {
      const [qa, cats] = await Promise.all([
        api.getKBQA(),
        api.getCategories(),
      ])
      setQaItems(qa)
      setCategories(cats)
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCreate = () => {
    setEditingItem(null)
    setFormData({ question: '', answer: '', category_id: '' })
    setIsDialogOpen(true)
  }

  const handleEdit = (item: KBQA) => {
    setEditingItem(item)
    setFormData({
      question: item.question,
      answer: item.answer,
      category_id: item.category_id?.toString() || '',
    })
    setIsDialogOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingItem) {
        await api.updateKBQA(editingItem.id, {
          question: formData.question,
          answer: formData.answer,
          category_id: formData.category_id ? parseInt(formData.category_id) : undefined,
        })
      } else {
        await api.createKBQA({
          question: formData.question,
          answer: formData.answer,
          category_id: formData.category_id ? parseInt(formData.category_id) : undefined,
        })
      }
      setIsDialogOpen(false)
      loadData()
    } catch (error) {
      console.error(error)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this item?')) return
    try {
      await api.deleteKBQA(id)
      loadData()
    } catch (error) {
      console.error(error)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Knowledge Base</h1>
        <Button onClick={handleCreate}>Add QA Item</Button>
      </div>

      <Card>
        <CardContent className="p-6">
          {loading ? (
            <p>Loading...</p>
          ) : (
            <div className="space-y-4">
              {qaItems.map((item) => (
                <div key={item.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="font-medium">Q: {item.question}</p>
                      <p className="text-sm text-muted-foreground mt-1">A: {item.answer}</p>
                      {item.category_id && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Category: {categories.find(c => c.id === item.category_id)?.title}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleEdit(item)}>
                        Edit
                      </Button>
                      <Button variant="destructive" size="sm" onClick={() => handleDelete(item.id)}>
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
            <DialogTitle>{editingItem ? 'Edit' : 'Create'} QA Item</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Question</label>
              <Input
                value={formData.question}
                onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Answer</label>
              <textarea
                className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={formData.answer}
                onChange={(e) => setFormData({ ...formData, answer: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Category</label>
              <select
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={formData.category_id}
                onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
              >
                <option value="">None</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.title}
                  </option>
                ))}
              </select>
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

