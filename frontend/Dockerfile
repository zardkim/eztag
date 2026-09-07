# 빌드 산출물(dist)은 정적 파일이라 아키텍처와 무관하다.
# --platform=$BUILDPLATFORM 을 지정해 arm64 이미지를 만들 때도 빌더는 네이티브(amd64)에서 돌린다.
# 이게 없으면 arm64 스테이지가 QEMU 에뮬레이션으로 npm 을 돌리다 멈추는 일이 생긴다
# (v0.10.3 릴리즈에서 "RUN npm install" 이 3시간 넘게 행 걸림).
FROM --platform=$BUILDPLATFORM node:20-alpine AS builder
WORKDIR /app

# lockfile 을 함께 복사하고 npm ci 를 쓴다.
# 예전에는 package.json 만 복사해 npm install 을 돌렸는데, 매번 의존성 트리를
# 레지스트리에서 새로 해석하느라 느리고 재현성도 없었다.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
