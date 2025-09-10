# PowerShell script для запуска админ-панели Alex Orator Bot

Write-Host "Starting Admin Panel for Alex Orator Bot..." -ForegroundColor Green
Write-Host ""

# Проверяем, установлен ли Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again." -ForegroundColor Yellow
    Read-Host "Press Enter to continue"
    exit 1
}

# Проверяем, установлен ли Streamlit
try {
    $streamlitVersion = streamlit --version 2>&1
    Write-Host "✅ Streamlit found: $streamlitVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Streamlit not found. Installing..." -ForegroundColor Yellow
    pip install streamlit
}

# Устанавливаем зависимости
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Запускаем админ-панель
Write-Host ""
Write-Host "Starting Admin Panel..." -ForegroundColor Green
Write-Host "Open your browser and go to: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""

streamlit run admin_app.py --server.port 8501 --server.address localhost
