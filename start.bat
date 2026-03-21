@echo off
echo ========================================
echo   PL Predictor - Starting...
echo ========================================
echo.
echo Building frontend...
cd /d "c:\Users\PC\DataScience\pl-web"
call npm run build
if errorlevel 1 (
    echo [ERROR] Frontend build failed!
    pause
    exit /b 1
)
echo.
echo Starting server on http://localhost:5000
cd /d "c:\Users\PC\DataScience\archive\pl-predictor"
python -m src.api
