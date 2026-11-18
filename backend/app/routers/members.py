from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import services
from ..database import get_db
from ..schemas import ErrorOut, LoanOut, MemberCreate, MemberOut, MemberUpdate

router = APIRouter(prefix="/members", tags=["สมาชิก"])

NOT_FOUND = {404: {"model": ErrorOut, "description": "ไม่พบสมาชิก"}}


@router.get("", response_model=list[MemberOut], summary="ค้นหาสมาชิก")
def list_members(q: str | None = None, db: Session = Depends(get_db)):
    """ค้นจากรหัส ชื่อ เบอร์โทร หรืออีเมล (ไม่ระบุ q = ทั้งหมด)"""
    return services.list_members(db, q)


@router.post(
    "",
    response_model=MemberOut,
    status_code=201,
    summary="เพิ่มสมาชิก",
    responses={409: {"model": ErrorOut, "description": "รหัสสมาชิกซ้ำ"}},
)
def create_member(body: MemberCreate, db: Session = Depends(get_db)):
    return services.create_member(db, **body.model_dump())


@router.get("/{member_id}", response_model=MemberOut, summary="ดูสมาชิก", responses=NOT_FOUND)
def get_member(member_id: str, db: Session = Depends(get_db)):
    return services.get_member(db, member_id)


@router.put(
    "/{member_id}", response_model=MemberOut, summary="แก้ไขหรือระงับสมาชิก", responses=NOT_FOUND
)
def update_member(member_id: str, body: MemberUpdate, db: Session = Depends(get_db)):
    """ส่ง status='suspended' เพื่อระงับ หรือ 'active' เพื่อเปิดใช้งานอีกครั้ง"""
    fields = body.model_dump(exclude_unset=True)
    for required in ("name", "status"):
        if fields.get(required) is None:
            fields.pop(required, None)  # ฟิลด์เหล่านี้ห้ามว่าง
    return services.update_member(db, member_id, **fields)


@router.get(
    "/{member_id}/loans",
    response_model=list[LoanOut],
    summary="ประวัติการยืมของสมาชิก",
    responses=NOT_FOUND,
)
def member_loans(member_id: str, db: Session = Depends(get_db)):
    return services.member_loans(db, member_id)
