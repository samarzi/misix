#!/bin/bash

# MISIX - Запуск полного приложения
echo "🤖 Запуск MISIX..."

# Запуск backend в фоне
echo "📡 Запуск backend..."
cd backend
python3 -c "
import asyncio
from app.web.main import create_app
import uvicorn

app = create_app()
uvicorn.run(app, host='0.0.0.0', port=8000)
" &
BACKEND_PID=$!

# Ожидание запуска backend
echo "⏳ Ожидание запуска backend..."
sleep 5

# Запуск frontend (статический misix-minimal)
echo "🌐 Запуск frontend..."
cd ../frontend
python3 -m http.server 5173 &
FRONTEND_PID=$!
cd ..

# Ожидание запуска frontend
echo "⏳ Ожидание запуска frontend..."
sleep 5

echo "✅ MISIX запущен!"
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend: http://localhost:8000"
echo "🤖 Telegram бот активен"
echo ""
echo "Нажмите Ctrl+C для остановки"

# Обработчик сигнала для корректного завершения
trap "echo '🛑 Остановка...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Ожидание завершения
wait
