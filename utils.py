"""
Funções auxiliares para o Dashboard NPS - Gobrax
Cálculos de métricas, formatações e processamento de dados
"""

import pandas as pd
import numpy as np
from datetime import datetime
from config import COLORS, CLASSIFICACAO_EMOJI, FLAG_EMOJI, NOTA_RANGES


# ═══════════════════════════════════════════════════════════════════════════════
# CÁLCULOS DE NPS
# ═══════════════════════════════════════════════════════════════════════════════

def calcular_nps(df: pd.DataFrame) -> float:
    """
    Calcula o NPS geral baseado na classificação das empresas.
    Fórmula: % Promotores - % Detratores

    Args:
        df: DataFrame com coluna 'classificacao_empresa'

    Returns:
        float: NPS calculado (-100 a 100)
    """
    if df.empty:
        return 0.0

    total = len(df)
    promotores = len(df[df['classificacao_empresa'] == 'Promotor'])
    detratores = len(df[df['classificacao_empresa'] == 'Detrator'])

    pct_promotores = (promotores / total) * 100
    pct_detratores = (detratores / total) * 100

    nps = pct_promotores - pct_detratores
    return round(nps, 1)


def calcular_nps_ponderado(df: pd.DataFrame) -> float:
    """
    Calcula o NPS ponderado pela frota.
    Fórmula: (Σ nota_media_empresa × qtd_frota) / Σ qtd_frota

    Args:
        df: DataFrame com colunas 'nota_media_empresa' e 'qtd_frota'

    Returns:
        float: NPS ponderado
    """
    if df.empty or 'qtd_frota' not in df.columns or 'nota_media_empresa' not in df.columns:
        return 0.0

    df_clean = df.dropna(subset=['qtd_frota', 'nota_media_empresa'])

    if df_clean.empty:
        return 0.0

    soma_ponderada = (df_clean['nota_media_empresa'] * df_clean['qtd_frota']).sum()
    soma_frota = df_clean['qtd_frota'].sum()

    if soma_frota == 0:
        return 0.0

    nps_ponderado = soma_ponderada / soma_frota
    return round(nps_ponderado, 2)


def calcular_distribuicao_classificacao(df: pd.DataFrame) -> dict:
    """
    Calcula a distribuição percentual de cada classificação.

    Args:
        df: DataFrame com coluna 'classificacao_empresa'

    Returns:
        dict: {'Promotor': X%, 'Neutro': Y%, 'Detrator': Z%}
    """
    if df.empty:
        return {"Promotor": 0, "Neutro": 0, "Detrator": 0}

    total = len(df)
    distribuicao = {}

    for classif in ['Promotor', 'Neutro', 'Detrator']:
        count = len(df[df['classificacao_empresa'] == classif])
        pct = (count / total) * 100
        distribuicao[classif] = round(pct, 1)

    return distribuicao


# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE FORMATAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

def formatar_numero(valor: float, decimais: int = 0, sufixo: str = "") -> str:
    """
    Formata número para exibição com separadores de milhar.

    Args:
        valor: Número a formatar
        decimais: Casas decimais
        sufixo: Sufixo opcional (%, pontos, etc)

    Returns:
        str: Número formatado
    """
    if pd.isna(valor):
        return "-"

    formato = f"{{:,.{decimais}f}}"
    numero_formatado = formato.format(valor).replace(",", ".")

    return f"{numero_formatado}{sufixo}"


def formatar_data(data) -> str:
    """
    Formata data para exibição em português (DD/MM/YYYY).

    Args:
        data: Data em formato datetime ou string

    Returns:
        str: Data formatada
    """
    if pd.isna(data):
        return "-"

    if isinstance(data, str):
        try:
            data = pd.to_datetime(data)
        except:
            return data

    if isinstance(data, (pd.Timestamp, datetime)):
        return data.strftime("%d/%m/%Y")

    return str(data)


