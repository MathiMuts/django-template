# syntax=docker/dockerfile:1

# --- INFO: Base Stage ---
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ARG APP_USER=www-data

WORKDIR /app

# Fix for vulnerability in base
RUN apt-get update && apt-get install -y --no-install-recommends \
    libc6 \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# --- INFO: Builder Stage (for Python dependencies) ---
FROM base AS builder
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# --- INFO: Final Stage ---
FROM base AS final

ENV TZ=Europe/Brussels

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-openbsd \
    procps \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN if ! getent group ${APP_USER} >/dev/null; then groupadd -r ${APP_USER}; fi && \
    if ! getent passwd ${APP_USER} >/dev/null; then \
        useradd --no-log-init -r -g ${APP_USER} -d /home/${APP_USER} -m ${APP_USER}; \
    fi
    
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# --- INFO: Application Setup ---
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY . .

RUN mkdir -p /app/staticfiles /app/media /app/theme/static /app/static

RUN chown -R ${APP_USER}:${APP_USER} /app

# Switch to non-root
USER ${APP_USER}

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]