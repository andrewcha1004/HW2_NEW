# OCR API Server

이미지를 업로드하면 **EasyOCR**로 텍스트를 추출하는 FastAPI 기반 서버입니다.

---

## 📁 프로젝트 구조

```
HW2/
├── main.py              # FastAPI 앱 진입점, 미들웨어, lifespan
├── Dockerfile           # Docker 빌드 설정 (최적화됨)
├── .dockerignore        # Docker 빌드 제외 목록
├── requirements.txt     # 의존성 패키지
├── .env.example         # 환경변수 템플릿
├── .github/workflows/
│   └── ci.yml          # GitHub Actions CI/CD 워크플로우 (Self-hosted 배포 포함)
└── app/
    ├── __init__.py
    ├── config.py        # pydantic-settings 기반 설정
    ├── ocr_engine.py    # EasyOCR 싱글톤 래퍼
    ├── router.py        # /ocr/extract 엔드포인트
    └── schemas.py       # 요청/응답 Pydantic 스키마
```

---

## 🐳 Docker & CI/CD 설정

이미지를 빌드하고 로컬 컴퓨터에 자동으로 배포하는 설정이 포함되어 있습니다.

### 1. 로컬에서 Docker 빌드 및 실행
```bash
docker build -t ocr-api .
docker run -p 8000:8000 ocr-api
```

### 2. GitHub Actions 자동 배포 (CD)
GitHub 리포지토리에 코드를 push하면 다음 과정이 자동으로 진행됩니다:
1. **CI**: Docker Hub로 최신 이미지를 빌드하여 push.
2. **CD**: 사용자 컴퓨터(Self-hosted Runner)에서 최신 이미지를 pull하고 컨테이너를 재시작.

> **필수 설정**: GitHub Secrets에 `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`을 등록해야 합니다.

---

## 🚀 실행 방법

### 1. 가상환경 생성 및 패키지 설치

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **주의**: `torch`가 포함되어 있어 설치에 시간이 걸릴 수 있습니다.  
> GPU가 없는 경우 CPU 전용 torch를 사용하면 더 빠릅니다:
> ```bash
> pip install torch==2.2.2 torchvision==0.17.2 --index-url https://download.pytorch.org/whl/cpu
> ```

### 2. 환경변수 설정 (선택)

```bash
cp .env.example .env
# .env 파일을 열어 필요한 값 수정
```

### 3. 서버 실행

```bash
# 개발 모드 (자동 재시작)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 또는 직접 실행
python main.py
```

### 4. API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📡 API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/` | 서버 상태 메시지 |
| GET | `/health` | 헬스체크 |
| POST | `/ocr/extract` | 이미지에서 텍스트 추출 |

### POST /ocr/extract

**요청**: `multipart/form-data` — `file` 필드에 이미지 첨부

**응답 예시**:
```json
{
  "success": true,
  "filename": "sample.png",
  "full_text": "Hello World 안녕하세요",
  "blocks": [
    {
      "text": "Hello World",
      "confidence": 0.9823,
      "bbox": [[10,5],[120,5],[120,30],[10,30]]
    }
  ],
  "language": ["ko", "en"],
  "total_blocks": 1
}
```

### curl 테스트 예시

```bash
curl -X POST http://localhost:8000/ocr/extract \
  -F "file=@/path/to/your/image.png"
```

---

## ⚙️ 주요 설계 결정

| 항목 | 선택 | 이유 |
|------|------|------|
| OCR 라이브러리 | EasyOCR | 설치 간편, 80개 이상 언어, 한국어 우수 |
| 모델 로딩 | 서버 시작 시 1회 (lifespan) | 매 요청마다 로드하면 매우 느림 |
| 싱글톤 패턴 | OCREngine | 메모리 효율, 중복 초기화 방지 |
| GPU | 기본값 False | CPU만으로도 동작; `.env`에서 변경 가능 |
