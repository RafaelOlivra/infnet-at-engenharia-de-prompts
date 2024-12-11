
import streamlit as st
import json

def load_insights(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['insights']

insights = load_insights('./data/insights_distribuicao_deputados.json')

st.set_page_config(page_title="Dashboard", layout="wide")

tabs = ["Overview", "Despesas", "Proposições"]
selected_tab = st.sidebar.radio("Navegação", tabs)


if selected_tab == "Overview":
    st.title("Visão Geral")
    st.subheader("Insights sobre a Distribuição dos Deputados")
    for insight in insights:
        st.write(insight)

elif selected_tab == "Despesas":
    st.title("Despesas")
    # Add your Despesas content here

elif selected_tab == "Proposições":
    st.title("Proposições")
    # Add your Proposições content here


