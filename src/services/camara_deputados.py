import requests
import pandas as pd
import streamlit as st
import time


class CamaraDeputados:
    def __init__(self):
        self.api_base_url = "https://dadosabertos.camara.leg.br/api/v2"

        self.request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    # ----------------------------
    # Deputados
    # ----------------------------

    def get_deputados(self) -> pd.DataFrame:
        resp = self._request(self.api_base_url + "/deputados")
        return pd.DataFrame(resp["dados"])

    def get_deputados_ids(self) -> pd.DataFrame:
        return self.get_deputados()["id"]

    def get_deputados_ids_list(self) -> list[int]:
        return self.get_deputados_ids().values.tolist()

    def get_deputado_expenses(
        self,
        id: int,
        ano: list = [2024],
        mes: list = [8],
        page: int = 1,
        page_limit: int = 0,
    ) -> pd.DataFrame:

        params = {"ano": ano, "mes": mes, "pagina": page}

        despesas = pd.DataFrame()
        while True:
            print(f"Getting page {page} for deputado {id}")
            resp = self._request(
                f"{self.api_base_url}/deputados/{id}/despesas", params=params
            )

            # If there are no more pages, break the loop
            if len(resp["dados"]) == 0 or resp["dados"] is None:
                print(" - No data found")
                break

            # If there is a page limit, break the loop
            if page_limit and page > page_limit:
                print(f"Page limit reached: {page_limit}")
                break

            # Use recursive function to get all pages
            print(f" - Got {len(resp['dados'])} expenses")
            despesas = pd.concat([despesas, pd.DataFrame(resp["dados"])])
            page += 1
            params["pagina"] = page
            time.sleep(0.5)

        # Order by date
        if "dataDocumento" in despesas.columns.to_list():
            despesas["dataDocumento"] = pd.to_datetime(despesas["dataDocumento"])
            despesas.sort_values(by="dataDocumento", inplace=True)

        # Reset the index
        despesas.reset_index(drop=True, inplace=True)

        return despesas

    def get_deputado_name_by_id(self, id: int) -> str:
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

            # If there are no more pages, break the loop
            if len(resp["dados"]) == 0 or resp["dados"] is None:
                print(" - No data found")
                break

            # If there is a page limit, break the loop
            if page_limit and page > page_limit:
                print(f"Page limit reached: {page_limit}")
                break

            # Use recursive function to get all pages
            print(f" - Got {len(resp['dados'])} proposicoes")
            proposicoes = pd.concat([proposicoes, pd.DataFrame(resp["dados"])])
            page += 1
            params["pagina"] = page
            time.sleep(0.5)

        # Order by date
        if "dataApresentacao" in proposicoes.columns.to_list():
            proposicoes["dataApresentacao"] = pd.to_datetime(
                proposicoes["dataApresentacao"]
            )
            proposicoes.sort_values(by="dataApresentacao", inplace=True)

        # Reset the index
        proposicoes.reset_index(drop=True, inplace=True)

        return proposicoes

    def get_proposition_details(self, id: int) -> pd.DataFrame:
        resp = self._request(f"{self.api_base_url}/proposicoes/{id}")
        return pd.DataFrame(resp["dados"])

    # ----------------------------
    # Utils
    # ----------------------------

    @st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
    def _request(_self, url: str, params: dict = {}) -> dict:
        # print(f"Requesting {url} with params {params}")
        resp = requests.get(url, headers=_self.request_headers, params=params)
        resp.raise_for_status()
        return resp.json()
