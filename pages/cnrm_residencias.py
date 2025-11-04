# ---------------------------------------------------------------
# Set up
# ---------------------------------------------------------------
import re
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import numpy as np
import pandas as pd
import json, unicodedata
import os
from datetime import datetime
import pytz
from pathlib import Path
from google.cloud import bigquery
from google.cloud import bigquery_storage
from google.cloud.bigquery import ScalarQueryParameter as Q
import plotly.express as px
import src.graph as graph
import hashlib

# ---------------------------------------------------------------
# BigQuery (região e tabela)
# ---------------------------------------------------------------
PROJECT_ID  = "escolap2p"
BQ_LOCATION = "southamerica-east1"
TABLE_ID    = "escolap2p.base_siscnrm.residentes_applications"

# grava credenciais no /tmp e exporta a env var
with open("/tmp/keyfile.json", "w") as f:
    json.dump(st.secrets["bigquery"].to_dict(), f)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/keyfile.json"

# --- cacheia os clients para não recriar a cada rerun
@st.cache_resource
def get_clients():
    bq  = bigquery.Client(project=PROJECT_ID, location=BQ_LOCATION)
    bqs = bigquery_storage.BigQueryReadClient()
    return bq, bqs

client, bqs = get_clients()

# ---------------------------------------------------------------
# Config da página
# ---------------------------------------------------------------
st.set_page_config(layout="wide", page_title="📊 Public Health Analytics")

# ---------------- Helpers para assets ----------------
APP_DIR = Path(__file__).resolve().parent
ASSETS = APP_DIR.parent / "assets"   # <--- ajuste aqui

def first_existing(*relative_paths: str) -> Path | None:
    for rel in relative_paths:
        p = ASSETS / rel
        if p.exists():
            return p
    return None

LOGO = first_existing("logo.png", "logo.jpg", "logo.jpeg", "logo.webp")
FOTO = first_existing("foto_gregorio.jpg", "foto_gregorio.png", "foto_gregorio.jpeg", "foto_gregorio.webp")

