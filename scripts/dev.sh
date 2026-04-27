#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

DEFAULT_BACKEND_PORT="${BACKEND_PORT:-5001}"
DEFAULT_FRONTEND_PORT="${FRONTEND_PORT:-5173}"

has_cmd() { command -v "$1" >/dev/null 2>&1; }

pick_lan_ip() {
  if [[ "$(uname -s)" == "Darwin" ]]; then
    ip="$(ipconfig getifaddr en0 2>/dev/null || true)"
    if [[ -z "$ip" ]]; then ip="$(ipconfig getifaddr en1 2>/dev/null || true)"; fi
    echo "$ip"
    return
  fi
  if has_cmd hostname; then
    ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
    echo "$ip"
    return
  fi
  echo ""
}

port_in_use() {
  local port="$1"
  if has_cmd lsof; then
    lsof -i ":$port" >/dev/null 2>&1
    return $?
  fi
  if has_cmd nc; then
    nc -z 127.0.0.1 "$port" >/dev/null 2>&1
    return $?
  fi
  return 1
}

ensure_free_port() {
  local port="$1"
  local name="$2"
  if port_in_use "$port"; then
    echo "⚠️  Порт $port занят ($name)."
    if has_cmd lsof; then
      echo "Процессы:"
      lsof -nP -i ":$port" || true
    fi
    echo "Введите 'k' чтобы убить процессы на порту, или любой другой символ чтобы использовать следующий порт:"
    read -r ans || true
    if [[ "${ans}" == "k" ]]; then
      if has_cmd lsof; then
        pids="$(lsof -t -i ":$port" 2>/dev/null || true)"
        if [[ -n "${pids}" ]]; then
          echo "$pids" | xargs kill -9 || true
          sleep 1
        fi
      fi
    else
      echo $((port + 1))
      return
    fi
  fi
  echo "$port"
}

BACKEND_PORT="$(ensure_free_port "$DEFAULT_BACKEND_PORT" "backend")"
FRONTEND_PORT="$(ensure_free_port "$DEFAULT_FRONTEND_PORT" "frontend")"

LAN_IP="$(pick_lan_ip)"
if [[ -z "${LAN_IP}" ]]; then
  LAN_IP="127.0.0.1"
fi

echo "Backend:  http://127.0.0.1:${BACKEND_PORT}  (LAN: http://${LAN_IP}:${BACKEND_PORT})"
echo "Frontend: http://127.0.0.1:${FRONTEND_PORT}  (LAN: http://${LAN_IP}:${FRONTEND_PORT})"
echo "QR Origin (пример): http://${LAN_IP}:${FRONTEND_PORT}"
echo

echo "▶️  Запуск backend..."
(
  cd "$BACKEND_DIR"
  export PYTHONPATH=.
  export PORT="$BACKEND_PORT"
  python3 app.py
) &
BACK_PID=$!

echo "▶️  Запуск frontend..."
(
  cd "$FRONTEND_DIR"
  export VITE_PROXY_TARGET="http://127.0.0.1:${BACKEND_PORT}"
  npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT"
) &
FRONT_PID=$!

echo
echo "✅ Запущено."
echo "- Frontend (LAN): http://${LAN_IP}:${FRONTEND_PORT}"
echo "- Backend  (LAN): http://${LAN_IP}:${BACKEND_PORT}"
echo
echo "Остановка: Ctrl+C"

trap 'kill $BACK_PID $FRONT_PID 2>/dev/null || true' INT TERM
wait

