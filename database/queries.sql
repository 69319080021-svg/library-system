-- =====================================================================
-- คำสั่ง SQL ที่ใช้บ่อย (ตรงกับที่ระบบทำผ่าน API)
-- =====================================================================

-- สถานะหนังสือทุกเล่ม: ว่าง / ถูกยืม (โดยใคร) / ปลดระวาง
SELECT b.book_id,
       b.title,
       CASE
           WHEN b.status = 'retired' THEN 'ปลดระวาง'
           WHEN l.loan_id IS NULL    THEN 'ว่าง'
           ELSE 'ถูกยืมโดย ' || l.member_id
       END AS availability
FROM books b
LEFT JOIN loans l ON l.book_id = b.book_id AND l.returned_at IS NULL
ORDER BY b.book_id;

-- รายการที่ยังไม่คืน
SELECT l.loan_id, l.book_id, b.title, l.member_id, m.name, l.borrowed_at, l.due_at
FROM loans l
JOIN books   b ON b.book_id   = l.book_id
JOIN members m ON m.member_id = l.member_id
WHERE l.returned_at IS NULL
ORDER BY l.borrowed_at DESC;

-- รายการเลยกำหนดคืน
SELECT l.loan_id, l.book_id, l.member_id, l.due_at, now() - l.due_at AS overdue_by
FROM loans l
WHERE l.returned_at IS NULL AND l.due_at < now()
ORDER BY l.due_at;

-- ประวัติการยืมของสมาชิก (เปลี่ยน 'M001' เป็นรหัสที่ต้องการ)
SELECT l.loan_id, l.book_id, b.title, l.borrowed_at, l.due_at, l.returned_at
FROM loans l
JOIN books b ON b.book_id = l.book_id
WHERE l.member_id = 'M001'
ORDER BY l.borrowed_at DESC;

-- ตรวจเงื่อนไขของโจทย์: ผลต้องเป็น 0 แถวเสมอ
-- (ถ้ามีแถว แปลว่ามีเล่มที่ค้างคืนเกิน 1 รายการ)
SELECT book_id, COUNT(*) AS active_loans
FROM loans
WHERE returned_at IS NULL
GROUP BY book_id
HAVING COUNT(*) > 1;
