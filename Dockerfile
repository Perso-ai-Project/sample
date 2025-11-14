FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 전체 backend 폴더 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 앱 실행 
CMD ["python", "-m", "uvicorn", "app.main_standalone:app, "--host", "0.0.0.0", "--port", "8000"]