@echo off
REM ═══════════════════════════════════════════════════════════════════════════════
REM Setup Script - Dashboard NPS Gobrax (Windows)
REM ═══════════════════════════════════════════════════════════════════════════════

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║         Dashboard NPS - Gobrax - Setup Automatico            ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Verificar Python
echo [1/4] Verificando instalacao do Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nao encontrado! Instale Python 3.9+ em https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python encontrado!
echo.

REM Criar ambiente virtual
echo [2/4] Criando ambiente virtual...
if not exist "venv" (
    python -m venv venv
    echo ✅ Ambiente virtual criado!
) else (
    echo ℹ️  Ambiente virtual ja existe
)
echo.

REM Ativar ambiente virtual e instalar dependencias
echo [3/4] Instalando dependencias...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo ✅ Dependencias instaladas!
echo.

REM Verificar credenciais
echo [4/4] Verificando configuracao de credenciais...
if not exist ".env" (
    echo ⚠️  Arquivo .env nao encontrado
    echo.
    echo Por favor, configure suas credenciais do BigQuery:
    echo.
    echo 1. Copie o arquivo .env.example para .env
    echo 2. Edite .env e adicione o caminho para seu service account JSON
    echo.
    echo Ou execute: gcloud auth application-default login
    echo.
) else (
    echo ✅ Arquivo .env encontrado
)
echo.

echo ═══════════════════════════════════════════════════════════════
echo.
echo ✅ Setup concluido!
echo.
echo Proximos passos:
echo 1. Configure suas credenciais do BigQuery (se ainda nao fez)
echo 2. Execute: run.bat
echo    Ou: streamlit run app.py
echo.
echo ═══════════════════════════════════════════════════════════════
echo.
pause