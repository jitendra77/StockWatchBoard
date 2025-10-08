@echo off

REM Display current directory
echo Current directory: %cd%

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH!
    pause
    exit /b 1
)

REM Check if Streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Error: Streamlit is not installed!
    echo Run: pip install streamlit
    pause
    exit /b 1
)

REM Launch Streamlit app
echo Starting Streamlit app...
REM Replace "app.py" with your actual Streamlit file name
streamlit run app.py --server.port 5000

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Streamlit app encountered an error.
    pause
)

REM Launch Streamlit app
echo Starting Streamlit app...
REM Replace "app.py" with your actual Streamlit file name

REM Start Streamlit in background and open Chrome
echo Opening Chrome browser...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://localhost:8501"

REM Wait a moment for Chrome to start, then launch Streamlit
timeout /t 2 /nobreak >nul
streamlit run app.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Streamlit app encountered an error.
    pause
)