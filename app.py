# ---------------------------------------------------------------
# app.py  — Public Health Analytics (menu + intro)
# ---------------------------------------------------------------
import streamlit as st
from pathlib import Path

# ---------------- Config da página ----------------
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
- 👥💬 [WhatsApp – Comunidade](https://chat.whatsapp.com/CBn0GBRQie5B8aKppPigdd)
- 🤝💬 [WhatsApp – Atendimento](https://patients2python.sprinthub.site/r/whatsapp-olz)
- 🎓 [Escola de Dados em Saúde](https://app.patients2python.com.br/browse)
    """, unsafe_allow_html=True)

# ---------------- Texto de apresentação ----------------
# ===== Descritivo longo =====
st.markdown("""
### Sobre este painel

Os **dados de saúde pública no Brasil estão disponíveis em grande quantidade** – sistemas como SIM, SINAN, CNES, SIH, SIA, SINASC, SISAB, SI-PNI, além de pesquisas do IBGE (Censos, PNAD, PNS), entre outros.  
No entanto, **o desafio não é acessar os dados, mas sim dar sentido a eles**: integrar fontes, tratar inconsistências, aplicar métodos analíticos transparentes e traduzir resultados em **insights acionáveis** para decisão.

Este painel se diferencia por apresentar as bases **analisadas sob a ótica de um Cientista de Dados em Saúde**, com curadoria temática, indicadores comparáveis e visualizações que ajudam gestores, pesquisadores e profissionais a **enxergar padrões, tendências e prioridades**.
""")

with st.expander("🎯 Objetivo e proposta de valor", expanded=True):
    st.markdown("""
- **Objetivo**: oferecer um ambiente único para **consulta, análise e comparação** de indicadores de saúde pública, agregando bases nacionais e componentes demográficos/socioeconômicos.  
- **Proposta de valor**: transformação de dados dispersos em **informação útil**, inclusive baixável, através de padronização, modelagem estatística, estratificações relevantes e **interpretação técnica**.
- **Resultados esperados**: apoio a planejamento, vigilância, avaliação de políticas, priorização de recursos e **formulação de perguntas de pesquisa**.
""")

with st.expander("👥 Para quem é"):
    st.markdown("""
- **Gestores e equipes de vigilância/assistência** que precisam monitorar indicadores, coberturas e padrões de utilização.
- **Pesquisadores e estudantes** interessados em séries históricas e hipóteses epidemiológicas.
- **Serviços e redes de atenção** que buscam entender capacidade instalada, produção e desfechos.
- **Organizações privadas e sociais** que planejam projetos baseados em evidências.
""")

with st.expander("🧭 O que você encontra aqui"):
    st.markdown("""
- **Estatísticas vitais**: nascimentos (SINASC) e mortalidade (SIM).  
- **Morbidade e vigilância**: notificações (SINAN), morbilidade hospitalar (SIH).  
- **Assistência**: produção hospitalar (SIH) e ambulatorial (SIA), imunizações (SI-PNI), nutricional (SISVAN).  
- **Rede assistencial**: estabelecimentos, equipes e recursos (CNES).  
- **Demografia e contexto**: população, educação, renda e saneamento (IBGE).  
- **Inquéritos**: PNS, PNAD-Saúde, VIGITEL, VIVA, entre outros.  
- **Financeiro**: recursos e valores aprovados de produção.
""")

with st.expander("🧪 Metodologia (resumo)"):
    st.markdown("""
- **Padronização de variáveis** (códigos IBGE, CNES, CID, CBO, faixas etárias).
- **Tratamento de séries históricas** com verificação de quebras metodológicas e mudanças de definição.
- **Indicadores** calculados com denominadores apropriados (ex.: população residente/estimada).
- **Estratificações** por tempo, território, sexo, idade, tipo de serviço/procedimento quando aplicável.
- **Visualizações** priorizando comparabilidade e leitura rápida (tendências, proporções, mapas).
- **Reprodutibilidade**: cada página indica claramente **fonte e período**; fórmulas/transformações são documentadas.
""")

with st.expander("🧩 Como usar"):
    st.markdown("""
1. **Escolha um tema** no menu lateral (ex.: Assistência à Saúde ▸ Produção Hospitalar).  
2. **Selecione filtros** (UF, município, período, estratos) para refinar a análise.  
3. **Interprete os gráficos e tabelas** — cada visual traz *tooltips* e notas sobre a fonte.  
4. **Compare territórios/tempos** para identificar tendências, sazonalidades e outliers.  
5. **Leve perguntas para sua prática**: o painel é um ponto de partida para hipóteses e decisões.
""")

with st.expander("🔒 Qualidade, limitações e ética"):
    st.markdown("""
- As fontes oficiais possuem **lag de atualização** e podem passar por revisões/retificações.  
- Mudanças de **definição/implantação** podem introduzir quebras nas séries. Isso é indicado quando pertinente.  
- **Dados sensíveis** são sempre tratados em nível **agregado** e com respeito à privacidade.  
- Recomenda-se **validar resultados** com documentos técnicos de cada sistema antes de uso normativo.
""")

with st.expander("🗺️ Roadmap (próximos passos)"):
    st.markdown("""
- Novas camadas: **tempo até evento** em oncologia, **linhas de cuidado** e **estratificação de risco**.  
- Indicadores de **qualidade assistencial** e **desfechos** com ajustes demográficos.  
- **Downloads reprodutíveis** (CSV/JSON) e **metadados** por indicador.  
- Integração com **BigQuery** para consultas avançadas.
""")

st.info("Dúvidas, sugestões ou correções metodológicas são bem-vindas. Este painel é vivo e evolutivo.")

col1, col2 = st.columns([3,1])

with col1:
    st.markdown(
        """
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

with col2:
    if FOTO:
        st.image(str(FOTO), caption="Dr. Gregório Victor Rodrigues", use_container_width=True)
    else:
        st.info(f"Foto não encontrada em {ASSETS}/foto_gregorio.(jpg|png|jpeg|webp)")

# ================= Rodapé (links) =================
st.markdown("""
<div class="app-footer">
  <span><strong>Conecte-se:</strong></span>
  <a href="https://www.linkedin.com/in/gregorio-healthdata/" target="_blank">💼 LinkedIn</a> ·
  <a href="https://www.youtube.com/@Patients2Python" target="_blank">▶️ YouTube</a> ·
  <a href="https://www.instagram.com/patients2python/" target="_blank">📸 Instagram</a> ·
  <a href="https://patients2python.com.br/" target="_blank">🌐 Site</a> ·
  <a href="https://github.com/gregrodrigues22" target="_blank">🐙 GitHub</a> ·
  <a href="https://chat.whatsapp.com/CBn0GBRQie5B8aKppPigdd" target="_blank">👥💬 WhatsApp Comunidade</a> ·
  <a href="https://patients2python.sprinthub.site/r/whatsapp-olz" target="_blank">🤝💬 WhatsApp Atendimento</a> ·
  <a href="https://app.patients2python.com.br/browse" target="_blank">🎓 Escola de Dados em Saúde</a>
</div>

<style>
.app-footer {
  position: fixed; left: 0; right: 0; bottom: 0;
  padding: 10px 16px;
  font-size: 0.95rem;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(6px);
  border-top: 1px solid #e5e7eb;
  z-index: 999;
}
.block-container { padding-bottom: 76px; }  /* evita sobrepor conteúdo */
.app-footer a { text-decoration: none; color: #0f6fff; margin: 0 4px; }
.app-footer a:hover { text-decoration: underline; }
</style>
""", unsafe_allow_html=True)