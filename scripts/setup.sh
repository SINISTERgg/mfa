#!/bin/bash

echo "🚀 Setting up MFA Authentication System..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Backend Setup
echo -e "${BLUE}Setting up Backend...${NC}"
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}Created .env file. Please update with your settings.${NC}"
fi

# Create database
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database created successfully!')"

# Create upload folder
mkdir -p stored_faces

cd ..

# Frontend Setup
echo -e "${BLUE}Setting up Frontend...${NC}"
cd frontend

# Install dependencies
npm install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}Created frontend .env file.${NC}"
fi

cd ..

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "To start the application:"
echo "1. Backend: cd backend && source venv/bin/activate && python app.py"
echo "2. Frontend: cd frontend && npm start"
echo ""
echo "Or use: ./scripts/start_dev.sh"
