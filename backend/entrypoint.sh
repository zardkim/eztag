#!/bin/bash
set -e

echo "=== eztag Backend Starting ==="

# DB 연결 대기
echo "Waiting for PostgreSQL..."
until python -c "
import psycopg2, os, sys
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('PostgreSQL ready')
except Exception as e:
    print(f'Not ready: {e}')
    sys.exit(1)
"; do
    sleep 2
done

# Alembic 마이그레이션
echo "Running database migrations..."
alembic upgrade head

# 데이터 디렉토리 생성
mkdir -p /app/data/covers
mkdir -p /app/data/logs
mkdir -p /app/data/backup

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 18011 --workers 1
