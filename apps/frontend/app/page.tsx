import ChatWidget from '@/components/ChatWidget'

// Force dynamic rendering (no static generation)
export const dynamic = 'force-dynamic'

export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto" dir="rtl">
        <h1 className="text-4xl font-bold text-primary mb-4">
          ربات چت با محدودیت دامنه
        </h1>
        <p className="text-muted-foreground mb-8">
          سوالات خود را بپرسید و پاسخ‌ها را از پایگاه دانش و منابع وب‌سایت ما دریافت کنید.
        </p>
      </div>
      <ChatWidget />
    </main>
  )
}

