#!/bin/bash
# eztag 업데이트 스크립트
# 사용법: ./scripts/update.sh [버전]
#   최신 버전: ./scripts/update.sh
#   특정 버전: ./scripts/update.sh 0.5.0

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

VERSION="${1:-latest}"

echo "=== eztag 업데이트: $VERSION ==="
echo ""

# .env 파일 확인
if [ ! -f .env ]; then
  echo "[!] .env 파일이 없습니다."
  echo "    cp env.sample .env 후 설정을 수정해 주세요."
  exit 1
fi

# data/library 디렉토리 확인
if [ ! -d data/library ]; then
  mkdir -p data/library
  echo "[+] data/library 폴더 생성"
fi

# 이미지 풀
echo "[1/3] 최신 이미지 다운로드..."
VERSION="$VERSION" docker compose pull

# 컨테이너 재시작
echo "[2/3] 컨테이너 재시작..."
VERSION="$VERSION" docker compose up -d --remove-orphans

# 상태 확인
echo "[3/3] 상태 확인..."
sleep 3
docker compose ps

echo ""
echo "업데이트 완료!"
echo "접속 주소: http://$(hostname -I | awk '{print $1}'):$(grep FRONTEND_PORT .env | cut -d= -f2 | tr -d ' ' || echo 5850)"