def truncar_texto(texto: str, max_chars: int = 100) -> str:
    """
    Trunca texto adicionando reticências se necessário.

    Args:
        texto: Texto a truncar
        max_chars: Número máximo de caracteres

    Returns:
        str: Texto truncado
    """
    if pd.isna(texto):
        return "-"

    texto = str(texto)

    if len(texto) <= max_chars:
        return texto

    return texto[:max_chars] + "..."


def adicionar_emoji_classificacao(classificacao: str) -> str:
    """
    Adiciona emoji à classificação.

    Args:
        classificacao: 'Promotor', 'Neutro' ou 'Detrator'

    Returns:
        str: Classificação com emoji
    """
    emoji = CLASSIFICACAO_EMOJI.get(classificacao, "")
    return f"{emoji} {classificacao}" if emoji else classificacao


def adicionar_emoji_flag(flag: str) -> str:
    """
    Adiciona emoji à flag de alerta.

    Args:
        flag: 'URGENTE', 'ATENÇÃO' ou 'OK'

    Returns:
        str: Flag com emoji
    """
    emoji = FLAG_EMOJI.get(flag, "")
    return f"{emoji} {flag}" if emoji else flag


# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE COR E ESTILO
# ═══════════════════════════════════════════════════════════════════════════════

def get_cor_nps(nps: float) -> str:
    """
    Retorna a cor adequada baseada no valor do NPS.

    Args:
        nps: Valor do NPS

    Returns:
        str: Código de cor hexadecimal
    """
    if nps >= 50:
        return COLORS['promotor']  # Verde
    elif nps >= 0:
        return COLORS['neutro']    # Amarelo
    else:
        return COLORS['detrator']  # Vermelho


def get_cor_classificacao(classificacao: str) -> str:
    """
    Retorna a cor baseada na classificação.

    Args:
        classificacao: 'Promotor', 'Neutro' ou 'Detrator'

    Returns:
        str: Código de cor hexadecimal
    """
    mapa_cores = {
        'Promotor': COLORS['promotor'],
        'Neutro': COLORS['neutro'],
        'Detrator': COLORS['detrator']
    }
    return mapa_cores.get(classificacao, COLORS['text'])


def get_cor_nota(nota: float) -> str:
    """
    Retorna a cor baseada na nota (0-10).

    Args:
        nota: Nota de 0 a 10

    Returns:
        str: Código de cor hexadecimal
    """
    if nota >= 9:
        return COLORS['promotor']
    elif nota >= 7:
        return COLORS['neutro']
    else:
        return COLORS['detrator']


# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSAMENTO DE DADOS
# ═══════════════════════════════════════════════════════════════════════════════

