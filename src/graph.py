import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px  
import pandas as pd
import plotly.express as px
import re
from plotly.subplots import make_subplots
import json
import streamlit as st
from pathlib import Path

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
            shapes=shapes, paper_bgcolor="white",
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

    # --- prepara base ---
    d = df[[grupo_col, valor_col]].copy()
    d[valor_col] = pd.to_numeric(d[valor_col], errors="coerce")
    d = d.groupby(grupo_col, as_index=False)[valor_col].sum()
    d = d.sort_values(valor_col, ascending=False)
    if top_n:
        d = d.head(top_n)

    total_geral = d[valor_col].sum()
    d["pct"] = np.where(total_geral > 0, d[valor_col] / total_geral * 100, 0.0)

    # formatação
    def fmt_int(v):  return f"{int(round(v)):,}".replace(",", ".")
    def fmt_pct(p):  return f"{p:.1f}".replace(".", ",") + "%"

    d["texto"] = d[valor_col].apply(fmt_int) + " (" + d["pct"].apply(fmt_pct) + ")"

    # --- paleta contínua ---
    colorscale = px.colors.sequential.Blues

    # --- cálculo de cor do texto ---
    def parse_rgb_any(c: str) -> tuple[int, int, int]:
        c = c.strip()
        if c.startswith("#"):
            h = c[1:]
            if len(h) == 3:
                h = "".join(ch * 2 for ch in h)
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        if c.lower().startswith("rgb"):
            nums = re.findall(r"[\d.]+", c)
            r, g, b = (float(nums[0]), float(nums[1]), float(nums[2]))
            return int(round(r)), int(round(g)), int(round(b))
        named = {"white": (255, 255, 255), "black": (0, 0, 0)}
        return named.get(c.lower(), (0, 0, 0))

    def cor_texto(rgb_tuple):
        r, g, b = rgb_tuple
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        return "black" if lum > 180 else "white"

    # amostra cores de acordo com os valores para definir contraste do texto
    norm = d[valor_col] / d[valor_col].max() if len(d) else [0]
    sample_hex = px.colors.sample_colorscale(colorscale, norm)
    text_colors = [cor_texto(parse_rgb_any(c)) for c in sample_hex]

    # espaçamento p/ rótulos
    x_max = float(d[valor_col].max()) if len(d) else 1.0
    x_pad = x_max * 0.12

    # cria figura
    fig = go.Figure()

    if orientation == "h":
        fig.add_bar(
            x=d[valor_col],
            y=d[grupo_col],
            orientation="h",
            marker=dict(
                color=d[valor_col],        # valores numéricos (não normalizados)
                colorscale=colorscale,     # define o degradê
                colorbar=dict(title="Total"),
                line=dict(color="rgba(0,0,0,0.30)", width=0.5)
            ),
            text=d["texto"],
            textfont=dict(color=text_colors, size=11),
            textposition="inside",
            hovertemplate="<b>%{y}</b><br>Total: %{x:,}<br>Participação: %{customdata:.1f}%<extra></extra>",
            customdata=d["pct"],
            name=""
        )

        fig.update_yaxes(
            type="category",
            categoryorder="array",
            categoryarray=d[grupo_col].tolist(),
            autorange="reversed",
            title_text=y_label
        )
        fig.update_xaxes(
            title_text=x_label,
            showgrid=True, gridcolor="rgba(0,0,0,0.06)",
            range=[0, x_max + x_pad]
        )

    else:
        fig.add_bar(
            x=d[grupo_col],
            y=d[valor_col],
            marker=dict(
                color=d[valor_col],
                colorscale=colorscale,
                colorbar=dict(title="Total"),
                line=dict(color="rgba(0,0,0,0.30)", width=0.5)
            ),
            text=d["texto"],
            textfont=dict(color=text_colors, size=11),
            textposition="inside",
            hovertemplate="<b>%{x}</b><br>Total: %{y:,}<br>Participação: %{customdata:.1f}%<extra></extra>",
            customdata=d["pct"],
            name=""
        )
        fig.update_xaxes(type="category", categoryarray=d[grupo_col].tolist(), title_text=y_label)
        fig.update_yaxes(title_text=x_label, showgrid=True, gridcolor="rgba(0,0,0,0.06)", range=[0, x_max + x_pad])

    fig.update_layout(
        title=dict(text=titulo, x=0.02, y=0.98),
        bargap=0.2,
        margin=dict(l=200 if orientation == "h" else 60, r=110, t=60, b=60),
        paper_bgcolor="white"
    )

    return fig

