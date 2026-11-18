"""เทสต์กฎอื่นที่เกี่ยวข้อง (T7–T12)"""

from datetime import datetime, timedelta, timezone

import pytest

from app.services import (
    ConflictError,
    NotFoundError,
    ValidationError,
    borrow_book,
    list_loans,
    retire_book,
    return_book,
    return_loan,
    update_member,
)


def test_t7_return_book_that_is_not_borrowed(db):
    """T7: คืนเล่มที่ไม่ได้ถูกยืม ต้อง error"""
    with pytest.raises(ConflictError, match="ไม่ได้ถูกยืมอยู่"):
        return_book(db, "B1")


def test_t8_return_same_loan_twice(db):
    """T8: คืนรายการเดิมซ้ำ ต้อง error และวันที่คืนเดิมไม่เปลี่ยน"""
    loan = borrow_book(db, "B1", "M1")
    first_return = datetime(2030, 1, 1, tzinfo=timezone.utc)
    return_loan(db, loan.loan_id, returned_at=first_return)

    with pytest.raises(ConflictError, match="คืนไปแล้ว"):
        return_loan(db, loan.loan_id, returned_at=first_return + timedelta(days=5))

    db.refresh(loan)
    assert loan.returned_at.replace(tzinfo=timezone.utc) == first_return


def test_t9_borrow_unknown_book(db):
    """T9a: ยืมเล่มที่ไม่มีในระบบ ต้องถูกปฏิเสธ"""
    with pytest.raises(NotFoundError, match="ไม่พบหนังสือ"):
        borrow_book(db, "NOPE", "M1")


def test_t9_borrow_retired_book(db):
    """T9b: ยืมเล่มที่ถูกปลดระวาง ต้องถูกปฏิเสธ"""
    retire_book(db, "B1")
    with pytest.raises(ConflictError, match="ปลดระวาง"):
        borrow_book(db, "B1", "M1")


def test_t10_suspended_member_cannot_borrow(db):
    """T10: สมาชิกที่ถูกระงับยืมไม่ได้ แต่ยังคืนเล่มที่ค้างอยู่ได้"""
    borrow_book(db, "B1", "M1")
    update_member(db, "M1", status="suspended")

    with pytest.raises(ConflictError, match="ระงับ"):
        borrow_book(db, "B2", "M1")

    return_book(db, "B1")  # คืนได้ตามปกติ


def test_t11_cannot_retire_borrowed_book(db):
    """T11: ปลดระวางเล่มที่ถูกยืมอยู่ ต้องถูกปฏิเสธ คืนแล้วจึงปลดได้"""
    borrow_book(db, "B1", "M1")

    with pytest.raises(ConflictError, match="ถูกยืมอยู่"):
        retire_book(db, "B1")

    return_book(db, "B1")
    assert retire_book(db, "B1").status == "retired"


def test_overdue_list(db):
    """รายการเลยกำหนด: ยังไม่คืนและเลยวันกำหนดคืนแล้วเท่านั้น"""
    long_ago = datetime(2020, 1, 1, tzinfo=timezone.utc)
    borrow_book(db, "B1", "M1", borrowed_at=long_ago)  # เลยกำหนด
    borrow_book(db, "B2", "M2")  # ยังไม่ถึงกำหนด

    assert [l.book_id for l in list_loans(db, "overdue")] == ["B1"]
    assert {l.book_id for l in list_loans(db, "active")} == {"B1", "B2"}

    return_book(db, "B1")
    assert list_loans(db, "overdue") == []


def test_t12_due_date_before_borrow_date(db):
    """T12: วันกำหนดคืนอยู่ก่อนวันยืม ต้องถูกปฏิเสธ"""
    t = datetime(2030, 1, 10, tzinfo=timezone.utc)
    with pytest.raises(ValidationError, match="วันกำหนดคืน"):
        borrow_book(db, "B1", "M1", borrowed_at=t, due_at=t - timedelta(days=1))
