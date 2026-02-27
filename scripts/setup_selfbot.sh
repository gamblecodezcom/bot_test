#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="${INSTALL_DIR:-/var/www/html/Runewager}"
ENV_FILE="/etc/runewager-qa.env"
SERVICE_FILE="/etc/systemd/system/runewager-qa.service"

read -r -p "Telegram API ID: " TELEGRAM_API_ID
read -r -p "Telegram API HASH: " TELEGRAM_API_HASH
read -r -p "Telegram phone (E.164, e.g. +15550001111): " TELEGRAM_PHONE
read -r -p "Target bot username (without @): " QA_TARGET_BOT

echo "Choose external AI profile: termux_qwen / termux_deepseek_r1 / deepseek_chat / gemini_free / chatgpt_free"
read -r -p "AI profile [termux_qwen]: " AI_PROVIDER
AI_PROVIDER="${AI_PROVIDER:-termux_qwen}"
read -r -p "AI model override (optional): " AI_MODEL

sudo rsync -a --delete "$ROOT_DIR/" "$INSTALL_DIR/"
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install pyrogram tgcrypto

sudo tee "$ENV_FILE" >/dev/null <<ENV
TELEGRAM_API_ID=$TELEGRAM_API_ID
TELEGRAM_API_HASH=$TELEGRAM_API_HASH
TELEGRAM_PHONE=$TELEGRAM_PHONE
QA_TARGET_BOT=$QA_TARGET_BOT
AI_PROVIDER=$AI_PROVIDER
AI_MODEL=$AI_MODEL
ENV

sudo tee "$SERVICE_FILE" >/dev/null <<UNIT
[Unit]
Description=RuneWager QA Telegram Executor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$INSTALL_DIR/.venv/bin/python -m qa_system.executor --service --root /var/www/html/Runewager
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

echo "Running one-time Telegram login..."
sudo bash -c "set -a; source $ENV_FILE; set +a; $INSTALL_DIR/.venv/bin/python -m qa_system.selfbot_runner --login --session-dir $INSTALL_DIR/qa/runtime"

sudo systemctl daemon-reload
sudo systemctl enable --now runewager-qa.service
sudo systemctl status --no-pager runewager-qa.service || true

echo "Setup complete. Service: runewager-qa.service"
