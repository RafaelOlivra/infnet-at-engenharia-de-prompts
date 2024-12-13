import pandas as pd
import json

from services.camara_deputados import CamaraDeputados
from services.gemini import Gemini
from services.chunk_summarizer import ChunkSummarizer
from services.faiss_kdb import FaissKDB

# Set gemini instance
gemini = Gemini()


# -------------------------------------
# Exercício 3: Process "Deputados" data
# -------------------------------------

# Gates
RETRIEVE_DEPUTADOS_PARQUET = False
GENERATE_PARTY_DISTRIBUTION_PARQUET = False
GENERATE_PARTY_DISTRIBUTION_CHART = False
GENERATE_PARTY_DISTRIBUTION_INSIGHTS = False


# Files
deputados_file = "./data/deputados.parquet"
deputados_distribution_file = "./data/02_intermediate/distribuicao_deputados.parquet"
deputados_distribution_pie_chart_file = "./data/distribuicao_deputados.png"
deputados_insights_file = "./data/insights_distribuicao_deputados.json"


def retrieve_deputados_parquet():
    """Request deputados data and save to parquet file."""
    deputados_df = CamaraDeputados().get_deputados()
    print(deputados_df.tail())
    deputados_df.to_parquet(deputados_file)


def generate_deputados_by_party_analysis():
    """Generate an AI powered analysis of the Deputados data."""

    # 3.a) Prepare the data for analysis
    prompt = f"""
    You have a .parquet file located at {deputados_file} with the deputados data
    extracted from the Câmara dos Deputados API (https://dadosabertos.camara.leg.br/api/v2/').
    The parquet file contains a column 'siglaPartido' with the party of each deputado:
    You need to generate a pandas DataFrame with the distribution of deputados by party.
    Rename the DataFrame columns to 'Partido' and 'Deputados'.
    You then need to save the DataFrame in a parquet file at {deputados_distribution_file}
    Don't explain anything, just generate the python code.
    """

    # Generate and Execute the code with Gemini
    if GENERATE_PARTY_DISTRIBUTION_PARQUET:
        code = gemini.ask_and_generate_python_code(prompt=prompt)
        exec(code)

    # Read the Deputados distribution parquet file
    df_party_distribution = pd.read_parquet(deputados_distribution_file)
    print(df_party_distribution)

    # 3.b) Generate a pie chart with the distribution of deputados by party

    prompt = f"""
    You have a .parquet file located at {deputados_distribution_file} with the deputados data
    extracted from the Câmara dos Deputados API.
    The parquet ONLY contains the columns 'Partido' and 'Deputados', where 'Partido' is the party of the deputado
    and 'Deputados' is the number of deputados in that party. There are no extra columns.

    You need to generate a pie chart using matplotlib with the distribution of deputados by party.
    You need to save the pie chart as a .png file at {deputados_distribution_pie_chart_file}.
    Don't explain anything, just generate the python code.
    """

    # Generate and Execute the code with Gemini
    if GENERATE_PARTY_DISTRIBUTION_CHART:
        code = gemini.ask_and_generate_python_code(prompt=prompt)
        exec(code)

    # 3.c) Generate insights about the distribution of deputados by party

    party_distribution_json = df_party_distribution.to_json(orient="records")

    prompt = f"""
    You are a smart data scientist that specializes in doing political analysis.
    You will receive a JSON file with the distribution of deputados by party.
    Based on the data, you need to generate 10 useful insights and analysis about the distribution of deputados by party,
    and how this influences the political landscape in Brazil. (The analysis should be returned in Portuguese).
    For each insight, you will generate a new item inside the "insights" key, following the structure:
    
    {{
        "insights": [
            "O partido com mais deputados é o XXX com YYY deputados",
            "O numero médio de deputados por partido é YYYY"
        ]
    }}
    
    Don't explain anything, just generate the JSON object.
    Bellow is the distribution of deputados by party JSON object:
    
    <|JSON|>
    {party_distribution_json}
    """

    # Generate and Execute the code with Gemini
    if GENERATE_PARTY_DISTRIBUTION_INSIGHTS:
        json_str = gemini.ask_and_generate_json_str(prompt=prompt)
        json_obj = json.loads(json_str)

        # Save the insights to a file
        with open(deputados_insights_file, "w") as file:
            json.dump(json_obj, file, indent=4)


