# ขั้นตอน Deploy

ภาพรวม: หน้าเว็บอยู่บน **Vercel** → เรียก API บน **Render** → เก็บข้อมูลใน **Neon** (PostgreSQL)

ทำตามลำดับ 1 → 2 → 3 → 4 เพราะแต่ละขั้นต้องใช้ค่าจากขั้นก่อนหน้า
ทุกบริการมีแพ็กเกจฟรี (ควรเช็กเงื่อนไขล่าสุดในหน้าราคาของแต่ละเจ้าก่อนสมัคร)

> ห้ามใส่รหัสผ่านหรือ connection string ลงในไฟล์ที่อยู่ใน Git
> ให้ใส่ในหน้าตั้งค่า Environment ของแต่ละบริการเท่านั้น

---

## 0. เตรียมโค้ดบน GitHub

โค้ดต้องอยู่บน GitHub ก่อน เพราะ Render และ Vercel ดึงโค้ดจากที่นั่น

---

## 1. ฐานข้อมูล: Neon

1. สมัครที่ neon.com (ล็อกอินด้วย GitHub ได้)
2. สร้าง Project ใหม่ เลือก Region ใกล้ไทย เช่น **Singapore**
3. กด **Connect** แล้วคัดลอก connection string ที่ขึ้นต้นด้วย `postgresql://...`
   เก็บไว้ใช้ในขั้นที่ 2 (ไม่ต้องสร้างตารางเอง back-end สร้างให้ตอนเปิดครั้งแรก)

---

## 2. Back-end: Render

1. สมัครที่ render.com ด้วยบัญชี GitHub
2. กด **New → Blueprint** แล้วเลือก repository นี้
   Render จะอ่านไฟล์ `render.yaml` และตั้งค่าให้เอง (โฟลเดอร์ `backend`, คำสั่ง build และ start)
3. ระบบจะถามค่าที่ต้องใส่เอง
   - `DATABASE_URL` = connection string จาก Neon (ขั้นที่ 1)
   - `ALLOWED_ORIGINS` = ใส่ `https://example.com` ไว้ก่อน แล้วค่อยกลับมาแก้ในขั้นที่ 4
4. รอ deploy เสร็จ แล้วจดที่อยู่ เช่น `https://library-api.onrender.com`
5. ทดสอบ: เปิด `https://library-api.onrender.com/docs` ต้องเห็นหน้าเอกสาร API

---

## 3. Front-end: Vercel

1. สมัครที่ vercel.com ด้วยบัญชี GitHub
2. กด **Add New → Project** แล้วเลือก repository นี้
3. ตั้งค่า
   - **Root Directory** = `frontend`
   - Framework Preset = **Vite** (ปกติเลือกให้เอง)
   - **Environment Variables**: `VITE_API_URL` = ที่อยู่ Render จากขั้นที่ 2 (ไม่มี `/` ท้าย)
4. กด **Deploy** แล้วจดที่อยู่ เช่น `https://library-xxx.vercel.app`

---

## 4. เชื่อมสองฝั่งให้คุยกันได้ (CORS)

1. กลับไปที่ Render → service `library-api` → **Environment**
2. แก้ `ALLOWED_ORIGINS` เป็นที่อยู่ Vercel จากขั้นที่ 3 เช่น `https://library-xxx.vercel.app`
   (ไม่มี `/` ท้าย ถ้ามีหลายที่ให้คั่นด้วย `,`)
3. บันทึก Render จะ deploy ใหม่ให้เอง

---

## 5. ตรวจรับ

เปิดที่อยู่ Vercel จากมือถือ (ใช้เน็ตมือถือก็ได้)

- [ ] เพิ่มหนังสือและสมาชิกได้
- [ ] ยืมหนังสือได้
- [ ] ยืมเล่มเดิมซ้ำขณะยังไม่คืน → ขึ้นว่า "หนังสือเล่มนี้ถูกยืมอยู่ ต้องคืนก่อนจึงจะยืมใหม่ได้"
- [ ] คืนแล้วยืมใหม่ได้

---

## ที่ deploy จริงของโปรเจกต์นี้ และวิธีอัปเดตหลังแก้โค้ด

| ส่วน | ที่อยู่ | วิธี deploy ที่ใช้ |
|---|---|---|
| หน้าเว็บ | https://library-system-omega-three.vercel.app | Vercel CLI จากเครื่อง (ไม่ได้เชื่อม Git) |
| API | https://library-api-4nzv.onrender.com | Render Blueprint จาก public repo URL |
| ฐานข้อมูล | Neon project `library` (Singapore) | — |

**แก้หน้าเว็บ (frontend):** ในโฟลเดอร์ `frontend` รัน

```bash
npx vercel --prod --build-env VITE_API_URL=https://library-api-4nzv.onrender.com
```

**แก้ API (backend) หรือ `render.yaml`:** `git push` ขึ้น GitHub แล้วไปที่ Render → Blueprints →
`library-system` → **Manual sync** (ถ้าแก้ `render.yaml`) หรือ service `library-api` →
**Manual Deploy → Deploy latest commit** (ถ้าแก้โค้ด)

**เปลี่ยนที่อยู่หน้าเว็บ:** แก้ค่า `ALLOWED_ORIGINS` ใน `render.yaml` แล้ว push และกด Manual sync

---

## ข้อควรรู้

- **Render แบบฟรีจะหลับเมื่อไม่มีคนใช้สักพัก** คนแรกที่เข้ามาต้องรอเกือบนาทีให้ server ตื่น
  ก่อนสาธิต ให้เปิด `/health` ของ Render ทิ้งไว้ก่อน 1–2 นาที
- หลังจากนี้ทุกครั้งที่ `git push` ขึ้น GitHub ทั้ง Render และ Vercel จะ deploy ใหม่ให้อัตโนมัติ
- ถ้าหน้าเว็บขึ้นว่า "เชื่อมต่อเซิร์ฟเวอร์ไม่ได้" ให้เช็ก
  1. `VITE_API_URL` ใน Vercel ถูกต้อง (แก้แล้วต้อง Redeploy)
  2. `ALLOWED_ORIGINS` ใน Render ตรงกับที่อยู่ Vercel
  3. Render ตื่นแล้ว (เปิด `/health` ดู)
