"""กฎทางธุรกิจของระบบ (รวมไว้ที่เดียว API เรียกใช้จากที่นี่)

กฎหลักของโจทย์: หนังสือเล่มเดียวกันมีรายการยืมที่ยังไม่คืนได้ไม่เกิน 1 รายการ
บังคับ 2 ชั้น
  1. ตรวจในโค้ดก่อนบันทึก เพื่อส่งข้อความที่ผู้ใช้อ่านเข้าใจ
  2. partial unique index ในฐานข้อมูล (uq_loans_one_active_per_book)
     กันกรณีมีคำขอยืมเล่มเดียวกันพร้อมกันจนหลุดชั้นที่ 1
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Book, Loan, Member

DEFAULT_LOAN_DAYS = 14

BORROWED_MESSAGE = "หนังสือเล่มนี้ถูกยืมอยู่ ต้องคืนก่อนจึงจะยืมใหม่ได้"


# ---------------------------------------------------------------- ข้อผิดพลาด


class LibraryError(Exception):
    """ข้อผิดพลาดทางธุรกิจ มีข้อความภาษาไทยไว้แสดงผู้ใช้"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(LibraryError):
    """ไม่พบข้อมูลที่อ้างถึง (API ตอบ 404)"""


class ConflictError(LibraryError):
    """ทำรายการขัดกับกฎ เช่น ยืมเล่มที่ยังไม่คืน (API ตอบ 409)"""


class ValidationError(LibraryError):
    """ข้อมูลที่ส่งมาไม่ถูกต้อง (API ตอบ 422)"""


# ---------------------------------------------------------------- เวลา


def now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime) -> datetime:
    """SQLite คืนค่าวันเวลาแบบไม่มี timezone มา ให้ถือว่าเป็น UTC เพื่อเทียบกันได้"""
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _like(q: str) -> str:
    return f"%{q.strip()}%"


# ---------------------------------------------------------------- หนังสือ


def get_book(db: Session, book_id: str) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise NotFoundError(f"ไม่พบหนังสือรหัส {book_id}")
    return book


def list_books(db: Session, q: str | None = None) -> list[Book]:
    stmt = select(Book).order_by(Book.book_id)
    if q and q.strip():
        stmt = stmt.where(
            or_(
                Book.book_id.ilike(_like(q)),
                Book.title.ilike(_like(q)),
                Book.author.ilike(_like(q)),
                Book.isbn.ilike(_like(q)),
            )
        )
    return list(db.scalars(stmt))


def create_book(
    db: Session, book_id: str, title: str, author: str | None = None, isbn: str | None = None
) -> Book:
    if db.get(Book, book_id) is not None:
        raise ConflictError(f"มีหนังสือรหัส {book_id} อยู่แล้ว")
    book = Book(book_id=book_id, title=title, author=author, isbn=isbn)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book_id: str, **fields) -> Book:
    book = get_book(db, book_id)
    for key in ("title", "author", "isbn"):
        if key in fields:
            setattr(book, key, fields[key])
    db.commit()
    db.refresh(book)
    return book


def retire_book(db: Session, book_id: str) -> Book:
    """ปลดระวางหนังสือ (ไม่ลบจริง เพื่อเก็บประวัติการยืมไว้)"""
    book = get_book(db, book_id)
    if get_active_loan(db, book_id) is not None:
        raise ConflictError("หนังสือเล่มนี้ถูกยืมอยู่ ต้องคืนก่อนจึงจะปลดระวางได้")
    book.status = "retired"
    db.commit()
    db.refresh(book)
    return book


def active_loans_by_book(db: Session, book_ids: list[str]) -> dict[str, Loan]:
    """map รหัสเล่ม -> รายการยืมที่ยังไม่คืน (ใช้แสดงสถานะว่าง/ถูกยืมในรายการหนังสือ)"""
    if not book_ids:
        return {}
    loans = db.scalars(
        select(Loan).where(Loan.book_id.in_(book_ids), Loan.returned_at.is_(None))
    )
    return {loan.book_id: loan for loan in loans}


# ---------------------------------------------------------------- สมาชิก


def get_member(db: Session, member_id: str) -> Member:
    member = db.get(Member, member_id)
    if member is None:
        raise NotFoundError(f"ไม่พบสมาชิกรหัส {member_id}")
    return member


def list_members(db: Session, q: str | None = None) -> list[Member]:
    stmt = select(Member).order_by(Member.member_id)
    if q and q.strip():
        stmt = stmt.where(
            or_(
                Member.member_id.ilike(_like(q)),
                Member.name.ilike(_like(q)),
                Member.phone.ilike(_like(q)),
                Member.email.ilike(_like(q)),
            )
        )
    return list(db.scalars(stmt))


