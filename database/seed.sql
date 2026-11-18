-- =====================================================================
-- ข้อมูลตัวอย่าง (รันหลัง schema.sql)
--   psql "<connection string>" -f database/seed.sql
-- รันซ้ำได้ แถวที่มีอยู่แล้วจะถูกข้าม (ON CONFLICT DO NOTHING)
-- =====================================================================

-- หนังสือ: B001 กับ B002 ชื่อและ ISBN เดียวกัน แต่เป็นคนละเล่ม
INSERT INTO books (book_id, title, author, isbn) VALUES
    ('B001', 'ภาษาไทยเบื้องต้น', 'ครูสมศรี', '9786160000011'),
    ('B002', 'ภาษาไทยเบื้องต้น', 'ครูสมศรี', '9786160000011'),
    ('B003', 'คณิตศาสตร์ ม.1',   NULL,       NULL)
ON CONFLICT (book_id) DO NOTHING;

-- สมาชิก
INSERT INTO members (member_id, name, phone) VALUES
    ('M001', 'สมชาย ใจดี',     '0812345678'),
    ('M002', 'สมหญิง รักอ่าน', NULL)
ON CONFLICT (member_id) DO NOTHING;

-- รายการยืม (ใส่เฉพาะตอนที่ตารางยังว่าง เพื่อให้รันซ้ำได้)
--   1) M001 ยืม B001 แล้วคืนแล้ว   -> เป็นประวัติ
--   2) M002 ยืม B001 ยังไม่คืน     -> รายการค้างคืน 1 รายการของ B001
INSERT INTO loans (book_id, member_id, borrowed_at, due_at, returned_at)
SELECT * FROM (VALUES
    ('B001', 'M001', now() - INTERVAL '10 days', now() + INTERVAL '4 days',  now() - INTERVAL '2 days'),
    ('B001', 'M002', now() - INTERVAL '1 day',   now() + INTERVAL '13 days', NULL::timestamptz)
) AS v(book_id, member_id, borrowed_at, due_at, returned_at)
WHERE NOT EXISTS (SELECT 1 FROM loans);