# ------------------------------------------------------------------
# 5) Gráfico de Mapa Regional
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# 5) Gráfico de Mapa Regional
# ------------------------------------------------------------------
UF_TO_REGIAO = {
    "AC": "Norte", "AL": "Nordeste", "AP": "Norte", "AM": "Norte", "BA": "Nordeste",
    "CE": "Nordeste", "DF": "Centro-Oeste", "ES": "Sudeste", "GO": "Centro-Oeste",
    "MA": "Nordeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste", "MG": "Sudeste",
    "PA": "Norte", "PB": "Nordeste", "PR": "Sul", "PE": "Nordeste", "PI": "Nordeste",
    "RJ": "Sudeste", "RN": "Nordeste", "RS": "Sul", "RO": "Norte", "RR": "Norte",
    "SC": "Sul", "SP": "Sudeste", "SE": "Nordeste", "TO": "Norte"
}

UF_TO_NOME = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins"
}

def choropleth_por_regiao(
    df: pd.DataFrame,
    *,
    region_col: str = "regiao",
    value_col: str  = "total",
    geojson_local: str = "src/grandes_regioes_json.geojson",
    title: str = "Distribuição de Certificados por Região",
    show_labels: bool = True,
    vmax_quantile: float = 0.95,     # aumenta contraste
):
    if df.empty or region_col not in df.columns or value_col not in df.columns:
        return px.choropleth(title="Sem dados para exibir")

    def _norm(s: pd.Series) -> pd.Series:
        return (s.astype(str).str.strip().str.lower()
                .str.replace(r"\s+", " ", regex=True)
                .str.replace("–", "-", regex=False)
                .str.replace(" - ", "-", regex=False)
                .str.replace("centro oeste", "centro-oeste", regex=False))

    CANON = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    df = df.copy()
    df["_key"] = _norm(df[region_col])
    d = (pd.DataFrame({"regiao": CANON})
         .assign(_key=_norm(pd.Series(CANON)))
         .merge(df[["_key", value_col]], on="_key", how="left"))
    d[value_col] = d[value_col].fillna(0)

    total_geral = float(d[value_col].sum()) or 1.0
    d["pct"] = d[value_col] / total_geral * 100
    d["tot_txt"] = d[value_col].apply(lambda v: f"{v:,.0f}".replace(",", "."))
    d["pct_txt"] = d["pct"].apply(lambda p: f"{p:.1f}%".replace(".", ","))

    gj = json.loads(Path(geojson_local).read_text(encoding="utf-8"))
    props = gj["features"][0].get("properties", {})
    if "NOME1" in props:
        feature_key, locations_col = "properties.NOME1", "regiao"
    elif "NOME2" in props:
        feature_key, locations_col = "properties.NOME2", "locations"
        d["locations"] = d["regiao"].str.upper().str.replace("Ô", "O")
    elif "SIGLA" in props:
        feature_key, locations_col = "properties.SIGLA", "locations"
        d["locations"] = d["regiao"].map({"Norte":"N","Nordeste":"NE","Centro-Oeste":"CO","Sudeste":"SE","Sul":"S"})
    elif "REGIAO" in props:
        feature_key, locations_col = "properties.REGIAO", "regiao"
    elif "regiao" in props:
        feature_key, locations_col = "properties.regiao", "regiao"
    else:
        raise ValueError("GeoJSON de regiões sem NOME1/NOME2/SIGLA/REGIAO/regiao.")

    vmax = float(d[value_col].quantile(vmax_quantile)) or float(d[value_col].max()) or 1.0

    fig = px.choropleth(
        d, geojson=gj, locations=locations_col, featureidkey=feature_key,
        color=value_col, color_continuous_scale=px.colors.sequential.Blues,
        range_color=(0, vmax), labels={value_col: "Total"}, title=title,
        custom_data=["tot_txt", "pct_txt"],
    )
    fig.update_traces(
        hovertemplate="<b>%{location}</b><br>Total: %{customdata[0]}<br>Participação: %{customdata[1]}<extra></extra>",
        marker_line_color="white", marker_line_width=0.6   # <<< contorno
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin=dict(l=10,r=10,t=60,b=10), template="plotly_white",
                      paper_bgcolor="white", plot_bgcolor="#f7f9fb",
                      coloraxis_colorbar=dict(title="Total"))

    if show_labels:
        REGION_LABEL_POS = {
            "Norte": (-60.5,-3.5), "Nordeste": (-41.0,-8.5),
            "Centro-Oeste": (-54.5,-15.5), "Sudeste": (-44.0,-20.5),
            "Sul": (-51.0,-28.5),
        }
        rows = [(lon,lat,f"{r.regiao}\n{r.tot_txt} ({r.pct_txt})")
                for _,r in d.iterrows() if (pos:=REGION_LABEL_POS.get(r.regiao)) and (lon:=pos[0]) is not None for lat in [pos[1]]]
        if rows:
            lons,lats,texts = zip(*rows)
            fig.add_trace(go.Scattergeo(lon=lons, lat=lats, mode="text", text=texts,
                                        textfont=dict(size=11,color="#222",family="Arial"),
                                        hoverinfo="skip", showlegend=False))
    return fig

