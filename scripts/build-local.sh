#!/bin/bash
# 로컬 Docker 빌드 스크립트 (GitHub Actions 없이 직접 빌드/푸시)
# 사용법: ./scripts/build-local.sh [--push]

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

VERSION=$(cat VERSION | tr -d '[:space:]')
PUSH=false
[ "$1" = "--push" ] && PUSH=true

echo "=== eztag v$VERSION 로컬 빌드 ==="
echo ""

echo "[1/2] Backend 빌드..."
docker build -t zardkim/eztag-backend:$VERSION \
             -t zardkim/eztag-backend:latest \
             backend/

echo "[2/2] Frontend 빌드..."
docker build -t zardkim/eztag-frontend:$VERSION \
             -t zardkim/eztag-frontend:latest \
             frontend/

echo ""
echo "빌드 완료: v$VERSION"

if [ "$PUSH" = true ]; then
  echo ""
  echo "Docker Hub에 푸시 중..."
  docker push zardkim/eztag-backend:$VERSION
  docker push zardkim/eztag-backend:latest
  docker push zardkim/eztag-frontend:$VERSION
  docker push zardkim/eztag-frontend:latest
  echo "푸시 완료"
else
  echo ""
  echo "푸시하려면: ./scripts/build-local.sh --push"
fi
