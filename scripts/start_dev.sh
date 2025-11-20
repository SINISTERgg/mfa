#!/bin/bash

echo "🚀 Starting MFA Authentication System..."

# Start backend in background
echo "Starting Backend..."
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!

cd ..

# Start frontend
echo "Starting Frontend..."
cd frontend
npm start &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ Application started!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Backend: http://localhost:5000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
