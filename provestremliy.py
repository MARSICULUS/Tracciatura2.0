import io
import base64
import math
import re
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import streamlit as st

# ── Costanti ────────────────────────────────────────────────────────────────

GDRIVE_URL = "https://docs.google.com/spreadsheets/d/1cCR9cyf44RDRYttIW21sbZTgNVut__wxXvKfJoM53Og/edit?usp=sharing"
SHEET_INDEX = 0

GRADE_ORDER = ["Smile", "Bianco", "Giallo", "Blu", "Verde", "Rosso"]
GRADE_COLORS = {
    "Smile":  "#9E9E9E",
    "Bianco": "#FCFCFC",
    "Giallo": "#FFD700",
    "Blu":    "#1F77B4",
    "Verde":  "#2CA02C",
    "Rosso":  "#D62728",
}
HOLD_COLORS = {
    "Viola":    "#800080",
    "Verde":    "#228B22",
    "Blu":      "#0000FF",
    "Giallo":   "#FFD700",
    "Rosso":    "#FF0000",
    "Nero":     "#000000",
    "Arancione":"#FF8C00",
    "Rosa":     "#FF69B4",
    "Menta":    "#A6FBB2",
    "Grigio":   "#A9A9A9",
}

ZONE_COORDS = {
    "New strapiombo":       (430, 250),
    "New verticale":        (520, 510),
    "New placca":           (580, 800),
    "sx legg. strapiombo":  (940, 710),
    "sx big strapiombo":    (860, 380),
    "verticale":            (1080, 160),
    "dx prua":              (1300, 250),
    "dx verticale":         (1350, 480),
    "dx placca":            (1350, 790),
}

# ── Caricamento e pulizia dati ───────────────────────────────────────────────

def _build_download_url(url: str) -> str:
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError(f"Impossibile estrarre l'ID dall'URL: {url}")
    file_id = match.group(1)
    if "spreadsheets" in url:
        return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    else:
        return f"https://drive.google.com/uc?export=download&id={file_id}"


@st.cache_data
def load_data(gdrive_url: str, sheet_index: int) -> pd.DataFrame:
    download_url = _build_download_url(gdrive_url)
    response = requests.get(download_url)
    response.raise_for_status()
    df = pd.read_excel(io.BytesIO(response.content), sheet_name=sheet_index)
    df = df[df["COLORE PRESE"].notnull()].copy()
    df["DATA SCADENZA"] = pd.to_datetime(df["DATA SCADENZA"])
    for col in df.select_dtypes("object").columns:
        df[col] = df[col].astype("category")
    df["GRADO"] = df["GRADO"].cat.reorder_categories(GRADE_ORDER, ordered=True)
    return df


def get_on_set(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["ON SET"] == True]


def get_missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    counts = df.isna().sum()
    result = (
        counts[counts > 0]
        .rename("Numero_na")
        .reset_index()
        .rename(columns={"index": "Caratteristica"})
    )
    result["Percentuale"] = result["Numero_na"] / len(df)
    return result.sort_values("Numero_na")


# ── Grafici ──────────────────────────────────────────────────────────────────

def fig_missing(df_na: pd.DataFrame) -> go.Figure:
    colors = ["lightgrey"] * (len(df_na) - 1) + ["red"]
    fig = go.Figure(go.Bar(
        x=df_na["Percentuale"],
        y=df_na["Caratteristica"],
        orientation="h",
        marker=dict(color=colors, line=dict(color="black", width=0.6), opacity=0.85),
    ))
    fig.update_layout(
        title=dict(text="Dati mancanti per caratteristica", font=dict(size=20)),
        xaxis=dict(tickformat=".0%", title=""),
        yaxis=dict(title=""),
        plot_bgcolor="white",
    )
    return fig


