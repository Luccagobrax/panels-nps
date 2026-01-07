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
    """
    try:
        from google.oauth2 import service_account

        # Usar secrets do Streamlit Cloud
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        client = bigquery.Client(credentials=credentials)
        return client
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao BigQuery: {str(e)}")
        st.info("🔧 Verifique se as credenciais do BigQuery estão configuradas corretamente nos Secrets.")
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

    # Renderizar sidebar e obter dados filtrados
    df_filtrado = renderizar_sidebar(df_completo)

    # Header
    renderizar_header()

    # Verificar se há dados após filtros
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
        return

    # Seções do dashboard (em ordem)
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

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #B0B0B0; padding: 20px;'>
            Dashboard NPS - Gobrax | Desenvolvido usando Streamlit
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