# ------------------------------------------------------------------
# 6) Gráfico de Mapa UF
# ------------------------------------------------------------------
# Reaproveite os helpers do arquivo anterior:
def fmt_num(x: float, casas: int = 0) -> str:
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ".").replace("X", ",")

def fmt_pct(p: float, casas: int = 1) -> str:
    s = f"{p:.{casas}f}".replace(".", ",")
    return s + "%"

# Mapeamento UF -> nome por extenso (caso o geojson use "name")
UF_TO_NOME = {
    "AC":"Acre","AL":"Alagoas","AP":"Amapá","AM":"Amazonas","BA":"Bahia",
    "CE":"Ceará","DF":"Distrito Federal","ES":"Espírito Santo","GO":"Goiás",
    "MA":"Maranhão","MT":"Mato Grosso","MS":"Mato Grosso do Sul","MG":"Minas Gerais",
    "PA":"Pará","PB":"Paraíba","PR":"Paraná","PE":"Pernambuco","PI":"Piauí",
    "RJ":"Rio de Janeiro","RN":"Rio Grande do Norte","RS":"Rio Grande do Sul",
    "RO":"Rondônia","RR":"Roraima","SC":"Santa Catarina","SP":"São Paulo",
    "SE":"Sergipe","TO":"Tocantins"
}

# Posições aproximadas (lon, lat) para rótulos por UF — opcional
STATE_LABEL_POS = {
    "AC": (-70.3, -9.5), "AL": (-36.6, -9.6), "AP": (-51.1,  1.5), "AM": (-63.5, -4.5),
    "BA": (-41.9,-12.5), "CE": (-39.5, -5.0), "DF": (-47.9,-15.8), "ES": (-40.5,-19.5),
    "GO": (-49.5,-15.9), "MA": (-45.5, -5.2), "MT": (-56.1,-13.2), "MS": (-54.5,-20.6),
    "MG": (-44.3,-18.5), "PA": (-52.0, -2.8), "PB": (-36.6, -7.2), "PR": (-51.6,-24.5),
    "PE": (-37.9, -8.5), "PI": (-43.0, -7.5), "RJ": (-42.5,-22.5), "RN": (-36.6, -5.9),
    "RS": (-53.0,-30.3), "RO": (-62.0,-10.8), "RR": (-61.3,  2.0), "SC": (-50.5,-27.0),
    "SP": (-48.0,-22.5), "SE": (-37.3,-10.5), "TO": (-48.5,-10.0),
}

