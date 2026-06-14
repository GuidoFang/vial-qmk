@echo off
chcp 65001 >nul
echo ============================================
echo   Vial 固件配置器 — 构建脚本
echo ============================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: 安装依赖
echo [1/3] 安装依赖...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

:: 打包 EXE
echo [2/3] 打包 EXE（PyInstaller）...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "VialConfigurator" ^
    --add-data "src;src" ^
    main.py

if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo [3/3] 完成！
echo.
echo 输出文件：dist\VialConfigurator.exe
echo.
pause
