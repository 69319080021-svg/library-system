"""เทสต์ผ่าน HTTP API (เหมือนที่หน้าเว็บจะเรียกใช้จริง)"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


@pytest.fixture
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    # ไม่ใช้ `with TestClient(...)` เพื่อไม่ให้ lifespan ไปสร้างไฟล์ library.db จริง
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def seeded(client):
    for b in ("B1", "B2"):
        r = client.post("/books", json={"book_id": b, "title": "ภาษาไทยเบื้องต้น", "isbn": "111"})
        assert r.status_code == 201
    for m, name in (("M1", "สมชาย"), ("M2", "สมหญิง")):
        r = client.post("/members", json={"member_id": m, "name": name})
        assert r.status_code == 201
    return client


def test_borrow_flow_and_one_active_loan_rule(seeded):
    c = seeded

    r = c.post("/loans", json={"book_id": "B1", "member_id": "M1"})
    assert r.status_code == 201
    loan = r.json()
    assert loan["returned_at"] is None
    assert loan["is_overdue"] is False

    # กฎหลัก: ยืมเล่มเดิมซ้ำขณะยังไม่คืน -> 409
    r = c.post("/loans", json={"book_id": "B1", "member_id": "M2"})
    assert r.status_code == 409
    assert "ถูกยืมอยู่" in r.json()["detail"]

    # สถานะในรายการหนังสือ
    books = {b["book_id"]: b for b in c.get("/books").json()}
    assert books["B1"]["available"] is False
    assert books["B1"]["borrowed_by"] == "M1"
    assert books["B1"]["active_loan_id"] == loan["loan_id"]
    assert books["B2"]["available"] is True

    # คืน แล้วคืนซ้ำ
    r = c.post(f"/loans/{loan['loan_id']}/return")
    assert r.status_code == 200
    assert r.json()["returned_at"] is not None
    r = c.post(f"/loans/{loan['loan_id']}/return")
    assert r.status_code == 409

    # คืนแล้วยืมใหม่ได้
    r = c.post("/loans", json={"book_id": "B1", "member_id": "M2"})
    assert r.status_code == 201

    # คืนด้วยรหัสเล่ม
    r = c.post("/books/B1/return")
    assert r.status_code == 200
    r = c.post("/books/B1/return")
    assert r.status_code == 409

    history = c.get("/members/M1/loans").json()
    assert len(history) == 1


def test_list_active_and_overdue(seeded):
    c = seeded
    past_due = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    # ยืมย้อนหลังผ่าน API ไม่ได้ จึงตั้งวันกำหนดคืนเป็นอดีตไม่ได้ (จะผิดกฎ T12)
    r = c.post("/loans", json={"book_id": "B1", "member_id": "M1", "due_at": past_due})
    assert r.status_code == 422

    c.post("/loans", json={"book_id": "B1", "member_id": "M1"})
    c.post("/loans", json={"book_id": "B2", "member_id": "M2"})
    c.post("/books/B2/return")

    assert [l["book_id"] for l in c.get("/loans?status=active").json()] == ["B1"]
    assert c.get("/loans?status=overdue").json() == []
    assert len(c.get("/loans").json()) == 2


def test_not_found_and_validation(seeded):
    c = seeded
    assert c.post("/loans", json={"book_id": "NOPE", "member_id": "M1"}).status_code == 404
    assert c.post("/loans", json={"book_id": "B1", "member_id": "NOPE"}).status_code == 404
    assert c.get("/books/NOPE").status_code == 404
    assert c.post("/loans/999/return").status_code == 404
    assert c.post("/books", json={"book_id": "B1", "title": "ซ้ำ"}).status_code == 409
    assert c.post("/books", json={"book_id": "", "title": "x"}).status_code == 422
    assert c.get("/loans?status=wrong").status_code == 422


def test_search_update_retire_and_suspend(seeded):
    c = seeded
    c.post("/books", json={"book_id": "C1", "title": "คณิตศาสตร์", "author": "อาจารย์ ก"})

    assert [b["book_id"] for b in c.get("/books", params={"q": "คณิต"}).json()] == ["C1"]
    assert len(c.get("/books", params={"q": "111"}).json()) == 2

    r = c.put("/books/C1", json={"title": "คณิตศาสตร์ ม.1"})
    assert r.json()["title"] == "คณิตศาสตร์ ม.1"
    assert r.json()["author"] == "อาจารย์ ก"  # ฟิลด์ที่ไม่ส่งมาไม่เปลี่ยน

    c.post("/loans", json={"book_id": "C1", "member_id": "M1"})
    assert c.post("/books/C1/retire").status_code == 409
    c.post("/books/C1/return")
    r = c.post("/books/C1/retire")
    assert r.status_code == 200
    assert r.json()["status"] == "retired"
    assert r.json()["available"] is False

    r = c.put("/members/M2", json={"status": "suspended"})
    assert r.json()["status"] == "suspended"
    r = c.post("/loans", json={"book_id": "B1", "member_id": "M2"})
    assert r.status_code == 409
    assert "ระงับ" in r.json()["detail"]
