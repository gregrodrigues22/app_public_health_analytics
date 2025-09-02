# ---------------------------------------------------------------
# Set up
# ---------------------------------------------------------------
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import json
import os
from datetime import datetime
import pytz
from pathlib import Path

from google.cloud import bigquery
from google.cloud import bigquery_storage

# ---------------------------------------------------------------
# BigQuery (região e tabela)
# ---------------------------------------------------------------
PROJECT_ID  = "escolap2p"
BQ_LOCATION = "southamerica-east1"
TABLE_ID    = "escolap2p.base_siscnrm.residentes_mart"

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
    colunas = ["programa", "instituicao", "regiao", "uf", "validacao"]
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
            ano_inicio,
            ano_termino
        FROM `{TABLE_ID}`
        WHERE ano_inicio IS NOT NULL OR ano_termino IS NOT NULL
    """
    job = client.query(query_anos, location=BQ_LOCATION)
    df_anos = job.to_dataframe(create_bqstorage_client=True, bqstorage_client=bqs)

    filtros["anos_inicio"] = sorted(df_anos["ano_inicio"].dropna().astype(int).unique().tolist())
    filtros["anos_termino"] = sorted(df_anos["ano_termino"].dropna().astype(int).unique().tolist())

    return filtros, datetime.now(pytz.timezone("America/Sao_Paulo"))

if "filtros" not in st.session_state:
    with st.spinner("⏳ Carregando filtros disponíveis..."):
        st.session_state["filtros"], st.session_state["ultima_atualizacao"] = consultar_filtros_com_anos()

filtros = st.session_state["filtros"]
ultima_atualizacao = st.session_state["ultima_atualizacao"]

# =====================================================================
# Filtros
# =====================================================================

programa_options    = ["(Todos)"] + filtros.get("programa", [])
instituicao_options = ["(Todas)"] + filtros.get("instituicao", [])
regiao_options      = ["(Todas)"] + filtros.get("regiao", [])
uf_options          = ["(Todas)"] + filtros.get("uf", [])
validacao_options   = ["(Todas)"] + filtros.get("validacao", [])
anos_inicio         = filtros.get("anos_inicio", [])
anos_termino        = filtros.get("anos_termino", [])

# =====================================================================
# Layout – Abas
# =====================================================================
tabs = st.tabs(["📺 Instruções de uso", "🧱 Metodologia & Dados", "⬇️ Download", "📈 Analytics"])

# ---------------------------------------------------------------------
# 1) Instruções
# ---------------------------------------------------------------------
with tabs[0]:
    st.subheader("Como usar")
    st.markdown("""
- Na aba **Metodologia** você pode encontrar detalhes de como os dados foram tratados, plotados e analisados.
- Na aba **Download** você pode baixar a **amostra filtrada** ou o **dataset completo** tratado.
- Na aba **Analytics** você encontra indicadores, séries históricas e rankings. Use os **filtros na barra** para restringir UF, Programa, Instituição e Período.
    """)
    st.markdown("---")
    st.markdown("### Vídeo passo a passo")
    st.video('https://youtu.be/O0fZTR70b7I?si=X1afmDxO9RHTUJ6t') 

# ---------------------------------------------------------------------
# 2) Metodologia
# ---------------------------------------------------------------------
with tabs[1]:
    st.subheader("Metodologia, engenharia de dados e fontes")

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("""
**Escopo**  
Registros de **certificados de residência médica** (CNRM).

**Aquisição & Atualização** 
- Fonte primária: *Comissão Nacional de Residência Médica (CNRM)*. 
- Periodicidade: quando houver atualização pública.  
- Pipeline: extração → padronização de colunas → tipos/normalização de datas → chaves canônicas (UF, programa, instituição).

**Tratamento principal**  
- `inicio`, `termino` e `data_emissao` convertidas para `datetime`.  
- Campos textuais (`programa`, `instituicao`, `uf`) padronizados.  
- Geração de colunas derivadas: `ano_inicio`, `ano_termino`.  
- Geração de campo de região para identificar região do país segundo `uf`.
- Geração de campo de validação: se linha não contiver data de ínicio OU data de término OU programa OU instituição OU nome do médico é definido como não validado.

**Limitações conhecidas**  
- Registros antigos podem vir sem CRM ou com `uf` faltante.  
- Homônimos e mudanças de nomenclatura institucional/programática podem exigir reconciliação (matching) adicional.
        """)

    with c2:
        st.markdown("#### Links úteis")
        st.markdown("""
