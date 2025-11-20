#!/bin/bash

echo "🧪 Running Tests..."

# Backend tests
echo "Running Backend Tests..."
cd backend
source venv/bin/activate
pytest tests/ -v

cd ..

# Frontend tests
echo "Running Frontend Tests..."
cd frontend
npm test -- --watchAll=false

cd ..

echo "✅ Tests complete!"
