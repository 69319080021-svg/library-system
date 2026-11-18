"""เทสต์กฎหลักของโจทย์ (T1–T6)

หนังสือเล่มเดียวกันมีรายการยืมที่ยังไม่คืนได้ไม่เกิน 1 รายการ
"""

import threading
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app import services
from app.models import Loan
from app.services import ConflictError, borrow_book, return_book


def count_active(db, book_id: str) -> int:
    return db.scalar(
        select(func.count()).where(Loan.book_id == book_id, Loan.returned_at.is_(None))
    )


def count_all(db, book_id: str) -> int:
    return db.scalar(select(func.count()).where(Loan.book_id == book_id))


def test_t1_borrow_available_book(db):
    """T1: ยืมเล่มที่ว่างอยู่ ต้องสำเร็จ"""
    loan = borrow_book(db, "B1", "M1")

    assert loan.loan_id is not None
    assert loan.returned_at is None
    assert count_active(db, "B1") == 1


@pytest.mark.parametrize("second_member", ["M1", "M2"], ids=["same-member", "other-member"])
def test_t2_cannot_borrow_book_that_is_not_returned(db, second_member):
    """T2: ยืมเล่มที่ยังไม่คืน ต้องถูกปฏิเสธ (ทั้งคนเดิมและคนอื่น)"""
    borrow_book(db, "B1", "M1")

    with pytest.raises(ConflictError, match="ถูกยืมอยู่"):
        borrow_book(db, "B1", second_member)

    assert count_active(db, "B1") == 1
    assert count_all(db, "B1") == 1


def test_t3_borrow_again_after_return(db):
    """T3: คืนแล้วยืมใหม่ได้ ประวัติมี 2 รายการ แต่ค้างคืนแค่ 1"""
    borrow_book(db, "B1", "M1")
    return_book(db, "B1")

    loan = borrow_book(db, "B1", "M2")

    assert loan.member_id == "M2"
    assert count_all(db, "B1") == 2
    assert count_active(db, "B1") == 1


def test_t4_concurrent_borrow_only_one_succeeds(db, session_factory, monkeypatch):
    """T4: สองคำขอยืมเล่มเดียวกันพร้อมกัน ต้องสำเร็จแค่ 1

    บังคับให้ทั้งสองคำขอผ่านการตรวจในโค้ด (ชั้นที่ 1) ไปก่อน แล้วค่อยบันทึกพร้อมกัน
    เพื่อพิสูจน์ว่าฐานข้อมูล (ชั้นที่ 2) ยังกันไว้ได้
    """
    both_checked = threading.Barrier(2, timeout=5)
    original_check = services.get_active_loan

    def check_then_wait(session, book_id):
        result = original_check(session, book_id)
        both_checked.wait()  # รอจนทั้งสองคำขอตรวจเสร็จ แล้วค่อยไปบันทึกพร้อมกัน
        return result

    monkeypatch.setattr(services, "get_active_loan", check_then_wait)

    results: dict[str, str] = {}

    def attempt(member_id: str):
        session = session_factory()
        try:
            borrow_book(session, "B1", member_id)
            results[member_id] = "ok"
        except ConflictError:
            results[member_id] = "conflict"
        finally:
            session.close()

    threads = [threading.Thread(target=attempt, args=(m,)) for m in ("M1", "M2")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert sorted(results.values()) == ["conflict", "ok"]
    assert count_active(db, "B1") == 1


def test_t5_another_copy_of_same_title_can_be_borrowed(db):
    """T5: B1 ถูกยืมอยู่ แต่ B2 (ชื่อ/ISBN เดียวกัน คนละเล่ม) ยังยืมได้"""
    borrow_book(db, "B1", "M1")

    loan = borrow_book(db, "B2", "M2")

    assert loan.book_id == "B2"
    assert count_active(db, "B1") == 1
    assert count_active(db, "B2") == 1


def test_t6_repeated_borrow_and_return_never_exceeds_one_active(db):
    """T6: ยืมและคืนสลับกันหลายรอบ ต้องไม่มีช่วงไหนที่ค้างคืนเกิน 1 รายการ"""
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    members = ["M1", "M2"]

    for i in range(6):
        t = start + timedelta(days=i * 2)
        borrow_book(db, "B1", members[i % 2], borrowed_at=t)
        assert count_active(db, "B1") == 1

        with pytest.raises(ConflictError):
            borrow_book(db, "B1", members[(i + 1) % 2], borrowed_at=t)
        assert count_active(db, "B1") == 1

        return_book(db, "B1", returned_at=t + timedelta(days=1))
        assert count_active(db, "B1") == 0

    assert count_all(db, "B1") == 6
