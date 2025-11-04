import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px  
import pandas as pd
import plotly.express as px
import re
from plotly.subplots import make_subplots
import json, unicodedata
import streamlit as st
from pathlib import Path
from typing import Union

# ------------------------------------------------------------------
# 1) PARETO genérico
# ------------------------------------------------------------------
def pareto_barh(
    df: pd.DataFrame,
    cat_col: str,
    value_col: str | None = None,          # None => faz contagem
    title: str = "",
    colorbar_title: str = "",
    highlight_value: str | None = None,    # ex.: "Não identificado"
):
    # 1) agrega e ordena
    if value_col is None:
        df_agg = df.groupby(cat_col, dropna=False).size().reset_index(name="count")
    else:
        df_agg = df.groupby(cat_col, dropna=False)[value_col].sum().reset_index(name="count")

    dfp = df_agg.sort_values("count", ascending=False).reset_index(drop=True)
    dfp[cat_col] = dfp[cat_col].astype(str)
    total = dfp["count"].sum()
    dfp["pct"] = 100 * dfp["count"] / total
    dfp["cum_pct"] = dfp["pct"].cumsum()
    dfp["label_text"] = [f"{c:,} ({p:.1f}%)".replace(",", ".") for c, p in zip(dfp["count"], dfp["pct"])]
    cats = dfp[cat_col]

    # 2) barras horizontais
    fig = go.Figure(go.Bar(
        y=cats,
        x=dfp["count"],
        orientation="h",
        text=dfp["label_text"],
        textposition="outside",
        cliponaxis=False,
        name="Quantidade",
        marker=dict(
            color=dfp["count"],
            colorscale="Blues",
            colorbar=dict(title=colorbar_title or "Quantidade", x=0.90, xanchor="left")
        ),
        hovertemplate="<b>%{y}</b><br>Qtde: %{x}<extra></extra>",
    ))

    # 3) curva de Pareto no eixo superior (x2)
    fig.add_trace(go.Scatter(
        x=dfp["cum_pct"],
        y=cats,
        mode="lines+markers+text",
        line=dict(color="black", width=3, shape="spline"),
        marker=dict(size=8, color="white", line=dict(color="black", width=2)),
        text=[f"{v:.1f}%" for v in dfp["cum_pct"]],
        textposition="middle right",
        name="Acumulado (%)",
        xaxis="x2",
        hovertemplate="<b>%{y}</b><br>Acumulado: %{x:.1f}%<extra></extra>",
    ))

    # 4) layout / eixos
    xmax = float(dfp["count"].max()) * 1.45
    left_margin = max(200, int(min(420, cats.map(len).max() * 8)))  # margem para rótulos longos

    fig.update_layout(
        title=title,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=left_margin, r=160, t=80, b=40),  # +top, +bottom
        height=max(440, 26 * len(dfp) + 170),
        legend=dict(
            orientation="h",
            y=1.02, yanchor="bottom",          # desce a legenda
            x=0.9, xanchor="center"
        ),
    )
    # domínio x + x2 (deixa um “gutter” à direita para a colorbar)
    x_domain = [0.0, 0.78]

    fig.update_layout(
        xaxis=dict(
            domain=x_domain,
            range=[0, xmax],
            title="Quantidade",
            title_standoff=6,                # respiro do título X
            showgrid=True, gridcolor="rgba(0,0,0,0.08)",
        ),
        xaxis2=dict(
            overlaying="x", side="top",
            domain=x_domain,
            range=[0, 105],                   # vai além de 100% para respiro
            tickvals=[0, 20, 40, 60, 80, 100],
            ticksuffix="%",
            showgrid=False,
            title="Acumulado (%)",
            title_standoff=10
        ),
        yaxis=dict(autorange="reversed", title=""),
    )

    # 5) faixas A/B/C (80/95) + linhas guias
    th_A, th_B = 80, 95
    for (x0, x1, col) in [(0, th_A, "rgba(46, 204, 113, 0.18)"),
                          (th_A, th_B, "rgba(243, 156, 18, 0.18)"),
                          (th_B, 100, "rgba(231, 76, 60, 0.16)")]:
        fig.add_shape(type="rect", xref="x2", yref="paper",
                      x0=x0, x1=x1, y0=0, y1=1, fillcolor=col, line=dict(width=0), layer="below")
    for x in (th_A, th_B):
        fig.add_shape(type="line", xref="x2", yref="paper",
                      x0=x, x1=x, y0=0, y1=1, line=dict(color="gray", width=2, dash="dash"))
    fig.add_annotation(x=th_A/2, y=0.5, xref="x2", yref="paper",
                       text="<b>A</b>", showarrow=False, font=dict(size=20, color="rgba(0,0,0,0.6)"))
    fig.add_annotation(x=(th_A+th_B)/2, y=0.5, xref="x2", yref="paper",
                       text="<b>B</b>", showarrow=False, font=dict(size=20, color="rgba(0,0,0,0.6)"))
    fig.add_annotation(x=(th_B+100)/2, y=0.5, xref="x2", yref="paper",
                       text="<b>C</b>", showarrow=False, font=dict(size=20, color="rgba(0,0,0,0.6)"))

    # 6) destaque opcional de uma categoria
    if highlight_value is not None and highlight_value in set(dfp[cat_col]):
        colors = [("crimson" if v == highlight_value else c)
                  for v, c in zip(dfp[cat_col], dfp["count"])]
        fig.update_traces(selector=dict(type="bar"),
                          marker=dict(color=colors, colorscale="Blues",
                                      colorbar=dict(title=colorbar_title or "Quantidade",
                                                    x=0.90, xanchor="left")))
    # Evita cortes na curva/labels
    fig.update_traces(
        selector=dict(type="bar"),
        marker=dict(
            color=dfp["count"],
            colorscale="Blues",
            colorbar=dict(title=colorbar_title or "Quantidade", x=0.88, xanchor="left")  # antes ~0.90
        )
    )
    return fig

