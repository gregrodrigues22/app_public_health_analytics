import numpy as np
import pandas as pd
import plotly.graph_objects as go

def pareto_plotly(
    df_raw,
    col_categoria="aluno_profissional_escolaridade_descricao",
    col_id="aluno_id",
    col_valor=None,
    metodo_contagem="nunique",
    titulo="Número de Alunos por Escolaridade — Pareto",
    corescale_barras="Blues",
    cor_curva="black",
    th_A=80,
    th_B=95,
    categoria_destacar="Não identificado",
    cor_destacada="crimson",
    largura_px=1200,
    altura_px=800,
    margem=dict(l=300, r=140, t=100, b=60)
):
    if col_categoria not in df_raw.columns:
        raise ValueError(f"Coluna de categoria '{col_categoria}' não encontrada.")
    if col_valor is not None and col_valor not in df_raw.columns:
        raise ValueError(f"col_valor '{col_valor}' não existe.")
    if col_valor is None and col_id is not None and col_id not in df_raw.columns:
        raise ValueError(f"col_id '{col_id}' não existe.")

    if (col_id is None) and (metodo_contagem == "nunique"):
        metodo_contagem = "size"

    if col_valor is not None:
        grp = df_raw.groupby(col_categoria, dropna=False)[col_valor].sum()
    elif col_id is not None and metodo_contagem == "nunique":
        grp = df_raw.groupby(col_categoria, dropna=False)[col_id].nunique()
    else:
        grp = df_raw.groupby(col_categoria, dropna=False).size()

    df_agg = grp.rename("count").reset_index()
    df_ordenado = df_agg.sort_values("count", ascending=False).reset_index(drop=True)
    total = df_ordenado["count"].sum()
    df_ordenado["pct"] = df_ordenado["count"] / total * 100.0
    df_ordenado["cum_pct"] = df_ordenado["pct"].cumsum()

    df_ordenado["label_texto"] = df_ordenado.apply(
        lambda r: f"{int(r['count']):,}".replace(",", ".") + f" ({r['pct']:.1f}%)", axis=1
    )
    cats = df_ordenado[col_categoria]

    cores_barras = df_ordenado["count"].copy()
    if categoria_destacar is not None:
        cores_barras = [
            cor_destacada if cat == categoria_destacar else val
            for cat, val in zip(df_ordenado[col_categoria], df_ordenado["count"])
        ]

    fig = go.Figure()

    # Barras horizontais
    fig.add_trace(go.Bar(
        y=cats,
        x=df_ordenado["count"],
        orientation="h",
        marker=dict(
            color=cores_barras,
            colorscale=corescale_barras,
            colorbar=dict(title="Número de Alunos", x=1.10, xanchor="left")
        ),
        text=df_ordenado["label_texto"],
        textposition="outside",
        name="Contagem",
        hovertemplate="<b>%{y}</b><br>Número: %{x}<extra></extra>"
    ))

    # Curva de Pareto
    fig.add_trace(go.Scatter(
        x=df_ordenado["cum_pct"],
        y=cats,
        mode="lines+markers+text",
        line=dict(color=cor_curva, width=3, shape="spline"),
        marker=dict(size=8, color="white", line=dict(color=cor_curva, width=2)),
        text=[f"{v:.1f}%" for v in df_ordenado["cum_pct"]],
        textposition="middle right",
        name="Acumulado (%)",
        xaxis="x2",
        hovertemplate="<b>%{y}</b><br>Acumulado: %{x:.1f}%<extra></extra>"
    ))

    xmax = df_ordenado["count"].max() * 1.45

    fig.update_layout(
        title=titulo,
        title_x=0.5,
        title_font=dict(size=22, family="Arial Black", color="#1f2c56"),
        width=largura_px,
        height=altura_px,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=margem,

        xaxis=dict(
            domain=[0.0, 0.80],
            title="Número de Alunos",
            range=[0, xmax],
            showgrid=True, gridcolor="rgba(0,0,0,0.08)",
            tickfont=dict(size=14), title_font=dict(size=18)
        ),

        xaxis2=dict(
            overlaying="x", side="top",
            domain=[0.0, 0.80],
            range=[0, 100],
            tick0=0, dtick=20, ticksuffix="%",
            showgrid=False,
            title="Acumulado (%)",
            title_font=dict(size=16),
            tickfont=dict(size=12)
        ),

        yaxis=dict(
            autorange="reversed",
            title=col_categoria,
            tickfont=dict(size=16),
            title_font=dict(size=18)
        ),

        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center")
    )

    for thres in [th_A, th_B]:
        fig.add_shape(type="line", xref="x2", yref="paper",
                      x0=thres, x1=thres, y0=0, y1=1,
                      line=dict(color="gray", width=2, dash="dash"))

    fig.add_shape(type="rect", xref="x2", yref="paper",
                  x0=0, x1=th_A, y0=0, y1=1,
                  fillcolor="rgba(46, 204, 113, 0.18)", line=dict(width=0), layer="below")
    fig.add_shape(type="rect", xref="x2", yref="paper",
                  x0=th_A, x1=th_B, y0=0, y1=1,
                  fillcolor="rgba(243, 156, 18, 0.18)", line=dict(width=0), layer="below")
    fig.add_shape(type="rect", xref="x2", yref="paper",
                  x0=th_B, x1=100, y0=0, y1=1,
                  fillcolor="rgba(231, 76, 60, 0.16)", line=dict(width=0), layer="below")

    fig.add_annotation(x=th_A/2, y=0.5, xref="x2", yref="paper",
                       text="<b>A</b>", showarrow=False,
                       font=dict(size=22, color="rgba(0,0,0,0.6)"))
    fig.add_annotation(x=(th_A+th_B)/2, y=0.5, xref="x2", yref="paper",
                       text="<b>B</b>", showarrow=False,
                       font=dict(size=22, color="rgba(0,0,0,0.6)"))
    fig.add_annotation(x=(th_B+100)/2, y=0.5, xref="x2", yref="paper",
                       text="<b>C</b>", showarrow=False,
                       font=dict(size=22, color="rgba(0,0,0,0.6)"))

    fig.update_traces(selector=dict(type="scatter"), cliponaxis=False)

    return fig