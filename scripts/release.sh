#!/bin/bash
# eztag 릴리즈 스크립트
# 사용법: ./scripts/release.sh [버전]
#   버전 지정:  ./scripts/release.sh 0.5.0
#   버전 미지정: VERSION 파일의 현재 버전 사용

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# ── 버전 결정 ────────────────────────────────────────────────
if [ -n "$1" ]; then
  NEW_VERSION="$1"
  echo "$NEW_VERSION" > VERSION
  echo "버전 변경: $NEW_VERSION"
else
  NEW_VERSION=$(cat VERSION | tr -d '[:space:]')
  echo "현재 버전 사용: $NEW_VERSION"
fi

TODAY=$(date +%Y-%m-%d)

# ── 버전 파일 동기화 ─────────────────────────────────────────
echo "backend/app/version.py 업데이트..."
cat > backend/app/version.py << EOF
APP_VERSION = "$NEW_VERSION"
APP_NAME = "eztag"
BUILD_DATE = "$TODAY"
EOF

echo "frontend/package.json 업데이트..."
python3 -c "
import json
with open('frontend/package.json', 'r') as f:
    pkg = json.load(f)
pkg['version'] = '$NEW_VERSION'
with open('frontend/package.json', 'w') as f:
    json.dump(pkg, f, indent=2, ensure_ascii=False)
    f.write('\n')
"

echo ""
echo "버전 동기화 완료: v$NEW_VERSION ($TODAY)"
echo ""
echo "다음 단계:"
echo "  1. CHANGELOG.md 업데이트 확인"
echo "  2. git add VERSION CHANGELOG.md backend/app/version.py frontend/package.json"
echo "  3. git commit -m \"chore: release v$NEW_VERSION\""
echo "  4. git tag v$NEW_VERSION"
echo "  5. git push origin main --tags"
echo "     → GitHub Actions가 Docker 빌드 & 릴리즈 자동 실행"