# ------------------------------------------------------------------
# 2) Barras por período + YoY + média + tendência + (opcional) MM
# ------------------------------------------------------------------
def bar_yoy_trend(
    df: pd.DataFrame,
    *,
    x: str,                             # coluna do eixo X (ano/período ou categoria)
    y: str,                             # coluna métrica
    title: str = "Série temporal",
    x_is_year: bool = True,             # se True, ordena numérico e pode preencher anos
    fill_missing_years: bool = True,    # preencher anos faltantes (min..max)
    show_ma: bool = True,
    ma_window: int = 3,
    show_mean: bool = True,
    show_trend: bool = True,
    legend_pos: str = "top",            # "top" ou "bottom"
    y_label: str | None = None,
) -> go.Figure:
    """
    Gráfico genérico:
      - barras por período/categoria (x,y)
      - Δ% p/p
      - média e tendência opcionais
      - opcionalmente preenche anos faltantes
    """
    if df.empty or x not in df.columns or y not in df.columns:
        fig = go.Figure()
        fig.update_layout(
            title="Sem dados",
            template="plotly_white",
            height=320, margin=dict(l=20, r=20, t=50, b=40),
        )
        return fig

    d0 = df[[x, y]].copy()
    d0[y] = pd.to_numeric(d0[y], errors="coerce")

    if x_is_year:
        d0[x] = pd.to_numeric(d0[x], errors="coerce").astype("Int64")
        d0 = d0.sort_values(x)
        if fill_missing_years and d0[x].notna().any():
            anos = pd.Series(range(int(d0[x].min()), int(d0[x].max()) + 1), name=x)
            d = anos.to_frame().merge(d0, on=x, how="left")
        else:
            d = d0.copy()
        d["x_str"] = d[x].astype(str)
        cat_array = d["x_str"].tolist()
    else:
        d0[x] = d0[x].astype(str)
        d = d0.sort_values(x).copy()
        d["x_str"] = d[x]
        cat_array = d["x_str"].tolist()

    # estatísticas
    media = float(d[y].mean(skipna=True)) if show_mean else np.nan
    d["yoy_pct"] = d[y].pct_change() * 100.0

    # trend
    if show_trend:
        grid_x = np.arange(len(d))
        yy = d[y].to_numpy(float)
        if np.isfinite(yy).sum() >= 2:
            valid = np.isfinite(yy)
            mcoef, bcoef = np.polyfit(grid_x[valid], yy[valid], 1)
            trend = mcoef * grid_x + bcoef
        else:
            trend = yy.copy()
    else:
        trend = None

    ymax = np.nanmax(d[y]) if d[y].notna().any() else 1.0
    span = max(1.0, ymax)
    top_room = ymax + span * 0.12

    # cores (verde = crescimento; vermelho = queda)
    GREEN_STRONG, GREEN_LIGHT = "#2e7d32", "#a5d6a7"   # verde
    RED_STRONG,   RED_LIGHT   = "#c62828", "#ef9a9a"   # vermelho
    MEAN_COLOR,   TREND_COLOR = "#7a7a7a", "#7a7a7a"

    above = d[y] >= media if show_mean else pd.Series(False, index=d.index)
    below = d[y] <  media if show_mean else pd.Series(False, index=d.index)

    fig = go.Figure()

    def add_bars(mask, color, name, txt_color):
        if mask.any():
            fig.add_bar(
                x=d.loc[mask, "x_str"], y=d.loc[mask, y],
                marker_color=color, marker_line_color="#455A64", marker_line_width=0.6,
                width=[0.92] * int(mask.sum()),
                name=name,
                text=[f"{int(v):,}".replace(",", ".") if pd.notna(v) else "" for v in d.loc[mask, y]],
                textposition="inside", insidetextanchor="middle",
                textfont=dict(color=txt_color, size=11),
                hovertemplate="<b>%{x}</b><br>Valor: %{y:,}<extra></extra>",
            )

    if show_mean:
        add_bars(above.fillna(False), GREEN_LIGHT, "Acima da média", "black")
        add_bars(below.fillna(False), RED_LIGHT,   "Abaixo da média", "black")
    else:
        add_bars(pd.Series(True, index=d.index), "#90caf9", "Valor", "black")

    if show_ma:
        ma = d[y].rolling(ma_window, min_periods=1).mean()
        fig.add_scatter(
            x=d["x_str"], y=ma, mode="lines",
            line=dict(dash="dash", width=2, color="#1f77b4"),
            name=f"Média móvel ({ma_window})",
        )

    if show_trend and trend is not None:
        fig.add_scatter(
            x=d["x_str"], y=trend, mode="lines",
            line=dict(width=2, color=TREND_COLOR),
            name="Tendência",
        )

    if show_mean:
        fig.add_scatter(
            x=d["x_str"], y=[media] * len(d),
            mode="lines",
            line=dict(dash="dot", width=3, color=MEAN_COLOR),
            name=f"Média ({int(media):,})".replace(",", "."),
        )

    # Δ% p/p (fora da barra) — cores coerentes
    delta_text  = ["" if pd.isna(v) else f"{v:+.1f}%" for v in d["yoy_pct"]]
    delta_color = [("#9e9e9e" if pd.isna(v) else (GREEN_STRONG if v > 0 else RED_STRONG))
                   for v in d["yoy_pct"]]
    fig.add_scatter(
        x=d["x_str"],
        y=(d[y].fillna(media if show_mean else d[y].median()) + span * 0.06),
        mode="text",
        text=delta_text,
        textfont=dict(size=11, color=delta_color),
        textposition="top center",
        hoverinfo="skip",
        showlegend=False,           # remove "Aa" da legenda
        cliponaxis=False,
    )

    # legenda e layout
    if legend_pos == "bottom":
        legend_cfg = dict(orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0)
        top_margin = 60; title_pad_b = 6
    else:
        legend_cfg = dict(orientation="h", yanchor="bottom", y=1.12, xanchor="left", x=0)
        top_margin = 110; title_pad_b = 28

    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)",
                     rangemode="tozero", range=[0, top_room])
    fig.update_xaxes(
        type="category", categoryorder="array", categoryarray=cat_array,
        tickmode="array", tickvals=cat_array, ticktext=cat_array
    )

    fig.update_layout(
        title=dict(text=title, y=0.98, pad=dict(b=title_pad_b)),
        barmode="overlay", bargap=0.02, bargroupgap=0.0,
        xaxis_title=x if y_label is None else None,
        yaxis_title=y_label or "Valor",
        hovermode="x unified",
        legend=legend_cfg,
        margin=dict(l=60, r=30, t=top_margin, b=50),
        paper_bgcolor="white"
    )

    return fig

