# ระบบห้องสมุดและยืมคืนหนังสือ

เว็บแอปจัดการหนังสือ (รายเล่ม) สมาชิก และการยืมคืน ใช้งานบนมือถือได้

**เงื่อนไขทดสอบ:** หนังสือเล่มเดียวกันมีรายการยืมที่ยังไม่คืนได้ไม่เกิน 1 รายการ
บังคับ 2 ชั้น คือตรวจในโค้ด (`backend/app/services.py`) และ partial unique index ในฐานข้อมูล
(`UNIQUE (book_id) WHERE returned_at IS NULL` ใน `backend/app/models.py`)

## เทคโนโลยี

| ส่วน | ใช้ |
|---|---|
| Front-end | React (Vite) + Tailwind CSS |
| Back-end | FastAPI (Python) + SQLAlchemy |
| ฐานข้อมูล | SQLite (บนเครื่อง) / PostgreSQL บน Neon (ตอน deploy) |
| ทดสอบ | pytest |
| Deploy | Vercel (หน้าเว็บ) + Render (API) + Neon (ฐานข้อมูล) |

## รันบนเครื่อง

**Back-end** (ในโฟลเดอร์ `backend`)

```bash
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\fastapi.exe dev app/main.py
```

เอกสาร API: http://127.0.0.1:8000/docs

**Front-end** (ในโฟลเดอร์ `frontend` เปิดอีกหน้าต่าง)

```bash
npm install
npm run dev
```

เปิด http://localhost:5173 (เพิ่ม `-- --host` ต่อท้ายเพื่อเปิดจากมือถือใน Wi-Fi เดียวกัน)

**รันเทสต์** (ในโฟลเดอร์ `backend`)

```bash
.\.venv\Scripts\python.exe -m pytest -v
```

## Deploy

ดูขั้นตอนใน [DEPLOY.md](DEPLOY.md)
