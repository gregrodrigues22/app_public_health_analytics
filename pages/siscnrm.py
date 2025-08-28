# ---------------------------------------------------------------
# Big Query
# ---------------------------------------------------------------
PROJECT_ID = "escolap2p" 
TABLE_ID = "escolap2p.cliente_espacoaurium.crm" 

with open("/tmp/keyfile.json", "w") as f:
    json.dump(st.secrets["bigquery"].to_dict(), f)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/keyfile.json"

client = bigquery.Client()

# ---------------------------------------------------------------
# Aquisição de dados do Big Query
# ---------------------------------------------------------------
@st.cache_data(ttl=3600)
def consultar_dados():
    client = bigquery.Client()
    query = """
        SELECT
            *
        FROM
            `escolap2p.base_siscnrm.residentes_raw`
    """
    df = client.query(query).to_dataframe()
    fuso_sp = pytz.timezone("America/Sao_Paulo")
    ultima_atualizacao = datetime.now(fuso_sp)
    return df, ultima_atualizacao

# Executa a query e transforma em DataFrame
df, ultima_atualizacao = consultar_dados()