# ------------------------------------------------------------------
# 3) Gráfico de Setor
# ------------------------------------------------------------------
def pie_standard(
    df: pd.DataFrame,
    names: str,                # coluna categórica
    values: str,               # coluna numérica
    title: str = "",
    hole: float = 0.35,        # 0 = pizza, 0.35 = donut
    sort: str = "desc",        # 'desc', 'asc', 'none'
    top_n: int | None = None,  # agrega além dos top_n em "Outros"
    others_label: str = "Outros",
    none_label: str = "(não informado)",
    show_legend: bool = True,
    legend_pos: str = "below_title",  # 'below_title' | 'right' | 'bottom'
    percent_digits: int = 1,
    number_digits: int = 0,
    thousands_sep: str = ".",
    min_pct_inside: float = 6,
    color_discrete_map: dict | None = None,
):
    import re
    import plotly.express as px

    if (
        df is None or df.empty
        or names not in df.columns
        or values not in df.columns
    ):
        return px.pie(
            pd.DataFrame({names: [], values: []}),
            names=names, values=values, title=title, hole=hole
        )

    d = df[[names, values]].copy()
    d[names] = d[names].fillna(none_label).astype(str)
    d[values] = pd.to_numeric(d[values], errors="coerce").fillna(0)
    d = d.groupby(names, as_index=False)[values].sum()

    if top_n is not None and top_n > 0 and len(d) > top_n:
        d = d.sort_values(values, ascending=False)
        top = d.head(top_n)
        tail = d.iloc[top_n:]
        outros_val = tail[values].sum()
        if outros_val > 0:
            d = pd.concat(
                [top, pd.DataFrame({names: [others_label], values: [outros_val]})],
                ignore_index=True
            )

    if sort == "desc":
        d = d.sort_values(values, ascending=False)
    elif sort == "asc":
        d = d.sort_values(values, ascending=True)

    total = d[values].sum()
    if total == 0:
        return px.pie(
            pd.DataFrame({names: [], values: []}),
            names=names, values=values, title=title, hole=hole
        )

    d["pct"] = (d[values] / total * 100)

    def fmt_num(x: float) -> str:
        s = f"{x:,.{number_digits}f}"
        return s.replace(",", "X").replace(".", thousands_sep).replace("X", ",")

    d["label_inside"] = d.apply(
        lambda r: f"{r['pct']:.{percent_digits}f}%\n{fmt_num(r[values])}",
        axis=1
    )

    textpos = ["inside" if p >= min_pct_inside else "outside" for p in d["pct"]]
    pull = [0.0 if p >= min_pct_inside else 0.03 for p in d["pct"]]

    fig = px.pie(
        d,
        names=names,
        values=values,
        title=title,
        hole=hole,
        color=names,
        color_discrete_map=color_discrete_map,
    )

    val_fmt = f",.{number_digits}f"
    pct_fmt = f".{percent_digits}%"

    fig.update_traces(
        text=d["label_inside"],
        textposition=textpos,
        textinfo="none",
        texttemplate="%{text}",
        pull=pull,
        hovertemplate=(
            "<b>%{label}</b><br>"
            f"Quantidade: %{{value:{val_fmt}}}<br>"
            f"Participação: %{{percent:{pct_fmt}}}"
            "<extra></extra>"
        ),
        textfont=dict(size=12),
        sort=False,
    )

    # --- legenda logo abaixo do título ---
    if legend_pos == "below_title":
        legend_cfg = dict(
            orientation="h",
            yanchor="top",
            y=1.0,              # ligeiramente abaixo do título
            xanchor="right",
            x=0.0,
            valign="top"
        )
        title_pad = 90          # aumenta o espaço para o título + legenda
    elif legend_pos == "bottom":
        legend_cfg = dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5
        )
        title_pad = 60
    else:
        legend_cfg = dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
        title_pad = 60

    fig.update_layout(
        showlegend=show_legend,
        legend=legend_cfg,
        margin=dict(l=10, r=10, t=title_pad, b=10),
        uniformtext_minsize=10,
        uniformtext_mode="show",
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="#f7f9fb",
    )

    return fig

