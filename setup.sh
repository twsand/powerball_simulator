#!/bin/bash
# Powerball Simulator - Raspberry Pi Setup Script
# Run this once after transferring files to the Pi

set -e

echo "🎱 Powerball Simulator Setup"
echo "============================"

# Update system
echo "📦 Updating system packages..."
sudo apt-get update

# Install system dependencies for Pygame
echo "🎮 Installing Pygame dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-pygame \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Make scripts executable
chmod +x main.py
chmod +x run_with_tunnel.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the simulator (local only):"
echo "  cd $(pwd)"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "To run with internet access (remote players):"
echo "  ./run_with_tunnel.sh"
echo ""
echo "To run on boot, see README.md for systemd service instructions."
