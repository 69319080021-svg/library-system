import { useState } from 'react'
import { api } from '../api.js'
import { Alert, Badge, Button, Card, Empty, Field, PageTitle, SearchBox } from '../components/ui.jsx'
import { useLoad } from '../useLoad.js'

const EMPTY_FORM = { book_id: '', title: '', author: '', isbn: '' }

function BookForm({ initial, isNew, onSave, onCancel }) {
  const [form, setForm] = useState(initial)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    setSaving(true)
    try {
      await onSave(form)
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  return (
    <Card className="mb-4">
      <form onSubmit={submit} className="space-y-3">
        <h2 className="font-semibold">{isNew ? 'เพิ่มหนังสือ' : `แก้ไขเล่ม ${initial.book_id}`}</h2>
        <Alert>{error}</Alert>
        {isNew && (
          <Field label="รหัสเล่ม *" value={form.book_id} onChange={set('book_id')} required hint="เช่น บาร์โค้ดที่ติดหนังสือ ห้ามซ้ำ ห้ามเว้นวรรค" />
        )}
        <Field label="ชื่อหนังสือ *" value={form.title} onChange={set('title')} required />
        <Field label="ผู้แต่ง" value={form.author ?? ''} onChange={set('author')} />
        <Field label="ISBN" value={form.isbn ?? ''} onChange={set('isbn')} hint="หนังสือชื่อเดียวกันหลายเล่มใช้ ISBN เดียวกันได้" />
        <div className="flex gap-2">
          <Button type="submit" disabled={saving}>บันทึก</Button>
          <Button type="button" variant="secondary" onClick={onCancel}>ยกเลิก</Button>
        </div>
      </form>
    </Card>
  )
}

function statusBadge(book) {
  if (book.status === 'retired') return <Badge>ปลดระวาง</Badge>
  if (book.available) return <Badge color="green">ว่าง</Badge>
  return <Badge color="amber">ถูกยืม · {book.borrowed_by}</Badge>
}

export default function Books() {
  const [q, setQ] = useState('')
  const [editing, setEditing] = useState(null) // null | 'new' | book
  const [message, setMessage] = useState({ type: 'success', text: '' })
  const { data: books, error, loading, reload } = useLoad(() => api.books.list(q), [q])

  async function save(form) {
    if (editing === 'new') {
      await api.books.create(form)
      setMessage({ type: 'success', text: `เพิ่มเล่ม ${form.book_id} แล้ว` })
    } else {
      await api.books.update(editing.book_id, { title: form.title, author: form.author, isbn: form.isbn })
      setMessage({ type: 'success', text: `แก้ไขเล่ม ${editing.book_id} แล้ว` })
    }
    setEditing(null)
    reload()
  }

  async function run(action, okText) {
    try {
      await action()
      setMessage({ type: 'success', text: okText })
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    }
    reload()
  }

  return (
    <>
      <PageTitle action={!editing && <Button onClick={() => setEditing('new')}>+ เพิ่มหนังสือ</Button>}>
        หนังสือ
      </PageTitle>

      <Alert type={message.type} onClose={() => setMessage({ ...message, text: '' })}>
        {message.text}
      </Alert>
      <Alert>{error}</Alert>

      {editing && (
        <BookForm
          key={editing === 'new' ? 'new' : editing.book_id}
          initial={editing === 'new' ? EMPTY_FORM : editing}
          isNew={editing === 'new'}
          onSave={save}
          onCancel={() => setEditing(null)}
        />
      )}

      <SearchBox value={q} onChange={setQ} placeholder="ค้นหา: รหัสเล่ม ชื่อ ผู้แต่ง หรือ ISBN" />

      {books?.length === 0 && !loading && <Empty>ไม่พบหนังสือ</Empty>}

      <div className="space-y-2">
        {books?.map((b) => (
          <Card key={b.book_id} className={b.status === 'retired' ? 'opacity-60' : ''}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="font-semibold text-slate-900">{b.title}</p>
                <p className="text-sm text-slate-500">
                  รหัส {b.book_id}
                  {b.author && ` · ${b.author}`}
                  {b.isbn && ` · ISBN ${b.isbn}`}
                </p>
              </div>
              {statusBadge(b)}
            </div>

            {b.status === 'active' && (
              <div className="mt-3 flex flex-wrap gap-2">
                <Button variant="secondary" onClick={() => setEditing(b)}>แก้ไข</Button>
                {!b.available && (
                  <Button variant="secondary" onClick={() => run(() => api.books.returnBook(b.book_id), `คืนเล่ม ${b.book_id} แล้ว`)}>
                    รับคืน
                  </Button>
                )}
                <Button
                  variant="danger"
                  onClick={() =>
                    confirm(`ปลดระวางเล่ม ${b.book_id}? หลังปลดระวางจะยืมไม่ได้อีก`) &&
                    run(() => api.books.retire(b.book_id), `ปลดระวางเล่ม ${b.book_id} แล้ว`)
                  }
                >
                  ปลดระวาง
                </Button>
              </div>
            )}
          </Card>
        ))}
      </div>
    </>
  )
}
