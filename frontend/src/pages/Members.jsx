import { useState } from 'react'
import { api, formatDate } from '../api.js'
import { Alert, Badge, Button, Card, Empty, Field, PageTitle, SearchBox } from '../components/ui.jsx'
import { useLoad } from '../useLoad.js'

const EMPTY_FORM = { member_id: '', name: '', phone: '', email: '' }

function MemberForm({ initial, isNew, onSave, onCancel }) {
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
        <h2 className="font-semibold">{isNew ? 'เพิ่มสมาชิก' : `แก้ไขสมาชิก ${initial.member_id}`}</h2>
        <Alert>{error}</Alert>
        {isNew && <Field label="รหัสสมาชิก *" value={form.member_id} onChange={set('member_id')} required hint="ห้ามซ้ำ ห้ามเว้นวรรค" />}
        <Field label="ชื่อ-นามสกุล *" value={form.name} onChange={set('name')} required />
        <Field label="เบอร์โทร" type="tel" value={form.phone ?? ''} onChange={set('phone')} />
        <Field label="อีเมล" type="email" value={form.email ?? ''} onChange={set('email')} />
        <div className="flex gap-2">
          <Button type="submit" disabled={saving}>บันทึก</Button>
          <Button type="button" variant="secondary" onClick={onCancel}>ยกเลิก</Button>
        </div>
      </form>
    </Card>
  )
}

function LoanHistory({ memberId }) {
  const { data: loans, error } = useLoad(() => api.members.loans(memberId), [memberId])
  if (error) return <Alert>{error}</Alert>
  if (!loans) return <p className="mt-3 text-sm text-slate-500">กำลังโหลด…</p>
  if (loans.length === 0) return <p className="mt-3 text-sm text-slate-500">ยังไม่เคยยืม</p>
  return (
    <ul className="mt-3 divide-y divide-slate-100 border-t border-slate-100 text-sm">
      {loans.map((l) => (
        <li key={l.loan_id} className="flex flex-wrap justify-between gap-2 py-2">
          <span>
            เล่ม <b>{l.book_id}</b> · ยืม {formatDate(l.borrowed_at)}
          </span>
          {l.returned_at ? (
            <span className="text-slate-500">คืน {formatDate(l.returned_at)}</span>
          ) : l.is_overdue ? (
            <Badge color="red">เลยกำหนด {formatDate(l.due_at)}</Badge>
          ) : (
            <Badge color="amber">ยังไม่คืน · กำหนด {formatDate(l.due_at)}</Badge>
          )}
        </li>
      ))}
    </ul>
  )
}

export default function Members() {
  const [q, setQ] = useState('')
  const [editing, setEditing] = useState(null) // null | 'new' | member
  const [openId, setOpenId] = useState(null)
  const [message, setMessage] = useState({ type: 'success', text: '' })
  const { data: members, error, loading, reload } = useLoad(() => api.members.list(q), [q])

  async function save(form) {
    if (editing === 'new') {
      await api.members.create(form)
      setMessage({ type: 'success', text: `เพิ่มสมาชิก ${form.member_id} แล้ว` })
    } else {
      await api.members.update(editing.member_id, {
        name: form.name,
        phone: form.phone || null,
        email: form.email || null,
      })
      setMessage({ type: 'success', text: `แก้ไขสมาชิก ${editing.member_id} แล้ว` })
    }
    setEditing(null)
    reload()
  }

  async function toggleStatus(m) {
    const status = m.status === 'active' ? 'suspended' : 'active'
    try {
      await api.members.update(m.member_id, { status })
      setMessage({ type: 'success', text: `${status === 'active' ? 'เปิดใช้งาน' : 'ระงับ'}สมาชิก ${m.member_id} แล้ว` })
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    }
    reload()
  }

  return (
    <>
      <PageTitle action={!editing && <Button onClick={() => setEditing('new')}>+ เพิ่มสมาชิก</Button>}>
        สมาชิก
      </PageTitle>

      <Alert type={message.type} onClose={() => setMessage({ ...message, text: '' })}>
        {message.text}
      </Alert>
      <Alert>{error}</Alert>

      {editing && (
        <MemberForm
          key={editing === 'new' ? 'new' : editing.member_id}
          initial={editing === 'new' ? EMPTY_FORM : editing}
          isNew={editing === 'new'}
          onSave={save}
          onCancel={() => setEditing(null)}
        />
      )}

      <SearchBox value={q} onChange={setQ} placeholder="ค้นหา: รหัส ชื่อ เบอร์โทร หรืออีเมล" />

      {members?.length === 0 && !loading && <Empty>ไม่พบสมาชิก</Empty>}

      <div className="space-y-2">
        {members?.map((m) => (
          <Card key={m.member_id}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="font-semibold text-slate-900">{m.name}</p>
                <p className="text-sm text-slate-500">
                  รหัส {m.member_id}
                  {m.phone && ` · ${m.phone}`}
                  {m.email && ` · ${m.email}`}
                </p>
              </div>
              {m.status === 'active' ? <Badge color="green">ใช้งาน</Badge> : <Badge color="red">ระงับ</Badge>}
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="secondary" onClick={() => setOpenId(openId === m.member_id ? null : m.member_id)}>
                {openId === m.member_id ? 'ซ่อนประวัติ' : 'ประวัติการยืม'}
              </Button>
              <Button variant="secondary" onClick={() => setEditing(m)}>แก้ไข</Button>
              <Button variant={m.status === 'active' ? 'danger' : 'secondary'} onClick={() => toggleStatus(m)}>
                {m.status === 'active' ? 'ระงับ' : 'เปิดใช้งาน'}
              </Button>
            </div>

            {openId === m.member_id && <LoanHistory memberId={m.member_id} />}
          </Card>
        ))}
      </div>
    </>
  )
}