# Request deputados data and save to parquet file
if RETRIEVE_DEPUTADOS_PARQUET:
    retrieve_deputados_parquet()

# Generate deputados by party analysis
generate_deputados_by_party_analysis()


# -------------------------------------
# Exercício 4: Process expenses data
# -------------------------------------

# Gates
RETRIEVE_DEPUTADOS_EXPENSES_PARQUET = False
GENERATE_EXPENSES_ANALYSIS_JSON = False
GENERATE_EXPENSES_INSIGHTS = False

# Files
expenses_file_original = "./data/02_intermediate/despesas-deputados-original.parquet"
expenses_file_grouped = "./data/serie_despesas_diárias_deputados.parquet"
expenses_analysis_results_file = (
    "./data/02_intermediate/resultados_analise_despesas.json"
)
expenses_insights_file = "./data/insights_despesas_deputados.json"


# 4.a) Request deputados expenses data and save to parquet file
def retrieve_deputados_expenses_parquet() -> pd.DataFrame:
    """Request deputados expenses data and save to parquet file."""
    deputados_ids = CamaraDeputados().get_deputados_ids_list()

    df_deputados_expenses = pd.DataFrame()
    for deputado_id in deputados_ids:

        # Print completion percentage
        completion_percentage = (
            0
            if "idDeputado" not in df_deputados_expenses.columns.to_list()
            else (
                len(df_deputados_expenses["idDeputado"].unique()) / len(deputados_ids)
            )
            * 100
        )
        print(f"\n[Completion: {completion_percentage:.2f}%]")

        deputado_expenses = CamaraDeputados().get_deputado_expenses(id=deputado_id)
        deputado_expenses["idDeputado"] = deputado_id
        df_deputados_expenses = pd.concat([df_deputados_expenses, deputado_expenses])

    print(f"\n[Completion: 100%]\n")

    # Save to parquet file
    df_deputados_expenses.reset_index(drop=True, inplace=True)
    df_deputados_expenses.to_parquet(expenses_file_original)
    return df_deputados_expenses


def save_grouped_deputados_expenses(
    df_deputados_expenses: pd.DataFrame,
) -> pd.DataFrame:
    """Group deputados expenses by dataDocumento, idDeputado and tipoDespesa."""

    # Fix some problematic values
    df_deputados_expenses["dataDocumento"] = pd.to_datetime(
        df_deputados_expenses["dataDocumento"]
    )
    df_deputados_expenses["urlDocumento"] = df_deputados_expenses[
        "urlDocumento"
    ].astype("string")

    df = (
        df_deputados_expenses.groupby(["dataDocumento", "idDeputado", "tipoDespesa"])
        .sum()
        .reset_index()
    )
    print(df.head())
    # Save to parquet file
    df.to_parquet(expenses_file_grouped)
    return df


def get_deputado_name_by_id(id: int) -> str:
    """Get deputado name by id."""
    return CamaraDeputados().get_deputado_name_by_id(id)


