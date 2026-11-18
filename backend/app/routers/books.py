from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import services
from ..database import get_db
from ..models import Book, Loan
from ..schemas import BookCreate, BookOut, BookUpdate, ErrorOut, LoanOut

router = APIRouter(prefix="/books", tags=["หนังสือ"])

NOT_FOUND = {404: {"model": ErrorOut, "description": "ไม่พบหนังสือ"}}


def to_out(book: Book, active_loan: Loan | None) -> BookOut:
    return BookOut.model_validate(
        {
            **{c: getattr(book, c) for c in ("book_id", "title", "author", "isbn", "status", "created_at")},
            "available": book.status == "active" and active_loan is None,
            "borrowed_by": active_loan.member_id if active_loan else None,
            "active_loan_id": active_loan.loan_id if active_loan else None,
        }
    )


def _one(db: Session, book: Book) -> BookOut:
    return to_out(book, services.get_active_loan(db, book.book_id))


@router.get("", response_model=list[BookOut], summary="ค้นหาหนังสือ")
def list_books(q: str | None = None, db: Session = Depends(get_db)):
    """ค้นจากรหัสเล่ม ชื่อ ผู้แต่ง หรือ ISBN (ไม่ระบุ q = ทั้งหมด)"""
    books = services.list_books(db, q)
    active = services.active_loans_by_book(db, [b.book_id for b in books])
    return [to_out(b, active.get(b.book_id)) for b in books]


@router.post(
    "",
    response_model=BookOut,
    status_code=201,
    summary="เพิ่มหนังสือ",
    responses={409: {"model": ErrorOut, "description": "รหัสเล่มซ้ำ"}},
)
def create_book(body: BookCreate, db: Session = Depends(get_db)):
    return _one(db, services.create_book(db, **body.model_dump()))


@router.get("/{book_id}", response_model=BookOut, summary="ดูหนังสือ", responses=NOT_FOUND)
def get_book(book_id: str, db: Session = Depends(get_db)):
    return _one(db, services.get_book(db, book_id))


@router.put("/{book_id}", response_model=BookOut, summary="แก้ไขหนังสือ", responses=NOT_FOUND)
def update_book(book_id: str, body: BookUpdate, db: Session = Depends(get_db)):
    fields = body.model_dump(exclude_unset=True)
    if fields.get("title") is None:
        fields.pop("title", None)  # ชื่อหนังสือห้ามว่าง
    return _one(db, services.update_book(db, book_id, **fields))


@router.post(
    "/{book_id}/retire",
    response_model=BookOut,
    summary="ปลดระวางหนังสือ",
    responses={**NOT_FOUND, 409: {"model": ErrorOut, "description": "เล่มนี้ยังถูกยืมอยู่"}},
)
def retire_book(book_id: str, db: Session = Depends(get_db)):
    """ไม่ลบจริง เพื่อเก็บประวัติการยืมไว้ ห้ามปลดระวางเล่มที่ยังถูกยืมอยู่"""
    return _one(db, services.retire_book(db, book_id))


@router.post(
    "/{book_id}/return",
    response_model=LoanOut,
    summary="คืนหนังสือด้วยรหัสเล่ม",
    responses={**NOT_FOUND, 409: {"model": ErrorOut, "description": "เล่มนี้ไม่ได้ถูกยืมอยู่"}},
)
def return_by_book(book_id: str, db: Session = Depends(get_db)):
    """ใช้เมื่อมีหนังสืออยู่ในมือ (เช่น สแกนบาร์โค้ด) โดยไม่ต้องรู้เลขที่รายการยืม"""
    return services.return_book(db, book_id)
