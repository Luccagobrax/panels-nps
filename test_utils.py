"""
Testes unitários para as funções auxiliares do Dashboard NPS
Execute: pytest test_utils.py
"""

import pytest
import pandas as pd
import numpy as np
from utils import (
    calcular_nps,
    calcular_nps_ponderado,
    calcular_distribuicao_classificacao,
    formatar_numero,
    formatar_data,
    truncar_texto,
    get_cor_nps,
    validar_dados
)


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def df_exemplo():
    """
    DataFrame de exemplo para testes.
    """
    return pd.DataFrame({
        'customer_id': [1, 2, 3, 4, 5],
        'customer_name': ['Empresa A', 'Empresa B', 'Empresa C', 'Empresa D', 'Empresa E'],
        'tipo_cliente': ['DAF', 'DAF', 'Multimarcas', 'DAF Montadora', 'DAF'],
        'qtd_frota': [100, 50, 200, 150, 75],
        'nota_media_empresa': [9.5, 7.5, 5.0, 8.0, 10.0],
        'classificacao_empresa': ['Promotor', 'Neutro', 'Detrator', 'Neutro', 'Promotor']
    })


@pytest.fixture
def df_vazio():
    """
    DataFrame vazio para testes de edge cases.
    """
    return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES DE CÁLCULO DE NPS
# ═══════════════════════════════════════════════════════════════════════════════

def test_calcular_nps_basico(df_exemplo):
    """
    Testa cálculo básico de NPS.
    """
    nps = calcular_nps(df_exemplo)
    # 2 promotores (40%) - 1 detrator (20%) = 20%
    assert nps == 20.0


def test_calcular_nps_vazio(df_vazio):
    """
    Testa NPS com DataFrame vazio.
    """
    nps = calcular_nps(df_vazio)
    assert nps == 0.0


def test_calcular_nps_apenas_promotores():
    """
    Testa NPS com 100% promotores.
    """
    df = pd.DataFrame({
        'classificacao_empresa': ['Promotor', 'Promotor', 'Promotor']
    })
    nps = calcular_nps(df)
    assert nps == 100.0


def test_calcular_nps_apenas_detratores():
    """
    Testa NPS com 100% detratores.
    """
    df = pd.DataFrame({
        'classificacao_empresa': ['Detrator', 'Detrator', 'Detrator']
    })
    nps = calcular_nps(df)
    assert nps == -100.0


def test_calcular_nps_ponderado_basico(df_exemplo):
    """
    Testa cálculo de NPS ponderado.
    """
    nps_ponderado = calcular_nps_ponderado(df_exemplo)
    # (9.5*100 + 7.5*50 + 5.0*200 + 8.0*150 + 10.0*75) / 575
    esperado = (950 + 375 + 1000 + 1200 + 750) / 575
    assert abs(nps_ponderado - esperado) < 0.01


def test_calcular_nps_ponderado_vazio(df_vazio):
    """
    Testa NPS ponderado com DataFrame vazio.
    """
    nps_ponderado = calcular_nps_ponderado(df_vazio)
    assert nps_ponderado == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES DE DISTRIBUIÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

def test_calcular_distribuicao_classificacao(df_exemplo):
    """
    Testa cálculo de distribuição de classificação.
    """
    dist = calcular_distribuicao_classificacao(df_exemplo)
    assert dist['Promotor'] == 40.0  # 2/5
    assert dist['Neutro'] == 40.0    # 2/5
    assert dist['Detrator'] == 20.0  # 1/5


def test_calcular_distribuicao_vazio(df_vazio):
    """
    Testa distribuição com DataFrame vazio.
    """
    dist = calcular_distribuicao_classificacao(df_vazio)
    assert dist['Promotor'] == 0
    assert dist['Neutro'] == 0
    assert dist['Detrator'] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES DE FORMATAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

def test_formatar_numero_basico():
    """
    Testa formatação básica de número.
    """
    assert formatar_numero(1000) == "1.000"
    assert formatar_numero(1000.5, 1) == "1.000,5"
    assert formatar_numero(1000, 0, "%") == "1.000%"


def test_formatar_numero_nan():
    """
    Testa formatação de NaN.
    """
    assert formatar_numero(np.nan) == "-"
    assert formatar_numero(pd.NA) == "-"


def test_formatar_data_string():
    """
    Testa formatação de data a partir de string.
    """
    resultado = formatar_data("2026-01-06")
    assert resultado == "06/01/2026"


def test_formatar_data_datetime():
    """
    Testa formatação de data a partir de datetime.
    """
    from datetime import datetime
    data = datetime(2026, 1, 6)
    resultado = formatar_data(data)
    assert resultado == "06/01/2026"


def test_formatar_data_nan():
    """
    Testa formatação de data NaN.
    """
    assert formatar_data(np.nan) == "-"
    assert formatar_data(None) == "-"


def test_truncar_texto_curto():
    """
    Testa truncamento de texto curto (não deve truncar).
    """
    texto = "Texto curto"
    resultado = truncar_texto(texto, 100)
    assert resultado == texto


def test_truncar_texto_longo():
    """
    Testa truncamento de texto longo.
    """
    texto = "A" * 150
    resultado = truncar_texto(texto, 100)
    assert len(resultado) == 103  # 100 chars + "..."
    assert resultado.endswith("...")


def test_truncar_texto_nan():
    """
    Testa truncamento de texto NaN.
    """
    assert truncar_texto(np.nan) == "-"
    assert truncar_texto(None) == "-"


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES DE COR
# ═══════════════════════════════════════════════════════════════════════════════

def test_get_cor_nps_positivo():
    """
    Testa cor para NPS positivo alto.
    """
    from config import COLORS
    cor = get_cor_nps(60)
    assert cor == COLORS['promotor']


def test_get_cor_nps_neutro():
    """
    Testa cor para NPS neutro.
    """
    from config import COLORS
    cor = get_cor_nps(25)
    assert cor == COLORS['neutro']


def test_get_cor_nps_negativo():
    """
    Testa cor para NPS negativo.
    """
    from config import COLORS
    cor = get_cor_nps(-10)
    assert cor == COLORS['detrator']


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES DE VALIDAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

def test_validar_dados_valido(df_exemplo):
    """
    Testa validação de dados válidos.
    """
    valido, mensagem = validar_dados(df_exemplo)
    assert valido is True
    assert mensagem == "OK"


def test_validar_dados_vazio(df_vazio):
    """
    Testa validação de DataFrame vazio.
    """
    valido, mensagem = validar_dados(df_vazio)
    assert valido is False
    assert "vazio" in mensagem.lower()


def test_validar_dados_colunas_faltando():
    """
    Testa validação com colunas faltando.
    """
    df = pd.DataFrame({
        'customer_id': [1, 2],
        'customer_name': ['A', 'B']
        # Faltando colunas obrigatórias
    })
    valido, mensagem = validar_dados(df)
    assert valido is False
    assert "faltando" in mensagem.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTAR TESTES
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])