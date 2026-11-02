# Test Setup Script for Next.js Frontend (PowerShell)
# This script helps verify the setup and test the application

Write-Host "🔍 Testing Next.js Frontend Setup..." -ForegroundColor Cyan
Write-Host ""

# Check Node.js version
Write-Host "1. Checking Node.js version..." -ForegroundColor Yellow
try {
    $nodeVersion = node -v
    Write-Host "   ✓ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check npm
Write-Host "2. Checking npm..." -ForegroundColor Yellow
try {
    $npmVersion = npm -v
    Write-Host "   ✓ npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ npm not found" -ForegroundColor Red
    exit 1
}

# Check if node_modules exists
Write-Host "3. Checking dependencies..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "   ⚠️  node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    npm install
} else {
    Write-Host "   ✓ Dependencies installed" -ForegroundColor Green
}

# Check for .env.local
Write-Host "4. Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env.local")) {
    Write-Host "   ⚠️  .env.local not found. Creating from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env.local"
        Write-Host "   ✓ Created .env.local (please update with your API URL)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  .env.example not found. Creating default .env.local..." -ForegroundColor Yellow
        @"
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
"@ | Out-File -FilePath ".env.local" -Encoding utf8
        Write-Host "   ✓ Created default .env.local" -ForegroundColor Green
    }
} else {
    Write-Host "   ✓ .env.local exists" -ForegroundColor Green
}

# Check TypeScript compilation
Write-Host "5. Checking TypeScript compilation..." -ForegroundColor Yellow
$tscOutput = npx tsc --noEmit 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ TypeScript errors found:" -ForegroundColor Red
    Write-Host $tscOutput
    exit 1
} else {
    Write-Host "   ✓ No TypeScript errors" -ForegroundColor Green
}

# Check if backend is running (optional)
Write-Host "6. Checking backend connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✓ Backend is running on http://localhost:8000" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  Backend not reachable at http://localhost:8000" -ForegroundColor Yellow
    Write-Host "      Make sure the backend is running before testing the frontend" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Setup check complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Update .env.local with your API URL and WebSocket URL"
Write-Host "2. Start the development server: npm run dev"
Write-Host "3. Open http://localhost:3000 in your browser"
Write-Host "4. Sign in with the operator account configured in backend .env"
