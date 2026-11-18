"""ตารางหลักของระบบ: books (หนังสือรายเล่ม), members (สมาชิก), loans (รายการยืม)"""

from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Book(Base):
    """หนังสือ 1 แถว = 1 เล่มจริง (ชื่อหรือ ISBN ซ้ำกันได้ถ้ามีหลายเล่ม)"""

    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'retired')", name="ck_books_status"),
    )

    book_id: Mapped[str] = mapped_column(String(50), primary_key=True)  # รหัสเล่ม / บาร์โค้ด
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str | None] = mapped_column(String(255))
    isbn: Mapped[str | None] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    loans: Mapped[list["Loan"]] = relationship(back_populates="book")


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'suspended')", name="ck_members_status"),
    )

    member_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="active")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    loans: Mapped[list["Loan"]] = relationship(back_populates="member")


class Loan(Base):
    """รายการยืม: returned_at เป็น NULL = ยังไม่คืน"""

    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint("due_at >= borrowed_at", name="ck_loans_due_after_borrow"),
        CheckConstraint(
            "returned_at IS NULL OR returned_at >= borrowed_at",
            name="ck_loans_return_after_borrow",
        ),
        # กฎหลักของโจทย์: หนังสือเล่มเดียวกันมีรายการที่ยังไม่คืนได้ไม่เกิน 1 รายการ
        # unique เฉพาะแถวที่ returned_at IS NULL (partial unique index)
        # รายการที่คืนแล้วไม่นับ จึงเก็บประวัติการยืมของเล่มเดิมได้หลายรายการ
        Index(
            "uq_loans_one_active_per_book",
            "book_id",
            unique=True,
            sqlite_where=text("returned_at IS NULL"),
            postgresql_where=text("returned_at IS NULL"),
        ),
    )

    loan_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.book_id"), index=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("members.member_id"), index=True)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    book: Mapped[Book] = relationship(back_populates="loans")
    member: Mapped[Member] = relationship(back_populates="loans")
