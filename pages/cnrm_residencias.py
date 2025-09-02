# ---------------------------------------------------------------
# Set up
# ---------------------------------------------------------------
import streamlit as st  
import plotly.graph_objects as go
import numpy as np
from google.cloud import bigquery
import pandas as pd
import json
from scipy.stats import linregress
from plotly.subplots import make_subplots
from plotly.colors import sequential
import os
from datetime import datetime
import pytz
from google.cloud import bigquery_storage
from pathlib import Path

# ---------------------------------------------------------------
# Big Query
# ---------------------------------------------------------------
PROJECT_ID   = "escolap2p"
BQ_LOCATION  = "southamerica-east1"  # sua tabela está nessa região
TABLE_ID     = "escolap2p.base_siscnrm.residentes_raw"

# credenciais (iguais às suas)
with open("/tmp/keyfile.json", "w") as f:
    json.dump(st.secrets["bigquery"].to_dict(), f)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/keyfile.json"

# clients já com location; BQ Storage acelera o to_dataframe()
client = bigquery.Client(project=PROJECT_ID, location=BQ_LOCATION)
bqs    = bigquery_storage.BigQueryReadClient()

# ---------------------------------------------------------------
# Aquisição de dados do BigQuery
# ---------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def consultar_dados(amostra=False):
    query = f"""
        SELECT *
        FROM `{TABLE_ID}`
    """
    # Para testar rápido, use amostra=True (depois mude para False)
    if amostra:
        query += "\nLIMIT 20000"

    job = client.query(query, location=BQ_LOCATION)
    job.result(timeout=180)  # garante conclusão do job

    df = job.to_dataframe(create_bqstorage_client=True, bqstorage_client=bqs)

    fuso_sp = pytz.timezone("America/Sao_Paulo")
    ultima_atualizacao = datetime.now(fuso_sp)
    return df, ultima_atualizacao

# Executa a query e transforma em DataFrame
# comece com amostra=True se estiver pesado, depois troque para False
df, ultima_atualizacao = consultar_dados(amostra=True)

# ---------------------------------------------------------------
# Config da página 
# ---------------------------------------------------------------
st.set_page_config(layout="wide", page_title="📊 Public Health Analytics")

# ---------------- Helpers para assets ----------------
APP_DIR = Path(__file__).resolve().parent
ASSETS = APP_DIR / "assets"

def first_existing(*relative_paths: str) -> Path | None:
    """Devolve o primeiro arquivo que existir em assets/ dentre as opções."""
    for rel in relative_paths:
        p = ASSETS / rel
        if p.exists():
            return p
    return None

# Tenta várias extensões (evita erro se trocar png/jpg)
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

# =====================================================================
# Dados (usa o df já carregado na app principal, se existir)
#    - Se rodar isolado, coloque aqui seu loader do BigQuery.
# =====================================================================
if "df" not in st.session_state:
    st.warning("Dataset não detectado no estado da sessão. Carregue o df antes ou adapte este loader.")
    # Exemplo de fallback (comente se não quiser):
    # from google.cloud import bigquery
    # client = bigquery.Client()
    # df = client.query("SELECT * FROM `escolap2p.base_siscnrm.residentes_raw`").to_dataframe()
    # st.session_state["df"] = df

df = st.session_state.get("df", None)
if df is None or df.empty:
    st.stop()

# Normalizações mínimas (não quebra se coluna não existir)
def _safe_to_datetime(s):
    try:
        return pd.to_datetime(s, errors="coerce")
    except Exception:
        return pd.to_datetime(pd.Series([None]*len(s)), errors="coerce")

for col_try in ["inicio", "termino", "data_emissao"]:
    if col_try in df.columns:
        df[col_try] = _safe_to_datetime(df[col_try])

# Colunas auxiliares
if "inicio" in df.columns:
    df["ano_inicio"] = df["inicio"].dt.year
if "termino" in df.columns:
    df["ano_termino"] = df["termino"].dt.year
if "uf" in df.columns:
    df["uf"] = df["uf"].astype(str).str.upper().str.strip()
if "programa" in df.columns:
    df["programa"] = df["programa"].astype(str).str.strip()
