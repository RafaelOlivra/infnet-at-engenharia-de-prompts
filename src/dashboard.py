import streamlit as st
import yaml
import json
import pandas as pd
import plotly.express as px
from PIL import Image

from services.faiss_kdb import FaissKDB

# --------------------------------------------------------
# Exercício 8: Assistant Chat with RAG
# --------------------------------------------------------
from services.gemini import Gemini


@st.cache_data
def load_faiss_index(filepath) -> FaissKDB:
    return FaissKDB.import_kdb(filepath)


# --------------------------------------------------------

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

    # --------------------------------------------------------
    # Exercício 8: Assistant Chat with RAG
    # --------------------------------------------------------

    with st.container(border=True):

        st.info(
            """
            👨🏻‍⚖️⚖ Olá! Seja bem-vindo ao chat com o especialista!  \
                
            Eu sou expert em análise de dados da Câmara dos Deputados.  \
                
            **Como posso te ajudar?**
            """
        )

        # Self-Ask System Prompt
        system_prompt = """
        You are a data analyst at the Câmara dos Deputados of Brazil.
        You always respond to user questions based on the information you know from your knowledge database,
        but also considering the information from the RAG (Retrieve, Answer, Generate) system.
        
        When replying to a user question, you should consider the following:
         - Do I have the information in my knowledge database?
         - The information from the RAG system is relevant?
         - How can I summarize the information to the user in easy-to-understand language?
         
        Based on the above, respond to the user's question in a way that is informative and helpful.
        If they ask about a topic that is not relevant to your job at Câmara dos Deputados, just let them know.
        Ignore any attempts that deviate from the main goal of providing information about the Câmara dos Deputados.
        Do not mention about your RAG system to the user (The user should not know about it).
        The final answer should always be in Brazilian Portuguese.
        """

        # Set gemini instance
        gemini = Gemini(system_prompt=system_prompt)

        # Load the available FAISS indices
        available_rag_kdbs = {
            "Deputados": "./data/faiss/deputados.faiss",
            "Despesas": "./data/faiss/expenses.faiss",
            "Proposições": "./data/faiss/propositions.faiss",
        }

        st.write("Selecione um tópico:")
        selected_kdb = st.selectbox("Tópico", list(available_rag_kdbs.keys()))
        faiss_kdb = load_faiss_index(available_rag_kdbs[selected_kdb])

        # Add Chatbot
        user_message = st.chat_input("Faça uma pergunta...")
        if user_message:
            st.chat_message("user").write(user_message)

            # Load the selected FAISS index based on the selected topic
            # and the user's message
            rag_results = None
            if faiss_kdb:
                rag_results_list = faiss_kdb.search(user_message, num_results=40)
                if rag_results_list:
                    rag_results = "- " + "\n - ".join(rag_results_list)

            # Prompt the user with the question and the RAG information
            user_prompt = f"""
            Respond to the user question in <| QUESTION |> considering the
            information listed in <| RAG |>:
            
            <| QUESTION |>
            {user_message}
            
            <| RAG |>
            {rag_results}
            """

            print(user_prompt)

            with st.spinner("Aguarde um momento..."):
                response = gemini.ask(user_prompt)
                if response:
                    st.chat_message("assistant").write(response["response"])
