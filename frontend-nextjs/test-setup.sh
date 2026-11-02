#!/bin/bash

# Test Setup Script for Next.js Frontend
# This script helps verify the setup and test the application

echo "🔍 Testing Next.js Frontend Setup..."
echo ""

# Check Node.js version
echo "1. Checking Node.js version..."
NODE_VERSION=$(node -v)
echo "   ✓ Node.js: $NODE_VERSION"
if ! command -v node &> /dev/null; then
    echo "   ❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check npm
echo "2. Checking npm..."
NPM_VERSION=$(npm -v)
echo "   ✓ npm: $NPM_VERSION"

# Check if node_modules exists
echo "3. Checking dependencies..."
if [ ! -d "node_modules" ]; then
    echo "   ⚠️  node_modules not found. Installing dependencies..."
    npm install
else
    echo "   ✓ Dependencies installed"
fi

# Check for .env.local
echo "4. Checking environment configuration..."
if [ ! -f ".env.local" ]; then
    echo "   ⚠️  .env.local not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env.local
        echo "   ✓ Created .env.local (please update with your API URL)"
    else
        echo "   ⚠️  .env.example not found. Creating default .env.local..."
        echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
        echo "NEXT_PUBLIC_WS_URL=ws://localhost:8000" >> .env.local
        echo "   ✓ Created default .env.local"
    fi
else
    echo "   ✓ .env.local exists"
fi

# Check TypeScript compilation
echo "5. Checking TypeScript compilation..."
if npx tsc --noEmit 2>&1 | grep -q "error"; then
    echo "   ❌ TypeScript errors found:"
    npx tsc --noEmit
    exit 1
else
    echo "   ✓ No TypeScript errors"
fi

# Check if backend is running (optional)
echo "6. Checking backend connection..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✓ Backend is running on http://localhost:8000"
else
    echo "   ⚠️  Backend not reachable at http://localhost:8000"
    echo "      Make sure the backend is running before testing the frontend"
fi

echo ""
echo "✅ Setup check complete!"
echo ""
echo "Next steps:"
echo "1. Update .env.local with your API URL and WebSocket URL"
echo "2. Start the development server: npm run dev"
echo "3. Open http://localhost:3000 in your browser"
echo "4. Sign in with the operator account configured in backend .env"
