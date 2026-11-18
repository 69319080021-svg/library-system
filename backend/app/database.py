"""การเชื่อมต่อฐานข้อมูล

- บนเครื่อง: ใช้ SQLite (ไฟล์ library.db) เป็นค่าเริ่มต้น
- ตอน deploy: ตั้งค่า environment variable DATABASE_URL ให้ชี้ไปที่ PostgreSQL
"""

import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

def normalize_url(url: str) -> str:
    """ผู้ให้บริการ PostgreSQL (เช่น Neon) ให้ URL แบบ postgres:// หรือ postgresql://
    แต่เราติดตั้งไดรเวอร์ psycopg (v3) จึงต้องบอก SQLAlchemy ให้ใช้ postgresql+psycopg://"""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


DATABASE_URL = normalize_url(os.getenv("DATABASE_URL", "sqlite:///./library.db"))


def make_engine(url: str):
    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False})

        # SQLite ปิดการตรวจ foreign key ไว้เป็นค่าเริ่มต้น ต้องเปิดเองทุกการเชื่อมต่อ
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_conn, _record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    return create_engine(url, pool_pre_ping=True)


engine = make_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """ใช้กับ FastAPI: เปิด session ต่อหนึ่งคำขอ แล้วปิดเมื่อเสร็จ"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