# ------------------------------------------------------------------
# 4) Gráfico de Barras
# ------------------------------------------------------------------
def bar_total_por_grupo(
    df: pd.DataFrame,
    *,
    grupo_col: str,
    valor_col: str,
    titulo: str = "Total por Grupo",
    x_label: str = "Certificados (distintos)",
    y_label: str = "Programa",
    top_n: int | None = 10,
    orientation: str = "h",
) -> go.Figure:
    import re

    d = df[[grupo_col, valor_col]].copy()
    d[valor_col] = pd.to_numeric(d[valor_col], errors="coerce")
    d = d.groupby(grupo_col, as_index=False)[valor_col].sum()
    d = d.sort_values(valor_col, ascending=False)
    if top_n:
        d = d.head(top_n)

    total_geral = d[valor_col].sum()
    d["pct"] = np.where(total_geral > 0, d[valor_col] / total_geral * 100, 0.0)

    def fmt_int(v):  return f"{int(round(v)):,}".replace(",", ".")
    def fmt_pct(p):  return f"{p:.1f}".replace(".", ",") + "%"

    d["texto"] = d[valor_col].apply(fmt_int) + " (" + d["pct"].apply(fmt_pct) + ")"
    colorscale = px.colors.sequential.Blues

    def parse_rgb_any(c: str):
        c = c.strip()
        if c.startswith("#"):
            h = c[1:];  h = "".join(ch*2 for ch in h) if len(h)==3 else h
            return tuple(int(h[i:i+2],16) for i in (0,2,4))
        if c.lower().startswith("rgb"):
            nums = re.findall(r"[\d.]+", c)
            return tuple(int(round(float(v))) for v in nums[:3])
        return (0, 0, 0)

    def cor_texto(rgb):
        r,g,b = rgb
        lum = 0.299*r + 0.587*g + 0.114*b
        return "black" if lum > 180 else "white"

    norm = d[valor_col] / d[valor_col].max() if len(d) else [0]
    sample_hex = px.colors.sample_colorscale(colorscale, norm)
    text_colors = [cor_texto(parse_rgb_any(c)) for c in sample_hex]

    x_max = float(d[valor_col].max()) if len(d) else 1.0
    x_pad = x_max * 0.12

    fig = go.Figure()

    if orientation == "h":
        fig.add_bar(
            x=d[valor_col], y=d[grupo_col], orientation="h",
            marker=dict(color=d[valor_col], colorscale=colorscale,
                        colorbar=dict(title="Total"),
                        line=dict(color="rgba(0,0,0,0.30)", width=0.5)),
            text=d["texto"], textfont=dict(color=text_colors, size=11),
            textposition="inside",
            hovertemplate="<b>%{y}</b><br>Total: %{x:,}<br>Participação: %{customdata:.1f}%<extra></extra>",
            customdata=d["pct"], name=""
        )

        fig.update_yaxes(
            type="category", categoryorder="array",
            categoryarray=d[grupo_col].tolist(), autorange="reversed",
            title_text=y_label
        )
        fig.update_xaxes(
            title_text=x_label,
            showgrid=True, gridcolor="rgba(0,0,0,0.06)",
            range=[0, x_max + x_pad],
            tickformat="~s",              # <<< rótulos no formato 5k, 10k, 15k…
            separatethousands=True
        )
    else:
        fig.add_bar(
            x=d[grupo_col], y=d[valor_col],
            marker=dict(color=d[valor_col], colorscale=colorscale,
                        colorbar=dict(title="Total"),
                        line=dict(color="rgba(0,0,0,0.30)", width=0.5)),
            text=d["texto"], textfont=dict(color=text_colors, size=11),
            textposition="inside",
            hovertemplate="<b>%{x}</b><br>Total: %{y:,}<br>Participação: %{customdata:.1f}%<extra></extra>",
            customdata=d["pct"], name=""
        )
        fig.update_xaxes(
            type="category", categoryorder="array",
            categoryarray=d[grupo_col].tolist(), title_text=y_label
        )
        fig.update_yaxes(
            title_text=x_label, showgrid=True, gridcolor="rgba(0,0,0,0.06)",
            range=[0, x_max + x_pad],
            tickformat="~s",              # <<< idem para a vertical
            separatethousands=True
        )

    fig.update_layout(
        title=dict(text=titulo, x=0.02, y=0.98),
        bargap=0.2,
        margin=dict(l=200 if orientation == "h" else 60, r=110, t=60, b=60),
        paper_bgcolor="white"
    )

    return fig
    
