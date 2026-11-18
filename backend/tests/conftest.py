"""ข้อมูลตั้งต้นสำหรับเทสต์

ทุกเทสต์ได้ฐานข้อมูลใหม่ของตัวเอง (ไฟล์ชั่วคราว) จึงไม่กระทบกันและไม่แตะ library.db จริง
- B1, B2: หนังสือชื่อเดียวกัน ISBN เดียวกัน แต่เป็นคนละเล่ม
- M1, M2: สมาชิกปกติ
"""

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, make_engine
from app.models import Book, Member


@pytest.fixture
def engine(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db(session_factory) -> Session:
    session = session_factory()
    session.add_all(
        [
            Book(book_id="B1", title="แฮร์รี่ พอตเตอร์ เล่ม 1", isbn="9786160400001"),
            Book(book_id="B2", title="แฮร์รี่ พอตเตอร์ เล่ม 1", isbn="9786160400001"),
            Member(member_id="M1", name="สมชาย ใจดี"),
            Member(member_id="M2", name="สมหญิง รักอ่าน"),
        ]
    )
    session.commit()
    yield session
    session.close()
