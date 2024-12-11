import streamlit as st
import yaml

with open("./data/config.yml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

st.title("Análise de Dados - Câmara dos Deputados")
st.write(config["overview_summary"])

tab1, tab2, tab3 = st.tabs(["Overview", "Despesas", "Proposições"])

with tab1:
    st.write("Overview content will go here")

with tab2:
    st.write("Despesas content will go here")

with tab3:
    st.write("Proposições content will go here")
