// ตัวเรียก back-end API ทั้งหมด (หน้าจอเรียกผ่านไฟล์นี้ที่เดียว)
//
// ตอนพัฒนา: ใช้ /api แล้ว Vite proxy ส่งต่อไปที่ FastAPI บนเครื่อง
// ตอน deploy: ตั้งค่า VITE_API_URL เป็นที่อยู่ของ back-end เช่น https://xxx.onrender.com
const BASE_URL = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

async function request(method, path, body) {
  let res
  try {
    res = await fetch(BASE_URL + path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(0, 'เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ ตรวจสอบว่า back-end เปิดอยู่')
  }

  const data = await res.json().catch(() => null)
  if (!res.ok) {
    // back-end ส่งข้อความภาษาไทยมาใน detail (ถ้าเป็นรายการ แปลว่าข้อมูลที่กรอกไม่ถูกต้อง)
    const message =
      typeof data?.detail === 'string' ? data.detail : 'ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง'
    throw new ApiError(res.status, message)
  }
  return data
}

const qs = (params) => {
  const p = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => v && p.set(k, v))
  const s = p.toString()
  return s ? `?${s}` : ''
}

// ส่งเฉพาะฟิลด์ที่มีค่า (ช่องว่าง = ไม่ส่ง)
const clean = (obj) =>
  Object.fromEntries(Object.entries(obj).map(([k, v]) => [k, v === '' ? null : v]))

export const api = {
  books: {
    list: (q) => request('GET', `/books${qs({ q })}`),
    create: (book) => request('POST', '/books', clean(book)),
    update: (id, book) => request('PUT', `/books/${encodeURIComponent(id)}`, clean(book)),
    retire: (id) => request('POST', `/books/${encodeURIComponent(id)}/retire`),
    returnBook: (id) => request('POST', `/books/${encodeURIComponent(id)}/return`),
  },
  members: {
    list: (q) => request('GET', `/members${qs({ q })}`),
    create: (member) => request('POST', '/members', clean(member)),
    update: (id, member) => request('PUT', `/members/${encodeURIComponent(id)}`, member),
    loans: (id) => request('GET', `/members/${encodeURIComponent(id)}/loans`),
  },
  loans: {
    list: (status = 'all') => request('GET', `/loans${qs({ status })}`),
    borrow: (bookId, memberId) =>
      request('POST', '/loans', { book_id: bookId, member_id: memberId }),
    returnLoan: (loanId) => request('POST', `/loans/${loanId}/return`),
  },
}

export const formatDate = (iso) =>
  iso ? new Date(iso).toLocaleDateString('th-TH', { day: 'numeric', month: 'short', year: 'numeric' }) : '-'
