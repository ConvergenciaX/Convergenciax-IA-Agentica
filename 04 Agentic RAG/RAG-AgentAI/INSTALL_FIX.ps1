# RAG-AgentAI — Fixed Installation Script (Python 3.13)
# Soluciona: pandas, Cython compilation errors
# Usage: powershell -ExecutionPolicy Bypass -File INSTALL_FIX.ps1

$PythonEnv = "C:\workspace-vc\env-llm-ia"

Write-Host "=" * 60
Write-Host "RAG-AgentAI — Installation Fix (Python 3.13)"
Write-Host "=" * 60
Write-Host ""

$pythonExe = Join-Path $PythonEnv "Scripts\python.exe"

if (!(Test-Path $pythonExe)) {
    Write-Host "✗ Python not found at: $PythonEnv" -ForegroundColor Red
    exit 1
}

$pyVersion = & $pythonExe --version
Write-Host "✓ Python: $pyVersion" -ForegroundColor Green

# Step 1: Upgrade pip, setuptools, wheel
Write-Host ""
Write-Host "→ Upgrade pip and build tools..." -ForegroundColor Cyan
& $pythonExe -m pip install --upgrade pip setuptools wheel -q

# Step 2: Clear pip cache
Write-Host "→ Clear pip cache..." -ForegroundColor Cyan
& $pythonExe -m pip cache purge

# Step 3: Install dependencies with explicit wheel-only mode
Write-Host ""
Write-Host "→ Install dependencies (wheels only, no compilation)..." -ForegroundColor Cyan
Write-Host "  This may take 3-5 minutes..."

# Use --only-binary to force wheels only (no source compilation)
$cmd = @(
    "-m", "pip", "install",
    "-r", "requirements.txt",
    "--only-binary", ":all:",
    "-v"
)

& $pythonExe @cmd

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "⚠️  Installation with wheels-only mode failed." -ForegroundColor Yellow
    Write-Host "   Trying with allow-compile mode (may take longer)..." -ForegroundColor Yellow
    Write-Host ""

    # Fallback: allow compilation but with verbose output
    & $pythonExe -m pip install -r requirements.txt --verbose

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "✗ Installation failed" -ForegroundColor Red
        Write-Host ""
        Write-Host "Common solutions:" -ForegroundColor Yellow
        Write-Host "1. Check Python version: $pythonExe --version" -ForegroundColor Gray
        Write-Host "2. Check disk space: ~5 GB free required" -ForegroundColor Gray
        Write-Host "3. Check internet: Try manually: pip install torch" -ForegroundColor Gray
        Write-Host "4. Check antivirus: May block compilation" -ForegroundColor Gray
        exit 1
    }
}

Write-Host ""
Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green

# Step 4: Verify installations
Write-Host ""
Write-Host "→ Verify critical packages..." -ForegroundColor Cyan

$packages = @(
    "langchain",
    "torch",
    "docling",
    "chromadb",
    "gradio"
)

foreach ($pkg in $packages) {
    & $pythonExe -c "import $pkg; print('✓ $pkg')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $pkg" -ForegroundColor Green
    }
    else {
        Write-Host "  ✗ $pkg NOT FOUND" -ForegroundColor Red
    }
}

# Step 5: Run smoke test
Write-Host ""
Write-Host "→ Run smoke test..." -ForegroundColor Cyan
& $pythonExe validate_smoke_test.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "⚠️  Smoke test failed. Check output above." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=" * 60
Write-Host "✓ INSTALLATION COMPLETE" -ForegroundColor Green
Write-Host "=" * 60
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Ensure Ollama is running: ollama serve (in another terminal)"
Write-Host "2. Ensure Chroma Docker is running:"
Write-Host "   docker run -d -p 8000:8000 chromadb/chroma:latest"
Write-Host "3. Start the app:"
Write-Host "   python app.py"
Write-Host ""
Write-Host "Open: http://127.0.0.1:5020"
Write-Host ""
