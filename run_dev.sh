#!/usr/bin/env bash
# 本地开发一键启动：先后台起 FastAPI 后端，再起 Vite 前端（代理 /api 到 8000）。
# 用法：bash run_dev.sh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "==> 启动后端 (FastAPI :8000)"
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    已生成 backend/.env，请填入 MINIMAX_API_KEY 与数据库凭据"
fi
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
UV_PID=$!
trap 'kill $UV_PID 2>/dev/null' EXIT

echo "==> 启动前端 (Vite :5173)"
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then
  npm install
fi
npm run dev -- --host 0.0.0.0 --port 5173

wait
