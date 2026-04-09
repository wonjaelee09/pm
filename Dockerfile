# Stage 1: build the Next.js frontend
FROM node:22-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python dependencies (uses lock file for reproducible builds)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-cache

# Copy backend source
COPY backend/ ./

# Copy built frontend (replaces placeholder static/)
COPY --from=frontend-builder /frontend/out/ ./static/

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