- 📚 **Fonte oficial**: [Portal CNRM](http://siscnrm.mec.gov.br/certificados)  <!-- TODO: ajuste se quiser -->
- 🗃️ **Tabela no BigQuery**: `escolap2p.base_siscnrm.residentes_raw`
- 🧪 **Reprodutibilidade**: código do ETL (em breve no GitHub)  <!-- TODO: link do repo -->
        """)

# ---------------------------------------------------------------------
# 3) Download
# ---------------------------------------------------------------------

with tabs[2]:
    st.subheader("Baixar dados tratados")
    st.info("Os downloads abaixo respeitam os **filtros** (quando aplicados).")

    c1, c2 = st.columns([1, 1])

    with c1:
        selected_programa = st.selectbox("Programas", options=programa_options, index=0)
        selected_instituicao = st.selectbox("Instituição", options=instituicao_options, index=0)
        selected_regiao = st.selectbox("Região", options=regiao_options, index=0)
        selected_uf = st.selectbox("UF", options=uf_options, index=0)
        selected_validacao = st.selectbox("Validação", options=validacao_options, index=0)

    with c2:

        range_inicio = None
        range_termino = None

        if anos_inicio:
            min_y, max_y = min(anos_inicio), max(anos_inicio)
            range_inicio = st.slider("Período (ano de início)", min_y, max_y, (min_y, max_y))

        if anos_termino:
            min_y, max_y = min(anos_termino), max(anos_termino)
            range_termino = st.slider("Período (ano de término)", min_y, max_y, (min_y, max_y))

    @st.cache_data(ttl=1800, show_spinner=True)
    def consultar_agrupado_por_filtros(
        programa=None,
        instituicao=None,
        regiao=None,
        uf=None,
        validacao=None,
        ano_inicio_range=None,
        ano_termino_range=None
    ):
        condicoes = []
        if programa and programa != "(Todos)":
            condicoes.append(f"programa = '{programa}'")
        if instituicao and instituicao != "(Todas)":
            condicoes.append(f"instituicao = '{instituicao}'")
        if regiao and regiao != "(Todas)":
            condicoes.append(f"regiao = '{regiao}'")
        if uf and uf != "(Todas)":
            condicoes.append(f"uf = '{uf}'")
        if validacao and validacao != "(Todas)":
            condicoes.append(f"validacao = '{validacao}'")
        if ano_inicio_range:
            condicoes.append(f"EXTRACT(YEAR FROM inicio) BETWEEN {ano_inicio_range[0]} AND {ano_inicio_range[1]}")
        if ano_termino_range:
            condicoes.append(f"EXTRACT(YEAR FROM termino) BETWEEN {ano_termino_range[0]} AND {ano_termino_range[1]}")

        where_clause = "WHERE " + " AND ".join(condicoes) if condicoes else ""

        group_dims = ["programa", "instituicao", "regiao", "uf", "validacao"]
        select_clause = ", ".join(group_dims)

        query = f"""
        SELECT
        {select_clause},
        COUNT(DISTINCT certificado) AS qtd_certificados,
        COUNT(DISTINCT medico) AS qtd_medicos
        FROM `{TABLE_ID}`
        {where_clause}
        GROUP BY {select_clause}
        ORDER BY qtd_certificados DESC
        """

        job = client.query(query, location=BQ_LOCATION)
        job.result(timeout=180)
        df = job.to_dataframe(create_bqstorage_client=True, bqstorage_client=bqs)

        return df
    
    if st.button("Consultar dados agregados"):
        with st.spinner("⏳ Consultando dados no BigQuery..."):
            df_resultado = consultar_agrupado_por_filtros(
                programa=selected_programa,
                instituicao=selected_instituicao,
                regiao=selected_regiao,
                uf=selected_uf,
                validacao=selected_validacao,
                ano_inicio_range=range_inicio,
                ano_termino_range=range_termino,
            )
        st.success("✅ Consulta finalizada com sucesso!")
        st.dataframe(df_resultado)

    def consultar_schema_tabela():
        table = client.get_table(TABLE_ID)
        schema_info = [{
            "coluna": field.name,
            "tipo": field.field_type,
            "modo": field.mode
        } for field in table.schema]
        return pd.DataFrame(schema_info)
    
    dict_cols = consultar_schema_tabela()

    # função utilitária
    def _csv_bytes(_df: pd.DataFrame) -> bytes:
        return _df.to_csv(index=False).encode("utf-8")

    # Botões de download
    colA, colB = st.columns(2)

    with colA:
        dict_cols = consultar_schema_tabela()
        st.download_button(
            "📥 Baixar dicionário (CSV)",
            data=_csv_bytes(dict_cols),
            file_name=f"cnrm_dicionario_{datetime.now().date()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    
    with colB:
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
with tabs[3]:
    st.subheader("Visão analítica")