if "instituicao" in df.columns:
    df["instituicao"] = df["instituicao"].astype(str).str.strip()

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
- Use os **filtros na barra lateral** para restringir UF, Programa, Instituição e Período.
- Na aba **Analytics** você encontra indicadores, séries históricas e rankings.
- Na aba **Download** você pode baixar a **amostra filtrada** ou o **dataset completo** tratado.
    """)
    st.markdown("---")
    st.markdown("### Vídeo passo a passo")
    VIDEO_URL = "https://youtu.be/XXXXXXXXXXX"  # TODO: troque pela URL do seu vídeo
    st.video(VIDEO_URL)

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

**Limitações conhecidas**  
- Registros antigos podem vir sem CRM ou com `uf` faltante.  
- Homônimos e mudanças de nomenclatura institucional/programática podem exigir reconciliação (matching) adicional.
        """)

        st.markdown("**Dicionário de campos (auto-gerado pelo schema atual):**")
        dict_cols = pd.DataFrame({
            "coluna": df.columns,
            "dtype": [str(t) for t in df.dtypes]
        })
        st.dataframe(dict_cols, use_container_width=True, hide_index=True)

    with c2:
        st.markdown("#### Links úteis")
        st.markdown("""
- 📚 **Fonte oficial**: [Portal CNRM](https://www.gov.br/mec/pt-br/assuntos/educacao-superior/residencia-medica)  <!-- TODO: ajuste se quiser -->
- 🗃️ **Tabela no BigQuery**: `escolap2p.base_siscnrm.residentes_raw`
- 🧪 **Reprodutibilidade**: código do ETL (em breve no GitHub)  <!-- TODO: link do repo -->
        """)

