# syntax=docker/dockerfile:1.7

FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

WORKDIR /app

RUN addgroup --system dhurandhar \
    && adduser --system --ingroup dhurandhar --home /app dhurandhar

COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-build /build/frontend/dist ./frontend/dist/
COPY output/evidence/codex-live-run-2026-07-16-gpt-5.6-sol.jsonl ./evidence/codex-live-run-2026-07-16-gpt-5.6-sol.jsonl

RUN mkdir -p /app/data /app/workspaces \
    && chown -R dhurandhar:dhurandhar /app/data /app/workspaces \
    && chown -R root:root /app/evidence \
    && chmod 0555 /app/evidence \
    && chmod 0444 /app/evidence/codex-live-run-2026-07-16-gpt-5.6-sol.jsonl

USER dhurandhar
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host ${APP_HOST:-0.0.0.0} --port ${PORT:-${APP_PORT:-8000}}"]
