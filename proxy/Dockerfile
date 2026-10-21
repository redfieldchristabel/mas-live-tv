FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    nodejs \
    npm \
    chromium \
    fonts-liberation \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN npm init -y >/dev/null 2>&1 && npm install ws --no-audit --no-fund

COPY proxy/proxy.py proxy/refresh_tokens.js ./
COPY proxy/entrypoint.sh ./
RUN chmod +x entrypoint.sh

# channels.json is mounted at /data
VOLUME ["/data"]

ENV PORT=8080 \
    REFRESH_SECONDS=1200 \
    PAGE_SECONDS=12 \
    CDP_PORT=9222

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
