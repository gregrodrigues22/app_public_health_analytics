import numpy as np
import pandas as pd
import plotly.graph_objects as go

def pareto_plotly(
    df_raw,
    col_categoria="aluno_profissional_escolaridade_descricao",
    col_id="aluno_id",
    col_valor=None,
    metodo_contagem="nunique",     # "nunique" (conta IDs únicos) | "size" (conta linhas)
    titulo="Número de Alunos por Escolaridade — Pareto",
    # Aparência/cores
    corescale_barras="Blues",
    cor_curva="black",
    # Thresholds de classificação ABC no eixo superior (% acumulado)
    th_A=80,
    th_B=95,
    # Destaques
    categoria_destacar="Não identificado",
    cor_destacada="crimson",
    # Layout básico
    largura_px=1200,
    altura_px=800,
    margem=dict(l=300, r=140, t=100, b=60)
):
    """
    Constrói um gráfico de PARETO horizontal usando Plotly, a partir de dados RAW.

    A função inclui internamente TODA a transformação necessária:
      - agrega por categoria (contagem de IDs únicos ou de linhas),
      - ordena do maior para o menor,
      - calcula % e % acumulado,
      - produz barras horizontais + curva de Pareto no eixo superior (x2),
      - adiciona faixas ABC (A: 0–th_A, B: th_A–th_B, C: th_B–100).

    PARÂMETROS
    ----------
    df_raw : pandas.DataFrame
        Base "crua" com uma coluna de ID (col_id) e uma categórica (col_categoria).
    col_categoria : str
        Nome da coluna categórica a ser analisada (eixos Y do Pareto).
    col_id : str | None
        Nome da coluna de ID. Se None, usamos contagem de linhas por categoria ("size").
    metodo_contagem : {"nunique","size"}
        - "nunique": conta IDs únicos por categoria.
        - "size": conta linhas por categoria.
    titulo : str
        Título do gráfico.
    corescale_barras : str
        Nome do colorscale do Plotly para as barras (ex.: "Blues", "Viridis").
    cor_curva : str
        Cor da curva de Pareto (ex.: "black").
    th_A, th_B : int
        Limiares (em %) para as faixas ABC no eixo superior.
    categoria_destacar : str | None
        Se informado, pinta essa categoria de cor fixa (cor_destacada), fora do degradê.
    cor_destacada : str
        Cor a aplicar na categoria destacada.
    largura_px, altura_px : int
        Tamanho do gráfico em pixels.
    margem : dict
        Margens do layout (l, r, t, b).

    RETORNO
    -------
    fig : plotly.graph_objects.Figure
        A figura de Pareto (você pode .show() ou .write_html()).
    """
    # ====================================================
    # A) VALIDAÇÕES E PREPARO
    # ====================================================
    # 1) Checamos colunas obrigatórias
    if col_categoria not in df_raw.columns:
        raise ValueError(f"Coluna de categoria '{col_categoria}' não encontrada no DataFrame.")
    if col_valor is not None and col_valor not in df_raw.columns:
        raise ValueError(f"Você informou col_valor='{col_valor}', mas essa coluna não existe no DataFrame.")
    if col_valor is None and col_id is not None and col_id not in df_raw.columns:
        raise ValueError(f"Você informou col_id='{col_id}', mas essa coluna não existe no DataFrame.")

    # 2) Definimos o método de contagem (didático):
    #    - "nunique": quantos IDs distintos por categoria (evita duplicidade do mesmo ID).
    #    - "size": quantas linhas por categoria (cada linha vale 1).
    if (col_id is None) and (metodo_contagem == "nunique"):
        # Se não há col_id, não é possível usar nunique corretamente → caímos para "size"
        metodo_contagem = "size"

    # ====================================================
    # B) AGREGAÇÃO (TRANSFORMAÇÃO PRINCIPAL DO PARETO)
    # ====================================================
    # 1) Agrupamos por categoria e computamos a contagem conforme método escolhido
    if col_valor is not None:
        # Se col_valor for passado, usamos a soma direta (base já agregada)
        grp = df_raw.groupby(col_categoria, dropna=False)[col_valor].sum()
    elif col_id is not None and metodo_contagem == "nunique":
        # Conta IDs distintos por categoria
        grp = df_raw.groupby(col_categoria, dropna=False)[col_id].nunique()
    else:
        # Conta linhas por categoria
        grp = df_raw.groupby(col_categoria, dropna=False).size()

    # 2) Renomeamos para "count" e transformamos em DataFrame (boa prática para manipular depois)
    df_agg = grp.rename("count").reset_index()

    # 3) Ordenamos do maior para o menor — requisito fundamental do Pareto
    df_ordenado = df_agg.sort_values("count", ascending=False).reset_index(drop=True)

    # 4) Calculamos a % de cada categoria e o % acumulado
    total = df_ordenado["count"].sum()
    df_ordenado["pct"] = df_ordenado["count"] / total * 100.0
    df_ordenado["cum_pct"] = df_ordenado["pct"].cumsum()

    # 5) (Opcional) Criamos um rótulo de texto para as barras (ex.: "66575 (45.9%)")
    df_ordenado["label_texto"] = df_ordenado.apply(
        lambda r: f"{int(r['count']):,}".replace(",", ".") + f" ({r['pct']:.1f}%)",
        axis=1
    )

    # 6) Extraímos as categorias na ordem final — importante para alinhar barras e linha
    cats = df_ordenado[col_categoria]

    # ====================================================
    # C) FIGURA INICIAL — BARRAS HORIZONTAIS
    # ====================================================
    # 1) Construímos o traço de barras horizontais (contagem)
    fig = go.Figure(go.Bar(
        y=cats,                               # eixo Y = categorias (ordenadas do maior p/ menor)
        x=df_ordenado["count"],               # eixo X = contagem
        orientation="h",                      # barras horizontais (Pareto clássico horizontal)
        marker=dict(
            color=df_ordenado["count"],       # usamos a contagem como "base" do degradê
            colorscale=corescale_barras,      # ex.: "Blues"
            colorbar=dict(
                title="Número de Alunos",     # título do colorbar
                x=1.12, xanchor="left"        # posicionamento à direita
            )
        ),
        text=df_ordenado["label_texto"],      # rótulo sobre as barras ("N (p%)")
        textposition="outside",
        name="Contagem"
    ))

    # ====================================================
    # D) CURVA DE PARETO (ACUMULADO %) NO EIXO SUPERIOR X2
    # ====================================================
    # 1) Adicionamos a curva do % acumulado (0..100)
    fig.add_trace(go.Scatter(
        x=df_ordenado["cum_pct"],             # eixo X2 (percentual acumulado)
        y=cats,                               # MESMAS categorias do eixo Y (mesmo ordenamento)
        mode="lines+markers+text",
        line=dict(color=cor_curva, width=3, shape="spline"),  # spline = suavização visual
        marker=dict(size=8, color="white", line=dict(color=cor_curva, width=2)),
        text=[f"{v:.1f}%" for v in df_ordenado["cum_pct"]],   # rótulo de % acima da linha
        textposition="middle right",
        name="Acumulado (%)",
        xaxis="x2"                             # <<< chave: plota no eixo superior (x2)
    ))

    # ====================================================
    # E) AJUSTES DE LAYOUT — EIXOS, MARGENS, TAMANHO
    # ====================================================
    # 1) Definimos uma folga na escala de contagem para caber rótulos fora das barras
    xmax = df_ordenado["count"].max() * 1.45

    # 2) Configuramos o layout com dois eixos X sobrepostos:
    #    - xaxis  = contagem (embaixo)
    #    - xaxis2 = percentual (em cima), overlaying em 'x'
    fig.update_layout(
        title=titulo,
        title_x=0.5,
        title_font=dict(size=22, family="Arial Black", color="#1f2c56"),
        width=largura_px,
        height=altura_px,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=margem,

        # Eixo X (contagem)
        xaxis=dict(
            domain=[0.0, 0.80],               # ocupa 80% da largura -> cria "gutter" à direita
            title="Número de Alunos",
            range=[0, xmax],
            showgrid=True, gridcolor="rgba(0,0,0,0.08)",
            tickfont=dict(size=14), title_font=dict(size=18)
        ),

        # Eixo X2 (percentual acumulado)
        xaxis2=dict(
            overlaying="x", side="top",       # sobrepõe x, mas aparece em cima
            domain=[0.0, 0.80],               # mesmo domínio do x (alinha escalas visuais)
            range=[0, 100],
            tick0=0, dtick=20, ticksuffix="%",
            showgrid=False,
            title="Acumulado (%)",
            title_font=dict(size=16),
            tickfont=dict(size=12)
        ),

        # Eixo Y (categorias) — invertido para que a maior fique no topo
        yaxis=dict(
            autorange="reversed",
            title=col_categoria,
            tickfont=dict(size=16, color="black"),
            title_font=dict(size=18)
        ),

        # Legenda
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center")
    )

    # 3) Linha vertical em 80% e 95% no eixo superior (referência ABC)
    fig.add_shape(type="line", xref="x2", yref="paper",
                  x0=th_A, x1=th_A, y0=0, y1=1,
                  line=dict(color="gray", width=2, dash="dash"))
    fig.add_shape(type="line", xref="x2", yref="paper",
                  x0=th_B, x1=th_B, y0=0, y1=1,
                  line=dict(color="gray", width=2, dash="dash"))

    # 4) Áreas ABC no eixo superior (retângulos de fundo)
    fig.add_shape(type="rect", xref="x2", yref="paper",
                  x0=0, x1=th_A, y0=0, y1=1,
                  fillcolor="rgba(46, 204, 113, 0.18)",  # verde
                  line=dict(width=0), layer="below")
    fig.add_shape(type="rect", xref="x2", yref="paper",
                  x0=th_A, x1=th_B, y0=0, y1=1,
                  fillcolor="rgba(243, 156, 18, 0.18)",  # laranja
                  line=dict(width=0), layer="below")
    fig.add_shape(type="rect", xref="x2", yref="paper",
                  x0=th_B, x1=100, y0=0, y1=1,
                  fillcolor="rgba(231, 76, 60, 0.16)",   # vermelho
                  line=dict(width=0), layer="below")

    # 5) Rótulos "A", "B", "C" no centro de cada faixa
    fig.add_annotation(x=th_A/2,   y=0.5, xref="x2", yref="paper",
                       text="<b>A</b>", showarrow=False,
                       font=dict(size=22, color="rgba(0,0,0,0.6)"))
    fig.add_annotation(x=(th_A+th_B)/2, y=0.5, xref="x2", yref="paper",
                       text="<b>B</b>", showarrow=False,
                       font=dict(size=22, color="rgba(0,0,0,0.6)"))
    fig.add_annotation(x=(th_B+100)/2,  y=0.5, xref="x2", yref="paper",
                       text="<b>C</b>", showarrow=False,
                       font=dict(size=22, color="rgba(0,0,0,0.6)"))

    # ====================================================
    # F) DESTAQUE DE UMA CATEGORIA ESPECÍFICA (ex.: "Não identificado")
    # ====================================================
    # 1) Substituímos a cor da barra dessa categoria por uma cor fixa (ex.: "crimson")
    if categoria_destacar is not None:
        colors = []
        for cat, val in zip(df_ordenado[col_categoria], df_ordenado["count"]):
            if cat == categoria_destacar:
                colors.append(cor_destacada)  # cor fixa para destaque
            else:
                colors.append(val)            # valor numérico => mantém degradê
        fig.update_traces(
            selector=dict(type="bar"),
            marker=dict(
                color=colors,
                colorscale=corescale_barras,
                colorbar=dict(
                    title="Número de Alunos",
                    x=0.90, xanchor="left"   # posiciona o colorbar no "gutter"
                )
            )
        )

    # 2) Evitar corte de rótulos/linha no limite do eixo
    fig.update_traces(selector=dict(type="scatter"), cliponaxis=False)

    return fig