def create_member(
    db: Session,
    member_id: str,
    name: str,
    phone: str | None = None,
    email: str | None = None,
) -> Member:
    if db.get(Member, member_id) is not None:
        raise ConflictError(f"มีสมาชิกรหัส {member_id} อยู่แล้ว")
    member = Member(member_id=member_id, name=name, phone=phone, email=email)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def update_member(db: Session, member_id: str, **fields) -> Member:
    """แก้ไขข้อมูลสมาชิก รวมถึงระงับ (status='suspended') หรือเปิดใช้งานอีกครั้ง

    สมาชิกที่ถูกระงับยังคืนหนังสือที่ค้างอยู่ได้ตามปกติ แค่ยืมเพิ่มไม่ได้
    """
    member = get_member(db, member_id)
    for key in ("name", "phone", "email", "status"):
        if key in fields:
            setattr(member, key, fields[key])
    db.commit()
    db.refresh(member)
    return member


def member_loans(db: Session, member_id: str) -> list[Loan]:
    get_member(db, member_id)
    return list(
        db.scalars(
            select(Loan).where(Loan.member_id == member_id).order_by(Loan.borrowed_at.desc())
        )
    )


# ---------------------------------------------------------------- ยืม / คืน


def get_active_loan(db: Session, book_id: str) -> Loan | None:
    """รายการยืมที่ยังไม่คืนของเล่มนี้ (มีได้มากสุด 1 รายการ)"""
    return db.scalars(
        select(Loan).where(Loan.book_id == book_id, Loan.returned_at.is_(None))
    ).first()


def list_loans(db: Session, status: str = "all") -> list[Loan]:
    """status: 'all' ทั้งหมด, 'active' ยังไม่คืน, 'overdue' ยังไม่คืนและเลยกำหนด"""
    stmt = select(Loan).order_by(Loan.borrowed_at.desc())
    if status in ("active", "overdue"):
        stmt = stmt.where(Loan.returned_at.is_(None))
    if status == "overdue":
        stmt = stmt.where(Loan.due_at < now())
    return list(db.scalars(stmt))


def borrow_book(
    db: Session,
    book_id: str,
    member_id: str,
    borrowed_at: datetime | None = None,
    due_at: datetime | None = None,
) -> Loan:
    book = get_book(db, book_id)
    if book.status != "active":
        raise ConflictError("หนังสือเล่มนี้ถูกปลดระวางแล้ว ยืมไม่ได้")

    member = get_member(db, member_id)
    if member.status != "active":
        raise ConflictError("สมาชิกถูกระงับ ยืมไม่ได้")

    borrowed_at = as_utc(borrowed_at or now())
    due_at = as_utc(due_at or borrowed_at + timedelta(days=DEFAULT_LOAN_DAYS))
    if due_at < borrowed_at:
        raise ValidationError("วันกำหนดคืนต้องไม่ก่อนวันยืม")

    # ชั้นที่ 1: ตรวจในโค้ด
    if get_active_loan(db, book_id) is not None:
        raise ConflictError(BORROWED_MESSAGE)

    loan = Loan(book_id=book_id, member_id=member_id, borrowed_at=borrowed_at, due_at=due_at)
    db.add(loan)
    try:
        db.commit()
    except IntegrityError:
        # ชั้นที่ 2: มีคนยืมเล่มเดียวกันตัดหน้าไปในจังหวะเดียวกัน ฐานข้อมูลจึงปฏิเสธ
        db.rollback()
        raise ConflictError(BORROWED_MESSAGE) from None
    db.refresh(loan)
    return loan


def _mark_returned(db: Session, loan: Loan, returned_at: datetime | None) -> Loan:
    returned_at = as_utc(returned_at or now())
    if returned_at < as_utc(loan.borrowed_at):
        raise ValidationError("วันที่คืนต้องไม่ก่อนวันยืม")
    loan.returned_at = returned_at
    db.commit()
    db.refresh(loan)
    return loan


def return_book(db: Session, book_id: str, returned_at: datetime | None = None) -> Loan:
    """คืนโดยระบุรหัสเล่ม (เช่น สแกนบาร์โค้ดที่ตัวหนังสือ)"""
    get_book(db, book_id)
    loan = get_active_loan(db, book_id)
    if loan is None:
        raise ConflictError("หนังสือเล่มนี้ไม่ได้ถูกยืมอยู่")
    return _mark_returned(db, loan, returned_at)


def return_loan(db: Session, loan_id: int, returned_at: datetime | None = None) -> Loan:
    """คืนโดยระบุรายการยืม (เช่น กดคืนจากรายการค้างคืน)"""
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise NotFoundError(f"ไม่พบรายการยืมเลขที่ {loan_id}")
    if loan.returned_at is not None:
        raise ConflictError("รายการนี้คืนไปแล้ว")
    return _mark_returned(db, loan, returned_at)