def choropleth_por_uf(
    df: pd.DataFrame,
    *,
    uf_col: str = "uf",
    value_col: str = "total",
    geojson_local: str = "src/brazil_geo.geojson",
    title: str = "Distribuição de Certificados por UF",
    show_labels: bool = False,
    vmax_quantile: float = 0.95,
):
    if df.empty or uf_col not in df.columns or value_col not in df.columns:
        return px.choropleth(title="Sem dados para exibir")

    UF_TO_NOME = {
        "AC":"Acre","AL":"Alagoas","AP":"Amapá","AM":"Amazonas","BA":"Bahia",
        "CE":"Ceará","DF":"Distrito Federal","ES":"Espírito Santo","GO":"Goiás",
        "MA":"Maranhão","MT":"Mato Grosso","MS":"Mato Grosso do Sul","MG":"Minas Gerais",
        "PA":"Pará","PB":"Paraíba","PR":"Paraná","PE":"Pernambuco","PI":"Piauí",
        "RJ":"Rio de Janeiro","RN":"Rio Grande do Norte","RS":"Rio Grande do Sul",
        "RO":"Rondônia","RR":"Roraima","SC":"Santa Catarina","SP":"São Paulo",
        "SE":"Sergipe","TO":"Tocantins"
    }

    base = pd.DataFrame({"uf": list(UF_TO_NOME.keys())})
    d = base.merge(df[[uf_col, value_col]].rename(columns={uf_col: "uf"}), on="uf", how="left")
    d[value_col] = d[value_col].fillna(0)
    d["uf"] = d["uf"].astype(str).str.upper().str.strip()

    total_geral = float(d[value_col].sum()) or 1.0
    d["pct"] = d[value_col] / total_geral * 100
    d["tot_txt"] = d[value_col].apply(lambda v: f"{v:,.0f}".replace(",", "."))
    d["pct_txt"] = d["pct"].apply(lambda p: f"{p:.1f}%".replace(".", ","))

    gj = json.loads(Path(geojson_local).read_text(encoding="utf-8"))
    props = gj["features"][0].get("properties", {})

    # Detecta automaticamente o campo de correspondência
    if "id" in props:
        feature_key, d["locations"] = "properties.id", d["uf"]
    elif "sigla" in props:
        feature_key, d["locations"] = "properties.sigla", d["uf"]
    elif "SIGLA" in props:
        feature_key, d["locations"] = "properties.SIGLA", d["uf"]
    elif "UF" in props:
        feature_key, d["locations"] = "properties.UF", d["uf"]
    elif "name" in props:
        feature_key, d["locations"] = "properties.name", d["uf"].map(UF_TO_NOME)
    else:
        # último recurso: alguns geojsons usam o "id" no nível da feature, não em properties
        if "id" in gj["features"][0]:
            feature_key, d["locations"] = "id", d["uf"]
        else:
            raise ValueError("GeoJSON de UFs sem id/sigla/UF/SIGLA/name (nem id no nível da feature).")

    vmax = float(d[value_col].quantile(vmax_quantile)) or float(d[value_col].max()) or 1.0

    fig = px.choropleth(
        d, geojson=gj, locations="locations", featureidkey=feature_key,
        color=value_col, color_continuous_scale=px.colors.sequential.Blues,
        range_color=(0, vmax), labels={value_col: "Total"}, title=title,
        custom_data=["tot_txt", "pct_txt", "uf"],
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[2]}</b><br>Total: %{customdata[0]}<br>Participação: %{customdata[1]}<extra></extra>",
        marker_line_color="white", marker_line_width=0.6
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin=dict(l=10,r=10,t=60,b=10), template="plotly_white",
                      paper_bgcolor="white", plot_bgcolor="#f7f9fb",
                      coloraxis_colorbar=dict(title="Total"))

    if show_labels:
        STATE_LABEL_POS = {
            "AC": (-70.3, -9.5), "AL": (-36.6, -9.6), "AP": (-51.1,  1.5), "AM": (-63.5, -4.5),
            "BA": (-41.9,-12.5), "CE": (-39.5, -5.0), "DF": (-47.9,-15.8), "ES": (-40.5,-19.5),
            "GO": (-49.5,-15.9), "MA": (-45.5, -5.2), "MT": (-56.1,-13.2), "MS": (-54.5,-20.6),
            "MG": (-44.3,-18.5), "PA": (-52.0, -2.8), "PB": (-36.6, -7.2), "PR": (-51.6,-24.5),
            "PE": (-37.9, -8.5), "PI": (-43.0, -7.5), "RJ": (-42.5,-22.5), "RN": (-36.6, -5.9),
            "RS": (-53.0,-30.3), "RO": (-62.0,-10.8), "RR": (-61.3,  2.0), "SC": (-50.5,-27.0),
            "SP": (-48.0,-22.5), "SE": (-37.3,-10.5), "TO": (-48.5,-10.0),
        }
        rows = []
        for _, r in d.iterrows():
            uf = r["uf"]
            if uf in STATE_LABEL_POS:
                lon, lat = STATE_LABEL_POS[uf]
                rows.append((lon, lat, f"{uf}\n{r['tot_txt']} ({r['pct_txt']})"))
        if rows:
            lons, lats, texts = zip(*rows)
            fig.add_trace(go.Scattergeo(lon=lons, lat=lats, mode="text", text=texts,
                                        textfont=dict(size=9, color="black"),
                                        hoverinfo="skip", showlegend=False))
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
        title=title, template="plotly_white",
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(side="bottom", tickangle=45)
    )
    return fig