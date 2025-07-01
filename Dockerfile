# 1. 베이스 이미지 선택
FROM python:3.12-slim

# 2. 작업 디렉터리 설정
WORKDIR /app

# 3. 파이썬 의존성 먼저 복사 & 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 소스 코드 복사
COPY *.py ./

# 5. 모델 폴더 복사
COPY policy-impl-classifier/ ./policy-impl-classifier/

# 6. 포트 설정 (FastAPI로 설정)
EXPOSE 8000

# 7. 서비스 실행 커맨드
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
