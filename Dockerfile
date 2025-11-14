FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 최소화 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Python 의존성 설치 (캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    find /usr/local/lib/python3.11 -type d -name '__pycache__' -exec rm -r {} + && \
    find /usr/local/lib/python3.11 -type f -name '*.pyc' -delete && \
    find /usr/local/lib/python3.11 -type f -name '*.pyo' -delete

# 필요한 파일만 복사 (불필요한 파일 제외)
COPY app ./app
COPY .env* ./

# 포트 노출
EXPOSE 8000

# 앱 실행 (경량화)
CMD ["python", "-m", "uvicorn", "app.main_standalone:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]