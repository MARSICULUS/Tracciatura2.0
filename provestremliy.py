import io
import base64
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import streamlit as st

# ── Costanti ────────────────────────────────────────────────────────────────

# Incolla qui l'URL completo del Google Sheet (o di un .xlsx su Drive).
# Il file deve essere condiviso come "Chiunque abbia il link può visualizzare".
GDRIVE_URL = "https://docs.google.com/spreadsheets/d/1cCR9cyf44RDRYttIW21sbZTgNVut__wxXvKfJoM53Og/edit?usp=sharing"
SHEET_INDEX = 0

GRADE_ORDER = ["Smile", "Bianco", "Giallo", "Blu", "Verde", "Rosso"]
GRADE_COLORS = {
    "Smile":  "#DDDDDD",
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

# ── Coordinate zone sulla mappa (x, y) in pixel su immagine 2000x1210 ───────
# Origine in alto a sinistra. Stimate dalla piantina annotata.
ZONE_COORDS = {
    "New strapiombo":       (430, 250),
    "New verticale":        (520, 510),
    "New placca":           (580, 800),
    "sx legg. strapiombo":  (940, 710),
    "sx big strapiombo":    (950, 280),
    "verticale":            (1080, 160 ),
    "dx prua":              (1300, 250 ),
    "dx verticale":         (1350, 480),
    "dx placca":            (1350, 790),
}


# ── Caricamento e pulizia dati ───────────────────────────────────────────────

import re

def _build_download_url(url: str) -> str:
    """
    Converte qualsiasi URL di Google Drive/Sheets in un URL di download diretto.
    - Google Sheets  → export come .xlsx
    - File Drive     → download diretto
    """
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
    df_tracciatori =  (
        df.groupby(["TRACCIATORE", "GRADO"], observed= False)
        .size()
        .reset_index(name="Conteggio")
        .pivot(index="TRACCIATORE", columns="GRADO", values="Conteggio")
        .sort_index(axis=1))
    fig = px.bar(
        df_tracciatori,
        orientation="h", color_discrete_map=GRADE_COLORS,
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


# ── Layout Streamlit ─────────────────────────────────────────────────────────

def fig_mappa(df_on: pd.DataFrame, grado: str, img_path: str) -> go.Figure:
    """Mappa della palestra con i boulder del grado selezionato."""
    import base64

    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    img_src = f"data:image/png;base64,{encoded}"

    IMG_W, IMG_H = 2000, 1210

    filtered = df_on[df_on["GRADO"] == grado]
    zone_counts = filtered.groupby("ZONA", observed=False).size().reset_index(name="Count")
    zone_counts = zone_counts[zone_counts["Count"] > 0]

    fig = go.Figure()

    # Sfondo piantina
    fig.add_layout_image(
        dict(
            source=img_src,
            xref="x", yref="y",
            x=0, y=0,
            sizex=IMG_W, sizey=IMG_H,
            sizing="stretch",
            layer="below",
        )
    )

    # Punti per ogni zona
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


def page_overview(df: pd.DataFrame) -> None:
    st.header("Overview generale")
    df_na = get_missing_summary(df)
    if not df_na.empty:
        st.plotly_chart(fig_missing(df_na), use_container_width=True)
    else:
        st.success("Nessun dato mancante nel database.")
    st.plotly_chart(fig_holds(df), use_container_width=True)
    st.plotly_chart(
        fig_grade_distribution(df, "Distribuzione di tutti i gradi"),
        use_container_width=True,
    )
    st.plotly_chart(fig_tracciatori(df, "conteggio tracciatori"))


def page_on_set(df: pd.DataFrame) -> None:
    st.header("Boulder on set")
    df_on = get_on_set(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Boulder on set", len(df_on))
    col2.metric("Zone attive", df_on["ZONA"].nunique())
    col3.metric("Gradi presenti", df_on["GRADO"].nunique())

    st.plotly_chart(
        fig_grade_distribution(df_on, "Distribuzione dei gradi on set"),
        use_container_width=True,
    )
    st.plotly_chart(fig_zone(df_on), use_container_width=True)
    with st.expander("Mostra dati grezzi"):
        st.dataframe(df_on, use_container_width=True)


def page_mappa(df: pd.DataFrame) -> None:
    st.header("Mappa boulder")
    df_on = get_on_set(df)

    grado = st.selectbox(
        "Seleziona il grado",
        options=GRADE_ORDER,
        index=2,
    )

    fig = fig_mappa(df_on, grado, "mappa_palestra.png")
    st.plotly_chart(fig, use_container_width=True)

    # Tabella riepilogativa
    filtered = df_on[df_on["GRADO"] == grado]
    if not filtered.empty:
        summary = filtered.groupby("ZONA", observed=False).size().reset_index(name="Boulder")
        summary = summary[summary["Boulder"] > 0].sort_values("Boulder", ascending=False)
        st.dataframe(summary, use_container_width=True, hide_index=True)
    else:
        st.info(f"Nessun boulder on set con grado {grado}.")


def main() -> None:
    st.set_page_config(page_title="Boulder Dashboard", layout="wide")

    df = load_data(GDRIVE_URL, SHEET_INDEX)

    pages = {"Overview generale": page_overview, "On set": page_on_set, "Mappa": page_mappa}
    choice = st.sidebar.selectbox("Sezione", list(pages.keys()))
    pages[choice](df)


if __name__ == "__main__":
    main()