def criar_distribuicao_notas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria DataFrame com a distribuição de notas de 0 a 10.

    Args:
        df: DataFrame com coluna 'nota_media_empresa'

    Returns:
        pd.DataFrame: DataFrame com colunas 'nota' e 'quantidade'
    """
    if df.empty or 'nota_media_empresa' not in df.columns:
        return pd.DataFrame({'nota': range(11), 'quantidade': [0] * 11})

    # Arredondar notas para inteiro mais próximo
    df_notas = df.copy()
    df_notas['nota_arredondada'] = df_notas['nota_media_empresa'].round().astype(int)

    # Contar frequência de cada nota
    distribuicao = df_notas['nota_arredondada'].value_counts().sort_index()

    # Criar DataFrame completo (0-10)
    todas_notas = pd.DataFrame({'nota': range(11)})
    todas_notas['quantidade'] = todas_notas['nota'].map(distribuicao).fillna(0).astype(int)

    return todas_notas


def calcular_nps_por_segmento(df: pd.DataFrame, coluna_segmento: str) -> pd.DataFrame:
    """
    Calcula NPS para cada valor único de um segmento.

    Args:
        df: DataFrame com dados
        coluna_segmento: Nome da coluna para segmentar

    Returns:
        pd.DataFrame: DataFrame com colunas 'segmento', 'nps', 'quantidade'
    """
    if df.empty or coluna_segmento not in df.columns:
        return pd.DataFrame(columns=['segmento', 'nps', 'quantidade'])

    resultados = []

    for segmento in df[coluna_segmento].dropna().unique():
        df_segmento = df[df[coluna_segmento] == segmento]
        nps = calcular_nps(df_segmento)
        quantidade = len(df_segmento)

        resultados.append({
            'segmento': segmento,
            'nps': nps,
            'quantidade': quantidade
        })

    df_resultado = pd.DataFrame(resultados)
    df_resultado = df_resultado.sort_values('nps', ascending=False)

    return df_resultado


def criar_heatmap_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria matriz para heatmap de NPS por Frota × Tempo de Casa.

    Args:
        df: DataFrame com dados

    Returns:
        pd.DataFrame: Matriz pivotada para heatmap
    """
    if df.empty:
        return pd.DataFrame()

    # Agrupar por faixa_frota e faixa_tempo_casa
    heatmap_data = df.groupby(['faixa_frota', 'faixa_tempo_casa']).agg({
        'nota_media_empresa': 'mean',
        'customer_id': 'count'
    }).reset_index()

    heatmap_data.columns = ['faixa_frota', 'faixa_tempo_casa', 'nps_medio', 'quantidade']

    # Pivotar para criar matriz
    matriz = heatmap_data.pivot(
        index='faixa_frota',
        columns='faixa_tempo_casa',
        values='nps_medio'
    )

    return matriz