def fig_holds(df: pd.DataFrame) -> go.Figure:
    df_prese = (
        df.groupby("COLORE PRESE", observed=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )
    fig = px.bar(
        df_prese, x="COLORE PRESE", y="Count",
        color="COLORE PRESE", color_discrete_map=HOLD_COLORS, text="Count",
    )
    fig.update_layout(
        title=dict(text="Boulder per colore delle prese", font=dict(size=20)),
        showlegend=False,
        xaxis=dict(title="", showgrid=False, showticklabels=False),
        yaxis=dict(title="", showgrid=False, tickfont=dict(size=16)),
        plot_bgcolor="white",
    )
    fig.update_traces(
        textposition="inside",
        textfont=dict(color="white", size=16),
        marker_line=dict(color="black", width=1),
    )
    return fig


def fig_grade_distribution(df: pd.DataFrame, title: str) -> go.Figure:
    dfp = df.groupby("GRADO", observed=False).size().reset_index(name="Conteggio")
    fig = px.bar(
        dfp, x="GRADO", y="Conteggio", text="Conteggio",
        color="GRADO", color_discrete_map=GRADE_COLORS,
    )
    fig.update_layout(
        title=dict(text=title, x=0.5),
        xaxis=dict(title="", showticklabels=False),
        yaxis=dict(title=""),
        showlegend=False,
        plot_bgcolor="white",
    )
    fig.update_traces(
        textposition="inside",
        textfont=dict(color="black"),
        marker_line=dict(color="black", width=0.5),
    )
    return fig


def fig_zone(df_on: pd.DataFrame) -> go.Figure:
    df_zone = (
        df_on.groupby(["ZONA", "GRADO"], observed=False)
        .size()
        .reset_index(name="Conteggio")
        .pivot(index="ZONA", columns="GRADO", values="Conteggio")
        .sort_index()
    )
    fig = px.bar(
        df_zone, barmode="group", orientation="v",
        color_discrete_map=GRADE_COLORS,
    )
    fig.update_layout(
        title=dict(text="Distribuzione dei gradi per zona", x=0.5),
        xaxis=dict(title="", tickangle=0),
        yaxis=dict(title=""),
        showlegend=False,
    )
    fig.update_traces(marker_line_color="black", marker_line_width=0.8)
    return fig


def fig_tracciatori(df: pd.DataFrame, title: str) -> go.Figure:
    df_tracciatori = (
        df.groupby(["TRACCIATORE", "GRADO"], observed=False)
        .size()
        .reset_index(name="Conteggio")
        .pivot(index="TRACCIATORE", columns="GRADO", values="Conteggio")
    )
    df_tracciatori["tot"] = df_tracciatori.sum(axis=1)
    df_tracciatori = df_tracciatori.sort_values("tot", ascending=True)
    fig = px.bar(df_tracciatori, orientation="h", color_discrete_map=GRADE_COLORS)
    fig.update_layout(
        title=dict(text=title, x=0.5),
        xaxis=dict(title="", showticklabels=False),
        yaxis=dict(title=""),
        showlegend=False,
        plot_bgcolor="white",
    )
    fig.update_traces(
        textposition="inside",
        textfont=dict(color="black"),
        marker_line=dict(color="black", width=0.5),
    )
    return fig


# ── Mappa grado singolo ──────────────────────────────────────────────────────

def fig_mappa(df_on: pd.DataFrame, grado: str, img_path: str) -> go.Figure:
    """Mappa della palestra con i boulder del grado selezionato."""
    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    img_src = f"data:image/png;base64,{encoded}"

    IMG_W, IMG_H = 2000, 1210

    filtered = df_on[df_on["GRADO"] == grado]
    zone_counts = filtered.groupby("ZONA", observed=False).size().reset_index(name="Count")
    zone_counts = zone_counts[zone_counts["Count"] > 0]

    fig = go.Figure()
    fig.add_layout_image(dict(
        source=img_src, xref="x", yref="y",
        x=0, y=0, sizex=IMG_W, sizey=IMG_H,
        sizing="stretch", layer="below",
    ))

    if not zone_counts.empty:
        xs, ys, texts, sizes = [], [], [], []
        for _, row in zone_counts.iterrows():
            zona = row["ZONA"]
            if zona in ZONE_COORDS:
                x, y = ZONE_COORDS[zona]
                xs.append(x)
                ys.append(y)
                texts.append(f"{zona}<br>{row['Count']} boulder")
                sizes.append(20 + row["Count"] * 8)

        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="markers+text",
            marker=dict(
                size=sizes,
                color=GRADE_COLORS.get(grado, "#888"),
                line=dict(color="black", width=2),
                opacity=0.85,
            ),
            text=[str(r["Count"]) for _, r in zone_counts.iterrows() if r["ZONA"] in ZONE_COORDS],
            textposition="middle center",
            textfont=dict(size=14, color="black", family="Arial Black"),
            hovertext=texts,
            hoverinfo="text",
        ))

    fig.update_layout(
        xaxis=dict(range=[0, IMG_W], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[IMG_H, 0], showgrid=False, zeroline=False, visible=False,
                   scaleanchor="x", scaleratio=1),
        margin=dict(l=0, r=0, t=30, b=0),
        plot_bgcolor="white",
        height=600,
        title=dict(text=f"Mappa boulder — {grado}", x=0.5),
    )
    return fig


# ── Mappa a torte ────────────────────────────────────────────────────────────

