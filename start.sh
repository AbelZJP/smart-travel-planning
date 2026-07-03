#!/bin/bash
# 一键启动开发服务器（后端 + 前端）
# 用法: bash start.sh

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🌍 智能旅行规划 — 开发服务器启动"
echo "================================"

# 启动后端
echo ""
echo "📦 启动后端 (FastAPI :8000)..."
cd "$ROOT_DIR/backend"

if [ ! -d "venv" ]; then
    echo "  创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  后端 PID: $BACKEND_PID"

# 等待后端就绪
sleep 2
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✅ 后端已就绪"
else
    echo "  ⚠️ 后端启动中..."
fi

# 启动前端
echo ""
echo "📦 启动前端 (Vite :3000)..."
cd "$ROOT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    echo "  安装依赖..."
    npm install --silent
fi

npm run dev &
FRONTEND_PID=$!
echo "  前端 PID: $FRONTEND_PID"

echo ""
echo "================================"
echo "✅ 启动完成！"
echo "  前端: http://localhost:3000/travel"
echo "  后端: http://localhost:8000"
echo "  健康: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "================================"

# 捕获退出信号，清理子进程
trap "echo ''; echo '🛑 停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
