# Dashboard NPS - Gobrax

Dashboard interativo de análise de Net Promoter Score (NPS) com dados do BigQuery.

## Funcionalidades

- Visão executiva com KPIs principais
- Análise de distribuição de notas
- Segmentações por tipo de cliente, frota, tempo de casa e lifecycle
- Mapa de calor de NPS
- Gestão de detratores prioritários
- Análise qualitativa com nuvem de palavras
- Tabela interativa de clientes

## Tecnologias

- **Streamlit** - Framework web
- **BigQuery** - Banco de dados
- **Plotly** - Visualizações interativas
- **Pandas** - Processamento de dados
- **WordCloud** - Nuvem de palavras

## Instalação Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar credenciais do BigQuery
# Adicione suas credenciais em .streamlit/secrets.toml

# Executar
streamlit run app.py
```

## Deploy no Streamlit Cloud

1. Fork este repositório
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte seu repositório
4. Configure os secrets do BigQuery
5. Deploy!

## Estrutura do Projeto

```
panels-nps/
├── app.py              # Aplicação principal
├── config.py           # Configurações e constantes
├── utils.py            # Funções auxiliares
├── requirements.txt    # Dependências
└── README.md          # Este arquivo
```

## Configuração de Secrets

Crie o arquivo `.streamlit/secrets.toml` com suas credenciais do BigQuery:

```toml
[gcp_service_account]
type = "service_account"
project_id = "seu-projeto"
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

## Autor

Desenvolvido por Gobrax

## Licença

MIT
