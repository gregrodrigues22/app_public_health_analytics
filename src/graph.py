import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px  
import pandas as pd
import plotly.express as px

# ------------------------------------------------------------------
# 1) PARETO genérico
# ------------------------------------------------------------------
def pareto_plotly(
    df: pd.DataFrame,
    *,
    col: str,                       # coluna categórica (eixo)
    valor: str,                     # coluna com a métrica (numérica)
    titulo: str = "Gráfico de Pareto",
    x_label: str | None = None,
    y_label: str | None = None,
    thresholds: tuple[float, float] = (0.80, 0.95),   # A:0–0.80, B:0.80–0.95, C:0.95–1.00
    top_n: int | None = None,       # se quiser limitar ao top N
    orientation: str = "h",         # "h" (horizontal) ou "v" (vertical)
) -> go.Figure:
    """
    Constrói um Pareto genérico:
    - agrupa por `col`, soma `valor`
    - ordena desc
    - calcula % e % acumulado
    - zonas A/B/C configuráveis por thresholds
    - desenha barras + linha acumulada (%)
    - funciona na horizontal (default) ou vertical

    Retorna: go.Figure
    """
    if df.empty or col not in df.columns or valor not in df.columns:
        fig = go.Figure()
        fig.update_layout(
            title="Sem dados",
            template="plotly_white",
            height=320, margin=dict(l=30, r=20, t=50, b=40),
        )
        return fig

    # agrega e ordena
    d = (
        df.groupby(col, as_index=False)[valor]
        .sum()
        .sort_values(valor, ascending=False)
        .reset_index(drop=True)
    )
    if top_n is not None and top_n > 0:
        d = d.iloc[:top_n].copy()

    total = d[valor].sum()
    d["pct"] = (d[valor] / total) * 100
    d["cum_pct"] = d["pct"].cumsum()

    # zonas
    a, b = thresholds
    bins = [0, a * 100, b * 100, 100.0]
    d["zona"] = pd.cut(d["cum_pct"], bins=bins, labels=["A", "B", "C"], include_lowest=True)

    # cores das zonas (fundo)
    cores = {"A": "#d4f4dd", "B": "#ffe5b4", "C": "#f9d5d3"}

    # shapes de zona (depende da orientação)
    shapes = []
    if orientation == "h":
        # horizontal: x = valor acumulado, y = paper
        for z in ["A", "B", "C"]:
            if (d["zona"] == z).any():
                x1 = d.loc[d["zona"] == z, valor].cumsum().max()
                shapes.append(dict(
                    type="rect", xref="x", yref="paper",
                    x0=0, y0=0, x1=x1, y1=1,
                    fillcolor=cores[z], opacity=0.20, layer="below", line_width=0,
                ))
    else:
        # vertical: y = valor acumulado, x = paper
        for z in ["A", "B", "C"]:
            if (d["zona"] == z).any():
                y1 = d.loc[d["zona"] == z, valor].cumsum().max()
                shapes.append(dict(
                    type="rect", xref="paper", yref="y",
                    x0=0, y0=0, x1=1, y1=y1,
                    fillcolor=cores[z], opacity=0.20, layer="below", line_width=0,
                ))

    # eixo
    eixo_cat = d[col].astype(str).tolist()

    fig = go.Figure()

    # barras
    if orientation == "h":
        fig.add_bar(
            y=d[col], x=d[valor], orientation="h",
            marker=dict(color=d[valor], colorscale="Blues",
                        colorbar=dict(title=y_label or "Valor")),
            text=[f"{v:,.0f}".replace(",", ".") for v in d[valor]],
            textposition="inside", insidetextanchor="middle",
            name=y_label or "Valor",
            hovertemplate=f"<b>%{{y}}</b><br>{valor}: %{{x:,}}<extra></extra>",
        )
        # linha acumulada %
        fig.add_scatter(
            x=d[valor].cumsum(), y=d["cum_pct"], yaxis="y2",
            mode="lines+markers", name="Acumulado (%)",
            line=dict(color="black", width=2), marker=dict(size=6, color="black"),
        )
        fig.update_layout(
            title=titulo,
            xaxis=dict(title=x_label or valor),
            yaxis=dict(title=y_label or col, automargin=True),
            yaxis2=dict(overlaying="y", side="right", range=[0, 100], ticksuffix="%", title="Acumulado (%)"),
            shapes=shapes, template="plotly_white",
            margin=dict(l=180, r=60, t=70, b=40),
        )
    else:
        fig.add_bar(
            x=d[col], y=d[valor], orientation="v",
            marker=dict(color=d[valor], colorscale="Blues",
                        colorbar=dict(title=y_label or "Valor")),
            text=[f"{v:,.0f}".replace(",", ".") for v in d[valor]],
            textposition="outside",
            name=y_label or "Valor",
            hovertemplate=f"<b>%{{x}}</b><br>{valor}: %{{y:,}}<extra></extra>",
        )
        fig.add_scatter(
            x=d[col], y=d[valor].cumsum() / total * 100,
            yaxis="y2", mode="lines+markers", name="Acumulado (%)",
            line=dict(color="black", width=2), marker=dict(size=6, color="black"),
        )
        fig.update_layout(
            title=titulo,
            xaxis=dict(title=x_label or col, categoryorder="array", categoryarray=eixo_cat),
            yaxis=dict(title=y_label or valor),
            yaxis2=dict(overlaying="y", side="right", range=[0,100], ticksuffix="%", title="Acumulado (%)"),
            shapes=shapes, template="plotly_white",
            margin=dict(l=60, r=60, t=70, b=80),
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

    # cores
    RED_STRONG, RED_LIGHT = "#2e7d32", "#a5d6a7" 
    GREEN_STRONG, GREEN_LIGHT = "#c62828",   "#ef9a9a"
    MEAN_COLOR, TREND_COLOR = "#7a7a7a", "#7a7a7a"

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
        add_bars(above.fillna(False), RED_LIGHT,   "Acima da média",  "black")
        add_bars(below.fillna(False), GREEN_LIGHT, "Abaixo da média", "black")
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

    # Δ% p/p (fora da barra)
    delta_text  = ["" if pd.isna(v) else f"{v:+.1f}%" for v in d["yoy_pct"]]
    delta_color = [("#9e9e9e" if pd.isna(v) else (RED_STRONG if v > 0 else GREEN_STRONG))
                   for v in d["yoy_pct"]]
    fig.add_scatter(
        x=d["x_str"], y=(d[y].fillna(media if show_mean else d[y].median()) + span * 0.06),
        mode="text", text=delta_text, textfont=dict(size=11, color=delta_color),
        textposition="top center", name="Δ % p/p", hoverinfo="skip", showlegend=True, cliponaxis=False,
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
        template="plotly_white",
        plot_bgcolor="#f7f9fb", paper_bgcolor="white",
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
    legend_pos: str = "right", # 'right' | 'bottom'
    percent_digits: int = 1,   # casas decimais do %
    number_digits: int = 0,    # casas decimais do valor absoluto
    thousands_sep: str = ".",  # separador de milhar
    min_pct_inside: float = 6, # < % manda rótulo para fora
    color_discrete_map: dict | None = None,  # opcional
):
    # validação mínima
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

    # agrega por categoria
    d = d.groupby(names, as_index=False)[values].sum()

    # top_n -> "Outros"
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

    # ordenação
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

    # formatação de número
    def fmt_num(x: float) -> str:
        s = f"{x:,.{number_digits}f}"
        return s.replace(",", "X").replace(".", thousands_sep).replace("X", ",")

    d["label_inside"] = d.apply(
        lambda r: f"{r['pct']:.{percent_digits}f}%\n{fmt_num(r[values])}",
        axis=1
    )

    # regra inside/outside + pull sutil
    textpos = ["inside" if p >= min_pct_inside else "outside" for p in d["pct"]]
    pull = [0.0 if p >= min_pct_inside else 0.03 for p in d["pct"]]

    fig = px.pie(
        d,
        names=names,
        values=values,
        title=title,
        hole=hole,
        color=names,                         # permite usar color_discrete_map se vier
        color_discrete_map=color_discrete_map,
    )

    # antes de update_traces
    val_fmt = f",.{number_digits}f"     # ex: ',.0f'  -> 98.487
    pct_fmt = f".{percent_digits}%"     # ex: '.1%'   -> 55.3%

    fig.update_traces(
        text=d["label_inside"],
        textposition=textpos,
        textinfo="none",
        texttemplate="%{text}",
        pull=pull,
        hovertemplate=(
            "<b>%{label}</b><br>"
            f"Quantidade: %{{value:{val_fmt}}}<br>"     # <-- value (singular) e chaves duplas
            f"Participação: %{{percent:{pct_fmt}}}"     # <-- percent com formato de %
            "<extra></extra>"
        ),
        textfont=dict(size=12),
        sort=False,
    )

    # legenda
    if legend_pos == "bottom":
        legend_cfg = dict(orientation="h", yanchor="top", y=-0.1, xanchor="left", x=0)
    else:
        legend_cfg = dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)

    fig.update_layout(
        showlegend=show_legend,
        legend=legend_cfg,
        margin=dict(l=10, r=10, t=60, b=10),
        uniformtext_minsize=10,
        uniformtext_mode="show",
        template="plotly_white",
        plot_bgcolor="#f7f9fb", paper_bgcolor="white",
    )
    
    return fig