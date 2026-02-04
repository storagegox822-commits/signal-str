#!/bin/bash

# Kill existing processes
echo "🛑 Stopping old processes..."
pkill -f "uvicorn app.main:app"
pkill -f "streamlit run dashboard.py"
pkill -f "python app/tg_bot.py"
sleep 2

# Start Backend
echo "🚀 Starting Backend (FastAPI)..."
source .venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Start Telegram Bot
echo "🤖 Starting Telegram Bot..."
nohup python app/tg_bot.py > bot.log 2>&1 &
BOT_PID=$!
echo "✅ Bot started (PID: $BOT_PID)"

# Start Frontend
echo "📊 Starting Dashboard (Streamlit)..."
nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > frontend.log 2>&1 &
FRONT_PID=$!
echo "✅ Dashboard started (PID: $FRONT_PID)"

echo "-----------------------------------"
echo "🎉 Signalizer 3.5 is Running!"
echo "-----------------------------------"
echo "🌍 Dashboard: http://localhost:8501"
echo "🔌 API Docs:  http://localhost:8000/docs"
echo "-----------------------------------"
echo "Logs: backend.log, frontend.log, bot.log"
