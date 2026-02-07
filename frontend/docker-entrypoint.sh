#!/bin/sh
# Ensure node_modules are populated (handles fresh anonymous volumes)
if [ ! -d "/app/node_modules/.package-lock.json" ] && [ ! -f "/app/node_modules/.package-lock.json" ]; then
  echo "Installing dependencies..."
  npm install
fi
exec "$@"
