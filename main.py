import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.ocr_engine import ocr_engine
from app.router import router

# ── 로깅 설정 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan: 앱 시작/종료 훅 ────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시: OCR 모델 로드
    logger.info("서버 시작 중... OCR 모델을 로딩합니다.")
    ocr_engine.initialize()
    logger.info("서버 준비 완료 ✅")
    yield
    # 종료 시: 필요한 정리 작업
    logger.info("서버 종료 중...")


# ── FastAPI 앱 생성 ───────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "이미지를 업로드하면 EasyOCR을 사용해 텍스트를 추출하는 MLOps API 서버입니다.\n\n"
        "**지원 언어**: 한국어(ko), 영어(en)\n"
        "**지원 형식**: JPG, PNG, BMP, TIFF, WebP"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS 미들웨어 ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용. 운영 시 특정 도메인으로 제한하세요.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 요청 처리 시간 로깅 미들웨어 ────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.1f}ms)")
    return response


# ── 전역 예외 핸들러 ─────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"처리되지 않은 예외: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "내부 서버 오류", "detail": str(exc)},
    )


# ── 라우터 등록 ───────────────────────────────────────────────
app.include_router(router)

# ── 정적 파일 및 UI 제공 ────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", tags=["UI"], include_in_schema=False)
async def serve_ui():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ── 헬스체크 ──────────────────────────────────────────────────
@app.get("/health", tags=["Health"], summary="서버 상태 확인")
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "ocr_languages": settings.ocr_languages,
        "gpu": settings.ocr_gpu,
    }


@app.get("/", tags=["Root"], include_in_schema=False)
async def root():
    return {"message": f"{settings.app_name} v{settings.app_version} 가 실행 중입니다. /docs 에서 API를 확인하세요."}


# ── 직접 실행 ─────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
