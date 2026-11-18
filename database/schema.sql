-- =====================================================================
-- ระบบห้องสมุดและยืมคืนหนังสือ : Database Script (PostgreSQL)
-- ---------------------------------------------------------------------
-- สร้างตารางหลัก 3 ตาราง
--   books   : หนังสือ 1 แถว = 1 เล่มจริง (ชื่อหรือ ISBN ซ้ำกันได้)
--   members : สมาชิก
--   loans   : รายการยืม (returned_at เป็น NULL = ยังไม่คืน)
--
-- เงื่อนไขทดสอบของโจทย์:
--   "หนังสือเล่มเดียวกันมีรายการยืมที่ยังไม่คืนได้ไม่เกินหนึ่งรายการ"
--   บังคับด้วย partial unique index: uq_loans_one_active_per_book (ท้ายไฟล์)
--
-- โครงสร้างตรงกับ backend/app/models.py (back-end สร้างตารางเหล่านี้ให้เอง
-- ตอนเปิด server ครั้งแรก ไฟล์นี้มีไว้สำหรับสร้างฐานข้อมูลด้วยมือหรือส่งงาน)
--
-- วิธีรัน (psql):  psql "<connection string>" -f database/schema.sql
-- หรือคัดลอกไปวางใน Neon Console > SQL Editor แล้วกด Run
-- =====================================================================

-- ---------------------------------------------------------------------
-- หนังสือ (รายเล่ม)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS books (
    book_id     VARCHAR(50)  NOT NULL,                  -- รหัสเล่ม / บาร์โค้ด
    title       VARCHAR(255) NOT NULL,                  -- ชื่อหนังสือ
    author      VARCHAR(255),                           -- ผู้แต่ง
    isbn        VARCHAR(20),                            -- ISBN (ซ้ำได้ถ้ามีหลายเล่ม)
    status      VARCHAR(20)  NOT NULL DEFAULT 'active', -- active = ใช้งาน, retired = ปลดระวาง
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    CONSTRAINT pk_books PRIMARY KEY (book_id),
    CONSTRAINT ck_books_status CHECK (status IN ('active', 'retired'))
);

CREATE INDEX IF NOT EXISTS ix_books_isbn ON books (isbn);

-- ---------------------------------------------------------------------
-- สมาชิก
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS members (
    member_id   VARCHAR(50)  NOT NULL,                  -- รหัสสมาชิก
    name        VARCHAR(255) NOT NULL,                  -- ชื่อ-นามสกุล
    phone       VARCHAR(30),
    email       VARCHAR(255),
    status      VARCHAR(20)  NOT NULL DEFAULT 'active', -- active = ใช้งาน, suspended = ระงับ
    joined_at   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    CONSTRAINT pk_members PRIMARY KEY (member_id),
    CONSTRAINT ck_members_status CHECK (status IN ('active', 'suspended'))
);

-- ---------------------------------------------------------------------
-- รายการยืม
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS loans (
    loan_id      SERIAL      NOT NULL,                  -- เลขที่รายการยืม (รันอัตโนมัติ)
    book_id      VARCHAR(50) NOT NULL,                  -- เล่มที่ยืม
    member_id    VARCHAR(50) NOT NULL,                  -- ผู้ยืม
    borrowed_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),                     -- วันยืม
    due_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (now() + INTERVAL '14 days'), -- กำหนดคืน
    returned_at  TIMESTAMP WITH TIME ZONE,                                            -- วันคืน (NULL = ยังไม่คืน)
    CONSTRAINT pk_loans PRIMARY KEY (loan_id),
    CONSTRAINT fk_loans_book   FOREIGN KEY (book_id)   REFERENCES books (book_id),
    CONSTRAINT fk_loans_member FOREIGN KEY (member_id) REFERENCES members (member_id),
    CONSTRAINT ck_loans_due_after_borrow    CHECK (due_at >= borrowed_at),
    CONSTRAINT ck_loans_return_after_borrow CHECK (returned_at IS NULL OR returned_at >= borrowed_at)
);

CREATE INDEX IF NOT EXISTS ix_loans_book_id   ON loans (book_id);
CREATE INDEX IF NOT EXISTS ix_loans_member_id ON loans (member_id);

-- ---------------------------------------------------------------------
-- กฎหลักของโจทย์: หนังสือเล่มเดียวกันมีรายการที่ยังไม่คืนได้ไม่เกิน 1 รายการ
-- unique เฉพาะแถวที่ returned_at IS NULL (partial unique index)
-- รายการที่คืนแล้วไม่นับ จึงเก็บประวัติการยืมของเล่มเดิมได้หลายรายการ
-- ---------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS uq_loans_one_active_per_book
    ON loans (book_id)
    WHERE returned_at IS NULL;
