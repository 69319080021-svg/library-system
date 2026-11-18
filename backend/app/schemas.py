"""รูปแบบข้อมูลที่รับเข้าและส่งออกทาง API"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, computed_field

from .services import as_utc, now

# วันเวลาที่ส่งออกจะมี timezone (UTC) เสมอ แม้ SQLite จะเก็บแบบไม่มี timezone
UtcDatetime = Annotated[datetime, AfterValidator(as_utc)]

Id = Annotated[str, Field(min_length=1, max_length=50, pattern=r"^\S+$")]
Text = Annotated[str, Field(min_length=1, max_length=255)]


# ---------------------------------------------------------------- หนังสือ


class BookCreate(BaseModel):
    book_id: Id = Field(examples=["B001"])
    title: Text = Field(examples=["ภาษาไทยเบื้องต้น"])
    author: str | None = Field(default=None, max_length=255)
    isbn: str | None = Field(default=None, max_length=20)


class BookUpdate(BaseModel):
    title: Text | None = None
    author: str | None = Field(default=None, max_length=255)
    isbn: str | None = Field(default=None, max_length=20)


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: str
    title: str
    author: str | None
    isbn: str | None
    status: Literal["active", "retired"]
    created_at: UtcDatetime
    available: bool = Field(description="ว่างให้ยืมไหม (ยังใช้งานอยู่และไม่มีรายการค้างคืน)")
    borrowed_by: str | None = Field(description="รหัสสมาชิกที่ยืมอยู่ (ถ้ามี)")
    active_loan_id: int | None = Field(description="เลขที่รายการยืมที่ยังไม่คืน (ถ้ามี)")


# ---------------------------------------------------------------- สมาชิก


class MemberCreate(BaseModel):
    member_id: Id = Field(examples=["M001"])
    name: Text = Field(examples=["สมชาย ใจดี"])
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)


class MemberUpdate(BaseModel):
    name: Text | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    status: Literal["active", "suspended"] | None = Field(
        default=None, description="'suspended' = ระงับ (ยืมเพิ่มไม่ได้), 'active' = ใช้งานได้"
    )


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    member_id: str
    name: str
    phone: str | None
    email: str | None
    status: Literal["active", "suspended"]
    joined_at: UtcDatetime


# ---------------------------------------------------------------- ยืม / คืน


class LoanCreate(BaseModel):
    book_id: Id = Field(examples=["B001"])
    member_id: Id = Field(examples=["M001"])
    due_at: datetime | None = Field(
        default=None, description="วันกำหนดคืน ถ้าไม่ระบุ = วันยืม + 14 วัน"
    )


class LoanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    loan_id: int
    book_id: str
    member_id: str
    borrowed_at: UtcDatetime
    due_at: UtcDatetime
    returned_at: UtcDatetime | None

    @computed_field
    @property
    def is_overdue(self) -> bool:
        """ยังไม่คืนและเลยวันกำหนดคืนแล้ว"""
        return self.returned_at is None and self.due_at < now()


class ErrorOut(BaseModel):
    detail: str = Field(examples=["หนังสือเล่มนี้ถูกยืมอยู่ ต้องคืนก่อนจึงจะยืมใหม่ได้"])