def _pie_traces_for_zone(zona: str, cx: float, cy: float, grade_counts: dict, r: float = 90) -> list:
    """Disegna una torta come poligoni Scatter centrata in (cx, cy)."""
    total = sum(grade_counts.values())
    if total == 0:
        return []
    traces = []
    angle = -math.pi / 2  # parte dall'alto
    for grado, count in grade_counts.items():
        if count == 0:
            continue
        sweep = 2 * math.pi * count / total
        n_pts = max(3, int(sweep / 0.15))
        angles = [angle + i * sweep / n_pts for i in range(n_pts + 1)]
        xs = [cx] + [cx + r * math.cos(a) for a in angles] + [cx]
        ys = [cy] + [cy + r * math.sin(a) for a in angles] + [cy]
        mid = angle + sweep / 2
        lx = cx + (r * 0.6) * math.cos(mid)
        ly = cy + (r * 0.6) * math.sin(mid)
        hover = f"<b>{zona}</b><br>{grado}: {count} boulder"
        traces.append(go.Scatter(
            x=xs, y=ys,
            mode="lines",
            fill="toself",
            fillcolor=GRADE_COLORS.get(grado, "#888"),
            line=dict(color="black", width=1),
            opacity=0.9,
            name=grado,
            legendgroup=grado,
            showlegend=False,
            hovertext=hover,
            hoverinfo="text",
        ))
        traces.append(go.Scatter(
            x=[lx], y=[ly],
            mode="text",
            text=[str(count)],
            textfont=dict(size=11, color="black", family="Arial Black"),
            hoverinfo="skip",
            showlegend=False,
        ))
        angle += sweep
    return traces


def fig_mappa_torte(df_on: pd.DataFrame, img_path: str) -> go.Figure:
    """Mappa con una torta per zona — ogni fetta è un grado."""
    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    img_src = f"data:image/png;base64,{encoded}"

    IMG_W, IMG_H = 2000, 1210

    fig = go.Figure()
    fig.add_layout_image(dict(
        source=img_src, xref="x", yref="y",
        x=0, y=0, sizex=IMG_W, sizey=IMG_H,
        sizing="stretch", layer="below",
    ))

    # Legenda manuale (un trace invisibile per grado)
    for grado in GRADE_ORDER:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=12, color=GRADE_COLORS.get(grado, "#888"),
                        line=dict(color="black", width=1)),
            name=grado,
            legendgroup=grado,
            showlegend=True,
        ))

    df_zone = (
        df_on.groupby(["ZONA", "GRADO"], observed=False)
        .size()
        .reset_index(name="Count")
    )

    for zona, (cx, cy) in ZONE_COORDS.items():
        zona_df = df_zone[df_zone["ZONA"] == zona]
        grade_counts = {g: int(zona_df[zona_df["GRADO"] == g]["Count"].sum()) for g in GRADE_ORDER}
        if sum(grade_counts.values()) == 0:
            continue
        for trace in _pie_traces_for_zone(zona, cx, cy, grade_counts):
            fig.add_trace(trace)
        # fig.add_annotation(
        #     x=cx, y=cy + 85,
        #     text=zona,
        #     showarrow=False,
        #     font=dict(size=11, color="black"),
        #     bgcolor="rgba(255,255,255,0.75)",
        #     borderpad=2,
        # )

    fig.update_layout(
        xaxis=dict(range=[0, IMG_W], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[IMG_H, 0], showgrid=False, zeroline=False, visible=False,
                   scaleanchor="x", scaleratio=1),
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="white",
        height=620,
        title=dict(text="Mappa boulder per zona (torte per grado)", x=0.5),
        legend=dict(title="Grado", orientation="v", x=1.01),
    )
    return fig


# ── Mappa boulder vecchi ─────────────────────────────────────────────────────

def fig_mappa_vecchi(df_top, img_path: str) -> go.Figure:
    """Mappa con i boulder più vecchi, colorati per grado."""
    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    img_src = f"data:image/png;base64,{encoded}"

    IMG_W, IMG_H = 2000, 1210

    fig = go.Figure()
    fig.add_layout_image(dict(
        source=img_src, xref="x", yref="y",
        x=0, y=0, sizex=IMG_W, sizey=IMG_H,
        sizing="stretch", layer="below",
    ))

    nome_col = next((c for c in ["NUMERO TARGHETTA", "NOME", "Nome", "BOULDER"] if c in df_top.columns), None)

    for grado in GRADE_ORDER:
        subset = df_top[df_top["GRADO"] == grado].reset_index(drop=True)
        if subset.empty:
            continue
        xs, ys, hover_texts, labels = [], [], [], []
        for zona, group in subset.groupby("ZONA", observed=False):
            group = group.reset_index(drop=True)
            if zona not in ZONE_COORDS:
                continue
            x, y = ZONE_COORDS[zona]
            xs.append(x)
            ys.append(y)
            righe = []
            for i in range(len(group)):
                nome = group[nome_col].iloc[i] if nome_col else f"Boulder {i+1}"
                data = group["DATA SCADENZA"].iloc[i]
                data_str = data.strftime('%d/%m/%Y') if pd.notna(data) else 'n/d'
                righe.append(f"• {nome}  ({data_str})")
            hover_texts.append(f"<b>{zona}</b><br>" + "<br>".join(righe))
            labels.append(str(len(group)))

        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="markers+text",
            name=grado,
            marker=dict(
                size=36,
                color=GRADE_COLORS.get(grado, "#888"),
                line=dict(color="black", width=2),
                opacity=0.9,
            ),
            text=labels,
            textposition="middle center",
            textfont=dict(size=13, color="black", family="Arial Black"),
            hovertext=hover_texts,
            hoverinfo="text",
        ))

    fig.update_layout(
        xaxis=dict(range=[0, IMG_W], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[IMG_H, 0], showgrid=False, zeroline=False, visible=False,
                   scaleanchor="x", scaleratio=1),
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="white",
        height=600,
        title=dict(text="I boulder più vecchi on set", x=0.5),
        legend=dict(title="Grado", orientation="v"),
    )
    return fig


