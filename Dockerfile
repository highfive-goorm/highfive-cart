FROM python:3.12

# 1-1. 타임존 설정 (tzdata 설치 + Asia/Seoul로 링크)
RUN apt-get update && apt-get install -y tzdata \
  && ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
  && echo "Asia/Seoul" > /etc/timezone \
  && apt-get clean && rm -rf /var/lib/apt/lists/*
  
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]