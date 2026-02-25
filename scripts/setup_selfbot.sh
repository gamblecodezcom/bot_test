#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="${INSTALL_DIR:-/opt/qa-selfbot}"
ENV_FILE="/etc/qa-selfbot.env"
SERVICE_FILE="/etc/systemd/system/qa-selfbot.service"

read -r -p "Telegram API ID: " TELEGRAM_API_ID
read -r -p "Telegram API HASH: " TELEGRAM_API_HASH
read -r -p "Telegram phone (E.164, e.g. +15550001111): " TELEGRAM_PHONE
read -r -s -p "Telegram 2FA password (leave blank if none): " TELEGRAM_PASSWORD
echo
read -r -p "Telegram OTP code from login message: " TELEGRAM_OTP

echo "Choose AI provider: openai / anthropic / groq / openrouter"
read -r -p "AI provider [openai]: " AI_PROVIDER
AI_PROVIDER="${AI_PROVIDER:-openai}"
read -r -p "AI model override (optional): " AI_MODEL
read -r -s -p "AI API key: " AI_API_KEY
echo

sudo mkdir -p "$INSTALL_DIR"
sudo rsync -a --delete "$ROOT_DIR/" "$INSTALL_DIR/"

python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install telethon

case "$AI_PROVIDER" in
  openai) AI_KEY_NAME="OPENAI_API_KEY" ;;
  anthropic) AI_KEY_NAME="ANTHROPIC_API_KEY" ;;
  groq) AI_KEY_NAME="GROQ_API_KEY" ;;
  openrouter) AI_KEY_NAME="OPENROUTER_API_KEY" ;;
  *) echo "Unsupported provider: $AI_PROVIDER" >&2; exit 1 ;;
esac

sudo tee "$ENV_FILE" >/dev/null <<ENV
TELEGRAM_API_ID=$TELEGRAM_API_ID
TELEGRAM_API_HASH=$TELEGRAM_API_HASH
TELEGRAM_PHONE=$TELEGRAM_PHONE
TELEGRAM_PASSWORD=$TELEGRAM_PASSWORD
TELEGRAM_OTP=$TELEGRAM_OTP
AI_PROVIDER=$AI_PROVIDER
AI_MODEL=$AI_MODEL
$AI_KEY_NAME=$AI_API_KEY
ENV

sudo tee "$SERVICE_FILE" >/dev/null <<UNIT
[Unit]
Description=QA Telegram Selfbot Runner
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$INSTALL_DIR/.venv/bin/python -m qa_system.selfbot_runner --service --session-dir $INSTALL_DIR/data
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

echo "Running one-time Telegram login..."
sudo bash -c "set -a; source "$ENV_FILE"; set +a; "$INSTALL_DIR/.venv/bin/python" -m qa_system.selfbot_runner --login --session-dir "$INSTALL_DIR/data""

sudo systemctl daemon-reload
sudo systemctl enable --now qa-selfbot.service
sudo systemctl status --no-pager qa-selfbot.service || true

echo "Setup complete. Service: qa-selfbot.service"
