#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Setup Script - Dashboard NPS Gobrax (Linux/Mac)
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         Dashboard NPS - Gobrax - Setup Automatico            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Verificar Python
echo "[1/4] Verificando instalação do Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado! Instale Python 3.9+"
    exit 1
fi
echo "✅ Python encontrado!"
echo ""

# Criar ambiente virtual
echo "[2/4] Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Ambiente virtual criado!"
else
    echo "ℹ️  Ambiente virtual já existe"
fi
echo ""

# Ativar ambiente virtual e instalar dependências
echo "[3/4] Instalando dependências..."
source venv/bin/activate
pip install -r requirements.txt
echo "✅ Dependências instaladas!"
echo ""

# Verificar credenciais
echo "[4/4] Verificando configuração de credenciais..."
if [ ! -f ".env" ]; then
    echo "⚠️  Arquivo .env não encontrado"
    echo ""
    echo "Por favor, configure suas credenciais do BigQuery:"
    echo ""
    echo "1. Copie o arquivo .env.example para .env"
    echo "2. Edite .env e adicione o caminho para seu service account JSON"
    echo ""
    echo "Ou execute: gcloud auth application-default login"
    echo ""
else
    echo "✅ Arquivo .env encontrado"
fi
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "✅ Setup concluído!"
echo ""
echo "Próximos passos:"
echo "1. Configure suas credenciais do BigQuery (se ainda não fez)"
echo "2. Execute: ./run.sh"
echo "   Ou: streamlit run app.py"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""