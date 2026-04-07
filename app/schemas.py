from pydantic import BaseModel, Field
from typing import List


class BoundingBox(BaseModel):
    """텍스트 블록의 위치 정보"""
    text: str = Field(..., description="인식된 텍스트")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 (0~1)")
    bbox: List[List[int]] = Field(..., description="[[x1,y1],[x2,y2],[x3,y3],[x4,y4]] 형태의 좌표")


class OCRResponse(BaseModel):
    """OCR API 응답 스키마"""
    success: bool = Field(True, description="처리 성공 여부")
    filename: str = Field(..., description="업로드된 파일명")
    full_text: str = Field(..., description="추출된 전체 텍스트 (공백 구분)")
    blocks: List[BoundingBox] = Field(..., description="개별 텍스트 블록 목록")
    language: List[str] = Field(..., description="사용된 OCR 언어 목록")
    total_blocks: int = Field(..., description="인식된 텍스트 블록 수")

    model_config = {"json_schema_extra": {
        "example": {
            "success": True,
            "filename": "sample.png",
            "full_text": "Hello World 안녕하세요",
            "blocks": [
                {
                    "text": "Hello World",
                    "confidence": 0.9823,
                    "bbox": [[10, 5], [120, 5], [120, 30], [10, 30]]
                }
            ],
            "language": ["ko", "en"],
            "total_blocks": 1
        }
    }}


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    success: bool = False
    error: str
    detail: str = ""
