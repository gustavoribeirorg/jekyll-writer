@echo off
echo ========================================================
echo   Compilando Jekyll Writer Desktop para Windows (.exe)
echo ========================================================
echo.

python -m PyInstaller --noconsole --onefile --name "JekyllWriter" --collect-all customtkinter main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   Compilacao concluida com sucesso!
    echo   O executavel standalone esta em: dist\JekyllWriter.exe
    echo ========================================================
) else (
    echo.
    echo [ERRO] Falha na compilacao do PyInstaller.
)
pause