def generate_deputados_expenses_analysis():
    """Generate an AI powered expense analysis of the Deputados data."""

    # 4.b) Generate an AI powered analysis of the Deputados expenses data with prompt-chaining
    df_expenses_columns = pd.read_parquet(expenses_file_grouped).columns.to_list()

    # Prompt 1
    prompt = f"""
    You are a smart data scientist that specializes in doing political analysis.
    You have a .parquet file located at {expenses_file_grouped} with the deputados' expenses data
    extracted from the Câmara dos Deputados API (https://dadosabertos.camara.leg.br/api/v2/).
    The parquet file contains the following columns: {df_expenses_columns}.
    
    Based on the data, you need to generate an AI-powered analysis of the deputados' expenses.
    You should prepare 3 different analyses and return the Python code to generate them.
    All the code should be generated in a single Python script.
    The result of the python execution should generate a JSON file (utf-8) at {expenses_analysis_results_file},
    with the following structure:
    
    {{
        "analysis": [
            "Total expenses by category: Category 1: R$ XXX, Category 2: R$ YYY",
            "Top 5 deputados with the highest expenses: Deputado 1: R$ XXX, Deputado 2: R$ YYY",
            "...The analysis 3",
        ]
    }}
    
    NOTE: "analysis" should contain only 3 elements.
    To get the Deputado name, you can use the function get_deputado_name_by_id(id).
    Utilize pandas for the analysis.
    Don't explain anything, just generate the python code.
    """

    # Generate and Execute the code with Gemini
    if GENERATE_EXPENSES_ANALYSIS_JSON:
        code = gemini.ask_and_generate_python_code(prompt=prompt)
        exec(code)

    # Read the analysis results
    analysis_results_str = ""
    with open(expenses_analysis_results_file, "r", encoding="utf-8") as file:
        analysis_results = json.load(file)
        print(analysis_results)
        # Make a string list of the analysis results
        analysis_results_str = "\n".join(analysis_results["analysis"])

    # Prompt 2
    prompt = f"""
    You are a smart data scientist that specializes in doing political analysis.
    You have the following analysis results about the deputados expenses:
    
    {analysis_results_str}
    
    Based on the data, you need to generate 5 useful insights about the expenses
    (The analysis should be returned in Portuguese).
    For each insight, you will generate a new item inside the "insights" key,
    following the structure:
    
    {{
        "insights": [
            "A categoria com maior gasto é XXX com o total de R$ YYY",
            "O gasto médio por deputado é R$ YYY",
            ...
        ]
    }}
    
    Don't explain anything, just generate the JSON object.
    """
    # Generate and Execute the code with Gemini
    if GENERATE_EXPENSES_INSIGHTS:
        json_str = gemini.ask_and_generate_json_str(prompt=prompt)
        json_obj = json.loads(json_str)

        # Save the insights to a file
        with open(expenses_insights_file, "w") as file:
            json.dump(json_obj, file, indent=4)


# Request deputados expenses data and save to parquet file
if RETRIEVE_DEPUTADOS_EXPENSES_PARQUET:
    df_expenses = retrieve_deputados_expenses_parquet()
    df_expenses = save_grouped_deputados_expenses(df_expenses)

# Generate deputados expenses analysis
generate_deputados_expenses_analysis()


# -------------------------------------
# Exercício 5: Propositions data
# -------------------------------------

# Gates
RETRIEVE_PROPOSITIONS_PARQUET = False
GENERATE_PROPOSITIONS_SUMMARY = False

# Files
propositions_file = "./data/proposicoes_deputados.parquet"
propositions_summary_file = "./data/sumarizacao_proposicoes.json"


# 5.a) Retrieve propositions data and save to parquet file
def retrieve_propositions_parquet() -> pd.DataFrame:
    """Retrieve propositions data and save to parquet file."""
    categories = {40: "Economia", 42: "Educação", 46: "Ciência, Tecnologia e Inovação"}
    df_propositions = pd.DataFrame()
    for cod_tema, tema in categories.items():
        propositions = CamaraDeputados().get_proposicoes(
            cod_tema=cod_tema, page=1, page_limit=1
        )
        propositions["tema"] = tema
        df_propositions = pd.concat([df_propositions, propositions[:10]])
    print(df_propositions.head())
    df_propositions.to_parquet(propositions_file)
    return df_propositions


