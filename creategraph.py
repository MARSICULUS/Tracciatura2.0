# Import libriries
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import streamlit as st

@st.cache
def import_data():
    return 0

# Important variables
pio.templates.default = "simple_white"
file_name = "DB_boulder.xlsx"