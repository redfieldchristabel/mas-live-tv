FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    nodejs \
    chromium \
    fonts-liberation \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY proxy.py refresh_tokens.js ./
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# channels.json is mounted at /data
VOLUME ["/data"]

ENV PORT=8080 \
    REFRESH_SECONDS=1200 \
    PAGE_SECONDS=12 \
    CDP_PORT=9222

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
