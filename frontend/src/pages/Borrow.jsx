import { useState } from 'react'
import { api, formatDate } from '../api.js'
import { Alert, Badge, Button, Card, Empty, PageTitle, SearchBox } from '../components/ui.jsx'
import { useLoad } from '../useLoad.js'

function Pick({ selected, disabled, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition disabled:cursor-not-allowed disabled:opacity-50 ${
        selected ? 'border-teal-600 bg-teal-50 ring-2 ring-teal-600/20' : 'border-slate-200 bg-white hover:border-teal-300'
      }`}
    >
      {children}
    </button>
  )
}

export default function Borrow() {
  const [memberQ, setMemberQ] = useState('')
  const [bookQ, setBookQ] = useState('')
  const [member, setMember] = useState(null)
  const [book, setBook] = useState(null)
  const [error, setError] = useState('')
  const [done, setDone] = useState(null)
  const [saving, setSaving] = useState(false)

  const members = useLoad(() => api.members.list(memberQ), [memberQ])
  const books = useLoad(() => api.books.list(bookQ), [bookQ])

  async function borrow() {
    setSaving(true)
    setError('')
    setDone(null)
    try {
      const loan = await api.loans.borrow(book.book_id, member.member_id)
      setDone({ loan, book, member })
      setBook(null)
      books.reload()
    } catch (err) {
      // เช่น 409 "หนังสือเล่มนี้ถูกยืมอยู่ ..." ถ้ามีคนยืมตัดหน้าไปก่อน
      setError(err.message)
      setBook(null)
      books.reload()
    } finally {
      setSaving(false)
    }
  }

  const activeBooks = books.data?.filter((b) => b.status === 'active') ?? []

  return (
    <>
      <PageTitle>ยืมหนังสือ</PageTitle>

      {done && (
        <Alert type="success" onClose={() => setDone(null)}>
          ✅ {done.member.name} ยืม “{done.book.title}” (เล่ม {done.book.book_id}) แล้ว กำหนดคืน{' '}
          <b>{formatDate(done.loan.due_at)}</b>
        </Alert>
      )}
      <Alert onClose={() => setError('')}>{error}</Alert>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <h2 className="mb-2 font-semibold">1. เลือกสมาชิก</h2>
          <SearchBox value={memberQ} onChange={setMemberQ} placeholder="ค้นหารหัสหรือชื่อสมาชิก" />
          <Alert>{members.error}</Alert>
          <div className="max-h-72 space-y-1.5 overflow-y-auto">
            {members.data?.length === 0 && <Empty>ไม่พบสมาชิก</Empty>}
            {members.data?.map((m) => (
              <Pick
                key={m.member_id}
                selected={member?.member_id === m.member_id}
                disabled={m.status !== 'active'}
                onClick={() => setMember(m)}
              >
                <span className="font-medium">{m.name}</span>{' '}
                <span className="text-slate-500">({m.member_id})</span>
                {m.status !== 'active' && <span className="ml-2"><Badge color="red">ระงับ</Badge></span>}
              </Pick>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="mb-2 font-semibold">2. เลือกหนังสือ</h2>
          <SearchBox value={bookQ} onChange={setBookQ} placeholder="ค้นหารหัสเล่ม ชื่อ หรือ ISBN" />
          <Alert>{books.error}</Alert>
          <div className="max-h-72 space-y-1.5 overflow-y-auto">
            {activeBooks.length === 0 && books.data && <Empty>ไม่พบหนังสือ</Empty>}
            {activeBooks.map((b) => (
              <Pick
                key={b.book_id}
                selected={book?.book_id === b.book_id}
                disabled={!b.available}
                onClick={() => setBook(b)}
              >
                <span className="font-medium">{b.title}</span>{' '}
                <span className="text-slate-500">({b.book_id})</span>
                {!b.available && <span className="ml-2"><Badge color="amber">ถูกยืมอยู่</Badge></span>}
              </Pick>
            ))}
          </div>
        </Card>
      </div>

      <Card className="sticky bottom-20 mt-4 md:bottom-4">
        <p className="mb-3 text-sm">
          <b>สมาชิก:</b> {member ? `${member.name} (${member.member_id})` : '—'}
          <br />
          <b>หนังสือ:</b> {book ? `${book.title} (${book.book_id})` : '—'}
        </p>
        <Button className="w-full" disabled={!member || !book || saving} onClick={borrow}>
          {saving ? 'กำลังบันทึก…' : 'ยืนยันการยืม'}
        </Button>
      </Card>
    </>
  )
}