# ── Layout Streamlit ─────────────────────────────────────────────────────────

def page_overview(df: pd.DataFrame) -> None:
    st.header("Overview generale")
    st.plotly_chart(fig_grade_distribution(df, "Distribuzione di tutti i gradi"), use_container_width=True)
    st.plotly_chart(fig_tracciatori(df, "Conteggio tracciatori"), use_container_width=True)
    st.plotly_chart(fig_holds(df), use_container_width=True)
    df_na = get_missing_summary(df)
    if not df_na.empty:
        st.plotly_chart(fig_missing(df_na), use_container_width=True)
    else:
        st.success("Nessun dato mancante nel database.")


def page_on_set(df: pd.DataFrame) -> None:
    st.header("Boulder on set")
    df_on = get_on_set(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Boulder on set", len(df_on))
    col2.metric("Zone attive", df_on["ZONA"].nunique())
    col3.metric("Gradi presenti", df_on["GRADO"].nunique())
    st.plotly_chart(fig_grade_distribution(df_on, "Distribuzione dei gradi on set"), use_container_width=True)
    st.plotly_chart(fig_zone(df_on), use_container_width=True)
    with st.expander("Mostra dati grezzi"):
        st.dataframe(df_on, use_container_width=True)


def page_mappa(df: pd.DataFrame) -> None:
    st.header("Mappa boulder")
    df_on = get_on_set(df)

    vista = st.radio(
        "Visualizzazione",
        ["Torte per zona (tutti i gradi)", "Grado singolo"],
        horizontal=True,
    )

    if vista == "Torte per zona (tutti i gradi)":
        fig = fig_mappa_torte(df_on, "mappa_palestra.png")
        st.plotly_chart(fig, use_container_width=True)
    else:
        grado = st.selectbox("Seleziona il grado", options=GRADE_ORDER, index=2)
        fig = fig_mappa(df_on, grado, "mappa_palestra.png")
        st.plotly_chart(fig, use_container_width=True)
        filtered = df_on[df_on["GRADO"] == grado]
        if not filtered.empty:
            summary = filtered.groupby("ZONA", observed=False).size().reset_index(name="Boulder")
            summary = summary[summary["Boulder"] > 0].sort_values("Boulder", ascending=False)
            st.dataframe(summary, use_container_width=True, hide_index=True)
        else:
            st.info(f"Nessun boulder on set con grado {grado}.")


def page_mappa_vecchi(df: pd.DataFrame) -> None:
    st.header("Boulder più vecchi")
    df_on = get_on_set(df)

    n = st.slider("Quanti boulder mostrare?", min_value=5, max_value=20, value=10, step=1)

    df_sorted = df_on.dropna(subset=["DATA SCADENZA"]).sort_values("DATA SCADENZA")
    df_top = df_sorted.head(n)

    fig = fig_mappa_torte(df_top, "mappa_palestra.png")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"Lista dei {n} boulder più vecchi")
    cols_show = [c for c in ["ID", "ZONA", "GRADO", "COLORE PRESE", "DATA SCADENZA"] if c in df_top.columns]
    st.dataframe(df_top[cols_show].reset_index(drop=True), use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="Boulder Dashboard", layout="wide")
    df = load_data(GDRIVE_URL, SHEET_INDEX)
    pages = {
        "On set":            page_on_set,
        "Mappa":             page_mappa,
        "Boulder vecchi":    page_mappa_vecchi,
        "Overview generale": page_overview,
    }
    choice = st.sidebar.selectbox("Sezione", list(pages.keys()))
    pages[choice](df)


if __name__ == "__main__":
    main()