# 5.b) Generate propositions summary
def generate_propositions_summary():
    """Generate an AI powered summary of the propositions data."""

    df_propositions = pd.read_parquet(propositions_file)
    # Convert the DataFrame to a readable text maintaining the columns order
    propositions = df_propositions.to_dict(orient="records")
    propositions_text = "\n".join(
        [
            f"{proposition['id']} - {proposition['siglaTipo']} - {proposition['ementa']}"
            for proposition in propositions
        ]
    )

    complete_text = f"""
    Current propositions:
    {propositions_text}
    """
    print(f"\nSummarizing propositions...\n")
    propositions_summary = ChunkSummarizer(
        ai_provider=gemini,
        text=complete_text,
        window_size=400,
        overlap_size=100,
        final_summary_prompt_append="\nReturn your answer in Brazilian Portuguese.",
    ).summarize()

    # Save the summary to a file
    with open(propositions_summary_file, "w", encoding="utf-8") as file:
        json.dump({"summary": propositions_summary}, file, indent=4)


# Request deputados expenses data and save to parquet file
if RETRIEVE_PROPOSITIONS_PARQUET:
    df_propositions = retrieve_propositions_parquet()

# Generate propositions summary
if GENERATE_PROPOSITIONS_SUMMARY:
    generate_propositions_summary()


# --------------------------------------------------------
# Exercício 6: Dashboard generation with Chain-of-Thoughts
# --------------------------------------------------------

# Gates
GENERATE_DASHBOARD = True
GENERATE_DASHBOARD_STEP_1 = False
GENERATE_DASHBOARD_STEP_2 = False
GENERATE_DASHBOARD_STEP_3 = False

# Files
dashboard_file = "./src/dashboard.py"
dashboard_generation_step_1_file = "./data/02_intermediate/dashboard_step_1.py"
dashboard_generation_step_2_file = "./data/02_intermediate/dashboard_step_2.py"
dashboard_generation_step_3_file = "./data/02_intermediate/dashboard_step_3.py"


def generate_dashboard_code_with_cot():
    """Generate the code to create a dashboard with the data generated in the previous exercises."""

    # 6.a) Generate the code to create a dashboard with the data generated in the previous exercises
    prompt = f"""
    You are a data scientist that specializes in creating dashboards with streamlit.
    Generate a streamlit dashboard with the following elements:
    A title with the text "Análise de Dados - Câmara dos Deputados".
    A description that you will get from the yaml file
    located at "./data/config.yml" (text is the key "overview_summary", the file is encoded as utf-8).
    And then add 3 tabs with the following names:
    - "Overview"
    - "Despesas"
    - "Proposições"
    
    Don't add any content of the tabs, just generate the Python code to create the dashboard.
    Don't explain anything, just generate the Python code.
    """

    # Generate and store the code
    if GENERATE_DASHBOARD_STEP_1:
        code = gemini.ask_and_generate_python_code(prompt=prompt)
        # Save the code to a file
        with open(dashboard_generation_step_1_file, "w", encoding="utf-8") as file:
            file.write(code)

    # 6.b) Add the deputados distribution chart to the dashboard
    prompt = f"""
    You are a data scientist that specializes in creating dashboards with streamlit.
    You have a streamlit that you generated in a previous step.
    You have 3 tabs with the following names:
    - "Overview"
    - "Despesas"
    - "Proposições"
    Right now, you need to add a pie chart with the distribution of deputados by party
    to the "Overview" tab with a subtitle containing the text "Distribuição de Deputados por Partido".
    The pie chart is located at {deputados_distribution_pie_chart_file}.
    Don't explain anything, just generate the Python code.
    """

    # Generate and store the code
    if GENERATE_DASHBOARD_STEP_2:
        code = gemini.ask_and_generate_python_code(prompt=prompt)
        # Save the code to a file
        with open(dashboard_generation_step_2_file, "w", encoding="utf-8") as file:
            file.write(code)

    # 6.c) Add the insights to the dashboard
    prompt = f"""
    You are a data scientist that specializes in creating dashboards with streamlit.
    You have a streamlit that you generated in a previous step.
    You have 3 tabs with the following names:
    - "Overview"
    - "Despesas"
    - "Proposições"
    Right now, you need to add the insights about the distributions of the deputados by party
    in the "Overview" tab, with subtitle "Insights sobre a Distribuição dos Deputados".
    The insights are located in JSON file {deputados_insights_file}, the JSON have the following structure:
    {{
    "insights": [
        "Insight 1",
        "Insight 2",
        "Insight 3",
        ]
    }}
    Don't explain anything, just generate the Python code.
    """

    # Generate and store the code
    if GENERATE_DASHBOARD_STEP_3:
        code = gemini.ask_and_generate_python_code(prompt=prompt)
        # Save the code to a file
        with open(dashboard_generation_step_3_file, "w", encoding="utf-8") as file:
            file.write(code)


