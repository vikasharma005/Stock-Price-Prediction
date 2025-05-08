$ErrorActionPreference = 'Stop'

Write-Host "Starting StockPredictPro Docker deployment..." -ForegroundColor Cyan

# Check if Docker is running
try {
    $dockerStatus = docker ps -q
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running. Please start Docker Desktop and try again."
    }
    Write-Host "Docker is running correctly" -ForegroundColor Green
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Ensure we're in the project directory
Set-Location (Split-Path $MyInvocation.MyCommand.Path)

# Stop any existing containers
Write-Host "Stopping any existing StockPredictPro containers..." -ForegroundColor Yellow
docker-compose down
Write-Host "Previous containers stopped" -ForegroundColor Green

# Start database first and wait for it to be ready
Write-Host "Starting PostgreSQL database..." -ForegroundColor Yellow
docker-compose up -d db
Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow

$counter = 0
$maxRetries = 30
$dbReady = $false

while (($counter -lt $maxRetries) -and (-not $dbReady)) {
    Start-Sleep -Seconds 2
    $counter++
    
    try {
        $result = docker-compose exec -T db pg_isready -U postgres
        if ($LASTEXITCODE -eq 0) {
            $dbReady = $true
            Write-Host "Database is ready!" -ForegroundColor Green
        } else {
            Write-Host "Database not ready yet, waiting... ($counter/$maxRetries)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Waiting for database to initialize... ($counter/$maxRetries)" -ForegroundColor Yellow
    }
}

if (-not $dbReady) {
    Write-Host "Error: Database did not become ready in time." -ForegroundColor Red
    exit 1
}

# Start Redis
Write-Host "Starting Redis cache..." -ForegroundColor Yellow
docker-compose up -d redis
Start-Sleep -Seconds 5

# Start API service
Write-Host "Starting API service..." -ForegroundColor Yellow
docker-compose up -d api
Write-Host "Waiting for API to initialize..." -ForegroundColor Yellow

$counter = 0
$maxRetries = 30
$apiReady = $false

while (($counter -lt $maxRetries) -and (-not $apiReady)) {
    Start-Sleep -Seconds 2
    $counter++
    
    try {
        $result = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 2
        if ($result.StatusCode -eq 200) {
            $apiReady = $true
            Write-Host "API is ready!" -ForegroundColor Green
        } else {
            Write-Host "API not ready yet, waiting... ($counter/$maxRetries)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Waiting for API to initialize... ($counter/$maxRetries)" -ForegroundColor Yellow
    }
}

# Start the rest of the services
Write-Host "Starting remaining services (Streamlit and Nginx)..." -ForegroundColor Yellow
docker-compose up -d streamlit nginx

Write-Host "`nStockPredictPro is now running!" -ForegroundColor Green
Write-Host "You can access the application at:" -ForegroundColor Cyan
Write-Host "  - Main UI: http://localhost:8501" -ForegroundColor White
Write-Host "  - API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Landing Page: http://localhost" -ForegroundColor White
Write-Host "`nTo view logs, use: docker-compose logs -f [service_name]" -ForegroundColor Cyan
Write-Host "To stop all services, use: docker-compose down" -ForegroundColor Cyan
