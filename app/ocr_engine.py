import io
import logging
from typing import Optional

import easyocr
import numpy as np
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)


class OCREngine:
    """EasyOCR를 래핑한 싱글톤 OCR 엔진"""

    _instance: Optional["OCREngine"] = None
    _reader: Optional[easyocr.Reader] = None

    def __new__(cls) -> "OCREngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """모델 로드 (앱 시작 시 1회만 실행)"""
        if self._reader is None:
            logger.info(
                f"EasyOCR 모델 로딩 중... (언어: {settings.ocr_languages}, GPU: {settings.ocr_gpu})"
            )
            self._reader = easyocr.Reader(
                lang_list=settings.ocr_languages,
                gpu=settings.ocr_gpu,
                verbose=False,
            )
            logger.info("EasyOCR 모델 로딩 완료")

    def extract_text(self, image_bytes: bytes) -> dict:
        """
        이미지 바이트에서 텍스트를 추출합니다.

        Returns:
            {
                "full_text": str,
                "blocks": [{"text": str, "confidence": float, "bbox": list}],
                "language": list[str]
            }
        """
        if self._reader is None:
            raise RuntimeError("OCR 엔진이 초기화되지 않았습니다.")

        # PIL → NumPy 변환
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)

        # OCR 수행 (detail=1: bbox + 텍스트 + 신뢰도)
        results = self._reader.readtext(image_np, detail=1, paragraph=False)

        blocks = []
        texts = []
        for bbox, text, confidence in results:
            text = text.strip()
            if not text:
                continue
            blocks.append(
                {
                    "text": text,
                    "confidence": round(float(confidence), 4),
                    "bbox": [list(map(int, pt)) for pt in bbox],  # [[x,y], ...]
                }
            )
            texts.append(text)

        return {
            "full_text": " ".join(texts),
            "blocks": blocks,
            "language": settings.ocr_languages,
        }


# 싱글톤 인스턴스
ocr_engine = OCREngine()
