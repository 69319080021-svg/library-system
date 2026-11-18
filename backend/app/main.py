import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

# CORS: อนุญาตให้หน้าเว็บที่อยู่ต่างโดเมน (เช่น Vercel) เรียก API นี้ได้
# ตั้งค่า ALLOWED_ORIGINS ตอน deploy เช่น "https://library-xxx.vercel.app"
# (หลายโดเมนคั่นด้วยจุลภาค) ตอนพัฒนาบนเครื่องไม่ต้องตั้ง เพราะใช้ Vite proxy
allowed_origins = [o.strip().rstrip("/") for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

STATUS_BY_ERROR ={NotFoundError: 404, ConflictError: 409, ValidationError: 422}


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
