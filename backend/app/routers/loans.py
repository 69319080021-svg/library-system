from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import services
from ..database import get_db
from ..schemas import ErrorOut, LoanCreate, LoanOut

router = APIRouter(prefix="/loans", tags=["ยืม-คืน"])


@router.get("", response_model=list[LoanOut], summary="รายการยืม")
def list_loans(
    status: Literal["all", "active", "overdue"] = "all", db: Session = Depends(get_db)
):
    """status: all = ทั้งหมด, active = ยังไม่คืน, overdue = ยังไม่คืนและเลยกำหนด"""
    return services.list_loans(db, status)


@router.post(
    "",
    response_model=LoanOut,
    status_code=201,
    summary="ยืมหนังสือ",
    responses={
        404: {"model": ErrorOut, "description": "ไม่พบหนังสือหรือสมาชิก"},
        409: {
            "model": ErrorOut,
            "description": "ยืมไม่ได้ เช่น เล่มนี้ถูกยืมอยู่ ถูกปลดระวาง หรือสมาชิกถูกระงับ",
        },
        422: {"model": ErrorOut, "description": "วันกำหนดคืนไม่ถูกต้อง"},
    },
)
def borrow(body: LoanCreate, db: Session = Depends(get_db)):
    """กฎหลัก: หนังสือเล่มเดียวกันมีรายการที่ยังไม่คืนได้ไม่เกิน 1 รายการ"""
    return services.borrow_book(db, body.book_id, body.member_id, due_at=body.due_at)


@router.post(
    "/{loan_id}/return",
    response_model=LoanOut,
    summary="คืนหนังสือด้วยเลขที่รายการยืม",
    responses={
        404: {"model": ErrorOut, "description": "ไม่พบรายการยืม"},
        409: {"model": ErrorOut, "description": "รายการนี้คืนไปแล้ว"},
    },
)
def return_loan(loan_id: int, db: Session = Depends(get_db)):
    return services.return_loan(db, loan_id)
