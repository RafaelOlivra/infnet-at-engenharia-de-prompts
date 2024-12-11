import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image


def app():
    st.set_page_config(page_title="Dashboard", layout="wide")

    st.sidebar.title("Navegação")
    selected_tab = st.sidebar.radio("", ["Overview", "Despesas", "Proposições"])

    if selected_tab == "Overview":
        st.title("Overview")
        st.subheader("Distribuição de Deputados por Partido")
        image = Image.open("./data/distribuicao_deputados.png")
        st.image(image, use_column_width=True)

    elif selected_tab == "Despesas":
        st.title("Despesas")
        # Add Despesas content here

    elif selected_tab == "Proposições":
        st.title("Proposições")
        # Add Proposições content here


if __name__ == "__main__":
    app()
