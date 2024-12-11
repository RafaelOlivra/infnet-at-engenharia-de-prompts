import streamlit as st
import yaml
import json
import pandas as pd
import plotly.express as px
from PIL import Image

with open("./data/config.yml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

st.title("Análise de Dados - Câmara dos Deputados")
st.write(config["overview_summary"])

tab1, tab2, tab3 = st.tabs(["Overview", "Despesas", "Proposições"])

with tab1:
    st.subheader("Distribuição de Deputados por Partido")
    image = Image.open("./data/distribuicao_deputados.png")
    st.image(image, use_container_width=True)

    st.subheader("Insights sobre a Distribuição dos Deputados")

    def load_insights(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["insights"]

    insights = load_insights("./data/insights_distribuicao_deputados.json")
    for insight in insights:
        st.write(insight)


insights = load_insights("./data/insights_distribuicao_deputados.json")

with tab2:
    try:
        with open("./data/insights_despesas_deputados.json", "r") as f:
            insights_despesas = json.load(f)
    except FileNotFoundError:
        st.error("File ./data/insights_despesas_deputados.json not found.")
        st.stop()

    try:
        despesas_df = pd.read_parquet("./data/serie_despesas_diárias_deputados.parquet")
    except FileNotFoundError:
        st.error("File ./data/serie_despesas_diárias_deputados.parquet not found.")
        st.stop()

    st.subheader("Insights sobre as Despesas dos Deputados")
    for insight in insights_despesas["insights"]:
        st.write(f"- {insight}")

    st.subheader("Despesas diárias por Deputado")
    deputados = despesas_df["idDeputado"].unique()
    selected_deputado = st.selectbox("Selecione o Deputado", deputados)
    filtered_df = despesas_df[despesas_df["idDeputado"] == selected_deputado]
    fig = px.bar(
        filtered_df,
        x="dataDocumento",
        y="valorDocumento",
        title=f"Despesas do Deputado {selected_deputado}",
    )
    st.plotly_chart(fig)

with tab3:
    try:
        proposicoes_df = pd.read_parquet("./data/proposicoes_deputados.parquet")
    except FileNotFoundError:
        st.error("File ./data/proposicoes_deputados.parquet not found.")
        st.stop()

    try:
        with open("./data/sumarizacao_proposicoes.json", "r") as f:
            sumarizacao_proposicoes = json.load(f)
    except FileNotFoundError:
        st.error("File ./data/sumarizacao_proposicoes.json not found.")
        st.stop()

    st.subheader("Proposições em Andamento")
    st.dataframe(proposicoes_df)
    st.subheader("Sumarização das Proposições")
    st.write(sumarizacao_proposicoes["summary"])
