"""
Configurações do Dashboard NPS - Gobrax
Contém constantes, paleta de cores, queries e configurações gerais
"""

# ═══════════════════════════════════════════════════════════════════════════════
# BIGQUERY CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ID = "equipe-dados"
DATASET_ID = "datawarehouse_gobrax"
VIEW_NAME = "vw_nps_dashboard"
FULL_TABLE_PATH = f"{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}"

# ═══════════════════════════════════════════════════════════════════════════════
# PALETA DE CORES (DARK MODE)
# ═══════════════════════════════════════════════════════════════════════════════

COLORS = {
    # Classificações NPS
    "promotor": "#10B981",      # Verde
    "neutro": "#F59E0B",        # Amarelo/Laranja
    "detrator": "#EF4444",      # Vermelho

    # Background e elementos
    "background": "#0E1117",
    "card": "#1E1E1E",
    "card_border": "#2D2D2D",
    "text": "#FAFAFA",
    "text_secondary": "#B0B0B0",

    # Alertas
    "urgente": "#DC2626",
    "atencao": "#F59E0B",
    "ok": "#10B981",

    # Gradiente para heatmap
    "heatmap_low": "#EF4444",
    "heatmap_mid": "#F5F5F5",
    "heatmap_high": "#10B981"
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAPEAMENTOS E EMOJIS
# ═══════════════════════════════════════════════════════════════════════════════

CLASSIFICACAO_EMOJI = {
    "Promotor": "😊",
    "Neutro": "😐",
    "Detrator": "😞"
}

FLAG_EMOJI = {
    "URGENTE": "🔴",
    "ATENÇÃO": "🟡",
    "OK": "🟢"
}

# ═══════════════════════════════════════════════════════════════════════════════
# QUERIES SQL
# ═══════════════════════════════════════════════════════════════════════════════

QUERY_MAIN = f"""
SELECT
    customer_id,
    customer_name,
    tipo_cliente,
    qtd_frota,
    tempo_casa_meses,
    faixa_tempo_casa,
    faixa_frota,
    nota_media_empresa,
    qtd_respostas,
    ultima_resposta,
    classificacao_empresa,
    comentarios_consolidados,
    responsavel_cs,
    lifecyclestage,
    lifecyclestage_descricao,
    status_do_cliente_novo_2_0,
    perfil_cliente_hubspot,
    frota_em_risco,
    dias_desde_resposta,
    flag_alerta,
    status_match_hubspot,
    qualidade_match
FROM `{FULL_TABLE_PATH}`
WHERE nota_media_empresa IS NOT NULL
"""

# ═══════════════════════════════════════════════════════════════════════════════
# STREAMLIT PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

PAGE_CONFIG = {
    "page_title": "Dashboard NPS - Gobrax",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# ═══════════════════════════════════════════════════════════════════════════════
# CSS CUSTOMIZADO
# ═══════════════════════════════════════════════════════════════════════════════

CUSTOM_CSS = f"""
<style>
    /* Tema Dark Global */
    .stApp {{
        background-color: {COLORS['background']};
        color: {COLORS['text']};
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {COLORS['card']};
        border-right: 1px solid {COLORS['card_border']};
    }}

    /* Cards de Métricas */
    div[data-testid="stMetric"] {{
        background-color: {COLORS['card']};
        padding: 20px;
        border-radius: 10px;
        border: 1px solid {COLORS['card_border']};
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}

    div[data-testid="stMetric"] label {{
        font-size: 16px !important;
        font-weight: 600 !important;
        color: {COLORS['text_secondary']} !important;
    }}

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        font-size: 36px !important;
        font-weight: 700 !important;
        color: {COLORS['text']} !important;
    }}

    /* Títulos */
    h1, h2, h3 {{
        color: {COLORS['text']} !important;
        font-weight: 700 !important;
    }}

    /* Tabelas */
    .dataframe {{
        background-color: {COLORS['card']} !important;
        border-radius: 8px;
    }}

    /* Botões */
    .stButton > button {{
        background-color: {COLORS['promotor']};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }}

    .stButton > button:hover {{
        background-color: #0D9668;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
        transform: translateY(-2px);
    }}

    /* Cards Customizados */
    .metric-card {{
        background: linear-gradient(135deg, {COLORS['card']} 0%, #252525 100%);
        padding: 24px;
        border-radius: 12px;
        border: 1px solid {COLORS['card_border']};
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
        text-align: center;
        margin-bottom: 20px;
    }}

    .metric-value {{
        font-size: 48px;
        font-weight: 700;
        margin: 10px 0;
    }}

    .metric-label {{
        font-size: 14px;
        color: {COLORS['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }}

    .metric-subtitle {{
        font-size: 12px;
        color: {COLORS['text_secondary']};
        margin-top: 8px;
    }}

    /* Seção de Alerta */
    .alert-section {{
        background-color: rgba(239, 68, 68, 0.1);
        border: 2px solid {COLORS['detrator']};
        border-radius: 12px;
        padding: 24px;
        margin: 20px 0;
    }}

    .alert-header {{
        font-size: 24px;
        font-weight: 700;
        color: {COLORS['detrator']};
        margin-bottom: 16px;
    }}

    /* Linha de Detrator */
    .detrator-row {{
        background-color: rgba(239, 68, 68, 0.15) !important;
    }}

    .neutro-row {{
        background-color: rgba(245, 158, 11, 0.1) !important;
    }}

    .promotor-row {{
        background-color: rgba(16, 185, 129, 0.1) !important;
    }}

    /* Scrollbar customizada */
    ::-webkit-scrollbar {{
        width: 10px;
        height: 10px;
    }}

    ::-webkit-scrollbar-track {{
        background: {COLORS['card']};
    }}

    ::-webkit-scrollbar-thumb {{
        background: {COLORS['card_border']};
        border-radius: 5px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: #404040;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: {COLORS['card']};
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        border: 1px solid {COLORS['card_border']};
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['promotor']};
        color: white;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {COLORS['card']};
        border-radius: 8px;
        border: 1px solid {COLORS['card_border']};
    }}

    /* Multiselect */
    .stMultiSelect [data-baseweb="tag"] {{
        background-color: {COLORS['promotor']} !important;
    }}
</style>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES DE FAIXAS
# ═══════════════════════════════════════════════════════════════════════════════

NOTA_RANGES = {
    "Detrator": (0, 6),
    "Neutro": (7, 8),
    "Promotor": (9, 10)
}

# ═══════════════════════════════════════════════════════════════════════════════
# STOPWORDS PARA WORDCLOUD (PORTUGUÊS)
# ═══════════════════════════════════════════════════════════════════════════════

STOPWORDS_PT = set([
    'a', 'o', 'e', 'é', 'de', 'da', 'do', 'em', 'um', 'uma', 'os', 'as',
    'dos', 'das', 'no', 'na', 'nos', 'nas', 'ao', 'aos', 'à', 'às',
    'por', 'para', 'com', 'sem', 'sob', 'sobre', 'mas', 'mais', 'menos',
    'que', 'qual', 'quando', 'onde', 'como', 'se', 'não', 'sim',
    'muito', 'muita', 'muitos', 'muitas', 'pouco', 'pouca', 'poucos', 'poucas',
    'todo', 'toda', 'todos', 'todas', 'este', 'esta', 'estes', 'estas',
    'esse', 'essa', 'esses', 'essas', 'aquele', 'aquela', 'aqueles', 'aquelas',
    'seu', 'sua', 'seus', 'suas', 'nosso', 'nossa', 'nossos', 'nossas',
    'foi', 'ser', 'ter', 'estar', 'fazer', 'há', 'pode', 'podem',
    'só', 'já', 'ainda', 'também', 'até', 'entre', 'depois', 'antes'
])

# ═══════════════════════════════════════════════════════════════════════════════
# CACHE TTL (Time To Live)
# ═══════════════════════════════════════════════════════════════════════════════

CACHE_TTL = 3600  # 1 hora em segundos
