#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_DIR="$ROOT_DIR/AbletonMCP_Remote_Script/"
TARGET_DIR="/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts/AbletonMCP_Remote_Script/"
APP_NAME="Ableton Live 12 Suite"

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Source Remote Script not found: $SOURCE_DIR" >&2
  exit 1
fi

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Target Remote Script directory not found: $TARGET_DIR" >&2
  exit 1
fi

echo "Syncing Remote Script into Ableton..."
rsync -a --delete --exclude '__pycache__' "$SOURCE_DIR" "$TARGET_DIR"

if osascript -e "tell application \"$APP_NAME\" to if it is running then return 1 else return 0" | grep -q "1"; then
  echo "Quitting $APP_NAME..."
  osascript -e "tell application \"$APP_NAME\" to quit"
  for _ in {1..60}; do
    if osascript -e "tell application \"$APP_NAME\" to if it is running then return 1 else return 0" | grep -q "0"; then
      break
    fi
    sleep 1
  done
fi

echo "Launching $APP_NAME..."
open -a "$APP_NAME"

echo "Waiting for Ableton to finish launching..."
sleep 12

echo "Remote Script sync and Ableton reload complete."
