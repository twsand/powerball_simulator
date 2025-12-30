#!/bin/bash
# Run Powerball Simulator with Cloudflare Tunnel for internet access

set -e

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared not found. Installing..."
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o /tmp/cloudflared
    chmod +x /tmp/cloudflared
    sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
    echo "✅ cloudflared installed"
fi

# Activate virtual environment
source venv/bin/activate

# Start the tunnel in background and capture URL
echo "🌐 Starting Cloudflare Tunnel..."
cloudflared tunnel --url http://localhost:5000 2>&1 | tee /tmp/tunnel.log &
TUNNEL_PID=$!

# Wait for tunnel URL to appear
sleep 5
TUNNEL_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/tunnel.log | head -1)

if [ -z "$TUNNEL_URL" ]; then
    echo "⏳ Waiting for tunnel URL..."
    sleep 5
    TUNNEL_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/tunnel.log | head -1)
fi

echo ""
echo "=============================================="
echo "🎱 POWERBALL SIMULATOR"
echo "=============================================="
echo ""
echo "📱 LOCAL URL:  http://$(hostname -I | awk '{print $1}'):5000"
echo "🌐 PUBLIC URL: $TUNNEL_URL"
echo ""
echo "Share the PUBLIC URL with remote players!"
echo "=============================================="
echo ""

# Cleanup function
cleanup() {
    echo "Shutting down..."
    kill $TUNNEL_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Run the main app
python main.py

# Cleanup on exit
kill $TUNNEL_PID 2>/dev/null
