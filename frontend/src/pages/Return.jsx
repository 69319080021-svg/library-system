import { useState } from 'react'
import { api, formatDate } from '../api.js'
import { Alert, Badge, Button, Card, Empty, Field, PageTitle } from '../components/ui.jsx'
import { useLoad } from '../useLoad.js'

export default function Return() {
  const [filter, setFilter] = useState('active') // active | overdue
  const [bookId, setBookId] = useState('')
  const [message, setMessage] = useState({ type: 'success', text: '' })
  const { data: loans, error, loading, reload } = useLoad(() => api.loans.list(filter), [filter])

  async function run(action, okText) {
    try {
      await action()
      setMessage({ type: 'success', text: okText })
      return true
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
      return false
    } finally {
      reload()
    }
  }

  async function returnByBookId(e) {
    e.preventDefault()
    const id = bookId.trim()
    if (id && (await run(() => api.books.returnBook(id), `คืนเล่ม ${id} แล้ว`))) setBookId('')
  }

  return (
    <>
      <PageTitle>คืนหนังสือ</PageTitle>

      <Alert type={message.type} onClose={() => setMessage({ ...message, text: '' })}>
        {message.text}
      </Alert>
      <Alert>{error}</Alert>

      <Card className="mb-4">
        <form onSubmit={returnByBookId} className="flex items-end gap-2">
          <div className="flex-1">
            <Field label="คืนด้วยรหัสเล่ม" value={bookId} onChange={(e) => setBookId(e.target.value)} placeholder="เช่น B001" />
          </div>
          <Button type="submit" disabled={!bookId.trim()}>คืน</Button>
        </form>
      </Card>

      <div className="mb-3 flex gap-2">
        {[
          ['active', 'ยังไม่คืนทั้งหมด'],
          ['overdue', 'เลยกำหนด'],
        ].map(([key, label]) => (
          <Button key={key} variant={filter === key ? 'primary' : 'secondary'} onClick={() => setFilter(key)}>
            {label}
          </Button>
        ))}
      </div>

      {loans?.length === 0 && !loading && <Empty>ไม่มีรายการ</Empty>}

      <div className="space-y-2">
        {loans?.map((l) => (
          <Card key={l.loan_id}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="text-sm">
                <p>
                  เล่ม <b>{l.book_id}</b> · สมาชิก <b>{l.member_id}</b>
                </p>
                <p className="text-slate-500">
                  ยืม {formatDate(l.borrowed_at)} · กำหนดคืน {formatDate(l.due_at)}{' '}
                  {l.is_overdue && <Badge color="red">เลยกำหนด</Badge>}
                </p>
              </div>
              <Button onClick={() => run(() => api.loans.returnLoan(l.loan_id), `คืนเล่ม ${l.book_id} แล้ว`)}>
                รับคืน
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </>
  )
}
