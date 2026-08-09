FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# データ永続化用ディレクトリ
RUN mkdir -p /data
ENV DATABASE_URL=sqlite+aiosqlite:////data/chat.db

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