# Generate the dashboard code
if GENERATE_DASHBOARD:
    generate_dashboard_code_with_cot()


# -------------------------------------------------------
# Exercício 7: Dashboard generation with Batch Prompting
# -------------------------------------------------------

# Gates
GENERATE_DASHBOARD_STEP_4 = False

# Files
dashboard_generation_step_4_file = "./data/02_intermediate/dashboard_step_4.py"


def generate_dashboard_code_with_bp():
    """Generate the code to create a dashboard with the data generated in the previous exercises."""

    # 7) Generate the remaining dashboard code with Batch Prompting

    # Get the columns of the expenses and propositions data
    daily_expenses_columns = pd.read_parquet(expenses_file_grouped).columns.to_list()
    daily_expenses_columns = ", ".join(daily_expenses_columns)
    propositions_columns = pd.read_parquet(propositions_file).columns.to_list()
    propositions_columns = ", ".join(propositions_columns)

    prompt = f"""
    You are a data scientist that specializes in creating dashboards with streamlit.
    You have a streamlit dashboard that you generated in a previous step.
    The dashboard has 3 tabs with the following names:
    - "Overview"
    - "Despesas"
    - "Proposições"
    ####
    You need to add the following elements to the "Despesas" tab (In this order):
    - A subtitle with the text "Insights sobre as Despesas dos Deputados".
    - List the insights from the JSON file located at {expenses_insights_file}.
        The JSON file has the following structure:
        {{
            "insights": [
                "Insight 1",
                "Insight 2",
                "Insight 3",
            ]
        }}
        
    - A subtitle with the text "Despesas diárias por Deputado".
    - A selectbox with the title "Selecione o Deputado" with the deputados names.
      This selectbox should be used to filter the data in the parquet file located at {expenses_file_grouped}.
      The expenses data has the following columns: {daily_expenses_columns}. (This was extracted from the Câmara API).
      The expenses data should be displayed in a bar chart with the x-axis as the "dataDocumento" and the y-axis as the "valorDocumento".
    
    Then add the following elements to the "Proposições" tab (In this order):
    - A subtitle with the text "Proposições em Andamento".
    - A table with the propositions data located at {propositions_file}.
      The propositions data has the following columns: {propositions_columns}. (This was extracted from the Câmara API).
      You can st.DataFrame to display the data.
    - A subtitle with the text "Sumarização das Proposições".
    Display the summary of the propositions data located at {propositions_summary_file}.
      The summary is a JSON file with the following structure:
      {{
          "summary": "The summary text"
      }}
    ####
    Don't explain anything, just generate the Python code.
    """

    # Generate and store the code
    code = gemini.ask_and_generate_python_code(prompt=prompt)
    # Save the code to a file
    with open(dashboard_generation_step_4_file, "w", encoding="utf-8") as file:
        file.write(code)


# Generate the dashboard code
if GENERATE_DASHBOARD_STEP_4:
    generate_dashboard_code_with_bp()


# --------------------------------------------------------
# Exercício 8: Prepare FAISS index with the collected data
# --------------------------------------------------------