def filtrar_detratores_prioritarios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra e ordena detratores por prioridade (urgência e frota).

    Args:
        df: DataFrame completo

    Returns:
        pd.DataFrame: DataFrame filtrado e ordenado
    """
    if df.empty:
        return pd.DataFrame()

    # Filtrar apenas detratores
    df_detratores = df[df['classificacao_empresa'] == 'Detrator'].copy()

    if df_detratores.empty:
        return pd.DataFrame()

    # Criar ordem de prioridade para flag_alerta
    prioridade_flag = {'URGENTE': 1, 'ATENÇÃO': 2, 'OK': 3}
    df_detratores['ordem_flag'] = df_detratores['flag_alerta'].map(prioridade_flag).fillna(3)

    # Ordenar: primeiro por flag, depois por frota (descendente)
    df_detratores = df_detratores.sort_values(
        by=['ordem_flag', 'qtd_frota'],
        ascending=[True, False]
    )

    # Remover coluna auxiliar
    df_detratores = df_detratores.drop('ordem_flag', axis=1)

    return df_detratores


def eh_comentario_valido(comentario: str) -> bool:
    """
    Verifica se o comentário é válido (não é apenas número de nota ou caracteres isolados).

    Args:
        comentario: Texto do comentário

    Returns:
        bool: True se o comentário for válido, False caso contrário
    """
    import re

    if pd.isna(comentario):
        return False

    comentario = str(comentario).strip()

    if not comentario:
        return False

    # Se o comentário tem 3 caracteres ou menos, é considerado inválido
    if len(comentario) <= 3:
        return False

    # Remover espaços e pontos para verificar se é apenas número
    comentario_limpo = comentario.replace(' ', '').replace('.', '').replace(',', '')

    # Se após remover pontuação o comentário é apenas dígitos, é inválido
    if comentario_limpo.isdigit():
        return False

    # Contar quantas letras/palavras reais existem
    palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{2,}\b', comentario)

    # Se não há pelo menos 2 palavras com 2+ letras, é inválido
    if len(palavras) < 2:
        return False

    # Verificar se o comentário tem pelo menos 10 caracteres alfabéticos
    letras = re.findall(r'[a-zA-ZÀ-ÿ]', comentario)
    if len(letras) < 10:
        return False

    return True


def processar_comentarios_por_classificacao(df: pd.DataFrame) -> dict:
    """
    Agrupa comentários por classificação.

    Args:
        df: DataFrame com dados

    Returns:
        dict: {classificacao: lista de dicts com comentários}
    """
    comentarios = {
        'Promotor': [],
        'Neutro': [],
        'Detrator': []
    }

    if df.empty:
        return comentarios

    for classif in ['Promotor', 'Neutro', 'Detrator']:
        df_classif = df[df['classificacao_empresa'] == classif].copy()

        # Filtrar apenas com comentários não-nulos
        df_classif = df_classif[df_classif['comentarios_consolidados'].notna()]
        df_classif = df_classif[df_classif['comentarios_consolidados'].str.strip() != '']

        # Filtrar comentários que são apenas números
        df_classif = df_classif[df_classif['comentarios_consolidados'].apply(eh_comentario_valido)]

        # Ordenar por data mais recente
        if 'ultima_resposta' in df_classif.columns:
            df_classif = df_classif.sort_values('ultima_resposta', ascending=False)

        # Pegar top 20
        df_classif = df_classif.head(20)

        for _, row in df_classif.iterrows():
            comentarios[classif].append({
                'empresa': row['customer_name'],
                'nota': row['nota_media_empresa'],
                'data': formatar_data(row.get('ultima_resposta')),
                'comentario': row['comentarios_consolidados']
            })

    return comentarios


def limpar_texto_para_wordcloud(texto: str, stopwords: set) -> str:
    """
    Limpa e processa texto para wordcloud.

    Args:
        texto: Texto a processar
        stopwords: Set de stopwords

    Returns:
        str: Texto limpo
    """
    if pd.isna(texto):
        return ""

    import re

    # Converter para minúsculas
    texto = texto.lower()

    # Remover pontuação e caracteres especiais
    texto = re.sub(r'[^\w\s]', ' ', texto)

    # Remover números
    texto = re.sub(r'\d+', '', texto)

    # Remover stopwords
    palavras = texto.split()
    palavras_filtradas = [p for p in palavras if p not in stopwords and len(p) > 2]

    return ' '.join(palavras_filtradas)


def gerar_texto_wordcloud(df: pd.DataFrame, stopwords: set) -> str:
    """
    Gera texto consolidado para wordcloud a partir dos comentários.

    Args:
        df: DataFrame com coluna 'comentarios_consolidados'
        stopwords: Set de stopwords

    Returns:
        str: Texto consolidado e limpo
    """
    if df.empty or 'comentarios_consolidados' not in df.columns:
        return ""

    comentarios = df['comentarios_consolidados'].dropna()

    if comentarios.empty:
        return ""

    # Filtrar comentários válidos (que não são apenas números)
    comentarios_validos = comentarios[comentarios.apply(eh_comentario_valido)]

    if comentarios_validos.empty:
        return ""

    # Concatenar todos os comentários válidos
    texto_completo = ' '.join(comentarios_validos.astype(str))

    # Limpar texto
    texto_limpo = limpar_texto_para_wordcloud(texto_completo, stopwords)

    return texto_limpo


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDAÇÕES
# ═══════════════════════════════════════════════════════════════════════════════

def validar_dados(df: pd.DataFrame) -> tuple:
    """
    Valida se o DataFrame possui as colunas necessárias.

    Args:
        df: DataFrame a validar

    Returns:
        tuple: (bool: válido, str: mensagem de erro)
    """
    colunas_obrigatorias = [
        'customer_id', 'customer_name', 'tipo_cliente',
        'qtd_frota', 'nota_media_empresa', 'classificacao_empresa'
    ]

    if df.empty:
        return False, "DataFrame está vazio. Verifique a conexão com o BigQuery."

    colunas_faltando = [col for col in colunas_obrigatorias if col not in df.columns]

    if colunas_faltando:
        return False, f"Colunas faltando: {', '.join(colunas_faltando)}"

    return True, "OK"
