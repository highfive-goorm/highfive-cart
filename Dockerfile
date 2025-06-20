FROM python:3.12-slim-bookworm

# 작업 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=ETC/UTC

# 런타임에 필요한 시스템 패키지 설치
# 타임존 설정을 위해 tzdata는 포함합니다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tzdata \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 이미지 내 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 의존성 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY app/ ./app/

# Non-root 사용자 생성 및 설정
RUN useradd --system --create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

# 서비스 포트 노출 (각 서비스에 맞게 수정)
EXPOSE 8002

# 컨테이너 시작 명령어 (각 서비스의 포트 및 시작 설정에 맞게 수정)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--log-level", "info", "--access-log"]