# Gates
GENERATE_FAISS_INDEX = True
PROCESS_DEPUTADOS_TO_FAISS = False
PROCESS_EXPENSES_TO_FAISS = False
PROCESS_PROPOSITIONS_TO_FAISS = False
LIMIT_EXPENSES_PER_DEPUTADO_COUNT = 8  # Use this so the file size is not too big

# Files
faiss_index_folder = "./data/faiss"


def generate_faiss_index():
    """Generate the FAISS index with the collected data."""

    faiss_db = FaissKDB(cache_folder=faiss_index_folder + "/cache")

    # DEPUTADOS
    # Add the deputados data to the index, converting each row to a text
    if PROCESS_DEPUTADOS_TO_FAISS:
        deputados_df = pd.read_parquet(deputados_file)
        deputados_df["text"] = deputados_df.apply(
            lambda row: f"{row['id']} {row['nome']} {row['siglaPartido']}", axis=1
        )

        # Add the deputados insights to the index
        with open(deputados_insights_file, "r") as file:
            deputados_insights = json.load(file)
            deputados_insights_text = "\n".join(deputados_insights["insights"])
            deputados_df = pd.concat(
                [
                    deputados_df,
                    pd.DataFrame([deputados_insights_text], columns=["text"]),
                ]
            )

        print(deputados_df)

        # Generate the index
        faiss_db.add_text(deputados_df["text"].to_list())

        # Export the index
        faiss_db.export_kdb(faiss_index_folder + "/deputados.faiss")

    # EXPENSES
    # Add the expenses data to the index, converting each row to a text
    if PROCESS_EXPENSES_TO_FAISS:
        expenses_df = pd.read_parquet(expenses_file_grouped)

        # Keep only the first 50 expenses of each deputado
        # Each deputado will have a maximum of 50 expenses
        if LIMIT_EXPENSES_PER_DEPUTADO_COUNT:
            _expenses_df = pd.DataFrame()
            for deputado_id in expenses_df["idDeputado"].unique():
                _expenses_df = pd.concat(
                    [
                        _expenses_df,
                        expenses_df[expenses_df["idDeputado"] == deputado_id][
                            :LIMIT_EXPENSES_PER_DEPUTADO_COUNT
                        ],
                    ]
                )
            expenses_df = _expenses_df

        # Add the expenses insights to the index
        with open(expenses_insights_file, "r") as file:
            expenses_insights = json.load(file)
            expenses_insights_text = "\n".join(expenses_insights["insights"])
            expenses_df = pd.concat(
                [
                    expenses_df,
                    pd.DataFrame([expenses_insights_text], columns=["text"]),
                ]
            )

        expenses_df["text"] = expenses_df.apply(
            lambda row: f"{row['idDeputado']} {row['tipoDespesa']} {row['valorDocumento']}",
            axis=1,
        )
        print(expenses_df)

        # Generate the index
        faiss_db.add_text(expenses_df["text"].to_list())

        # Export the index
        faiss_db.export_kdb(faiss_index_folder + "/expenses.faiss")

    # PROPOSITIONS
    # Add the propositions data to the index, converting each row to a text
    if PROCESS_PROPOSITIONS_TO_FAISS:
        propositions_df = pd.read_parquet(propositions_file)
        propositions_df["text"] = propositions_df.apply(
            lambda row: f"{row['id']} {row['siglaTipo']} {row['ementa']}",
            axis=1,
        )

        # Add the propositions summary to the index
        with open(propositions_summary_file, "r", encoding="utf-8") as file:
            propositions_summary = json.load(file)
            propositions_summary_text = propositions_summary["summary"]
            propositions_df = pd.concat(
                [
                    propositions_df,
                    pd.DataFrame([propositions_summary_text], columns=["text"]),
                ]
            )

        print(propositions_df)
        faiss_db.add_text(propositions_df["text"].to_list())

        # Export the index
        faiss_db.export_kdb(faiss_index_folder + "/propositions.faiss")


# Generate the FAISS index
if GENERATE_FAISS_INDEX:
    generate_faiss_index()
