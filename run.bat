@echo off
REM ═══════════════════════════════════════════════════════════════════════════════
REM Run Script - Dashboard NPS Gobrax (Windows)
REM ═══════════════════════════════════════════════════════════════════════════════

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║              Dashboard NPS - Gobrax - Iniciando              ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Verificar se o ambiente virtual existe
if not exist "venv" (
    echo ❌ Ambiente virtual nao encontrado!
    echo.
    echo Execute primeiro: setup.bat
    echo.
    pause
    exit /b 1
)

REM Ativar ambiente virtual
call venv\Scripts\activate.bat

REM Executar Streamlit
echo 🚀 Iniciando Dashboard NPS...
echo.
echo O dashboard abrira automaticamente no navegador.
echo URL: http://localhost:8501
echo.
echo Pressione Ctrl+C para parar o servidor.
echo.
echo ═══════════════════════════════════════════════════════════════
echo.

streamlit run app.py