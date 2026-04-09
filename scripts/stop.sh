#!/usr/bin/env bash
set -e

CONTAINER_NAME="pm-app"

if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
  echo "Stopping $CONTAINER_NAME..."
  docker stop "$CONTAINER_NAME"
fi

if docker ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
  echo "Removing $CONTAINER_NAME..."
  docker rm "$CONTAINER_NAME"
fi

echo "Done."
