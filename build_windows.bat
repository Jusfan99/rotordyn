@echo off
REM ==========================================
REM  RotorDyn Windows .exe 一键打包脚本
REM ==========================================
REM  使用方法:
REM    1. 安装 Python 3.12+  (https://www.python.org/downloads/)
REM    2. 把项目拷贝到 Windows 电脑
REM    3. 双击运行 build_windows.bat  或在 cmd 中运行
REM ==========================================

echo.
echo ====================================
echo  RotorDyn Windows Build Script
echo ====================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.12+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] Failed to create venv
    pause
    exit /b 1
)

echo [2/4] Installing dependencies...
.venv\Scripts\pip install --upgrade pip
.venv\Scripts\pip install -e .
.venv\Scripts\pip install pyinstaller pywebview
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [3/4] Building .exe with PyInstaller...
.venv\Scripts\pyinstaller main.py ^
    --name RotorDyn ^
    --onedir ^
    --windowed ^
    --noconfirm ^
    --clean ^
    --collect-all nicegui ^
    --hidden-import plotly ^
    --hidden-import engineio.async_drivers.aiohttp
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed
    pause
    exit /b 1
)

echo.
echo [4/4] Build complete!
echo.
echo ====================================
echo  Output: dist\RotorDyn\RotorDyn.exe
echo ====================================
echo.
echo Double-click RotorDyn.exe to run!
echo.

pause
