from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

from . import models  # noqa: F401  (import เพื่อให้ตารางถูกลงทะเบียนกับ Base)
from .database import Base, engine
from .routers import books, loans, members
from .services import ConflictError, LibraryError, NotFoundError, ValidationError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # สร้างตารางที่ยังไม่มี ตอนเปิด server
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Library API",
    description="ระบบห้องสมุดและยืมคืนหนังสือ",
    lifespan=lifespan,
)

STATUS_BY_ERROR = {NotFoundError: 404, ConflictError: 409, ValidationError: 422}


@app.exception_handler(LibraryError)
def handle_library_error(_request: Request, exc: LibraryError):
    """แปลงข้อผิดพลาดทางธุรกิจเป็น HTTP status + ข้อความภาษาไทย"""
    status = next((code for cls, code in STATUS_BY_ERROR.items() if isinstance(exc, cls)), 400)
    return JSONResponse(status_code=status, content={"detail": exc.message})


app.include_router(books.router)
app.include_router(members.router)
app.include_router(loans.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/health", tags=["ระบบ"])
def health():
    return {"status": "ok"}
