FROM node:24-bookworm-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/index.html frontend/tsconfig*.json frontend/vite.config.ts ./
COPY frontend/public ./public
COPY frontend/src ./src
RUN npm run build

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng fonts-noto-core ca-certificates && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 brandproof
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
COPY backend ./backend
COPY --from=frontend /frontend/dist ./frontend-dist
RUN uv sync --locked --no-dev && mkdir -p /app/data && chown -R brandproof:brandproof /app
USER brandproof
ENV PATH="/app/.venv/bin:$PATH" BRANDPROOF_DATABASE_URL="sqlite:////app/data/brandproof.db" BRANDPROOF_FRONTEND_DIST=/app/frontend-dist PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/api/v1/health',timeout=3)"
CMD ["python", "-m", "brandproof.serve"]
