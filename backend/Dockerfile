FROM python:3.11-slim

WORKDIR /app

# psycopg2-binary 는 wheel 배포판이라 libpq-dev·gcc 가 필요 없다 (제거).
# curl·gnupg 는 아래 PGDG 저장소 등록에 필요하므로 유지한다.
#
# ⚠ PGDG 저장소 코드네임은 베이스 이미지의 Debian 코드네임과 반드시 일치해야 한다.
#    python:3.11-slim 은 trixie(Debian 13) 로 올라갔다 → bookworm-pgdg 사용 시
#    libpq5 의존성(libldap-2.5-0)이 풀리지 않아 빌드가 깨진다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
       | gpg --dearmor -o /usr/share/keyrings/postgresql-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/postgresql-archive-keyring.gpg] \
       https://apt.postgresql.org/pub/repos/apt trixie-pgdg main" \
       > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update && apt-get install -y --no-install-recommends \
       postgresql-client-15 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

EXPOSE 18011

ENTRYPOINT ["/app/entrypoint.sh"]
