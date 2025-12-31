'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { MessageCircle, X, Send } from 'lucide-react'
import { api, type ChatResponse, type SourceInfo } from '@/lib/api'
import { cn } from '@/lib/utils'

interface Message {
  role: 'user' | 'bot'
  content: string
  sources?: SourceInfo[]
  refused?: boolean
  debug?: {
    llm_called: boolean
    retrieval_hits: {
      kb: number
      website: number
    }
  }
}

interface ChatWidgetProps {
  forceOpen?: boolean
}

export default function ChatWidget({ forceOpen = false }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(forceOpen)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  // Sync isOpen with forceOpen prop
  useEffect(() => {
    if (forceOpen) {
      setIsOpen(true)
    }
  }, [forceOpen])

  // Load greeting when chat opens for the first time (only if no messages exist)
  useEffect(() => {
    if (isOpen && messages.length === 0 && !sessionId) {
      api.getGreeting()
        .then(({ message }) => {
          setMessages([{ role: 'bot', content: message }])
        })
        .catch(() => {
          // If greeting fails, use default
          setMessages([{ role: 'bot', content: 'سلام! چطور می‌تونم کمکتون کنم؟' }])
        })
    }
  }, [isOpen, messages.length, sessionId])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response: ChatResponse = await api.chat({
        session_id: sessionId || undefined,
        message: userMessage,
      })

      if (!sessionId) {
        setSessionId(response.session_id)
      }

      setMessages(prev => [
        ...prev,
        {
          role: 'bot',
          content: response.answer,
          sources: response.sources,
          refused: response.refused,
          debug: response.debug, // Only present in development
        },
      ])
    } catch (error: any) {
      console.error('Chat error:', error)
      let errorMessage = 'متأسفانه خطایی رخ داد. لطفا دوباره تلاش کنید.'
      
      // Provide more specific error messages
      if (error?.message) {
        if (error.message.includes('Network error') || error.message.includes('fetch')) {
          errorMessage = 'خطای اتصال: لطفا مطمئن شوید که سرور در حال اجرا است.'
        } else if (error.message.includes('500')) {
          errorMessage = 'خطای سرور: لطفا مطمئن شوید که پایگاه داده و سرویس‌ها در حال اجرا هستند.'
        } else {
          errorMessage = error.message
        }
      }
      
      setMessages(prev => [
        ...prev,
        {
          role: 'bot',
          content: errorMessage,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      {/* Floating Button - only show if not forced open */}
      {!forceOpen && (
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            'fixed bottom-6 right-6 z-50 h-14 w-14 rounded-full bg-primary text-white shadow-lg transition-all hover:scale-110 hover:shadow-xl',
            isOpen && 'hidden'
          )}
          aria-label="Open chat"
        >
          <MessageCircle className="h-6 w-6 mx-auto" />
        </button>
      )}

      {/* Chat Panel */}
      {isOpen && (
        <Card className={cn(
          'z-50 w-96 h-[600px] flex flex-col shadow-2xl',
          forceOpen ? 'relative mx-auto my-8' : 'fixed bottom-6 right-6'
        )}>
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b bg-primary text-primary-foreground rounded-t-lg">
            <h2 className="font-semibold text-lg">دستیار چت</h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsOpen(false)}
              className="text-primary-foreground hover:bg-primary/80"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-muted-foreground mt-8" dir="rtl">
                <p>هر سوالی از پایگاه دانش دارید بپرسید!</p>
              </div>
            )}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={cn(
                  'flex',
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={cn(
                    'max-w-[80%] rounded-lg px-4 py-2',
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  )}
                  dir="rtl"
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-muted rounded-lg px-4 py-2" dir="rtl">
                  <p className="text-sm text-muted-foreground">در حال فکر کردن...</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t">
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="پیام خود را بنویسید..."
                dir="rtl"
                disabled={loading}
              />
              <Button onClick={handleSend} disabled={loading || !input.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </Card>
      )}
    </>
  )
}

