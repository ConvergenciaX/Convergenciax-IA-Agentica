# RAG-AgentAI — Automated Installation Script (PowerShell)
# Usage: powershell -ExecutionPolicy Bypass -File INSTALL.ps1

param(
    [string]$PythonEnv = "C:\workspace-vc\env-llm-ia",
    [string]$OllamaModel = "qwen2.5:7b-instruct-q4_K_M"
)

Write-Host "=" * 60
Write-Host "RAG-AgentAI — Installation Script"
Write-Host "=" * 60
Write-Host ""
Write-Host "Configuration:"
Write-Host "  Python environment: $PythonEnv"
Write-Host "  Ollama model: $OllamaModel"
Write-Host ""

# Colors
$colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
}

function Write-Step {
    param([string]$message)
    Write-Host "`n→ $message" -ForegroundColor $colors.Info
}

function Write-Success {
    param([string]$message)
    Write-Host "✓ $message" -ForegroundColor $colors.Success
}

function Write-Error-Msg {
    param([string]$message)
    Write-Host "✗ $message" -ForegroundColor $colors.Error
}

# Step 1: Verify Python environment
Write-Step "Verifying Python environment..."
$pythonExe = Join-Path $PythonEnv "Scripts\python.exe"

if (!(Test-Path $pythonExe)) {
    Write-Error-Msg "Python environment not found at: $PythonEnv"
    Write-Host "Create it with: python -m venv $PythonEnv"
    exit 1
}

$pyVersion = & $pythonExe --version
Write-Success "Python found: $pyVersion"

# Step 2: Upgrade pip
Write-Step "Upgrading pip..."
& $pythonExe -m pip install --upgrade pip -q
Write-Success "pip upgraded"

# Step 3: Install requirements
Write-Step "Installing dependencies from requirements.txt..."
Write-Host "This may take 5-10 minutes (downloading torch, docling, etc.)..."

if (!(Test-Path "requirements.txt")) {
    Write-Error-Msg "requirements.txt not found in current directory"
    exit 1
}

& $pythonExe -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Error-Msg "Failed to install dependencies"
    Write-Host "Try running manually:"
    Write-Host "  $pythonExe -m pip install -r requirements.txt --force-reinstall"
    exit 1
}

Write-Success "Dependencies installed"

# Step 4: Verify Ollama
Write-Step "Checking Ollama..."

try {
    $ollamaList = ollama list 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Ollama is installed and running"
        Write-Host $ollamaList
    }
    else {
        Write-Error-Msg "Ollama command failed. Is it installed?"
        Write-Host "Download from: https://ollama.ai"
        exit 1
    }
}
catch {
    Write-Error-Msg "Ollama not found. Install from https://ollama.ai"
    exit 1
}

# Step 5: Download models (optional)
Write-Host ""
Write-Host "Would you like to download the required models now?" -ForegroundColor $colors.Warning
Write-Host "(This requires Ollama running and will take 15-20 minutes)"
Write-Host ""
$response = Read-Host "Download models? (y/N)"

if ($response -eq "y" -or $response -eq "Y") {
    Write-Step "Downloading embedding model..."
    ollama pull mxbai-embed-large

    Write-Step "Downloading text model (this takes a few minutes)..."
    ollama pull $OllamaModel

    Write-Success "Models downloaded. Verify with: ollama list"
}
else {
    Write-Host "Skipping model download." -ForegroundColor $colors.Warning
    Write-Host "Remember to download manually:"
    Write-Host "  ollama pull mxbai-embed-large"
    Write-Host "  ollama pull $OllamaModel"
}

# Step 6: Verify Chroma Docker
Write-Step "Checking Docker/Chroma..."

$dockerCheck = docker ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error-Msg "Docker not found or not running"
    Write-Host "Install Docker Desktop: https://docker.com/products/docker-desktop"
}
else {
    Write-Success "Docker is running"

    $chromaRunning = docker ps --format "table {{.Image}}" | Select-String "chroma"
    if ($chromaRunning) {
        Write-Success "Chroma Docker is running"
    }
    else {
        Write-Host "Chroma Docker not running. Start it with:" -ForegroundColor $colors.Warning
        Write-Host "  docker run -d -p 8000:8000 chromadb/chroma:latest"
    }
}

# Step 7: Run smoke test
Write-Step "Running smoke test..."
Write-Host ""

& $pythonExe validate_smoke_test.py

if ($LASTEXITCODE -ne 0) {
    Write-Error-Msg "Smoke test failed. Check errors above."
    exit 1
}

Write-Success "Smoke test PASSED"

# Step 8: Summary
Write-Host ""
Write-Host "=" * 60
Write-Host "INSTALLATION COMPLETE" -ForegroundColor $colors.Success
Write-Host "=" * 60
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Make sure Ollama is running: ollama serve (in another terminal)"
Write-Host "2. Make sure Chroma Docker is running: docker run -p 8000:8000 chromadb/chroma:latest"
Write-Host "3. Start the app:"
Write-Host ""
Write-Host "   $pythonExe activate"  # Note: This is pseudo-code for instructions
Write-Host "   & '$pythonEnv\Scripts\Activate.ps1'"
Write-Host "   python app.py"
Write-Host ""
Write-Host "4. Open browser: http://127.0.0.1:5020"
Write-Host ""
Write-Host "Documentation:"
Write-Host "  • SETUP.md  - Environment setup guide"
Write-Host "  • MANUAL.md - Usage guide and architecture"
Write-Host ""