# ---------------------------------------------------------------------
# 3) Download
# ---------------------------------------------------------------------
with tabs[2]:
    st.subheader("Baixar dados tratados")

    st.info("Os downloads abaixo respeitam os **filtros da barra lateral** (quando aplicados).")

    # função utilitária
    def _csv_bytes(_df: pd.DataFrame) -> bytes:
        return _df.to_csv(index=False).encode("utf-8")

    # Botões de download
    colA, colB = st.columns(2)
    with colA:
        st.download_button(
            "⬇️ Baixar dados filtrados (CSV)",
            data=_csv_bytes(df),
            file_name=f"cnrm_residentes_filtrado_{datetime.now().date()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with colB:
        st.download_button(
            "⬇️ Baixar dicionário (CSV)",
            data=_csv_bytes(dict_cols),
            file_name=f"cnrm_dicionario_{datetime.now().date()}.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ---------------------------------------------------------------------
# 4) Analytics
# ---------------------------------------------------------------------
with tabs[3]:
    st.subheader("Visão analítica")

    # ----------------------- Filtros (sidebar) -----------------------
    with st.sidebar:
        st.markdown("### 🔎 Filtros – CNRM")
        uf_opts = ["(todas)"] + sorted([u for u in df["uf"].dropna().unique().tolist()]) if "uf" in df.columns else ["(todas)"]
        uf_sel = st.selectbox("UF", uf_opts, index=0)

        prog_opts = ["(todos)"] + sorted(df["programa"].dropna().unique().tolist()) if "programa" in df.columns else ["(todos)"]
        prog_sel = st.selectbox("Programa", prog_opts, index=0)

        inst_opts = ["(todas)"] + sorted(df["instituicao"].dropna().unique().tolist()) if "instituicao" in df.columns else ["(todas)"]
        inst_sel = st.selectbox("Instituição", inst_opts, index=0)

        # período por ano de término (se existir)
        min_y = int(np.nanmin(df["ano_termino"])) if "ano_termino" in df.columns and df["ano_termino"].notna().any() else 1980
        max_y = int(np.nanmax(df["ano_termino"])) if "ano_termino" in df.columns and df["ano_termino"].notna().any() else datetime.now().year
        year_range = st.slider("Período (ano de término)", min_y, max_y, (min_y, max_y))

    # aplica filtros
    dff = df.copy()
    if "uf" in df.columns and uf_sel != "(todas)":
        dff = dff[dff["uf"] == uf_sel]
    if "programa" in df.columns and prog_sel != "(todos)":
        dff = dff[dff["programa"] == prog_sel]
    if "instituicao" in df.columns and inst_sel != "(todas)":
        dff = dff[dff["instituicao"] == inst_sel]
    if "ano_termino" in df.columns:
        dff = dff[(dff["ano_termino"] >= year_range[0]) & (dff["ano_termino"] <= year_range[1])]

    # ----------------------- Indicadores (cards) ---------------------
    total_reg = len(dff)
    qtd_inst = dff["instituicao"].nunique() if "instituicao" in dff.columns else np.nan
    qtd_prog = dff["programa"].nunique() if "programa" in dff.columns else np.nan
    qtd_uf = dff["uf"].nunique() if "uf" in dff.columns else np.nan
    periodo_txt = f"{int(np.nanmin(dff['ano_termino']))}–{int(np.nanmax(dff['ano_termino']))}" if "ano_termino" in dff.columns and not dff.empty else "—"

    if {"inicio", "termino"}.issubset(dff.columns):
        dur_meses = (dff["termino"] - dff["inicio"]).dt.days / 30.4375
        media_dur = np.nanmean(dur_meses)
    else:
        media_dur = np.nan

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Registros", f"{total_reg:,}".replace(",", "."))
    c2.metric("Instituições", f"{qtd_inst:,}".replace(",", "."))
    c3.metric("Programas", f"{qtd_prog:,}".replace(",", "."))
    c4.metric("UFs", f"{qtd_uf:,}".replace(",", "."))
    c5.metric("Período (término)", periodo_txt)

    if not np.isnan(media_dur):
        st.caption(f"⏱️ Duração média (aprox.): **{media_dur:.1f}** meses")

    st.markdown("---")

    # ----------------------- Gráficos -------------------------------
    # Série por ano de término
    if "ano_termino" in dff.columns:
        ts = dff.groupby("ano_termino").size().reset_index(name="qtd").sort_values("ano_termino")
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(x=ts["ano_termino"], y=ts["qtd"], mode="lines+markers", name="Concluintes"))
        fig_ts.update_layout(title="Série histórica – concluintes por ano de término",
                             xaxis_title="Ano de término", yaxis_title="Quantidade", height=380)
        st.plotly_chart(fig_ts, use_container_width=True)

    colA, colB = st.columns(2)

    # Top Programas
    if "programa" in dff.columns:
        top_prog = (dff["programa"]
                    .value_counts()
                    .reset_index()
                    .rename(columns={"index": "programa", "programa": "qtd"})
                    .head(15))
        fig_p = go.Figure(go.Bar(x=top_prog["qtd"], y=top_prog["programa"], orientation="h"))
        fig_p.update_layout(title="Top 15 Programas (por registros)",
                            xaxis_title="Quantidade", yaxis_title="", height=450)
        colA.plotly_chart(fig_p, use_container_width=True)

    # Top Instituições
    if "instituicao" in dff.columns:
        top_inst = (dff["instituicao"]
                    .value_counts()
                    .reset_index()
                    .rename(columns={"index": "instituicao", "instituicao": "qtd"})
                    .head(15))
        fig_i = go.Figure(go.Bar(x=top_inst["qtd"], y=top_inst["instituicao"], orientation="h"))
        fig_i.update_layout(title="Top 15 Instituições (por registros)",
                            xaxis_title="Quantidade", yaxis_title="", height=450)
        colB.plotly_chart(fig_i, use_container_width=True)

    # Distribuição por UF
    if "uf" in dff.columns:
        dist_uf = dff["uf"].value_counts().reset_index().rename(columns={"index": "uf", "uf": "qtd"})
        fig_uf = go.Figure(go.Bar(x=dist_uf["uf"], y=dist_uf["qtd"]))
        fig_uf.update_layout(title="Distribuição por UF", xaxis_title="UF", yaxis_title="Quantidade", height=350)
        st.plotly_chart(fig_uf, use_container_width=True)

    st.caption("Obs.: indicadores e gráficos respeitam os filtros selecionados.")