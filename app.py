# ---------------------------------------------------------------
# Setup & Config
# ---------------------------------------------------------------
import streamlit as st
from pathlib import Path

# ---------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------
st.set_page_config(layout="wide", page_title="📊 Public Health Analytics")

# Paths robustos para assets
APP_DIR = Path(__file__).resolve().parent
ASSETS = APP_DIR / "assets"
LOGO = ASSETS / "logo.png"
FOTO = ASSETS / "foto_gregorio.jpg"

# ---------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------
st.markdown(
    """
    <div style='background: linear-gradient(to right, #004e92, #000428); padding: 40px; border-radius: 12px; margin-bottom:30px'>
        <h1 style='color: white;'>📊 Public Health Analytics</h1>
        <p style='color: white;'>Explore as possibilidades de engajamento da população.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# Sidebar (único) com categorias e submenus
# ---------------------------------------------------------------
with st.sidebar:
    if LOGO.exists():
        st.image(str(LOGO), use_container_width=True)
    st.markdown("<hr style='border:none;border-top:1px solid #ccc;'/>", unsafe_allow_html=True)
    st.header("Menu")

    # Atalhos gerais (garanta que os arquivos existem)
    st.page_link("app.py", label="Análise", icon="📊")
    st.page_link("pages/criacao.py", label="Referência", icon="✅")

    st.markdown("<hr style='border:none;border-top:1px solid #ccc;'/>", unsafe_allow_html=True)

    # ---- Categorias (estilo TABNET) ----
    with st.expander("Análises Demográficas e Socioeconômicas", expanded=False):
        st.page_link("pages/demo/populacao.py", label="População (IBGE)", icon="👨‍👩‍👧‍👦")
        st.page_link("pages/demo/educacao.py", label="Educação (IBGE)", icon="🎓")
        st.page_link("pages/demo/trabalho_renda.py", label="Trabalho e Renda (IBGE)", icon="💼")
        st.page_link("pages/demo/saneamento.py", label="Saneamento (IBGE)", icon="🚰")

    with st.expander("Força de Trabalho em Saúde", expanded=False):
        # Ajuste o path/label conforme o conteúdo real
        st.page_link("pages/forca_trabalho/cnrm_residencias.py", label="Residências Médicas (SISCNRM)", icon="🏠")
        st.page_link("pages/rede/cnes_rh_cbo2002.py", label="Profissionais de Saúde (CNES)", icon="👩‍⚕️")

    with st.expander("Rede Assistencial", expanded=False):
        st.page_link("pages/rede/cnes_estabelecimentos.py", label="Estabelecimentos (CNES)", icon="🏨")
        st.page_link("pages/rede/cnes_recursos_fisicos.py", label="Recursos Físicos (CNES)", icon="🛠️")
        st.page_link("pages/rede/cnes_equipes.py", label="Equipes de Saúde (CNES)", icon="👥")

    with st.expander("Assistência à Saúde", expanded=True):
        st.page_link("pages/assistencia/producao_hospitalar.py", label="Produção Hospitalar (SIH/SUS)", icon="🛏️")
        st.page_link("pages/assistencia/producao_ambulatorial.py", label="Produção Ambulatorial (SIA/SUS)", icon="🩺")
        st.page_link("pages/assistencia/imunizacoes.py", label="Imunizações (SI-PNI)", icon="💉")
        st.page_link("pages/assistencia/vigilancia_alimentar.py", label="Vigilância Alimentar e Nutricional (SISVAN)", icon="🍽️")

    with st.expander("Morbidade", expanded=False):
        st.page_link("pages/epidemiologia/morbilidade_sih.py", label="Morbidade Hospitalar (SIH/SUS)", icon="🏥")
        st.page_link("pages/epidemiologia/notificacoes_2001_2006.py", label="Notificações (SINAN)", icon="📜")
        st.page_link("pages/epidemiologia/cancer_siscan.py", label="Câncer de colo de útero e mama (SISCAN)", icon="🎗️")

    with st.expander("Estatísticas Vitais", expanded=False):
        st.page_link("pages/vitais/nascidos_vivos.py", label="Nascidos Vivos (SINASC)", icon="👶")
        st.page_link("pages/vitais/mortalidade_cid10.py", label="Mortalidade (SIM)", icon="⚰️")

    with st.expander("Inquéritos e Pesquisas", expanded=False):
        st.page_link("pages/inqueritos/pns_2013.py", label="PNS", icon="🧾")
        st.page_link("pages/inqueritos/pnad_basico.py", label="PNAD", icon="📄")
        st.page_link("pages/inqueritos/vigitel.py", label="VIGITEL", icon="☎️")
        st.page_link("pages/inqueritos/viva.py", label="VIVA – Violências e Acidentes", icon="🚨")
        st.page_link("pages/inqueritos/saude_bucal_1996.py", label="Inquérito de Saúde Bucal – 1996", icon="🦷")
        st.page_link("pages/inqueritos/prev_esquistossomose.py", label="Prevalência de Esquistossomose 2011/2015", icon="🧪")

    with st.expander("Informações Financeiras", expanded=False):
        st.page_link("pages/financeiro/recursos_federais.py", label="Recursos Federais do SUS", icon="🏛️")
        st.page_link("pages/financeiro/valores_producao.py", label="Valores aprovados da produção SUS", icon="💳")

    st.markdown("<hr style='border:none;border-top:1px solid #ccc;'/>", unsafe_allow_html=True)

# ---------------------------------------------------------------
# Texto de Apresentação
# ---------------------------------------------------------------
col1, col2 = st.columns([1,3])
with col1:
    if FOTO.exists():
        st.image(str(FOTO), caption="Dr. Gregório Victor Rodrigues", use_container_width=True)

with col2:
    st.markdown(
        """
        ### Sobre este painel

        Os **dados de saúde pública no Brasil estão disponíveis em grande quantidade** – 
        sistemas como SIM, SINAN, CNES, SIH e outros oferecem um volume enorme de informações.  
        No entanto, **o desafio não é acessar os dados, mas sim dar sentido a eles**.  

        Este painel se diferencia por apresentar as bases **analisadas sob a ótica de um Cientista de Dados em Saúde**,
        trazendo contexto, interpretação e visualizações que apoiam gestores, pesquisadores e profissionais de saúde 
        a transformar dados em **insights práticos**.

        ---
        #### Criado por
        **Gregório Victor Rodrigues**  
        Médico pela **UFMG** | Médico de Família e Comunidade (**HOB**)  
        Mestre em Saúde Pública / Epidemiologia (**UFMG**)  
        Doutorando em Saúde Pública / Epidemiologia (**UFMG**)  
        Especialista em Informática e Ciência de Dados em Saúde (**Einstein**)  
        MBA em Gestão em Saúde (**FGV**)  
        Green Belt Lean6Sigma (**Voitto**) | Scrum Master (**Scrum Org**)  

        Pesquisador-colaborador do **Nescon-UFMG** e **UNA-SUS**; 
        consultor independente em projetos de ciência de dados em saúde 
        para **empresas, secretarias e organizações de saúde**.  
        Foi professor de Práticas em Saúde Baseada em Evidências (Uni-BH / Grupo Ânima) 
        e de Introdução à Atenção Primária (UFMG).
        """,
        unsafe_allow_html=True
    )