# ------------------------------------------------------------------
# 7) Heatmap
# ------------------------------------------------------------------
def _fmt_int(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")

def heatmap_absoluto(
    df: pd.DataFrame,
    *,
    row_col: str,
    col_col: str,
    value_col: str,
    title: str = "",
    percent_of: str | None = "row",          # "row", "col", "all" ou None
    show_totals: str | bool = False,         # False | "row" | "col" | "both"
    zero_as_blank: bool = True,
    decimals: int = 1,
):
    # 1) pivô
    p = (
        df.pivot_table(index=row_col, columns=col_col, values=value_col,
                       aggfunc="sum", fill_value=0)
        .sort_index()
    )

    # 2) adiciona totais se solicitado
    base_for_scale = p.copy()
    if show_totals in ("row", "both", True):
        p["Total"] = p.sum(axis=1)
    if show_totals in ("col", "both", True):
        p.loc["Total"] = p.sum(axis=0)

    # 3) percentuais (só para as células "normais")
    Z = p.values.astype(float)
    pct = np.full_like(Z, np.nan, dtype=float)

    # fatias sem as linhas/colunas de total (para não calcular % nelas)
    rows_norm = slice(0, base_for_scale.shape[0])
    cols_norm = slice(0, base_for_scale.shape[1])

    if percent_of in ("row", "col", "all"):
        if percent_of == "row":
            denom = base_for_scale.sum(axis=1).replace(0, np.nan).values[:, None]
            pct_part = (base_for_scale.values / denom) * 100
        elif percent_of == "col":
            denom = base_for_scale.sum(axis=0).replace(0, np.nan).values[None, :]
            pct_part = (base_for_scale.values / denom) * 100
        else:  # "all"
            denom = base_for_scale.values.sum() or np.nan
            pct_part = (base_for_scale.values / denom) * 100

        pct[rows_norm, cols_norm] = pct_part

    # 4) texto (valor + %)
    if zero_as_blank:
        mask_zero = Z == 0
    else:
        mask_zero = np.zeros_like(Z, dtype=bool)

    def _cell_text(v, p):
        if np.isnan(p):
            return _fmt_int(v) if v != 0 else ""
        return f"{_fmt_int(v)} ({p:.{decimals}f}%)" if v != 0 else ""

    text = np.empty(Z.shape, dtype=object)
    for i in range(Z.shape[0]):
        for j in range(Z.shape[1]):
            text[i, j] = "" if mask_zero[i, j] else _cell_text(Z[i, j], pct[i, j])

    # 5) cores: escala baseada só nas células sem total
    vmax = float(base_for_scale.values.max()) or 1.0

    fig = go.Figure(
        go.Heatmap(
            z=Z, x=list(p.columns), y=list(p.index),
            colorscale="Blues", zmin=0, zmax=vmax,
            text=text, texttemplate="%{text}",
            hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>Total: %{z:,.0f}<extra></extra>",
            colorbar={"title": "Total absoluto"}
        )
    )

    fig.update_layout(
        title=title,
        template="plotly_white",
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(
            side="bottom",
            tickangle=0,
            tickmode="array",              # <--- força ticks manuais
            tickvals=list(p.columns),      # <--- todos os anos (ou colunas)
            ticktext=[str(x) for x in p.columns],
            type="category",               # <--- garante eixo categórico
        ),
        yaxis=dict(type="category"),
    )
    return fig

# ------------------------------------------------------------------
# 8) Entradas e Saídas
# ------------------------------------------------------------------
def barras_bilaterais_entradas_saidas_ano(
    df: pd.DataFrame,
    *,
    ano_col: str = "ano",
    entradas_col: str = "entradas",
    saidas_col: str = "saidas",
    titulo: str = "Entradas (+) vs Saídas (–) por ano",
    cor_entradas: str = "rgb(19, 93, 171)",
    cor_saidas: str = "rgb(0, 176, 239)",
    cor_media_entradas: str = "rgba(128, 128, 128, 0.5)",
    cor_media_saidas: str = "rgba(128, 128, 128, 0.5)",
    altura: int = 560,
    largura: int = 1100,
) -> go.Figure:
    """
    Desenha barras bilaterais por ano, com linhas de média de entrada e saída:
      - Entradas positivas
      - Saídas negativas (hover mostra valor positivo)
      - Linhas médias horizontais (para Entradas e Saídas)
    """
    if df.empty or not set([ano_col, entradas_col, saidas_col]).issubset(df.columns):
        fig = go.Figure()
        fig.update_layout(
            title="Sem dados",
            template="plotly_white",
            height=320, margin=dict(l=30, r=20, t=50, b=40),
        )
        return fig

    d = df.copy().sort_values(ano_col)
    d["_saidas_neg"] = -pd.to_numeric(d[saidas_col], errors="coerce").fillna(0).astype(int)
    d[entradas_col]   =  pd.to_numeric(d[entradas_col], errors="coerce").fillna(0).astype(int)

    # médias
    media_entradas = d[entradas_col].mean()
    media_saidas   = d[saidas_col].mean()

    fig = go.Figure()

    # barras positivas
    fig.add_bar(
        x=d[ano_col],
        y=d[entradas_col],
        name="Entradas",
        marker_color=cor_entradas,
        hovertemplate="Ano=%{x}<br>Entradas=%{y:,}<extra></extra>",
        text=[f"{v:,}" if v > 0 else "" for v in d[entradas_col]],
        textposition="outside",
        textfont=dict(size=14, color="black"),
        cliponaxis=False,
    )

    # barras negativas
    fig.add_bar(
        x=d[ano_col],
        y=d["_saidas_neg"],
        name="Saídas",
        marker_color=cor_saidas,
        hovertemplate="Ano=%{x}<br>Saídas=%{customdata:,}<extra></extra>",
        customdata=d[saidas_col],
        text=[f"{v:,}" if v > 0 else "" for v in d[saidas_col]],
        textposition="outside",
        textfont=dict(size=14, color="black"),
        cliponaxis=False,
    )

    # eixo Y com folga
    max_abs = max(d[entradas_col].max(), d[saidas_col].max())
    margem = 1.35
    fig.update_yaxes(range=[-max_abs*margem, max_abs*margem])

    # linhas de média
    fig.add_hline(
        y=media_entradas,
        line_dash="dash",
        line_color=cor_media_entradas,
        annotation_text=f"Média Entradas ({media_entradas:,.0f})",
        annotation_position="top left",
        annotation_font=dict(color=cor_media_entradas, size=13),
    )

    fig.add_hline(
        y=-media_saidas,
        line_dash="dash",
        line_color=cor_media_saidas,
        annotation_text=f"Média Saídas ({media_saidas:,.0f})",
        annotation_position="bottom left",
        annotation_font=dict(color=cor_media_saidas, size=13),
    )

    # layout geral
    fig.update_layout(
        title=titulo,
        barmode="relative",
        xaxis=dict(title="Ano"),
        yaxis=dict(title="Qtd. de médicos (distintos)", tickformat=","),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=1.14),
        height=altura,
        width=largura,
        margin=dict(l=70, r=40, t=90, b=60),
        paper_bgcolor="white",
        plot_bgcolor="white",
        template="plotly_white",
    )

    return fig