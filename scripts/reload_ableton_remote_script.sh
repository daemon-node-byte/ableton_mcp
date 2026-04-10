#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_DIR="$ROOT_DIR/AbletonMCP_Remote_Script/"
TARGET_DIR="/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts/AbletonMCP_Remote_Script/"
APP_NAME="Ableton Live 12 Suite"
APP_EXECUTABLE="/Applications/Ableton Live 12 Suite.app/Contents/MacOS/Live"
SESSION_PATH="${ABLETON_SESSION_PATH:-}"

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

if [[ -z "$SESSION_PATH" ]] && pgrep -f "$APP_EXECUTABLE" >/dev/null; then
  SESSION_PATH="$(cd "$ROOT_DIR" && uv run python - <<'PY' 2>/dev/null || true
from mcp_server.client import AbletonRemoteClient
try:
    path = str(AbletonRemoteClient.from_env().send_command("get_session_path", {}).get("path", "") or "").strip()
    print(path)
except Exception:
    pass
PY
)"
fi

if pgrep -f "$APP_EXECUTABLE" >/dev/null; then
  echo "Quitting $APP_NAME..."
  osascript -e "tell application \"$APP_NAME\" to quit"
  for _ in {1..60}; do
    if ! pgrep -f "$APP_EXECUTABLE" >/dev/null; then
      break
    fi
    sleep 1
  done
  if pgrep -f "$APP_EXECUTABLE" >/dev/null; then
    echo "$APP_NAME did not quit cleanly; terminating process..." >&2
    pkill -TERM -f "$APP_EXECUTABLE" || true
    for _ in {1..20}; do
      if ! pgrep -f "$APP_EXECUTABLE" >/dev/null; then
        break
      fi
      sleep 1
    done
  fi
fi

if [[ -n "$SESSION_PATH" && -f "$SESSION_PATH" ]]; then
  echo "Launching $APP_NAME with saved Live Set..."
  open -a "$APP_NAME" "$SESSION_PATH"
else
  echo "Launching $APP_NAME..."
  open -a "$APP_NAME"
fi

echo "Waiting for Ableton to finish launching..."
sleep 12

echo "Remote Script sync and Ableton reload complete."
