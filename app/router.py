import io
import logging
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from gtts import gTTS

from app.config import settings
from app.ocr_engine import ocr_engine
from app.schemas import ErrorResponse, OCRResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])

# 허용 MIME 타입
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/bmp",
    "image/tiff",
    "image/webp",
}
MAX_BYTES = settings.max_upload_size_mb * 1024 * 1024  # MB → bytes


@router.post(
    "/extract",
    response_model=OCRResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 파일 형식 또는 크기"},
        422: {"model": ErrorResponse, "description": "처리 불가 이미지"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    summary="이미지에서 텍스트 추출",
    description=(
        "이미지 파일을 업로드하면 EasyOCR을 사용해 텍스트를 추출합니다.\n\n"
        "- 지원 형식: JPG, PNG, BMP, TIFF, WebP\n"
        f"- 최대 파일 크기: {settings.max_upload_size_mb} MB\n"
        f"- 지원 언어: {', '.join(settings.ocr_languages)}"
    ),
)
async def extract_text(
    file: Annotated[UploadFile, File(description="텍스트를 추출할 이미지 파일")],
) -> OCRResponse:
    # 1. Content-Type 검증
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 파일 형식입니다: {file.content_type}. "
                   f"허용: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    # 2. 파일 읽기 및 크기 검증
    image_bytes = await file.read()
    if len(image_bytes) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"파일 크기가 너무 큽니다 ({len(image_bytes) / 1024 / 1024:.1f} MB). "
                   f"최대 {settings.max_upload_size_mb} MB까지 허용됩니다.",
        )

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="빈 파일입니다.",
        )

    # 3. OCR 수행
    logger.info(f"OCR 시작: {file.filename} ({len(image_bytes)} bytes)")
    try:
        result = ocr_engine.extract_text(image_bytes)
    except Exception as e:
        logger.error(f"OCR 처리 중 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"이미지 처리에 실패했습니다: {str(e)}",
        )

    logger.info(f"OCR 완료: {file.filename} → {len(result['blocks'])}개 블록 인식")

    # 4. 간단한 요약 로직 (첫 2~3문장 또는 일정 길이 추출)
    full_text = result["full_text"]
    if not full_text:
        summary = "인식된 텍스트가 없습니다."
    else:
        # 문장 단위로 나누기 (단순 마침표 기준)
        sentences = [s.strip() for s in full_text.split('.') if s.strip()]
        if len(sentences) > 2:
            summary = ". ".join(sentences[:2]) + "..."
        else:
            summary = full_text[:200] + ("..." if len(full_text) > 200 else "")

    return OCRResponse(
        success=True,
        filename=file.filename or "unknown",
        full_text=full_text,
        summary=summary,
        blocks=result["blocks"],
        language=result["language"],
        total_blocks=len(result["blocks"]),
    )


@router.post("/tts", summary="텍스트를 음성으로 변환")
async def text_to_speech(
    text: Annotated[str, File(description="음성으로 변환할 텍스트")],
) -> StreamingResponse:
    """
    전달받은 텍스트를 gTTS를 이용해 음성(MP3)으로 변환하여 스트리밍합니다.
    """
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="변환할 텍스트가 없습니다.",
        )

    try:
        # 한국어 우선, 영어 포함 (gTTS는 단일 언어 설정이 기본이나 ko가 en도 무난히 읽음)
        tts = gTTS(text=text, lang="ko")
        
        # 메모리 버퍼에 저장
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        return StreamingResponse(
            mp3_fp,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"},
        )
    except Exception as e:
        logger.error(f"TTS 생성 중 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER__ERROR,
            detail=f"음성 변환에 실패했습니다: {str(e)}",
        )
