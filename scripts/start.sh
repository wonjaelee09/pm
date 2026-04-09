#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="pm-app"
CONTAINER_NAME="pm-app"
PORT=8000
DATA_DIR="$PROJECT_DIR/data"

mkdir -p "$DATA_DIR"

echo "Building $IMAGE_NAME..."
docker build -t "$IMAGE_NAME" "$PROJECT_DIR"

echo "Starting container on port $PORT..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --env-file "$PROJECT_DIR/.env" \
  -e DB_PATH=/app/data/kanban.db \
  -p "$PORT:8000" \
  -v "$DATA_DIR:/app/data" \
  "$IMAGE_NAME"

echo "Running at http://localhost:$PORT"
