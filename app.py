import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
from datetime import datetime
import os

# Imports locais
from config import (
    PAGE_CONFIG, CUSTOM_CSS, COLORS, QUERY_MAIN,
    QUERY_USUARIOS_INATIVOS, QUERY_USUARIOS_RESPONDERAM,
    CLASSIFICACAO_EMOJI, FLAG_EMOJI, STOPWORDS_PT, CACHE_TTL
)
from utils import (
    calcular_nps, calcular_nps_ponderado, calcular_distribuicao_classificacao,
    formatar_numero, formatar_data, truncar_texto, adicionar_emoji_classificacao,
    adicionar_emoji_flag, get_cor_nps, get_cor_classificacao, get_cor_nota,
    criar_distribuicao_notas, calcular_nps_por_segmento, criar_heatmap_data,
    filtrar_detratores_prioritarios, processar_comentarios_por_classificacao,
    gerar_texto_wordcloud, validar_dados
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(**PAGE_CONFIG)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE CONEXÃO E CACHE
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_bigquery_client():
    """
    Cria e retorna cliente do BigQuery (cached).
    Suporta execução local e no Streamlit Cloud.
    """
    from google.oauth2 import service_account
    import json

    # Tentar usar secrets do Streamlit Cloud primeiro
    try:
        if "gcp_service_account" in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"]
            )
            client = bigquery.Client(credentials=credentials)
            return client
    except Exception:
        # Se falhar ao acessar secrets, continuar para tentar arquivo local
        pass

    # Se não estiver no Streamlit Cloud, tentar usar credenciais locais
    # Tentar múltiplos caminhos para o arquivo de credenciais
    caminhos_possiveis = [
        "credentials.json",
        os.path.join(os.path.dirname(__file__), "credentials.json"),
        os.path.join(os.getcwd(), "credentials.json"),
    ]

    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            try:
                credentials = service_account.Credentials.from_service_account_file(caminho)

                # Extrair project_id do arquivo de credenciais
                with open(caminho, 'r') as f:
                    creds_data = json.load(f)
                    project_id = creds_data.get('project_id')

                client = bigquery.Client(credentials=credentials, project=project_id)
                return client
            except Exception as e:
                st.warning(f"⚠️ Falha ao usar {caminho}: {str(e)}")
                continue

    # Se não encontrou arquivo, tentar credenciais padrão do ambiente
    try:
        client = bigquery.Client()
        return client
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao BigQuery: {str(e)}")

        # Informações de debug
        st.warning("📍 **Informações de Debug:**")
        st.code(f"""
Diretório atual: {os.getcwd()}
Diretório do script: {os.path.dirname(__file__)}
Arquivo credentials.json existe? {os.path.exists('credentials.json')}
        """)

        st.info("""
        🔧 **Como configurar as credenciais localmente:**

        **Opção 1 - Arquivo de credenciais (Recomendado):**
        1. Baixe o arquivo JSON de credenciais da sua conta de serviço do GCP
        2. Renomeie para `credentials.json`
        3. Coloque na pasta raiz do projeto
        4. Verifique se o arquivo tem permissões de leitura

        **Opção 2 - Google Cloud CLI:**
        1. Instale o Google Cloud CLI
        2. Execute: `gcloud auth application-default login`

        **Opção 3 - Variável de ambiente:**
        1. Configure: `set GOOGLE_APPLICATION_CREDENTIALS=caminho\\para\\credentials.json`
        """)
        st.stop()

@st.cache_data(ttl=CACHE_TTL)
def carregar_dados():
    """
    Carrega dados do BigQuery com cache de 1 hora.
    """
    try:
        client = get_bigquery_client()

        with st.spinner("📊 Carregando dados do BigQuery..."):
            df = client.query(QUERY_MAIN).to_dataframe()

        # Validar dados
        valido, mensagem = validar_dados(df)
        if not valido:
            st.error(f"❌ Erro na validação dos dados: {mensagem}")
            st.stop()

        return df

    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        st.stop()


