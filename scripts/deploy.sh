#!/bin/bash

echo "🚀 Deploying MFA Authentication System..."

# Build frontend
echo "Building Frontend..."
cd frontend
npm run build

cd ..

# Copy build to backend static folder
mkdir -p backend/static
cp -r frontend/build/* backend/static/

echo "✅ Deployment build complete!"
echo "Static files are in backend/static/"
