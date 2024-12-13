import requests
import pandas as pd
import streamlit as st
import time


class CamaraDeputados:
    def __init__(self):
        """
        Initialize the CamaraDeputados API service with the base URL and request headers.
        """
        self.api_base_url = "https://dadosabertos.camara.leg.br/api/v2"

        self.request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    # ----------------------------
    # Deputados
    # ----------------------------

    def get_deputados(self) -> pd.DataFrame:
        """
        Get all deputados (representatives) data from the API.

        :return: DataFrame containing the deputados data.
        """
        resp = self._request(self.api_base_url + "/deputados")
        return pd.DataFrame(resp["dados"])

    def get_deputados_ids(self) -> pd.DataFrame:
        """
        Get a DataFrame containing only the IDs of all deputados.

        :return: DataFrame with deputados IDs.
        """
        return self.get_deputados()["id"]

    def get_deputados_ids_list(self) -> list[int]:
        """
        Get a list of IDs for all deputados.

        :return: List of deputados IDs.
        """
        return self.get_deputados_ids().values.tolist()

    def get_deputado_expenses(
        self,
        id: int,
        ano: list = [2024],
        mes: list = [8],
        page: int = 1,
        page_limit: int = 0,
    ) -> pd.DataFrame:
        """
        Get the expenses of a specific deputado by ID, optionally filtered by year and month.

        :param id: ID of the deputado.
        :param ano: List of years to filter expenses (default: [2024]).
        :param mes: List of months to filter expenses (default: [8]).
        :param page: Starting page for paginated results (default: 1).
        :param page_limit: Maximum number of pages to fetch (default: 0 for no limit).
        :return: DataFrame containing the deputado's expenses.
        """
        params = {"ano": ano, "mes": mes, "pagina": page}

        despesas = pd.DataFrame()
        while True:
            print(f"Getting page {page} for deputado {id}")
            resp = self._request(
                f"{self.api_base_url}/deputados/{id}/despesas", params=params
            )

            if len(resp["dados"]) == 0 or resp["dados"] is None:
                print(" - No data found")
                break

            if page_limit and page > page_limit:
                print(f"Page limit reached: {page_limit}")
                break

            print(f" - Got {len(resp['dados'])} expenses")
            despesas = pd.concat([despesas, pd.DataFrame(resp["dados"])])
            page += 1
            params["pagina"] = page
            time.sleep(0.5)

        if "dataDocumento" in despesas.columns.to_list():
            despesas["dataDocumento"] = pd.to_datetime(despesas["dataDocumento"])
            despesas.sort_values(by="dataDocumento", inplace=True)

        despesas.reset_index(drop=True, inplace=True)

        return despesas

    def get_deputado_name_by_id(self, id: int) -> str:
        """
        Get the civil name of a deputado by their ID.

        :param id: ID of the deputado.
        :return: Civil name of the deputado.
        """
        resp = self._request(f"{self.api_base_url}/deputados/{id}")
        return resp["dados"]["nomeCivil"]

    # ----------------------------
    # Proposicoes
    # ----------------------------
    def get_proposicoes(
        self,
        data_inicio: str = "2024-08-01",
        data_fim: str = "2024-08-31",
        cod_tema: int = 46,
        page: int = 1,
        page_limit: int = 0,
    ) -> pd.DataFrame:
        """
        Get legislative propositions within a specified date range and theme.

        :param data_inicio: Start date for propositions (format: YYYY-MM-DD, default: "2024-08-01").
        :param data_fim: End date for propositions (format: YYYY-MM-DD, default: "2024-08-31").
        :param cod_tema: Theme code for filtering propositions (default: 46).
        :param page: Starting page for paginated results (default: 1).
        :param page_limit: Maximum number of pages to fetch (default: 0 for no limit).
        :return: DataFrame containing the propositions data.
        """
        params = {
            "dataInicio": data_inicio,
            "dataFim": data_fim,
            "codTema": cod_tema,
            "pagina": page,
        }
        proposicoes = pd.DataFrame()
        while True:
            print(f"Getting page {page} for proposicoes")
            resp = self._request(f"{self.api_base_url}/proposicoes", params=params)

            if len(resp["dados"]) == 0 or resp["dados"] is None:
                print(" - No data found")
                break

            if page_limit and page > page_limit:
                print(f"Page limit reached: {page_limit}")
                break

            print(f" - Got {len(resp['dados'])} proposicoes")
            proposicoes = pd.concat([proposicoes, pd.DataFrame(resp["dados"])])
            page += 1
            params["pagina"] = page
            time.sleep(0.5)

        if "dataApresentacao" in proposicoes.columns.to_list():
            proposicoes["dataApresentacao"] = pd.to_datetime(
                proposicoes["dataApresentacao"]
            )
            proposicoes.sort_values(by="dataApresentacao", inplace=True)

        proposicoes.reset_index(drop=True, inplace=True)

        return proposicoes

    def get_proposition_details(self, id: int) -> pd.DataFrame:
        """
        Get detailed information about a specific proposition by ID.

        :param id: ID of the proposition.
        :return: DataFrame containing the proposition details.
        """
        resp = self._request(f"{self.api_base_url}/proposicoes/{id}")
        return pd.DataFrame(resp["dados"])

    # ----------------------------
    # Utils
    # ----------------------------

    @st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
    def _request(_self, url: str, params: dict = {}) -> dict:
        """
        Perform a GET request to the specified URL with optional parameters.

        :param url: API endpoint to request.
        :param params: Dictionary of query parameters to include in the request.
        :return: JSON response as a dictionary.
        """
        resp = requests.get(url, headers=_self.request_headers, params=params)
        resp.raise_for_status()
        return resp.json()
