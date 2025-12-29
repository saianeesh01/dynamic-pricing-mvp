@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo.
echo ========================================
echo Starting Pricing Dashboard...
echo ========================================
echo.
echo The dashboard will open at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.
streamlit run pricing_dashboard.py
pause


