#!/bin/bash
set -e

echo "🌶️ Starting ChiliHead OpsManager v2.1..."

# Start Open-WebUI in the background on port 8080
export WEBUI_PORT=8080
bash /app/backend/start.sh &

# Wait for Open-WebUI to be ready
echo "Waiting for Open-WebUI to start..."
for i in {1..30}; do
  if curl -f http://localhost:8080/ > /dev/null 2>&1; then
    echo "✅ Open-WebUI is ready"
    break
  fi
  echo "Waiting... ($i/30)"
  sleep 2
done

# Start simple HTTP server for ChiliHead interface on port 3040
echo "🚀 Starting ChiliHead interface on port 3040..."
cd /app/backend/static/chilihead
python3 -m http.server 3040 &

# Keep container running
wait -n
