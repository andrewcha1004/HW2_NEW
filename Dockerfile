# 1단계: 빌드용 기본 이미지 (slim 버전으로 최적화)
FROM python:3.10-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    EASYOCR_MODULE_PATH=/app/models

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (EasyOCR/OpenCV 실행에 필요)
# libgl1-mesa-glx, libglib2.0-0은 OpenCV의 필수 런타임 라이브러리입니다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
COPY requirements.txt .

# pip 캐시를 활용하여 빌드 속도 개선
# CPU 전용 torch를 설치하여 이미지 크기 축소 (사용자 환경이 CPU일 가능성이 높으므로)
RUN pip install --no-cache-dir torch==2.2.2 torchvision==0.17.2 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 모델 사전 다운로드 (컨테이너 실행 시 지연 방지)
# 한국어(ko)와 영어(en) 모델을 빌드 시점에 미리 다운로드합니다.
RUN python -c "import easyocr; easyocr.Reader(['ko', 'en'])"

# 비루트(non-root) 사용자 보안 설정
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# 포트 개방
EXPOSE 8000

# 서버 실행 명령
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
