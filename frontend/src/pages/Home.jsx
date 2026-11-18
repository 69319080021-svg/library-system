import { Link } from 'react-router-dom'
import { api, formatDate } from '../api.js'
import { Alert, Card, PageTitle } from '../components/ui.jsx'
import { useLoad } from '../useLoad.js'

async function loadSummary() {
  const [books, active, overdue] = await Promise.all([
    api.books.list(),
    api.loans.list('active'),
    api.loans.list('overdue'),
  ])
  const inUse = books.filter((b) => b.status === 'active')
  return { total: inUse.length, borrowed: active.length, available: inUse.filter((b) => b.available).length, overdue }
}

function Stat({ label, value, to, color }) {
  return (
    <Link to={to}>
      <Card className="h-full transition hover:border-teal-300">
        <p className="text-sm text-slate-500">{label}</p>
        <p className={`mt-1 text-3xl font-bold ${color}`}>{value ?? '–'}</p>
      </Card>
    </Link>
  )
}

export default function Home() {
  const { data, error } = useLoad(loadSummary)

  return (
    <>
      <PageTitle>ภาพรวม</PageTitle>
      <Alert>{error}</Alert>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="หนังสือทั้งหมด" value={data?.total} to="/books" color="text-slate-900" />
        <Stat label="ว่างให้ยืม" value={data?.available} to="/borrow" color="text-green-700" />
        <Stat label="ถูกยืมอยู่" value={data?.borrowed} to="/return" color="text-amber-700" />
        <Stat label="เลยกำหนดคืน" value={data?.overdue.length} to="/return" color="text-red-700" />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <Link to="/borrow" className="rounded-xl bg-teal-700 py-4 text-center font-semibold text-white hover:bg-teal-800">
          📤 ยืมหนังสือ
        </Link>
        <Link to="/return" className="rounded-xl border border-teal-700 bg-white py-4 text-center font-semibold text-teal-800 hover:bg-teal-50">
          📥 คืนหนังสือ
        </Link>
      </div>

      {data?.overdue.length > 0 && (
        <Card className="mt-4">
          <h2 className="mb-2 font-semibold text-red-700">รายการเลยกำหนดคืน</h2>
          <ul className="divide-y divide-slate-100 text-sm">
            {data.overdue.map((l) => (
              <li key={l.loan_id} className="flex justify-between py-2">
                <span>
                  เล่ม <b>{l.book_id}</b> · สมาชิก {l.member_id}
                </span>
                <span className="text-red-700">กำหนด {formatDate(l.due_at)}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </>
  )
}