@st.cache_data(ttl=CACHE_TTL)
def carregar_usuarios_inativos():
    """
    Carrega dados de usuarios inativos do BigQuery com cache de 1 hora.
    """
    try:
        client = get_bigquery_client()

        with st.spinner("Carregando usuarios inativos..."):
            df = client.query(QUERY_USUARIOS_INATIVOS).to_dataframe()

        # Normalize column names from the query.
        rename_map = {
            "nome_usuario": "user_name",
            "email_usuario": "email",
            "empresa": "customer_name",
        }
        for src, dst in rename_map.items():
            if dst not in df.columns and src in df.columns:
                df = df.rename(columns={src: dst})

        required_cols = ["user_name", "email", "customer_name", "perfil", "ultima_atividade"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Erro: colunas ausentes em usuarios inativos: {', '.join(missing_cols)}")
            return pd.DataFrame()

        return df

    except Exception as e:
        st.error(f"Erro ao carregar usuarios inativos: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def carregar_usuarios_responderam():
    """
    Carrega dados de usuários que responderam ao NPS do BigQuery com cache de 1 hora.
    """
    try:
        client = get_bigquery_client()

        with st.spinner("📝 Carregando usuários que responderam..."):
            df = client.query(QUERY_USUARIOS_RESPONDERAM).to_dataframe()

        return df

    except Exception as e:
        st.error(f"❌ Erro ao carregar usuários que responderam: {str(e)}")
        return pd.DataFrame()


def limpar_cache():
    """
    Limpa o cache de dados.
    """
    st.cache_data.clear()
    st.success("✅ Cache limpo! Recarregando dados...")
    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE INTERFACE - SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

def renderizar_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renderiza sidebar com filtros e retorna DataFrame filtrado.
    """
    with st.sidebar:
        st.markdown("# 📊 Dashboard NPS")
        st.markdown("### Gobrax")
        st.markdown("---")

        st.markdown("### 🔍 Filtros")

        # Filtro: Tipo de Cliente
        tipos_disponiveis = sorted(df['tipo_cliente'].dropna().unique().tolist())
        tipos_selecionados = st.multiselect(
            "Tipo de Cliente",
            options=tipos_disponiveis,
            default=tipos_disponiveis,
            key="filtro_tipo"
        )

        # Filtro: Faixa de Frota
        frotas_disponiveis = sorted(df['faixa_frota'].dropna().unique().tolist())
        frotas_selecionadas = st.multiselect(
            "Faixa de Frota",
            options=frotas_disponiveis,
            default=frotas_disponiveis,
            key="filtro_frota"
        )

        # Filtro: Faixa de Tempo de Casa
        tempos_disponiveis = sorted(df['faixa_tempo_casa'].dropna().unique().tolist())
        tempos_selecionados = st.multiselect(
            "Tempo de Casa",
            options=tempos_disponiveis,
            default=tempos_disponiveis,
            key="filtro_tempo"
        )

        # Filtro: Classificação
        classificacoes = ['Promotor', 'Neutro', 'Detrator']
        classificacoes_selecionadas = st.multiselect(
            "Classificação NPS",
            options=classificacoes,
            default=classificacoes,
            key="filtro_classificacao"
        )

        # Filtro: Responsável CS (se disponível)
        if 'responsavel_cs' in df.columns:
            responsaveis_disponiveis = sorted(df['responsavel_cs'].dropna().unique().tolist())
            if responsaveis_disponiveis:
                responsaveis_selecionados = st.multiselect(
                    "Responsável CS",
                    options=responsaveis_disponiveis,
                    default=responsaveis_disponiveis,
                    key="filtro_responsavel"
                )
            else:
                responsaveis_selecionados = []
        else:
            responsaveis_selecionados = []

        # Filtro: Lifecycle Stage
        if 'lifecyclestage_descricao' in df.columns:
            lifecycles_disponiveis = sorted(df['lifecyclestage_descricao'].dropna().unique().tolist())
            if lifecycles_disponiveis:
                lifecycles_selecionados = st.multiselect(
                    "Lifecycle Stage",
                    options=lifecycles_disponiveis,
                    default=lifecycles_disponiveis,
                    key="filtro_lifecycle"
                )
            else:
                lifecycles_selecionados = lifecycles_disponiveis
        else:
            lifecycles_selecionados = []

        st.markdown("---")

        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                limpar_cache()

        with col2:
            if st.button("🗑️ Limpar", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        st.markdown("---")
        st.markdown(f"**Última atualização:**")
        st.markdown(f"_{datetime.now().strftime('%d/%m/%Y %H:%M')}_")

    # Aplicar filtros
    df_filtrado = df.copy()

    if tipos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['tipo_cliente'].isin(tipos_selecionados)]

    if frotas_selecionadas:
        df_filtrado = df_filtrado[df_filtrado['faixa_frota'].isin(frotas_selecionadas)]

    if tempos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['faixa_tempo_casa'].isin(tempos_selecionados)]

    if classificacoes_selecionadas:
        df_filtrado = df_filtrado[df_filtrado['classificacao_empresa'].isin(classificacoes_selecionadas)]

    if responsaveis_selecionados and 'responsavel_cs' in df.columns:
        df_filtrado = df_filtrado[df_filtrado['responsavel_cs'].isin(responsaveis_selecionados)]

    if lifecycles_selecionados and 'lifecyclestage_descricao' in df.columns:
        df_filtrado = df_filtrado[df_filtrado['lifecyclestage_descricao'].isin(lifecycles_selecionados)]

    return df_filtrado


# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE INTERFACE - SEÇÕES DO DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def renderizar_header():
    """
    Renderiza header do dashboard.
    """
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='margin: 0; font-size: 82px;'>📊 Dashboard NPS</h1>
            <p style='font-size: 20px; color: #B0B0B0; margin-top: 10px;'>
                Net Promoter Score - Análise Completa
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")


def renderizar_visao_executiva(df: pd.DataFrame):
    """
    Renderiza seção de Visão Executiva com KPIs principais.
    """
    st.markdown("## 💎 Visão Executiva")

    # Calcular métricas
    nps_geral = calcular_nps(df)
    nps_ponderado = calcular_nps_ponderado(df)
    total_empresas = len(df)
    total_respostas = df['qtd_respostas'].sum()
    total_frota = df['qtd_frota'].sum()

    # Frota em risco (detratores)
    frota_risco = df[df['classificacao_empresa'] == 'Detrator']['qtd_frota'].sum()

    # KPIs em 4 colunas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        cor_nps = get_cor_nps(nps_geral)
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid {cor_nps};'>
                <div class='metric-label'>NPS GERAL</div>
                <div class='metric-value' style='color: {cor_nps};'>{nps_geral:.1f}</div>
                <div class='metric-subtitle'>% Promotores - % Detratores</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid {COLORS['promotor']};'>
                <div class='metric-label'>NPS PONDERADO</div>
                <div class='metric-value' style='color: {COLORS['promotor']};'>{nps_ponderado:.2f}</div>
                <div class='metric-subtitle'>Ponderado por Frota</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid {COLORS['text']};'>
                <div class='metric-label'>EMPRESAS</div>
                <div class='metric-value' style='color: {COLORS['text']};'>{formatar_numero(total_empresas)}</div>
                <div class='metric-subtitle'>{formatar_numero(total_respostas)} respostas</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid {COLORS['neutro']};'>
                <div class='metric-label'>FROTA TOTAL</div>
                <div class='metric-value' style='color: {COLORS['neutro']};'>{formatar_numero(total_frota)}</div>
                <div class='metric-subtitle' style='color: {COLORS['detrator']};'>{formatar_numero(frota_risco)} em risco</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Distribuição percentual e gráfico de pizza
    distribuicao = calcular_distribuicao_classificacao(df)

    # Container para centralizar os cards com o gráfico
    col_left, col_cards, col_pizza, col_right = st.columns([0.5, 3, 2, 0.5])

    with col_cards:
        # Adicionar padding top para centralizar verticalmente
        st.markdown("<div style='padding-top: 35px;'></div>", unsafe_allow_html=True)

        # Cards de percentual em linha
        cards_col1, cards_col2, cards_col3 = st.columns(3)

        with cards_col1:
            st.markdown(f"""
                <div style='text-align: center; padding: 20px; background: rgba(16, 185, 129, 0.1); border-radius: 8px;'>
                    <div style='font-size: 32px; font-weight: 700; color: {COLORS['promotor']};'>
                        {distribuicao['Promotor']:.1f}%
                    </div>
                    <div style='font-size: 14px; color: {COLORS['text_secondary']};'>Promotores</div>
                </div>
            """, unsafe_allow_html=True)

        with cards_col2:
            st.markdown(f"""
                <div style='text-align: center; padding: 20px; background: rgba(245, 158, 11, 0.1); border-radius: 8px;'>
                    <div style='font-size: 32px; font-weight: 700; color: {COLORS['neutro']};'>
                        {distribuicao['Neutro']:.1f}%
                    </div>
                    <div style='font-size: 14px; color: {COLORS['text_secondary']};'>Neutros</div>
                </div>
            """, unsafe_allow_html=True)

        with cards_col3:
            st.markdown(f"""
                <div style='text-align: center; padding: 20px; background: rgba(239, 68, 68, 0.1); border-radius: 8px;'>
                    <div style='font-size: 32px; font-weight: 700; color: {COLORS['detrator']};'>
                        {distribuicao['Detrator']:.1f}%
                    </div>
                    <div style='font-size: 14px; color: {COLORS['text_secondary']};'>Detratores</div>
                </div>
            """, unsafe_allow_html=True)

    with col_pizza:
        # Gráfico de pizza
        fig_pizza = go.Figure(data=[go.Pie(
            labels=['Promotor', 'Neutro', 'Detrator'],
            values=[distribuicao['Promotor'], distribuicao['Neutro'], distribuicao['Detrator']],
            hole=0.5,
            marker=dict(colors=[COLORS['promotor'], COLORS['neutro'], COLORS['detrator']]),
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(size=14, color='white')
        )])

        fig_pizza.update_layout(
            showlegend=False,
            height=250,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig_pizza, use_container_width=True, config={'displayModeBar': False})


def renderizar_distribuicao_notas(df: pd.DataFrame):
    """
    Renderiza gráfico de distribuição de notas.
    """
    st.markdown("## 📊 Distribuição de Notas")

    df_notas = criar_distribuicao_notas(df)

    # Cores por faixa
    cores = []
    for nota in df_notas['nota']:
        if nota >= 9:
            cores.append(COLORS['promotor'])
        elif nota >= 7:
            cores.append(COLORS['neutro'])
        else:
            cores.append(COLORS['detrator'])

    fig = go.Figure()

    # Barras
    fig.add_trace(go.Bar(
        x=df_notas['nota'],
        y=df_notas['quantidade'],
        marker=dict(color=cores),
        text=df_notas['quantidade'],
        textposition='outside',
        hovertemplate='<b>Nota %{x}</b><br>Quantidade: %{y}<extra></extra>'
    ))

    # Linhas verticais nos limites
    fig.add_vline(x=6.5, line_dash="dash", line_color=COLORS['text_secondary'],
                  annotation_text="Limite Detrator", annotation_position="top")
    fig.add_vline(x=8.5, line_dash="dash", line_color=COLORS['text_secondary'],
                  annotation_text="Limite Promotor", annotation_position="top")

    # Calcular range do eixo Y com margem de 15% para os rótulos
    max_quantidade = df_notas['quantidade'].max()
    y_range = [0, max_quantidade * 1.15]

    fig.update_layout(
        xaxis_title="Nota (0-10)",
        yaxis_title="Quantidade de Empresas",
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=1,
            gridcolor=COLORS['card_border']
        ),
        yaxis=dict(gridcolor=COLORS['card_border'], range=y_range),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLORS['text']),
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)


def renderizar_segmentacoes(df: pd.DataFrame):
    """
    Renderiza gráficos de segmentação (Tipo, Frota, Tempo, Lifecycle).
    """
    st.markdown("## 🎯 Segmentações")

    # Gráfico 1: Tipo de Cliente
    st.markdown("### NPS por Tipo de Cliente")
    df_tipo = calcular_nps_por_segmento(df, 'tipo_cliente')

    if not df_tipo.empty:
        fig = go.Figure(go.Bar(
            x=df_tipo['nps'],
            y=df_tipo['segmento'],
            orientation='h',
            marker=dict(color=df_tipo['nps'].apply(get_cor_nps)),
            text=df_tipo['nps'].apply(lambda x: f"{x:.1f}"),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>NPS: %{x:.1f}<br>Empresas: %{customdata}<extra></extra>',
            customdata=df_tipo['quantidade']
        ))

        fig.update_layout(
            xaxis_title="NPS",
            yaxis_title="",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text']),
            height=300,
            xaxis=dict(gridcolor=COLORS['card_border']),
            yaxis=dict(gridcolor=COLORS['card_border'])
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados disponíveis")

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico 2: Faixa de Frota
    st.markdown("### NPS por Faixa de Frota")
    df_frota = calcular_nps_por_segmento(df, 'faixa_frota')

    if not df_frota.empty:
        # Ordenar alfabeticamente
        df_frota = df_frota.sort_values('segmento')

        fig = go.Figure(go.Bar(
            x=df_frota['nps'],
            y=df_frota['segmento'],
            orientation='h',
            marker=dict(color=df_frota['nps'].apply(get_cor_nps)),
            text=df_frota['nps'].apply(lambda x: f"{x:.1f}"),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>NPS: %{x:.1f}<br>Empresas: %{customdata}<extra></extra>',
            customdata=df_frota['quantidade']
        ))

        fig.update_layout(
            xaxis_title="NPS",
            yaxis_title="",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text']),
            height=300,
            xaxis=dict(gridcolor=COLORS['card_border']),
            yaxis=dict(gridcolor=COLORS['card_border'])
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados disponíveis")

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico 3: Tempo de Casa
    st.markdown("### NPS por Tempo de Casa")
    df_tempo = calcular_nps_por_segmento(df, 'faixa_tempo_casa')

    if not df_tempo.empty:
        # Ordenar alfabeticamente
        df_tempo = df_tempo.sort_values('segmento')

        fig = go.Figure(go.Bar(
            x=df_tempo['segmento'],
            y=df_tempo['nps'],
            marker=dict(color=df_tempo['nps'].apply(get_cor_nps)),
            text=df_tempo['nps'].apply(lambda x: f"{x:.1f}"),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>NPS: %{y:.1f}<br>Empresas: %{customdata}<extra></extra>',
            customdata=df_tempo['quantidade']
        ))

        # Calcular range do eixo Y com margem de 15% para os rótulos
        max_nps = df_tempo['nps'].max()
        min_nps = df_tempo['nps'].min()
        y_padding = (max_nps - min_nps) * 0.15 if max_nps != min_nps else 10
        y_range = [min(min_nps - 5, 0), max_nps + y_padding]

        fig.update_layout(
            xaxis_title="Tempo de Casa",
            yaxis_title="NPS",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text']),
            height=400,
            xaxis=dict(gridcolor=COLORS['card_border'], tickangle=-45),
            yaxis=dict(gridcolor=COLORS['card_border'], range=y_range)
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados disponíveis")

    st.markdown("<br>", unsafe_allow_html=True)


def renderizar_heatmap(df: pd.DataFrame):
    """
    Renderiza mapa de calor (Tempo × Frota).
    """
    st.markdown("## 🔥 Mapa de Calor: NPS por Porte × Tempo de Relacionamento")

    matriz = criar_heatmap_data(df)

    if not matriz.empty:
        fig = go.Figure(data=go.Heatmap(
            z=matriz.values,
            x=matriz.columns,
            y=matriz.index,
            colorscale=[
                [0, COLORS['detrator']],
                [0.5, COLORS['heatmap_mid']],
                [1, COLORS['promotor']]
            ],
            text=matriz.values.round(2),
            texttemplate='%{text}',
            textfont={"size": 14, "color": "black"},
            hovertemplate='Frota: %{y}<br>Tempo: %{x}<br>NPS: %{z:.2f}<extra></extra>',
            colorbar=dict(title="NPS Médio")
        ))

        fig.update_layout(
            xaxis_title="Tempo de Casa",
            yaxis_title="Faixa de Frota",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text']),
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Dados insuficientes para criar o heatmap")


def renderizar_tabela_clientes(df: pd.DataFrame):
    """
    Renderiza tabela interativa com todos os clientes.
    """
    st.markdown("## 📋 Tabela de Clientes")

    # Preparar dados para exibição
    df_display = df.copy()

    # Formatar colunas
    df_display['Razão Social'] = df_display['customer_name']
    df_display['Tipo'] = df_display['tipo_cliente']
    df_display['Frota'] = df_display['qtd_frota'].apply(lambda x: formatar_numero(x))
    df_display['Tempo (meses)'] = df_display['tempo_casa_meses'].apply(lambda x: formatar_numero(x))
    df_display['NPS'] = df_display['nota_media_empresa'].apply(lambda x: formatar_numero(x, 1))
    df_display['Classificação'] = df_display['classificacao_empresa'].apply(adicionar_emoji_classificacao)
    df_display['Respostas'] = df_display['qtd_respostas'].apply(lambda x: formatar_numero(x))
    df_display['Responsável CS'] = df_display['responsavel_cs'].fillna('-')
    df_display['Lifecycle'] = df_display['lifecyclestage_descricao'].fillna('-')
    df_display['Última Resposta'] = df_display['ultima_resposta'].apply(formatar_data)
    df_display['Comentários'] = df_display['comentarios_consolidados'].apply(lambda x: truncar_texto(x, 100))

    # Selecionar colunas para exibição
    colunas_exibir = [
        'Razão Social', 'Tipo', 'Frota', 'Tempo (meses)', 'NPS',
        'Classificação', 'Respostas', 'Responsável CS', 'Lifecycle',
        'Última Resposta', 'Comentários'
    ]

    df_display = df_display[colunas_exibir]

    # Ordenar: Detratores primeiro, depois por frota
    ordem_classif = {'Detrator': 1, 'Neutro': 2, 'Promotor': 3}
    df_display['_ordem'] = df_display['Classificação'].map(ordem_classif)
    df_display = df_display.sort_values(['_ordem', 'Frota'], ascending=[True, False])
    df_display = df_display.drop('_ordem', axis=1)

    # Exibir tabela
    st.dataframe(
        df_display,
        use_container_width=True,
        height=600
    )

    # Botão de download CSV
    csv = df_display.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"nps_clientes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def renderizar_usuarios_inativos(df_inativos: pd.DataFrame):
    """
    Renderiza seção de usuários que acessaram a plataforma mas não responderam ao NPS.
    """
    st.markdown("## 📋 Usuários Inativos no NPS")

    if df_inativos.empty:
        st.info("✅ Não há usuários inativos no momento!")
        return

    # Calcular dias desde último acesso
    df_inativos['dias_sem_acesso'] = (pd.to_datetime('today') - pd.to_datetime(df_inativos['ultima_atividade'])).dt.days

    # Calcular métricas
    total_inativos = len(df_inativos)
    total_empresas = df_inativos['customer_name'].nunique()
    media_dias = df_inativos['dias_sem_acesso'].mean()

    # Exibir cards de métricas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid {COLORS['detrator']};'>
                <div class='metric-label'>USUÁRIOS INATIVOS</div>
                <div class='metric-value' style='color: {COLORS['detrator']};'>{formatar_numero(total_inativos)}</div>
                <div class='metric-subtitle'>Não responderam ao NPS</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid {COLORS['neutro']};'>
                <div class='metric-label'>EMPRESAS ÚNICAS</div>
                <div class='metric-value' style='color: {COLORS['neutro']};'>{formatar_numero(total_empresas)}</div>
                <div class='metric-subtitle'>Com usuários inativos</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid {COLORS['text']};'>
                <div class='metric-label'>MÉDIA DE DIAS</div>
                <div class='metric-value' style='color: {COLORS['text']};'>{formatar_numero(media_dias, 1)}</div>
                <div class='metric-subtitle'>Desde último acesso</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Filtros
    st.markdown("### 🔍 Filtros")
    col_filtro1, col_filtro2 = st.columns(2)

    with col_filtro1:
        empresas_disponiveis = sorted(df_inativos['customer_name'].dropna().unique().tolist())
        empresas_selecionadas = st.multiselect(
            "Filtrar por Empresa",
            options=empresas_disponiveis,
            default=empresas_disponiveis,
            key="filtro_empresa_inativos"
        )

    with col_filtro2:
        perfis_disponiveis = sorted(df_inativos['perfil'].dropna().unique().tolist())
        perfis_selecionados = st.multiselect(
            "Filtrar por Perfil",
            options=perfis_disponiveis,
            default=perfis_disponiveis,
            key="filtro_perfil_inativos"
        )

    # Aplicar filtros
    df_filtrado = df_inativos.copy()
    if empresas_selecionadas:
        df_filtrado = df_filtrado[df_filtrado['customer_name'].isin(empresas_selecionadas)]
    if perfis_selecionados:
        df_filtrado = df_filtrado[df_filtrado['perfil'].isin(perfis_selecionados)]

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico: Top 10 empresas com mais usuários inativos
    st.markdown("### 📊 Top 10 Empresas com Mais Usuários Inativos")

    empresas_count = df_filtrado['customer_name'].value_counts().head(10)

    if not empresas_count.empty:
        fig = go.Figure(go.Bar(
            x=empresas_count.values,
            y=empresas_count.index,
            orientation='h',
            marker=dict(color=COLORS['detrator']),
            text=empresas_count.values,
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Usuários Inativos: %{x}<extra></extra>'
        ))

        fig.update_layout(
            xaxis_title="Quantidade de Usuários Inativos",
            yaxis_title="",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text']),
            height=400,
            xaxis=dict(gridcolor=COLORS['card_border']),
            yaxis=dict(gridcolor=COLORS['card_border'])
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados disponíveis para exibir o gráfico")

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabela com cores condicionais
    st.markdown("### 📋 Tabela de Usuários Inativos")

    # Preparar dados para exibição
    df_display = df_filtrado.copy()
    df_display['Nome'] = df_display['user_name']
    df_display['Email'] = df_display['email']
    df_display['Empresa'] = df_display['customer_name']
    df_display['Perfil'] = df_display['perfil']
    df_display['Última Atividade'] = pd.to_datetime(df_display['ultima_atividade']).dt.strftime('%d/%m/%Y')
    df_display['Dias Sem Acesso'] = df_display['dias_sem_acesso']

    # Aplicar cores condicionais
    def aplicar_cor_linha(row):
        dias = row['Dias Sem Acesso']
        if dias < 14:
            return '#d4edda'  # Verde claro
        elif dias <= 30:
            return '#fff3cd'  # Amarelo claro
        else:
            return '#ffcccc'  # Vermelho claro

    df_display['_cor'] = df_display.apply(aplicar_cor_linha, axis=1)

    # Selecionar colunas para exibição
    colunas_exibir = ['Nome', 'Email', 'Empresa', 'Perfil', 'Última Atividade', 'Dias Sem Acesso']

    # Ordenar por dias sem acesso (decrescente)
    df_display = df_display.sort_values('Dias Sem Acesso', ascending=False)

    # Exibir tabela
    st.dataframe(
        df_display[colunas_exibir],
        use_container_width=True,
        height=600
    )

    # Botão de download CSV
    csv = df_display[colunas_exibir].to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"usuarios_inativos_nps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )



def renderizar_usuarios_responderam(df_responderam: pd.DataFrame):
    """
    Renderiza secao de usuarios que responderam ao NPS.
    """
    st.markdown("## Usuarios que Responderam ao NPS")

    if df_responderam.empty:
        st.info("Nao ha usuarios com respostas no momento.")
        return

    required_cols = ["user_name", "email", "customer_name", "score", "comment"]
    missing_cols = [col for col in required_cols if col not in df_responderam.columns]
    if missing_cols:
        st.error(f"Erro: colunas ausentes em usuarios responderam: {', '.join(missing_cols)}")
        return

    total_respostas = len(df_responderam)
    total_empresas = df_responderam["customer_name"].nunique()
    media_score = df_responderam["score"].mean()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid {COLORS['promotor']};'>
                <div class='metric-label'>RESPOSTAS</div>
                <div class='metric-value' style='color: {COLORS['promotor']};'>{formatar_numero(total_respostas)}</div>
                <div class='metric-subtitle'>Usuarios que responderam</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid {COLORS['neutro']};'>
                <div class='metric-label'>EMPRESAS</div>
                <div class='metric-value' style='color: {COLORS['neutro']};'>{formatar_numero(total_empresas)}</div>
                <div class='metric-subtitle'>Empresas unicas</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid {COLORS['text']};'>
                <div class='metric-label'>MEDIA SCORE</div>
                <div class='metric-value' style='color: {COLORS['text']};'>{formatar_numero(media_score, 1)}</div>
                <div class='metric-subtitle'>Nota media</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    df_display = df_responderam.copy()
    df_display["Nome"] = df_display["user_name"]
    df_display["Email"] = df_display["email"]
    df_display["Empresa"] = df_display["customer_name"]
    df_display["Score"] = df_display["score"].apply(lambda x: formatar_numero(x, 1))
    df_display["Comentario"] = df_display["comment"].fillna("-")

    colunas_exibir = ["Nome", "Email", "Empresa", "Score", "Comentario"]

    st.dataframe(
        df_display[colunas_exibir],
        use_container_width=True,
        height=600
    )

    csv = df_display[colunas_exibir].to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"usuarios_responderam_nps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def renderizar_detratores_risco(df: pd.DataFrame):
    """
    Renderiza seção de gestão de detratores em risco.
    """
    st.markdown("## ⚠️ Gestão de CS - Detratores Prioritários")

    df_detratores = filtrar_detratores_prioritarios(df)

    if df_detratores.empty:
        st.success("✅ Não há detratores no momento!")
        return

    # Métricas de alerta
    total_detratores = len(df_detratores)
    frota_total_risco = df_detratores['qtd_frota'].sum()
    urgentes = len(df_detratores[df_detratores['flag_alerta'] == 'URGENTE'])

    st.markdown(f"""
        <div class='alert-section'>
            <div class='alert-header'>🚨 ATENÇÃO: {total_detratores} Clientes Detratores</div>
            <div style='display: flex; gap: 20px; margin-top: 10px;'>
                <div style='flex: 1;'>
                    <div style='font-size: 36px; font-weight: 700; color: {COLORS['detrator']};'>
                        {formatar_numero(frota_total_risco)}
                    </div>
                    <div style='font-size: 14px; color: {COLORS['text_secondary']};'>
                        Veículos em Risco
                    </div>
                </div>
                <div style='flex: 1;'>
                    <div style='font-size: 36px; font-weight: 700; color: {COLORS['urgente']};'>
                        {urgentes}
                    </div>
                    <div style='font-size: 14px; color: {COLORS['text_secondary']};'>
                        Casos Urgentes
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Preparar tabela
    df_display = df_detratores.copy()

    df_display['Flag'] = df_display['flag_alerta'].apply(adicionar_emoji_flag)
    df_display['Empresa'] = df_display['customer_name']
    df_display['NPS'] = df_display['nota_media_empresa'].apply(lambda x: formatar_numero(x, 1))
    df_display['Frota Risco'] = df_display['qtd_frota'].apply(lambda x: formatar_numero(x))
    df_display['Dias s/ Resposta'] = df_display['dias_desde_resposta'].apply(lambda x: formatar_numero(x))
    df_display['Responsável'] = df_display['responsavel_cs'].fillna('-')
    df_display['Comentários'] = df_display['comentarios_consolidados'].apply(lambda x: truncar_texto(x, 80))

    colunas_exibir = ['Flag', 'Empresa', 'NPS', 'Frota Risco', 'Dias s/ Resposta', 'Responsável', 'Comentários']

    st.dataframe(
        df_display[colunas_exibir],
        use_container_width=True,
        height=400
    )

    # Comentários por classificação
    st.markdown("### 📝 Comentários por Classificação")

    comentarios = processar_comentarios_por_classificacao(df)

    tab1, tab2, tab3 = st.tabs(["Promotores", "Neutros", "Detratores"])

    with tab1:
        if comentarios['Promotor']:
            for com in comentarios['Promotor']:
                st.markdown(f"""
                    <div style='background: rgba(16, 185, 129, 0.1); padding: 15px; border-radius: 8px;
                                border-left: 4px solid {COLORS['promotor']}; margin-bottom: 10px;'>
                        <div style='font-weight: 600; color: {COLORS['promotor']};'>
                            {com['empresa']} - Nota: {com['nota']:.1f} | {com['data']}
                        </div>
                        <div style='margin-top: 8px; color: {COLORS['text']};'>
                            {com['comentario']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum comentário de promotores disponível")

    with tab2:
        if comentarios['Neutro']:
            for com in comentarios['Neutro']:
                st.markdown(f"""
                    <div style='background: rgba(245, 158, 11, 0.1); padding: 15px; border-radius: 8px;
                                border-left: 4px solid {COLORS['neutro']}; margin-bottom: 10px;'>
                        <div style='font-weight: 600; color: {COLORS['neutro']};'>
                            {com['empresa']} - Nota: {com['nota']:.1f} | {com['data']}
                        </div>
                        <div style='margin-top: 8px; color: {COLORS['text']};'>
                            {com['comentario']}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum comentário de neutros disponível")

    with tab3:
        if comentarios['Detrator']:
            for com in comentarios['Detrator']:
                st.markdown(f"""
                    <div style='background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 8px;
                                border-left: 4px solid {COLORS['detrator']}; margin-bottom: 10px;'>
                        <div style='font-weight: 600; color: {COLORS['detrator']};'>
                            {com['empresa']} - Nota: {com['nota']:.1f} | {com['data']}
                        </div>
                        <div style='margin-top: 8px; color: {COLORS['text']};'>
                            {com['comentario']}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum comentário de detratores disponível")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN - APLICAÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """
    Função principal que orquestra o dashboard.
    """
    # Carregar dados
    df_completo = carregar_dados()
    df_inativos = carregar_usuarios_inativos()
    df_responderam = carregar_usuarios_responderam()

    # Renderizar sidebar e obter dados filtrados
    df_filtrado = renderizar_sidebar(df_completo)

    # Header
    renderizar_header()

    # Verificar se há dados após filtros
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
        return

    # Criar tabs para organizar as seções
    tab1, tab2, tab3 = st.tabs([
        "📊 Dashboard Principal",
        "📋 Usuários Inativos no NPS",
        "📝 Usuários que Responderam"
    ])

    with tab1:
        # Seções do dashboard principal (em ordem)
        renderizar_visao_executiva(df_filtrado)
        st.markdown("<br><br>", unsafe_allow_html=True)

        renderizar_distribuicao_notas(df_filtrado)
        st.markdown("<br><br>", unsafe_allow_html=True)

        renderizar_segmentacoes(df_filtrado)
        st.markdown("<br><br>", unsafe_allow_html=True)

        renderizar_heatmap(df_filtrado)
        st.markdown("<br><br>", unsafe_allow_html=True)

        renderizar_tabela_clientes(df_filtrado)
        st.markdown("<br><br>", unsafe_allow_html=True)

        renderizar_detratores_risco(df_filtrado)
        st.markdown("<br><br>", unsafe_allow_html=True)

    with tab2:
        # Seção de usuários inativos
        renderizar_usuarios_inativos(df_inativos)

    with tab3:
        # Seção de usuários que responderam
        renderizar_usuarios_responderam(df_responderam)

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #B0B0B0; padding: 20px;'>
            Dashboard NPS - Gobrax | Desenvolvido usando Streamlit
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()