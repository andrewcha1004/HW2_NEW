from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "OCR API Server"
    app_version: str = "1.0.0"
    debug: bool = False

    # EasyOCR settings
    ocr_languages: list[str] = ["ko", "en"]  # 한국어 + 영어
    ocr_gpu: bool = False  # GPU 없으면 False

    # Upload constraints
    max_upload_size_mb: int = 10
    allowed_extensions: list[str] = ["jpg", "jpeg", "png", "bmp", "tiff", "webp"]

    class Config:
        env_file = ".env"


settings = Settings()
