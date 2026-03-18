#!/bin/bash
set -e

echo "=== WhiteVPN Installation ==="

# Update system
apt-get update
apt-get install -y python3-venv python3-pip

# Create directory
mkdir -p /opt/whitevpn
cd /opt/whitevpn

# Copy files (assumes files are already in /opt/whitevpn)
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup systemd services
echo "Setting up systemd services..."
cp deploy/whitevpn-bot.service /etc/systemd/system/
cp deploy/whitevpn-api.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable whitevpn-bot
systemctl enable whitevpn-api

echo "Starting services..."
systemctl start whitevpn-bot
systemctl start whitevpn-api

echo "=== Installation complete ==="
echo "Bot status: $(systemctl is-active whitevpn-bot)"
echo "API status: $(systemctl is-active whitevpn-api)"
echo ""
echo "Check logs:"
echo "  journalctl -u whitevpn-bot -f"
echo "  journalctl -u whitevpn-api -f"
