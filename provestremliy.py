# Import libriries
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import streamlit as st


#IMPORT FILES
file_name = "DB_boulder.xlsx"
n_page = 0
# pio.templates.default = "plotly_dark"

df = pd.read_excel(file_name, sheet_name= n_page)
df = df[df["COLORE PRESE"].notnull()]
df["DATA SCADENZA"] = pd.to_datetime(df["DATA SCADENZA"])
for i in df.columns:
    if df[i].dtype == "object":
        df[i] = df[i].astype("category")

df["GRADO"] = df["GRADO"].cat.reorder_categories(["Smile", "Bianco", "Giallo", "Blu", "Verde", "Rosso"], ordered=True)


df_on = df[df["ON SET"] == True]

df_na = pd.DataFrame(columns= ["Caratteristica", "Numero_na"])

for i in df.columns:
    df_na._set_value(index = len(df_na), col = "Caratteristica", value = i)
    na = df[i].isna().sum()
    df_na._set_value(index = len(df_na)-1, col = "Numero_na", value = na)

df_na["Percentuali"] = df_na['Numero_na'] / len(df)

#GRAFICI
#Grafico che mostra quanti dati mancano nel database
# Selezionare solo le caratteristiche che hanno valori nulli
dfp_na = df_na[df_na["Numero_na"] != 0].sort_values("Numero_na", ascending=True)
# Colori delle colonne
colors = ['lightgrey'] * (len(dfp_na) - 1) + ['red']

fig_na = go.Figure()

fig_na.add_trace(go.Bar(
    x = dfp_na['Percentuali'],
    y = dfp_na['Caratteristica'],
    orientation = 'h',
    marker=dict(
        color=colors, 
        line=dict(color='black', width=0.6), 
        opacity=0.85)
))

#COLORI DELLE PRESE DEI VARI BOULDER
df_prese = df.groupby("COLORE PRESE", observed=False).size().reset_index(name="Count")
df_prese = df_prese.sort_values("Count", ascending=False)
cdm = {
    "Viola": "#800080",      # purple
    "Verde": "#228B22",      # green
    "Blu": "#0000FF",        # blue
    "Giallo": "#FFD700",     # gold/yellow
    "Rosso": "#FF0000",      # red
    "Nero": "#000000",       # black
    "Arancione": "#FF8C00",  # orange
    "Rosa": "#FF69B4",       # pink
    "Menta": "#A6FBB2",      # mint
    "Grigio": "#A9A9A9",     # dark grey
    }

fig_prese = px.bar(df_prese, x = "COLORE PRESE", y = "Count", color = "COLORE PRESE", color_discrete_map = cdm, text = "Count")

fig_prese.update_layout(
    title = dict(text="Numero di boulder per colore delle prese", x = 0,  font = dict(size = 30)),
    showlegend = False,
    xaxis=dict(title = "", showgrid=False,showticklabels = False),
    yaxis=dict(title = "", showgrid=False, tickfont = dict(size = 20)),
    plot_bgcolor="white"
)
fig_prese.update_traces(
    textposition='inside',  # posiziona il numero all’interno della barra
    textfont=dict(color='white', size=20),
    marker_line  = dict(color = "black", width = 1)
)

#Distrubuzione dei gradi
dfp_grade_on = df_on.groupby("GRADO", observed=False).size().reset_index(name = "conto")

fig_grade_on = px.bar(
    dfp_grade_on,
    x = "GRADO",
    y = "conto",
    text = "conto",
    color="GRADO",
    color_discrete_map={
        "Smile": "#DDDDDD",  
        "Bianco": "#FCFCFC", 
        "Giallo": "#FFD700", 
        "Blu": "#1F77B4",    
        "Verde": "#2CA02C",  
        "Rosso": "#D62728"
        })
fig_grade_on.update_layout(
    title = dict(text = "Distribuzione dei gradi nella palestra", x = 0.5),
    xaxis = dict(title = "", showticklabels = False),
    yaxis = dict(title = ""),
    showlegend=False)
fig_grade_on.update_traces(
    textposition='inside',  # posiziona il numero all’interno della barra
    textfont=dict(color='black'),  # colore e dimensione del testo
    marker_line=dict(color="black", width=0.5)
)

dfp_grade = df.groupby("GRADO", observed=False).size().reset_index(name = "conto")
fig_grade_all = px.bar(
    dfp_grade,
    x = "GRADO",
    y = "conto",
    text = "conto",
    color="GRADO",
    color_discrete_map={
        "Smile": "#DDDDDD",  
        "Bianco": "#FCFCFC", 
        "Giallo": "#FFD700", 
        "Blu": "#1F77B4",    
        "Verde": "#2CA02C",  
        "Rosso": "#D62728"
        })
fig_grade_all.update_layout(
    title = dict(text = "Distribuzione dei gradi nella palestra", x = 0.5),
    xaxis = dict(title = "", showticklabels = False),
    yaxis = dict(title = ""),
    showlegend=False)
fig_grade_all.update_traces(
    textposition='inside',  # posiziona il numero all’interno della barra
    textfont=dict(color='black'),  # colore e dimensione del testo
    marker_line=dict(color="black", width=0.5)
)

#boulder nelle zone
df_zone = df_on.groupby(["ZONA", "GRADO"], observed=False).size().reset_index(name="Conteggio")
df_zone = df_zone.pivot(columns="GRADO", index = "ZONA", values="Conteggio")


df_zone.loc[:,"somma"] = df_zone.sum(axis=1)
df_zone = df_zone.sort_values("somma")
df_zone.drop("somma", axis=1, inplace=True)
df_zone = df_zone.sort_index()
df_zone

fig_zona = px.bar(
    df_zone, 
    barmode="group", orientation="v",
    color_discrete_map={
        "Smile": "#DDDDDD",  
        "Bianco": "#FCFCFC", 
        "Giallo": "#FFD700", 
        "Blu": "#1F77B4",    
        "Verde": "#2CA02C",  
        "Rosso": "#D62728"
        }
    )
fig_zona.update_traces(
    marker_line_color="black",
    marker_line_width=0.8
)
fig_zona.update_layout(
    title = dict(text = "Distribuzione dei gradi per zona", x = 0.5),
    xaxis=dict(title = "",tickangle=0),
    yaxis=dict(title = "",tickangle=0),
    showlegend=False)





#DASH BOARD
st.write(df.dtypes)

add_sidebar = st.sidebar.selectbox("", ("Overview generale", "On set"))
if add_sidebar == "Overview generale":
    st.write("da mettere overview generale")
    st.plotly_chart(fig_na)
    st.plotly_chart(fig_prese)
    st.plotly_chart(fig_grade_all)
if add_sidebar == "On set":
    st.write("da mettere le cose on set")
    st.dataframe(df_on)
    st.dataframe(dfp_grade_on)
    st.plotly_chart(fig_grade_on)
    st.plotly_chart(fig_zona)

