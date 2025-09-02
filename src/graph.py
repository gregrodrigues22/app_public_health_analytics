import numpy as np
import pandas as pd
import plotly.graph_objects as go

def pareto_plotly(df, col="instituicao", valor="qtd_certificados", titulo="Instituições com mais residentes certificados — Pareto"):
    # Agrupamento e ordenação
    df_agg = df.groupby(col, as_index=False)[valor].sum()
    df_agg = df_agg.sort_values(by=valor, ascending=False)
    df_agg["pct"] = df_agg[valor] / df_agg[valor].sum() * 100
    df_agg["cum_pct"] = df_agg["pct"].cumsum()

    # Zonas de Pareto
    df_agg["zona"] = pd.cut(df_agg["cum_pct"],
                            bins=[0, 80, 95, 100],
                            labels=["A", "B", "C"],
                            include_lowest=True)

    # Cores por zona
    cores = {"A": "#d4f4dd", "B": "#ffe5b4", "C": "#f9d5d3"}
    shapes = []
    for zona in ["A", "B", "C"]:
        if zona in df_agg["zona"].values:
            max_val = df_agg[df_agg["zona"] == zona][valor].cumsum().max()
            shapes.append(dict(
                type="rect",
                xref="x",
                yref="paper",
                x0=0,
                y0=0,
                x1=max_val,
                y1=1,
                fillcolor=cores[zona],
                opacity=0.2,
                layer="below",
                line_width=0,
            ))

    # Altura proporcional ao número de categorias
    altura_px = max(500, 20 * len(df_agg))

    fig = go.Figure()

    # Barras horizontais
    fig.add_trace(go.Bar(
        y=df_agg[col],
        x=df_agg[valor],
        orientation="h",
        marker=dict(
            color=df_agg[valor],
            colorscale="Blues",
            colorbar=dict(title="Número de Alunos"),
        ),
        text=df_agg[valor],
        name="Número de Alunos",
    ))

    # Linha do Pareto
    fig.add_trace(go.Scatter(
        x=df_agg[valor].cumsum(),
        y=df_agg["cum_pct"],
        yaxis="y2",
        mode="lines+markers",
        name="Acumulado (%)",
        line=dict(color="black", width=2),
        marker=dict(color="black", size=6),
    ))

    # Layout
    fig.update_layout(
        height=altura_px,
        title=dict(
            text=titulo,
            font=dict(size=20),
            x=0.5
        ),
        xaxis=dict(title="Número de Alunos"),
        yaxis=dict(title=col, automargin=True),
        yaxis2=dict(
            overlaying="y",
            side="right",
            range=[0, 100],
            tick0=0,
            dtick=20,
            ticksuffix="%",
            showgrid=False,
            title="Acumulado (%)",
        ),
        shapes=shapes,
        template="plotly_white",
        margin=dict(l=180, r=50, t=80, b=40),
    )

    return fig