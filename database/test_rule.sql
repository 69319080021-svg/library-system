-- =====================================================================
-- ทดสอบเงื่อนไขของโจทย์ด้วย SQL ล้วน (รันหลัง schema.sql + seed.sql)
--   "หนังสือเล่มเดียวกันมีรายการยืมที่ยังไม่คืนได้ไม่เกินหนึ่งรายการ"
--
--   psql "<connection string>" -f database/test_rule.sql
--
-- ทุกขั้นอยู่ใน transaction แล้ว ROLLBACK ท้ายไฟล์ ข้อมูลจริงจึงไม่เปลี่ยน
-- =====================================================================

BEGIN;

-- ล้างรายการยืมใน transaction นี้ เพื่อเริ่มทดสอบจากสถานะที่รู้แน่นอน
DELETE FROM loans;

-- T1: ยืม B001 ครั้งแรก -> ต้องสำเร็จ
INSERT INTO loans (book_id, member_id) VALUES ('B001', 'M001');

-- T2: ยืม B001 ซ้ำขณะยังไม่คืน -> ต้องถูกปฏิเสธด้วย unique_violation
DO $$
BEGIN
    INSERT INTO loans (book_id, member_id) VALUES ('B001', 'M002');
    RAISE EXCEPTION 'T2 FAILED: ยืมเล่มที่ยังไม่คืนซ้ำได้';
EXCEPTION
    WHEN unique_violation THEN
        RAISE NOTICE 'T2 PASSED: ยืม B001 ซ้ำไม่ได้ (uq_loans_one_active_per_book)';
END $$;

-- T5: เล่มอื่นที่ชื่อ/ISBN เดียวกัน (B002) ยังยืมได้
INSERT INTO loans (book_id, member_id) VALUES ('B002', 'M002');

-- T3: คืน B001 แล้วยืมใหม่ -> ต้องสำเร็จ
UPDATE loans SET returned_at = now() WHERE book_id = 'B001' AND returned_at IS NULL;
INSERT INTO loans (book_id, member_id) VALUES ('B001', 'M002');

-- ตรวจผล: ทุกเล่มต้องมีรายการค้างคืนไม่เกิน 1 รายการ
DO $$
DECLARE
    worst INT;
BEGIN
    SELECT COALESCE(MAX(c), 0) INTO worst FROM (
        SELECT COUNT(*) AS c FROM loans WHERE returned_at IS NULL GROUP BY book_id
    ) t;
    IF worst > 1 THEN
        RAISE EXCEPTION 'FAILED: มีเล่มที่ค้างคืน % รายการ', worst;
    END IF;
    RAISE NOTICE 'PASSED: ทุกเล่มมีรายการค้างคืนไม่เกิน 1 รายการ';
END $$;

-- ดูภาพรวม: ประวัติ B001 มี 2 รายการ แต่ค้างคืนแค่ 1
SELECT book_id,
       COUNT(*)                                   AS total_loans,
       COUNT(*) FILTER (WHERE returned_at IS NULL) AS active_loans
FROM loans
GROUP BY book_id
ORDER BY book_id;

ROLLBACK;
