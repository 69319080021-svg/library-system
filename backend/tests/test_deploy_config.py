"""ตรวจการตั้งค่าที่ใช้ตอน deploy (PostgreSQL)"""

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex

from app.database import normalize_url
from app.models import Loan


def test_normalize_postgres_url_uses_psycopg3():
    assert normalize_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalize_url("postgresql://u:p@h/db?sslmode=require") == (
        "postgresql+psycopg://u:p@h/db?sslmode=require"
    )
    assert normalize_url("sqlite:///./library.db") == "sqlite:///./library.db"


def test_one_active_loan_index_on_postgresql():
    """กฎหลักต้องถูกสร้างเป็น partial unique index บน PostgreSQL ด้วย"""
    index = next(i for i in Loan.__table__.indexes if i.name == "uq_loans_one_active_per_book")
    sql = str(CreateIndex(index).compile(dialect=postgresql.dialect()))
    assert "CREATE UNIQUE INDEX uq_loans_one_active_per_book ON loans (book_id)" in sql
    assert "WHERE returned_at IS NULL" in sql