# ---------------- Cabeçalho ----------------
st.markdown(
    """
    <div style='background: linear-gradient(to right, #004e92, #000428); padding: 40px; border-radius: 12px; margin-bottom:30px'>
        <h1 style='color: white;'>📊 Public Health Analytics</h1>
        <p style='color: white;'>Explore as possibilidades de infinitas de análises de dados públicos.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("""
<style>
/* Esconde a lista padrão de páginas no topo da sidebar */
[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ---------------- Sidebar (único) ----------------
with st.sidebar:
    if LOGO:
        st.image(str(LOGO), use_container_width=True)
    else:
        st.warning(f"Logo não encontrada em {ASSETS}/logo.(png|jpg|jpeg|webp)")
    st.markdown("<hr style='border:none;border-top:1px solid #ccc;'/>", unsafe_allow_html=True)
    st.header("Menu")

    # ---- Categorias (estilo TABNET) ----
    with st.expander("Análises Demográficas", expanded=False):
        st.page_link("pages/populacao.py", label="População (IBGE)", icon="👨‍👩‍👧‍👦")
        st.page_link("pages/educacao.py", label="Educação (IBGE)", icon="🎓")
        st.page_link("pages/trabalho_renda.py", label="Trabalho e Renda (IBGE)", icon="💼")
        st.page_link("pages/saneamento.py", label="Saneamento (IBGE)", icon="🚰")

    with st.expander("Força de Trabalho", expanded=False):
        st.page_link("pages/cnrm_residencias.py", label="Residências Md (CNRM)", icon="🏠")
        st.page_link("pages/cnes_rh.py", label="Profissionais (CNES)", icon="👩‍⚕️")

    with st.expander("Rede Assistencial", expanded=False):
        st.page_link("pages/cnes_estabelecimentos.py", label="Estabelecimentos (CNES)", icon="🏨")
        st.page_link("pages/cnes_recursos_fisicos.py", label="Recursos Físicos (CNES)", icon="🛠️")
        st.page_link("pages/cnes_equipes.py", label="Equipes de Saúde (CNES)", icon="👥")

    with st.expander("Assistência à Saúde", expanded=False):
        st.page_link("pages/producao_hospitalar.py", label="Produção Hosp (SIH)", icon="🛏️")
        st.page_link("pages/producao_ambulatorial.py", label="Produção Amb (SIA)", icon="🩺")
        st.page_link("pages/imunizacoes.py", label="Imunizações (SI-PNI)", icon="💉")

    with st.expander("Morbidade", expanded=False):
        st.page_link("pages/morbilidade_sih.py", label="Morbidade Hosp (SIH)", icon="🏥")
        st.page_link("pages/notificacoes.py", label="Notificações (SINAN)", icon="📜")
        st.page_link("pages/cancer_siscan.py", label="Câncer (SISCAN)", icon="🎗️")

    with st.expander("Estatísticas Vitais", expanded=False):
        st.page_link("pages/nascidos_vivos.py", label="Nascidos Vivos (SINASC)", icon="👶")
        st.page_link("pages/mortalidade_cid.py", label="Mortalidade (SIM)", icon="⚰️")

    with st.expander("Inquéritos e Pesquisas", expanded=False):
        st.page_link("pages/pns.py", label="PNS", icon="🧾")
        st.page_link("pages/pnad_basico.py", label="PNAD", icon="📄")
        st.page_link("pages/vigitel.py", label="VIGITEL", icon="☎️")
        st.page_link("pages/viva.py", label="VIVA", icon="🚨")

    with st.expander("Informações Financeiras", expanded=False):
        st.page_link("pages/recursos_federais.py", label="Recursos Federais", icon="🏛️")
        st.page_link("pages/valores_producao.py", label="Valores aprovados", icon="💳")

    st.markdown("<hr style='border:none;border-top:1px solid #ccc;'/>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<hr/>", unsafe_allow_html=True)
    st.subheader("Conecte-se")
    st.markdown("""
- 💼 [LinkedIn](https://www.linkedin.com/in/gregorio-healthdata/)
- ▶️ [YouTube](https://www.youtube.com/@Patients2Python)
- 📸 [Instagram](https://www.instagram.com/patients2python/)
- 🌐 [Site](https://patients2python.com.br/)
- 🐙 [GitHub](https://github.com/gregrodrigues22)
- 👥💬 [Comunidade](https://chat.whatsapp.com/CBn0GBRQie5B8aKppPigdd)
- 🤝💬 [WhatsApp](https://patients2python.sprinthub.site/r/whatsapp-olz)
- 🎓 [Escola](https://app.patients2python.com.br/browse)
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------
# Config da página 
# ---------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def consultar_filtros_com_anos():
    colunas = ["programa_padronizado", "instituicao_padronizada", "regiao", "uf", "validacao_final"]
    filtros = {}

    # Consultar valores únicos para colunas categóricas
    for col in colunas:
        query = f"SELECT DISTINCT {col} FROM `{TABLE_ID}` WHERE {col} IS NOT NULL"
        job = client.query(query, location=BQ_LOCATION)
        df = job.to_dataframe(create_bqstorage_client=True, bqstorage_client=bqs)
        filtros[col] = sorted(df[col].dropna().unique().tolist())

    # Consulta para os anos já existentes
    query_anos = f"""
        SELECT DISTINCT
            formacao_inicio_ano,
            formacao_termino_ano
        FROM `{TABLE_ID}`
        WHERE formacao_inicio_ano IS NOT NULL OR formacao_termino_ano IS NOT NULL
    """
    job = client.query(query_anos, location=BQ_LOCATION)
    df_anos = job.to_dataframe(create_bqstorage_client=True, bqstorage_client=bqs)

    filtros["formacao_inicio_ano"] = sorted(df_anos["formacao_inicio_ano"].dropna().astype(int).unique().tolist())
    filtros["formacao_termino_ano"] = sorted(df_anos["formacao_termino_ano"].dropna().astype(int).unique().tolist())

    return filtros, datetime.now(pytz.timezone("America/Sao_Paulo"))

if "filtros" not in st.session_state:
    with st.spinner("⏳ Carregando dados..."):
        st.session_state["filtros"], st.session_state["ultima_atualizacao"] = consultar_filtros_com_anos()

filtros = st.session_state["filtros"]
ultima_atualizacao = st.session_state["ultima_atualizacao"]

# =====================================================================
# Filtros
# =====================================================================

programa_options    = ["(Todos)"] + filtros.get("programa_padronizado", [])
instituicao_options = ["(Todas)"] + filtros.get("instituicao_padronizada", [])
regiao_options      = ["(Todas)"] + filtros.get("regiao", [])
uf_options          = ["(Todas)"] + filtros.get("uf", [])
validacao_options   = ["(Todas)"] + filtros.get("validacao_final", [])
anos_inicio         = filtros.get("formacao_inicio_ano", [])
anos_termino        = filtros.get("formacao_termino_ano", [])

# =====================================================================
# Layout – Abas
# =====================================================================

def custom_tabs(tabs_list, default=0, cor="rgb(0,161,178)"):
    import streamlit as st
    active_tab = st.radio("", tabs_list, index=default)
    selected = tabs_list.index(active_tab) + 1

    st.markdown(f"""
        <style>
        div[role=radiogroup] {{
            border-bottom: 2px solid rgba(49, 51, 63, 0.1);
            flex-direction: row;
            gap: 2rem;
        }}
        div[role=radiogroup] > label > div:first-of-type {{
            display: none
        }}
        div[role=radiogroup] label {{
            padding-bottom: 0.5em;
            border-radius: 0;
            position: relative;
            top: 3px;
            cursor: pointer;
        }}
        div[role=radiogroup] label p {{
            font-weight: 500;
        }}
        div[role=radiogroup] label:nth-child({selected}) {{
            border-bottom: 3px solid {cor};
        }}
        div[role=radiogroup] label:nth-child({selected}) p {{
            color: {cor};
        }}
        </style>
    """, unsafe_allow_html=True)

    return active_tab

aba = custom_tabs(["📺 Intruções de uso", "🧱 Metodologia", "📥 Downloads", "📈 Analytics"], cor="rgb(0,161,178)")

# ---------------------------------------------------------------------
# Instruções
# ---------------------------------------------------------------------

if aba == "📺 Intruções de uso":
    st.subheader("📺 Intruções de uso")
    st.markdown("""
- Na aba **Metodologia** você pode encontrar detalhes de como os dados foram tratados, plotados e analisados.
- Na aba **Download** você pode baixar a **amostra filtrada** ou o **dataset completo** tratado.
- Na aba **Analytics** você encontra indicadores, séries históricas e rankings. Use os **filtros na barra** para restringir UF, Programa, Instituição e Período.
    """)
    st.markdown("---")
    st.markdown("### Vídeo passo a passo")
    st.video('https://youtu.be/O0fZTR70b7I?si=X1afmDxO9RHTUJ6t') 


# ---------------------------------------------------------------------
# Metodologia
# ---------------------------------------------------------------------

client = bigquery.Client(project=st.secrets["bigquery"]["project_id"], location="southamerica-east1")
TABLE_ID = "escolap2p.base_siscnrm.residentes_applications"

@st.cache_data(ttl=3600, show_spinner=False)
def baseline_counts(table_id: str):
    # Consolida por certificado_hash: se qualquer linha for 'Sim', o hash é válido
    sql = f"""
    WITH por_hash AS (
      SELECT
        certificado_hash,
        MAX(CASE WHEN LOWER(TRIM(validacao_final)) = 'sim' THEN 1 ELSE 0 END) AS is_valid
      FROM `{table_id}`
      GROUP BY certificado_hash
    )
    SELECT
      SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) AS certificados_validos,
      SUM(CASE WHEN is_valid = 0 THEN 1 ELSE 0 END) AS certificados_invalidos
    FROM por_hash
    """
    df = client.query(sql).result().to_dataframe()
    return {
        "cert_validos":   int(df.loc[0, "certificados_validos"] or 0),
        "cert_invalidos": int(df.loc[0, "certificados_invalidos"] or 0),
    }

BASE = baseline_counts(TABLE_ID)  # ← calculado uma vez e “congelado”
fmt = lambda x: f"{x:,}".replace(",", ".")

if aba == "🧱 Metodologia":
    st.subheader("🧱 Metodologia")

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("""
**Escopo**  
- Registros de **certificados de residência médica** (CNRM).

**Aquisição & Atualização** 
- Fonte primária: *Comissão Nacional de Residência Médica (CNRM)*.
- Periodicidade: quando houver atualização pública.  
- Pipeline: extração → padronização de colunas → normalização de datas → enriquecimento (vide abaixo).

**Transformações**  
- Aquisição de dados por UF e empilhamento de todos os dados através do site [Portal CNRM](http://siscnrm.mec.gov.br/certificados).
- Renomeação de nome das colunas.
- Enriquecimento inferindo sexo biológico através do nome do médico.
- Data de início da residência, data de término da residência e data de emissão do certificado padronizadas como data.
- Campos textuais (`programa`, `instituicao`, `uf`) padronizados.  
- Padronização do nome do médico, com criação de identificador único hash para Nome do Médico.
- Padronização do CRM do médico certificado, com criação de identificador único hash para CRM.
- Padronização do Certificado do médico certificado, com criação de identificador único para Certificado.
- Geração de colunas derivadas: `ano_inicio`, `ano_termino`.  
- Enriquecimento com a geração de campo de região para identificar região do país segundo `uf`.
- Padronização de nome de especialidades de acordo com [Resolução CFM](https://sistemas.cfm.org.br/normas/arquivos/resolucoes/BR/2024/2380_2024.pdf?)
- Padronização de duração da formação segundo especialidades de acordo com [Resolução CFM](https://sistemas.cfm.org.br/normas/arquivos/resolucoes/BR/2024/2380_2024.pdf?)
- Padronização de pré-requisitos da formação segundo especialidades de acordo com [Resolução CFM](https://sistemas.cfm.org.br/normas/arquivos/resolucoes/BR/2024/2380_2024.pdf?)
- Padronização de nome da área de atuação de acordo com [Resolução CFM](https://sistemas.cfm.org.br/normas/arquivos/resolucoes/BR/2024/2380_2024.pdf?)
- Padronização de duração da formação segundo área de atuação de acordo com [Resolução CFM](https://sistemas.cfm.org.br/normas/arquivos/resolucoes/BR/2024/2380_2024.pdf?)
- Padronização de pré-requisitos da formação segundo área de atuação de acordo com [Resolução CFM](https://sistemas.cfm.org.br/normas/arquivos/resolucoes/BR/2024/2380_2024.pdf?)
- Criação de coluna derivada de tipo de formação como especialidade ou área de atuação.
- Geração de campo de validação através de verificação de campos válidos: 
  - se linha não contiver data de ínicio OU data de término é considerada inválida.
  - se linha não contiver programa OU instituição OU nome do médico é considerada inválida. 
  - se linha contiver nome de especialidade ou nome de área de atuação não definida pela resolução do CFM é considerada inválida.
  - se linha contiver data de término com diferença de data de início maior que 2 vezes o tempo padrão de duração da formação é considerada inválida.
  - verificação se determinado certificado emitido tem de fato critérios de pré-requesitos. Caso não linha é considerada inválida.
  - ao final, número de linhas inválidas ficam abaixo contabilizadas. 
  - linhas não validadas são descartadas para análise.

**Limitações conhecidas**  
- Registros com dados inválidos.  
- Homônimos de nomes de médicos. 
- Mudanças de nomenclatura institucional e de programa.
        """)

    a, b = st.columns(2)
    a.metric("Certificados válidos (distinct, base)",   fmt(BASE["cert_validos"]),   border=True)
    b.metric("Certificados inválidos (distinct, base)", fmt(BASE["cert_invalidos"]), border=True)

    with c2:
        st.markdown("#### Links úteis")
        st.markdown("""
- 📚 **Fonte oficial**: [Portal CNRM](http://siscnrm.mec.gov.br/certificados)
- 📚 **Referência oficial**: [Resolução CFM](https://sistemas.cfm.org.br/normas/arquivos/resolucoes/BR/2024/2380_2024.pdf?)
- 🧪 **Reprodutibilidade**: código do ETL (em breve no GitHub).
- 🗃️ **Tabela no BigQuery**: `escolap2p.base_siscnrm.residentes_applications`
        """)

    st.warning("⚠️ Quer ter acesso completo a toda metodologia e conjunto de dados do estado bruto ao tratado? Entre em contato conosco: contato@patients2python.com.br ou pelo whatsapp +55 31 9927-5197")

# ---------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------

if aba == "📥 Downloads":

    st.subheader("📥 Downloads")

    def consultar_schema_tabela():
        table = client.get_table(TABLE_ID)
        return pd.DataFrame([{
            "coluna": field.name,
            "tipo": field.field_type,
            "modo": field.mode
        } for field in table.schema])

    dict_cols = consultar_schema_tabela()

    def _csv_bytes(_df: pd.DataFrame) -> bytes:
        return _df.to_csv(index=False).encode("utf-8")

    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("**Consulte o dicionário com a estrutura dos dados raw**")
        st.download_button(
            "📄 Baixar dicionário (CSV)",
            data=dict_cols.to_csv(index=False).encode('utf-8'),
            file_name=f"crnm_dicionario_{datetime.now().date()}.csv",
            mime="text/csv",
            use_container_width=True,
            key="botao_dicionario"
            )

    # Filtros
    st.markdown("**Aplique filtros para personalizar os dados a serem baixados**")
    c3, c4 = st.columns([1, 1])

    with c3:
        selected_programa = st.selectbox("Programas", options=programa_options, index=0, key="selectbox_programa_download")
        selected_instituicao = st.selectbox("Instituição", options=instituicao_options, index=0, key="selected_instituicao_download")
        selected_regiao = st.selectbox("Região", options=regiao_options, index=0, key="selected_regiao_download")
        selected_uf = st.selectbox("UF", options=uf_options, index=0, key="selected_uf_download")

    with c4:
        range_inicio = None
        range_termino = None

        if anos_inicio:
            anos_inicio_limpos = sorted(set(int(ano) for ano in anos_inicio if pd.notnull(ano) and str(ano).isdigit()))
            if anos_inicio_limpos:
                min_inicio, max_inicio = min(anos_inicio_limpos), max(anos_inicio_limpos)
                range_inicio = st.slider(
                    "Período (ano de início)", 
                    min_inicio, 
                    max_inicio, 
                    (min_inicio, max_inicio)
                )

        if anos_termino:
            anos_termino_limpos = sorted(set(int(ano) for ano in anos_termino if pd.notnull(ano) and str(ano).isdigit()))
            if anos_termino_limpos:
                min_termino, max_termino = min(anos_termino_limpos), max(anos_termino_limpos)
                range_termino = st.slider(
                    "Período (ano de término)", 
                    min_termino, 
                    max_termino, 
                    (min_termino, max_termino)
                )

    @st.cache_data(ttl=1800, show_spinner=True)
    def consultar_agrupado_por_filtros(
        programa_padronizado=None,
        instituicao_padronizada=None,
        regiao=None,
        uf=None,
        validacao_final=None,
        formacao_inicio_ano=None,
        formacao_termino_ano=None
    ):
        condicoes = []
        
        condicoes.append("LOWER(TRIM(validacao_final)) = 'sim'")

        if programa_padronizado and programa_padronizado != "(Todos)":
            condicoes.append(f"programa_padronizado = '{programa_padronizado}'")
        if instituicao_padronizada and instituicao_padronizada != "(Todas)":
            condicoes.append(f"instituicao_padronizada = '{instituicao_padronizada}'")
        if regiao and regiao != "(Todas)":
            condicoes.append(f"regiao = '{regiao}'")
        if uf and uf != "(Todas)":
            condicoes.append(f"uf = '{uf}'")
        if formacao_inicio_ano:
            condicoes.append(f"formacao_inicio_ano BETWEEN {formacao_inicio_ano[0]} AND {formacao_inicio_ano[1]}")
        if formacao_termino_ano:
            condicoes.append(f"formacao_termino_ano BETWEEN {formacao_termino_ano[0]} AND {formacao_termino_ano[1]}")

        where_clause = "WHERE " + " AND ".join(condicoes) if condicoes else ""

        group_dims = ["regiao", "uf", "instituicao_padronizada", "programa_padronizado","formacao_inicio_ano","formacao_termino_ano"]
        select_clause = ", ".join(group_dims)

        query = f"""
        SELECT
        {select_clause},
        COUNT(DISTINCT certificado_hash) AS qtd_certificados
        FROM `{TABLE_ID}`
        {where_clause}
        GROUP BY {select_clause}
        ORDER BY qtd_certificados DESC
        """

        job = client.query(query, location=BQ_LOCATION)
        job.result(timeout=180)
        df = job.to_dataframe(create_bqstorage_client=True, bqstorage_client=bqs)

        # --- NOVO: total sem supercontagem (mesmo WHERE, sem GROUP BY) ---
        query_total = f"""
        SELECT COUNT(DISTINCT certificado_hash) AS total_validos
        FROM `{TABLE_ID}`
        {where_clause}
        """
        total = client.query(query_total, location=BQ_LOCATION).result().to_dataframe().iloc[0]["total_validos"]

        return df, int(total)
    
    st.info("Os downloads abaixo respeitam os **filtros** (quando aplicados).")

    def manter_aba_download():
        st.session_state["aba_ativa"] = abas[2]

    if st.button("Consultar dados agregados"):
        with st.spinner("⏳ Consultando dados no BigQuery..."):
            df_resultado, total = consultar_agrupado_por_filtros(
                programa_padronizado=selected_programa,
                instituicao_padronizada=selected_instituicao,
                regiao=selected_regiao,
                uf=selected_uf,
                formacao_inicio_ano=range_inicio,
                formacao_termino_ano=range_termino,
            )
        st.success("✅ Consulta finalizada com sucesso!")
        valor_formatado = f"{total:,}".replace(",", ".")
        st.metric("Certificados válidos", valor_formatado, border=True)
        st.dataframe(df_resultado)

    if 'df_resultado' in locals() and not df_resultado.empty:
        st.download_button(
            "📥 Baixar dados filtrados (CSV)",
            data=_csv_bytes(df_resultado),
            file_name=f"cnrm_residentes_filtrado_{datetime.now().date()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.warning("⚠️ Realize uma consulta antes de baixar os dados.")

# ---------------------------------------------------------------------
# 4) Analytics
# ---------------------------------------------------------------------

if aba == "📈 Analytics":
    import numpy as np
    import pandas as pd
    import plotly.express as px
    from google.cloud import bigquery

    st.subheader("📈 Analytics")

    # --- BigQuery / Tabela e colunas ---
    client = bigquery.Client(
        project=st.secrets["bigquery"]["project_id"],
        location="southamerica-east1",
    )
    TABLE_ID = "escolap2p.base_siscnrm.residentes_applications"

    # Mapeie os nomes das colunas usadas na sua tabela
    COL_PROG     = "programa_padronizado"
    COL_INST     = "instituicao_padronizada"
    COL_REGIAO   = "regiao"
    COL_UF       = "uf"
    COL_ANO_INI  = "formacao_inicio_ano"
    COL_ANO_FIM  = "formacao_termino_ano"

    # NOVOS FILTROS
    COL_SEXO         = "medico_sexo_inferido"                       # 'masculino'/'feminino'/...
    COL_TIPO_FORM    = "formacao_padronizada_tipo"                  # ex.: 'Programa de Residência'
    COL_ESPEC_BASICA = "formacao_padronizada_especialidade_basica"  # 'Sim'/'Não'
    COL_ENTRADA_DIR  = "formacao_padronizada_entrada_direta"        # 'Sim'/'Não'
    COL_ETAPA        = "formacao_etapa_residencia"                  # 'R1','R2','R3',...
    COL_DURACAO      = "formacao_duracao_anos"                      # numérico
    COL_ANO_EMISSAO  = "certificado_emissao_ano"                    # ano

    def _to_list(x):
        """Converte ndarray/None para lista sem ambiguidade booleana."""
        return [] if x is None else list(x)

    @st.cache_data(ttl=1800, show_spinner=True)
    def carregar_opcoes_filtros():
        """
        Busca no BigQuery as listas de opções e limites de anos (apenas válidos).
        Retorna um dict com listas ordenadas + min/max.
        """
        sql = f"""
        WITH base AS (
          SELECT
            LOWER(TRIM(validacao_final)) AS vf,

            {COL_PROG}   AS prog,
            {COL_INST}   AS inst,
            {COL_REGIAO} AS regiao,
            UPPER({COL_UF}) AS uf,

            CAST({COL_ANO_INI} AS INT64) AS ano_ini,
            CAST({COL_ANO_FIM} AS INT64) AS ano_fim,

            {COL_SEXO}          AS sexo,
            {COL_TIPO_FORM}     AS tipo_form,
            {COL_ESPEC_BASICA}  AS espec_basica,
            {COL_ENTRADA_DIR}   AS entrada_dir,
            {COL_ETAPA}         AS etapa,
            CAST({COL_DURACAO} AS INT64) AS duracao,
            CAST({COL_ANO_EMISSAO} AS INT64) AS ano_emissao
          FROM `{TABLE_ID}`
        )
        SELECT
          -- opções "clássicas"
          ARRAY_AGG(DISTINCT prog   IGNORE NULLS ORDER BY prog)   AS programas,
          ARRAY_AGG(DISTINCT inst   IGNORE NULLS ORDER BY inst)   AS instituicoes,
          ARRAY_AGG(DISTINCT regiao IGNORE NULLS ORDER BY regiao) AS regioes,
          ARRAY_AGG(DISTINCT uf     IGNORE NULLS ORDER BY uf)     AS ufs,

          -- limites dos anos de formação
          MIN(ano_ini) AS min_ini, MAX(ano_ini) AS max_ini,
          MIN(ano_fim) AS min_fim, MAX(ano_fim) AS max_fim,

          -- NOVOS: opções adicionais
          ARRAY_AGG(DISTINCT sexo         IGNORE NULLS ORDER BY sexo)        AS sexos,
          ARRAY_AGG(DISTINCT tipo_form    IGNORE NULLS ORDER BY tipo_form)   AS tipos_form,
          ARRAY_AGG(DISTINCT espec_basica IGNORE NULLS ORDER BY espec_basica) AS op_espec_basica,
          ARRAY_AGG(DISTINCT entrada_dir  IGNORE NULLS ORDER BY entrada_dir)  AS op_entrada_dir,
          ARRAY_AGG(DISTINCT etapa        IGNORE NULLS ORDER BY etapa)        AS etapas,

          -- limites para sliders adicionais
          MIN(duracao)     AS min_dur,     MAX(duracao)     AS max_dur,
          MIN(ano_emissao) AS min_emissao, MAX(ano_emissao) AS max_emissao

        FROM base
        WHERE vf = 'sim'
        """
        df = client.query(sql).result().to_dataframe()
        r = df.iloc[0]
        return dict(
            programas       = _to_list(r["programas"]),
            instituicoes    = _to_list(r["instituicoes"]),
            regioes         = _to_list(r["regioes"]),
            ufs             = _to_list(r["ufs"]),
            min_ini         = int(r["min_ini"]) if pd.notna(r["min_ini"]) else 1980,
            max_ini         = int(r["max_ini"]) if pd.notna(r["max_ini"]) else 2026,
            min_fim         = int(r["min_fim"]) if pd.notna(r["min_fim"]) else 1980,
            max_fim         = int(r["max_fim"]) if pd.notna(r["max_fim"]) else 2026,

            sexos           = _to_list(r["sexos"]),
            tipos_form      = _to_list(r["tipos_form"]),
            op_espec_basica = _to_list(r["op_espec_basica"]),
            op_entrada_dir  = _to_list(r["op_entrada_dir"]),
            etapas          = _to_list(r["etapas"]),
            min_dur         = int(r["min_dur"]) if pd.notna(r["min_dur"]) else 1,
            max_dur         = int(r["max_dur"]) if pd.notna(r["max_dur"]) else 6,
            min_emissao     = int(r["min_emissao"]) if pd.notna(r["min_emissao"]) else 1980,
            max_emissao     = int(r["max_emissao"]) if pd.notna(r["max_emissao"]) else 2026,
        )

    # Carrega opções e limites
    op = carregar_opcoes_filtros()

    # -------------------- FILTROS (topo) --------------------
    st.info("🔎 **Sessão de Filtros: Use os controles abaixo para refinar os resultados.**")

    # Linha 1 — filtros clássicos
    c1, c2, c3, c4 = st.columns(4)
    selected_programa = c1.selectbox(
        "Programas", options=["(Todos)"] + op["programas"], index=0, key="f_programa",
    )
    selected_instituicao = c2.selectbox(
        "Instituição", options=["(Todas)"] + op["instituicoes"], index=0, key="f_instituicao",
    )
    selected_regiao = c3.selectbox(
        "Região", options=["(Todas)"] + op["regioes"], index=0, key="f_regiao",
    )
    selected_uf = c4.selectbox(
        "UF", options=["(Todas)"] + op["ufs"], index=0, key="f_uf",
    )

    # Linha 2 — novos selects
    c5, c6, c7, c8 = st.columns(4)
    selected_sexo = c5.selectbox(
        "Sexo do médico", options=["(Todos)"] + op["sexos"], index=0, key="f_sexo",
    )
    selected_tipo_form = c6.selectbox(
        "Tipo de formação", options=["(Todos)"] + op["tipos_form"], index=0, key="f_tipo_form",
    )
    selected_espec_basica = c7.selectbox(
        "Especialidade básica?", options=["(Ambos)"] + op["op_espec_basica"], index=0, key="f_espec_basica",
    )
    selected_entrada_dir = c8.selectbox(
        "Entrada direta?", options=["(Ambos)"] + op["op_entrada_dir"], index=0, key="f_entrada_dir",
    )

    # Linha 3 — sliders adicionais
    s1, s2 = st.columns(2)

    padrao_duracao_min = max(op["min_dur"], 1)
    padrao_duracao_max = min(op["max_dur"], 6)
    range_duracao = s1.slider(
        "Duração (anos)",
        min_value=op["min_dur"], 
        max_value=op["max_dur"],
        value=(padrao_duracao_min,padrao_duracao_max), 
        step=1, key="f_duracao",
    )
    
    # Ano de emissão do certificado: padrão 2012–2024 (respeitando os limites)
    padrao_emissao_min = max(op["min_emissao"], 2012)
    padrao_emissao_max = min(op["max_emissao"], 2024)
    range_emissao = s2.slider(
        "Ano de emissão do certificado [Filtro padrão para Dados Qualitativos]",
        min_value=op["min_emissao"], max_value=op["max_emissao"],
        value=(padrao_emissao_min, padrao_emissao_max),
        step=1, key="f_emissao",
    )

    # Linha 4 — sliders de período de formação
    s3, s4 = st.columns(2)

    # valores padrão desejados, mas respeitando os limites do dataset
    padrao_ini_min = max(op["min_ini"], 2010)
    padrao_ini_max = min(op["max_ini"], 2022)
    range_inicio = s3.slider(
        "Ano de início da formação [Filtro padrão para Dados Qualitativos]",
        min_value=op["min_ini"], max_value=op["max_ini"],
        value=(padrao_ini_min, padrao_ini_max),
        step=1, key="f_range_inicio",
    )

    # Término: padrão 2010–2024
    padrao_fim_min = max(op["min_fim"], 2010)
    padrao_fim_max = min(op["max_fim"], 2024)
    range_termino = s4.slider(
        "Ano de término da formação [Filtro padrão para Dados Qualitativos]",
        min_value=op["min_fim"], max_value=op["max_fim"],
        value=(padrao_fim_min, padrao_fim_max),
        step=1, key="f_range_termino",
    )

    st.caption("Os gráficos abaixo respeitam os **filtros** quando aplicados.")

    # =================================================================
    # WHERE baseado nos ALIASES (para Grandes Números)
    # =================================================================
    def _where_from_filters() -> str:
        cond = []
        cond.append("LOWER(TRIM(validacao_final)) = 'sim'")

        if selected_programa and selected_programa != "(Todos)":
            cond.append(f"programa = '{selected_programa}'")
        if selected_instituicao and selected_instituicao != "(Todas)":
            cond.append(f"instituicao = '{selected_instituicao}'")
        if selected_regiao and selected_regiao != "(Todas)":
            cond.append(f"regiao = '{selected_regiao}'")
        if selected_uf and selected_uf != "(Todas)":
            cond.append(f"uf = '{selected_uf}'")

        if "selected_sexo" in globals() and selected_sexo and selected_sexo != "(Todos)":
            cond.append(f"sexo = '{selected_sexo.lower()}'")

        if "selected_tipo_form" in globals() and selected_tipo_form and selected_tipo_form != "(Todos)":
            cond.append(f"tipo_formacao = '{selected_tipo_form}'")

        if "selected_espec_basica" in globals() and selected_espec_basica and selected_espec_basica != "(Ambos)":
            cond.append(f"esp_basica = '{selected_espec_basica.lower()}'")

        if "selected_entrada_dir" in globals() and selected_entrada_dir and selected_entrada_dir != "(Ambos)":
            cond.append(f"entrada_direta = '{selected_entrada_dir.lower()}'")

        # Duração [min, max] — inclui nulos
        if "range_duracao" in globals() and isinstance(range_duracao, (list, tuple)) and len(range_duracao) == 2:
            dmin, dmax = range_duracao
            cond.append(f"(duracao_anos BETWEEN {int(dmin)} AND {int(dmax)} OR duracao_anos IS NULL)")

        # Ano de início [min, max] — inclui nulos
        if "range_inicio" in globals() and isinstance(range_inicio, (list, tuple)) and len(range_inicio) == 2:
            amin, amax = range_inicio
            cond.append(f"(ano_ini BETWEEN {int(amin)} AND {int(amax)} OR ano_ini IS NULL)")

        # Ano de término [min, max] — inclui nulos
        if "range_termino" in globals() and isinstance(range_termino, (list, tuple)) and len(range_termino) == 2:
            tmin, tmax = range_termino
            cond.append(f"(ano_fim BETWEEN {int(tmin)} AND {int(tmax)} OR ano_fim IS NULL)")

        # Ano de emissão [min, max] — inclui nulos
        if "range_emissao" in globals() and isinstance(range_emissao, (list, tuple)) and len(range_emissao) == 2:
            emin, emax = range_emissao
            cond.append(f"(ano_emissao BETWEEN {int(emin)} AND {int(emax)} OR ano_emissao IS NULL)")

        return ("WHERE " + " AND ".join(cond)) if cond else ""

    # =================================================================
    # WHERE para a TABELA BRUTA (para gráficos) — nomes reais das colunas
    # =================================================================
    def where_for_raw_table(prefix_with_and: bool = False) -> str:
        cond = []

        if selected_programa and selected_programa != "(Todos)":
            cond.append(f"{COL_PROG} = '{selected_programa}'")
        if selected_instituicao and selected_instituicao != "(Todas)":
            cond.append(f"{COL_INST} = '{selected_instituicao}'")
        if selected_regiao and selected_regiao != "(Todas)":
            cond.append(f"{COL_REGIAO} = '{selected_regiao}'")
        if selected_uf and selected_uf != "(Todas)":
            cond.append(f"UPPER({COL_UF}) = '{selected_uf}'")

        if "selected_sexo" in globals() and selected_sexo and selected_sexo != "(Todos)":
            cond.append(f"LOWER(TRIM({COL_SEXO})) = '{selected_sexo.lower()}'")

        if "selected_tipo_form" in globals() and selected_tipo_form and selected_tipo_form != "(Todos)":
            cond.append(f"{COL_TIPO_FORM} = '{selected_tipo_form}'")

        if "selected_espec_basica" in globals() and selected_espec_basica and selected_espec_basica != "(Ambos)":
            cond.append(f"LOWER(TRIM({COL_ESPEC_BASICA})) = '{selected_espec_basica.lower()}'")

        if "selected_entrada_dir" in globals() and selected_entrada_dir and selected_entrada_dir != "(Ambos)":
            cond.append(f"LOWER(TRIM({COL_ENTRADA_DIR})) = '{selected_entrada_dir.lower()}'")

        if "range_duracao" in globals() and isinstance(range_duracao, (list, tuple)) and len(range_duracao) == 2:
            dmin, dmax = range_duracao
            cond.append(f"CAST({COL_DURACAO} AS INT64) BETWEEN {int(dmin)} AND {int(dmax)}")

        if "range_inicio" in globals() and isinstance(range_inicio, (list, tuple)) and len(range_inicio) == 2:
            amin, amax = range_inicio
            cond.append(f"CAST({COL_ANO_INI} AS INT64) BETWEEN {int(amin)} AND {int(amax)}")

        if "range_termino" in globals() and isinstance(range_termino, (list, tuple)) and len(range_termino) == 2:
            tmin, tmax = range_termino
            cond.append(f"CAST({COL_ANO_FIM} AS INT64) BETWEEN {int(tmin)} AND {int(tmax)}")

        if "range_emissao" in globals() and isinstance(range_emissao, (list, tuple)) and len(range_emissao) == 2:
            emin, emax = range_emissao
            cond.append(f"CAST({COL_ANO_EMISSAO} AS INT64) BETWEEN {int(emin)} AND {int(emax)}")

        if not cond:
            return ""
        return ("AND " if prefix_with_and else "WHERE ") + " AND ".join(cond)

    # =================================================================
    # Grandes Números  (mantém como estava)
    # =================================================================
    # ========= chave de cache/refresh baseada nos filtros =========

     # -------------------- Seção (topo) --------------------
    st.info("📏 Sessão de Grandes Números: Visão rápida dos números gerais segundo os filtros aplicados**")
    
    def filtros_hash() -> str:
        filtros_dict = {
            "prog": selected_programa,
            "inst": selected_instituicao,
            "reg": selected_regiao,
            "uf":  selected_uf,
            "sexo": selected_sexo,
            "tipo": selected_tipo_form,
            "esp":  selected_espec_basica,
            "ent":  selected_entrada_dir,
            "dur":  tuple(range_duracao) if isinstance(range_duracao, (list, tuple)) else range_duracao,
            "ini":  tuple(range_inicio)  if isinstance(range_inicio,  (list, tuple)) else range_inicio,
            "fim":  tuple(range_termino) if isinstance(range_termino, (list, tuple)) else range_termino,
            "emi":  tuple(range_emissao) if isinstance(range_emissao, (list, tuple)) else range_emissao,
        }
        return hashlib.md5(str(filtros_dict).encode()).hexdigest()

    FILTROS_KEY = filtros_hash()

    # ========= helpers cacheados que respeitam os filtros =========
    @st.cache_data(ttl=900, show_spinner=False)
    def run_sql(sql: str, filtros_key: str) -> pd.DataFrame:
        """Executa SQL e cacheia por TTL + hash dos filtros."""
        return client.query(sql).result().to_dataframe()

    @st.cache_data(ttl=900, show_spinner=False)
    def consultar_big_numbers_cached(where_clause: str, filtros_key: str) -> dict:
        sql = f"""
        WITH base AS (
        SELECT
            LOWER(TRIM(validacao_final))                         AS vf,
            {COL_PROG}                                           AS programa,
            {COL_INST}                                           AS instituicao,
            {COL_REGIAO}                                         AS regiao,
            UPPER({COL_UF})                                      AS uf,
            LOWER(TRIM(medico_sexo_inferido))                    AS sexo,
            formacao_padronizada_tipo                            AS tipo_formacao,
            LOWER(TRIM(formacao_padronizada_especialidade_basica)) AS esp_basica,
            LOWER(TRIM(formacao_padronizada_entrada_direta))     AS entrada_direta,
            CAST(formacao_duracao_anos AS INT64)                 AS duracao_anos,
            CAST(formacao_inicio_ano  AS INT64)                  AS ano_ini,
            CAST(formacao_termino_ano AS INT64)                  AS ano_fim,
            CAST(certificado_emissao_ano AS INT64)               AS ano_emissao,
            medico_nome_hash,
            certificado_hash
        FROM `{TABLE_ID}`
        )
        SELECT
        COUNT(DISTINCT IF(vf = 'sim', certificado_hash, NULL)) AS cert_validos,
        COUNT(DISTINCT IF(vf != 'sim' OR vf IS NULL, certificado_hash, NULL)) AS cert_invalidos,
        COUNT(DISTINCT IF(vf = 'sim', instituicao,       NULL)) AS instituicoes_validas,
        COUNT(DISTINCT IF(vf = 'sim', programa,          NULL)) AS programas_validos,
        COUNT(DISTINCT IF(vf = 'sim', regiao,            NULL)) AS regioes_validas,
        COUNT(DISTINCT IF(vf = 'sim', uf,                NULL)) AS ufs_validas,
        COUNT(DISTINCT IF(vf = 'sim', medico_nome_hash,  NULL)) AS medicos_formados_validos,
        SAFE_DIVIDE(
            COUNT(DISTINCT IF(vf = 'sim', certificado_hash, NULL)),
            COUNT(DISTINCT IF(vf = 'sim', medico_nome_hash,  NULL))
        ) AS media_cert_por_medico,
        AVG(IF(vf = 'sim', duracao_anos, NULL)) AS media_duracao_anos
        FROM base
        {where_clause.replace("validacao_final", "vf")}
        """
        df = client.query(sql).result().to_dataframe()
        row = df.iloc[0].to_dict()
        return {
            "cert_validos":               int(row.get("cert_validos", 0) or 0),
            "cert_invalidos":             int(row.get("cert_invalidos", 0) or 0),
            "instituicoes_validas":       int(row.get("instituicoes_validas", 0) or 0),
            "programas_validos":          int(row.get("programas_validos", 0) or 0),
            "regioes_validas":            int(row.get("regioes_validas", 0) or 0),
            "ufs_validas":                int(row.get("ufs_validas", 0) or 0),
            "medicos_formados_validos":   int(row.get("medicos_formados_validos", 0) or 0),
            "media_cert_por_medico":    float(row.get("media_cert_por_medico", 0.0) or 0.0),
            "media_duracao_anos":       float(row.get("media_duracao_anos", 0.0) or 0.0),
        }

    # ===============================================================
    # a partir daqui, tudo fica dentro de um spinner único
    # ===============================================================
    with st.spinner("🔄 Recalculando conforme filtros..."):

        # -------- Grandes números (usa cache por hash) --------
        where_clause = _where_from_filters()
        nums = consultar_big_numbers_cached(where_clause, FILTROS_KEY)

        fmt_int = lambda v: f"{int(v):,}".replace(",", ".")
        fmt_1d  = lambda v: f"{v:.2f}".replace(".", ",")

        c1, c2, c3, c4 = st.columns(4)
        c5, c6, c7, c8 = st.columns(4)

        c1.metric("Certificados válidos",     fmt_int(nums["cert_validos"]))
        c2.metric("Instituições (dist.)",     fmt_int(nums["instituicoes_validas"]))
        c3.metric("Programas (dist.)",        fmt_int(nums["programas_validos"]))
        c4.metric("Regiões (dist.)",          fmt_int(nums["regioes_validas"]))
        c5.metric("UFs (dist.)",              fmt_int(nums["ufs_validas"]))
        c6.metric("Médicos formados (dist.)", fmt_int(nums["medicos_formados_validos"]))
        c7.metric("Média de certificados por médico", fmt_1d(nums["media_cert_por_medico"]))
        c8.metric("Média de duração (anos)",          fmt_1d(nums["media_duracao_anos"]))

        # ------------------------------------------------------------
        # Gráficos — use run_sql(sql, FILTROS_KEY) em vez de _run
        # ------------------------------------------------------------
        # -------------------- Seção (topo) --------------------
        st.info("📊 Sessão de Gráficos: Visuais para resposta de perguntas segundo os filtros aplicados**")
        # ========= Certificados por ano =========
        with st.expander("Quantos certificados foram emitidos por ano?", expanded=True):
            sql = f"""
            SELECT CAST({COL_ANO_EMISSAO} AS INT64) AS ano,
                COUNT(DISTINCT certificado_hash) AS qtd
            FROM `{TABLE_ID}`
            WHERE LOWER(TRIM(validacao_final)) = 'sim'
            {where_for_raw_table(prefix_with_and=True)}
            GROUP BY ano
            HAVING ano IS NOT NULL
            ORDER BY ano
            """
            df_y = run_sql(sql, FILTROS_KEY)
            df_y["qtd"] = pd.to_numeric(df_y["qtd"], errors="coerce").fillna(0).astype(np.int64)
            fig = graph.bar_yoy_trend(
                df_y, x="ano", y="qtd",
                title="Quantidade de certificados (válidos) emitidos por ano",
                x_is_year=True, fill_missing_years=True,
                show_ma=False, ma_window=0, show_mean=True, show_trend=True,
                y_label="Certificados (distintos)", legend_pos="top",
            )
            st.plotly_chart(fig, use_container_width=True)

        # ---------- Regiões ----------
        with st.expander("Quantos certificados foram emitidos por Regiões do País?", expanded=True):
            sql_reg = f"""
            SELECT {COL_REGIAO} AS regiao,
                COUNT(DISTINCT certificado_hash) AS total
            FROM `{TABLE_ID}`
            WHERE LOWER(TRIM(validacao_final)) = 'sim'
            {where_for_raw_table(prefix_with_and=True)}
            GROUP BY regiao
            HAVING regiao IS NOT NULL
            """
            df_reg = run_sql(sql_reg, FILTROS_KEY)
            df_reg["total"] = pd.to_numeric(df_reg["total"], errors="coerce").fillna(0).astype(np.int64)
            if df_reg.empty:
                st.info("Sem dados para os filtros atuais.")
            else:
                fig = graph.pareto_barh(
                    df=df_reg, cat_col="regiao", value_col="total",
                    title="Gráfico de Pareto dos Certificados Emitidos por Região",
                    colorbar_title="Certificados",
                )
                st.plotly_chart(fig, use_container_width=True)

        # ---------- UF ----------
        with st.expander("Quantos certificados foram emitidos por UF do País?", expanded=True):
            sql_uf = f"""
            SELECT {COL_UF} AS uf,
                COUNT(DISTINCT certificado_hash) AS total
            FROM `{TABLE_ID}`
            WHERE LOWER(TRIM(validacao_final)) = 'sim'
            {where_for_raw_table(prefix_with_and=True)}
            GROUP BY uf
            HAVING uf IS NOT NULL
            """
            df_uf = run_sql(sql_uf, FILTROS_KEY)
            df_uf["total"] = pd.to_numeric(df_uf["total"], errors="coerce").fillna(0).astype(np.int64)
            if df_uf.empty:
                st.info("Sem dados para os filtros atuais.")
            else:
                fig = graph.pareto_barh(
                    df=df_uf, cat_col="uf", value_col="total",
                    title="Gráfico de Pareto dos Certificados Emitidos por UF",
                    colorbar_title="Certificados",
                )
                st.plotly_chart(fig, use_container_width=True)

        # ---------- Programas ----------
        with st.expander("Quais foram os programas que mais emitiram certificados (Top 10)?", expanded=True):
            sql_prog = f"""
            SELECT {COL_PROG} AS programa,
                COUNT(DISTINCT certificado_hash) AS qtd
            FROM `{TABLE_ID}`
            WHERE LOWER(TRIM(validacao_final)) = 'sim'
            {where_for_raw_table(prefix_with_and=True)}
            GROUP BY programa
            HAVING programa IS NOT NULL
            """
            df_prog = run_sql(sql_prog, FILTROS_KEY)
            df_prog["qtd"] = pd.to_numeric(df_prog["qtd"], errors="coerce").fillna(0).astype(np.int64)
            if df_prog.empty:
                st.info("Sem dados para os filtros atuais.")
            else:
                fig = graph.bar_total_por_grupo(
                    df_prog, grupo_col="programa", valor_col="qtd", top_n=10,
                    titulo="Programas Top 10 com mais certificados (válidos)",
                    x_label="Certificados (distintos)", y_label="Programa",
                )
                st.plotly_chart(fig, use_container_width=True)

        # ---------- Instituições ----------
        with st.expander("Quais foram as Instituições que mais emitiram certificados (Top 10)?", expanded=True):
            sql_inst = f"""
            SELECT {COL_INST} AS instituicao,
                COUNT(DISTINCT certificado_hash) AS qtd
            FROM `{TABLE_ID}`
            WHERE LOWER(TRIM(validacao_final)) = 'sim'
            {where_for_raw_table(prefix_with_and=True)}
            GROUP BY instituicao
            HAVING instituicao IS NOT NULL
            """
            df_inst = run_sql(sql_inst, FILTROS_KEY)
            df_inst["qtd"] = pd.to_numeric(df_inst["qtd"], errors="coerce").fillna(0).astype(np.int64)
            if df_inst.empty:
                st.info("Sem dados para os filtros atuais.")
            else:
                fig = graph.bar_total_por_grupo(
                    df_inst, grupo_col="instituicao", valor_col="qtd", top_n=10,
                    titulo="Instituições Top 10 com mais certificados (válidos)",
                    x_label="Certificados (distintos)", y_label="Instituição",
                )
                st.plotly_chart(fig, use_container_width=True)

        # ---------- Sexo ----------
        with st.expander("Quantos certificados foram emitidos por sexo do médico?", expanded=True):
            sql = f"""
            SELECT COALESCE(LOWER(TRIM(medico_sexo_inferido)), '(não informado)') AS sexo,
                COUNT(DISTINCT certificado_hash) AS qtd
            FROM `{TABLE_ID}`
            WHERE LOWER(TRIM(validacao_final)) = 'sim'
            {where_for_raw_table(prefix_with_and=True)}
            GROUP BY sexo
            ORDER BY qtd DESC
            """
            df_sexo = run_sql(sql, FILTROS_KEY)
            df_sexo["qtd"] = pd.to_numeric(df_sexo["qtd"], errors="coerce").fillna(0).astype(np.int64)
            cores = {"masculino": "#60A5FA", "feminino": "#F87171", "(não informado)": "#94A3B8"}
            fig = graph.pie_standard(df_sexo, names="sexo", values="qtd", top_n=2,
                                    title="Quantidade de certificados (válidos) emitidos por sexo do médico",
                                    color_discrete_map=cores, legend_pos="below_title")
            st.plotly_chart(fig, use_container_width=True)

        # ---------- Entradas x Saídas ----------
        with st.expander("Quantos médicos entraram e saíram por ano de residência?", expanded=True):
            COL_MED_HASH = "medico_nome_hash"
            COL_ANO_RES  = "formacao_ano_residencia"
            COL_ANO_INI  = "formacao_inicio_ano"
            COL_ANO_FIM  = "formacao_termino_ano"
            sql_ano = f"""
            WITH base AS (
            SELECT
                CAST({COL_ANO_RES} AS INT64)    AS ano_res,
                CAST({COL_ANO_INI} AS INT64)    AS ano_inicio,
                CAST({COL_ANO_FIM} AS INT64)    AS ano_termino,
                {COL_MED_HASH} AS medico_hash
            FROM `{TABLE_ID}`
            WHERE {COL_MED_HASH} IS NOT NULL
                {where_for_raw_table(prefix_with_and=True)}
            ),
            entradas AS (
            SELECT ano_res AS ano, COUNT(DISTINCT medico_hash) AS qtd
            FROM base WHERE ano_inicio IS NOT NULL AND ano_res = ano_inicio
            GROUP BY 1
            ),
            saidas AS (
            SELECT ano_res AS ano, COUNT(DISTINCT medico_hash) AS qtd
            FROM base WHERE ano_termino IS NOT NULL AND ano_res = ano_termino
            GROUP BY 1
            )
            SELECT COALESCE(e.ano, s.ano) AS ano,
                COALESCE(e.qtd, 0) AS entradas,
                COALESCE(s.qtd, 0) AS saidas
            FROM entradas e
            FULL OUTER JOIN saidas s ON e.ano = s.ano
            ORDER BY ano
            """
            df_ano = run_sql(sql_ano, FILTROS_KEY)
            if df_ano.empty:
                st.info("Sem dados para os filtros atuais.")
            else:
                df_ano["entradas"] = pd.to_numeric(df_ano["entradas"], errors="coerce").fillna(0).astype(int)
                df_ano["saidas"]   = pd.to_numeric(df_ano["saidas"],   errors="coerce").fillna(0).astype(int)
                df_ano["ano"]      = pd.to_numeric(df_ano["ano"],      errors="coerce").astype("Int64")
                df_ano = df_ano[df_ano["ano"].notna()].copy()
                df_ano["ano"] = df_ano["ano"].astype(int)
                fig = graph.barras_bilaterais_entradas_saidas_ano(
                    df_ano, ano_col="ano", entradas_col="entradas", saidas_col="saidas",
                    titulo="Entradas (+) vs Saídas (–) por ano (médicos distintos)",
                    cor_entradas="rgb(19, 93, 171)", cor_saidas="rgb(0, 176, 239)",
                    altura=560, largura=1100,
                )
                st.plotly_chart(fig, use_container_width=True)

        # ---------- Heatmap Residentes ----------
        with st.expander("Qual a quantidade de Residentes por momento do Ciclo de Formação e por Ano?", expanded=True):
            sql_residente = f"""
            SELECT
            CAST(formacao_ano_residencia AS INT64) AS ano,
            formacao_etapa_residencia    AS etapa,
            COUNT(DISTINCT IF(LOWER(TRIM(validacao_final))='sim', medico_nome_hash, NULL)) AS qtd
            FROM `{TABLE_ID}`
            WHERE LOWER(TRIM(validacao_final)) = 'sim'
            {where_for_raw_table(prefix_with_and=True)}
            GROUP BY ano, etapa
            """
            df_residente = run_sql(sql_residente, FILTROS_KEY)
            df_residente["ano"] = pd.to_numeric(df_residente["ano"], errors="coerce").astype(np.int64)
            df_residente["qtd"] = pd.to_numeric(df_residente["qtd"], errors="coerce").fillna(0).astype(np.int64)
            df_residente = df_residente.sort_values(["etapa", "ano"])
            fig = graph.heatmap_absoluto(
                df_residente, row_col="etapa", col_col="ano", value_col="qtd",
                title="Total de residentes por ciclo da formação e ano (absoluto + % no ano)",
                percent_of="col", show_totals="col", zero_as_blank=True, decimals=1,
            )
            st.plotly_chart(fig, use_container_width=True)