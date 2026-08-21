# ============================================================
# scraper.py
# FOOTBALL AI BOT - RAPIDAPI FOOTBALL PREDICTION
# ============================================================

import requests
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_URL = "https://football-prediction-api.p.rapidapi.com"

RAPID_HOST = "football-prediction-api.p.rapidapi.com"


def obter_rapidapi_key() -> str:
    """Lê a chave do Streamlit Secrets."""

    try:
        chave = st.secrets.get("RAPIDAPI_KEY", "")
    except Exception:
        chave = ""

    return str(chave).strip()


# ============================================================
# MOTOR PRINCIPAL
# ============================================================

class FootballAIEngine:

    def __init__(self, liga_nome: str = "UEFA"):

        self.liga_nome = liga_nome
        self.api_key = obter_rapidapi_key()

        self.headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": RAPID_HOST,
            "x-rapidapi-key": self.api_key
        }

    # ========================================================
    # REQUEST
    # ========================================================

    def _get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict]:

        if not self.api_key:
            print("ERRO: RAPIDAPI_KEY não configurada.")
            return None

        try:

            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=self.headers,
                params=params or {},
                timeout=30
            )

            print(
                "RapidAPI:",
                response.status_code,
                response.url
            )

            if response.status_code != 200:

                print(
                    "Erro RapidAPI:",
                    response.text[:1000]
                )

                return None

            return response.json()

        except requests.Timeout:

            print("Timeout na RapidAPI.")
            return None

        except requests.RequestException as e:

            print(
                f"Erro de conexão RapidAPI: {e}"
            )

            return None

        except Exception as e:

            print(
                f"Erro inesperado: {e}"
            )

            return None

    # ========================================================
    # TESTAR API
    # ========================================================

    def testar_api(
        self,
        data_str: Optional[str] = None
    ) -> Dict[str, Any]:

        if not data_str:
            data_str = datetime.now().strftime("%Y-%m-%d")

        data = self._get(
            "/api/v2/predictions",
            {
                "market": "classic",
                "iso_date": data_str,
                "federation": "UEFA"
            }
        )

        if data is None:

            return {
                "ok": False,
                "mensagem": "Não foi possível contactar a RapidAPI."
            }

        return {
            "ok": True,
            "mensagem": "RapidAPI conectada.",
            "dados": data
        }

    # ========================================================
    # BUSCAR PREVISÕES
    # ========================================================

    def buscar_previsoes(
        self,
        data_str: str,
        federation: str = "UEFA"
    ) -> List[Dict]:

        data = self._get(
            "/api/v2/predictions",
            {
                "market": "classic",
                "iso_date": data_str,
                "federation": federation
            }
        )

        if not data:
            return []

        # ====================================================
        # A API pode devolver diferentes estruturas.
        # Tentamos encontrar automaticamente a lista.
        # ====================================================

        resposta = None

        if isinstance(data, list):
            resposta = data

        elif isinstance(data, dict):

            for chave in [
                "data",
                "predictions",
                "response",
                "results"
            ]:

                if isinstance(data.get(chave), list):
                    resposta = data[chave]
                    break

        if resposta is None:
            resposta = []

        jogos = []

        for item in resposta:

            if not isinstance(item, dict):
                continue

            jogo = self._normalizar_jogo(item)

            if jogo:
                jogos.append(jogo)

        return jogos

    # ========================================================
    # NORMALIZAR JOGO
    # ========================================================

    def _normalizar_jogo(
        self,
        item: Dict
    ) -> Optional[Dict]:

        # ----------------------------------------------------
        # Procurar nomes das equipas
        # ----------------------------------------------------

        home = (
            item.get("home_team")
            or item.get("home")
            or item.get("team_home")
            or item.get("home_name")
            or ""
        )

        away = (
            item.get("away_team")
            or item.get("away")
            or item.get("team_away")
            or item.get("away_name")
            or ""
        )

        # Algumas APIs colocam as equipas dentro de "teams"

        teams = item.get("teams", {})

        if isinstance(teams, dict):

            home = (
                home
                or teams.get("home", {}).get("name", "")
                if isinstance(
                    teams.get("home"),
                    dict
                )
                else home
            )

            away = (
                away
                or teams.get("away", {}).get("name", "")
                if isinstance(
                    teams.get("away"),
                    dict
                )
                else away
            )

        if not home and not away:

            # Última tentativa
            home = str(
                item.get("home_team_name", "")
            )

            away = str(
                item.get("away_team_name", "")
            )

        if not home or not away:
            return None

        # ----------------------------------------------------
        # Mercado / previsão principal
        # ----------------------------------------------------

        prediction = (
            item.get("prediction")
            or item.get("predicted")
            or item.get("result")
            or item.get("outcome")
            or ""
        )

        # ----------------------------------------------------
        # Confiança
        # ----------------------------------------------------

        confidence = (
            item.get("confidence")
            or item.get("probability")
            or item.get("percentage")
            or item.get("prob")
            or 0
        )

        try:

            if isinstance(confidence, str):

                confidence = (
                    confidence
                    .replace("%", "")
                    .replace(",", ".")
                    .strip()
                )

            confidence = float(confidence)

            if confidence <= 1:
                confidence *= 100

        except Exception:

            confidence = 0.0

        # ----------------------------------------------------
        # Data
        # ----------------------------------------------------

        match_date = (
            item.get("iso_date")
            or item.get("date")
            or item.get("match_date")
            or ""
        )

        # ----------------------------------------------------
        # ID
        # ----------------------------------------------------

        fixture_id = (
            item.get("fixture_id")
            or item.get("id")
            or item.get("match_id")
        )

        return {

            "fixture_id": fixture_id,

            "home": str(home),

            "away": str(away),

            "home_team": str(home),

            "away_team": str(away),

            "date": match_date,

            "prediction": prediction,

            "confidence": round(
                confidence,
                1
            ),

            "raw": item
        }

    # ========================================================
    # PALPITES DO DIA
    # ========================================================

    def gerar_palpites_do_dia(
        self,
        data_str: str,
        minimo: int = 5
    ) -> List[Dict]:

        jogos = self.buscar_previsoes(
            data_str
        )

        if not jogos:
            return []

        # ====================================================
        # Ordenar pela confiança
        # ====================================================

        jogos.sort(
            key=lambda x: x.get(
                "confidence",
                0
            ),
            reverse=True
        )

        # ====================================================
        # Se houver 10+, usamos 10 ou mais.
        #
        # Se houver poucos, usamos todos disponíveis.
        # ====================================================

        if len(jogos) >= 10:

            return jogos

        return jogos

    # ========================================================
    # PESQUISA POR EQUIPAS
    # ========================================================

    def pesquisar_confronto(
        self,
        equipa_casa: str,
        equipa_fora: str,
        data_str: str
    ) -> List[Dict]:

        jogos = self.buscar_previsoes(
            data_str
        )

        casa = equipa_casa.lower().strip()
        fora = equipa_fora.lower().strip()

        encontrados = []

        for jogo in jogos:

            home = jogo["home"].lower()
            away = jogo["away"].lower()

            if (
                casa in home
                and
                fora in away
            ):

                encontrados.append(jogo)

        return encontrados

    # ========================================================
    # H2H
    #
    # A API fornecida é principalmente uma API de
    # previsões. Portanto não vamos fingir que ela fornece
    # H2H se a resposta não trouxer esse dado.
    # ========================================================

    def analisar_h2h(
        self,
        equipa_casa: str,
        equipa_fora: str,
        data_str: str
    ) -> Dict[str, Any]:

        encontrados = self.pesquisar_confronto(
            equipa_casa,
            equipa_fora,
            data_str
        )

        if not encontrados:

            return {
                "encontrado": False,
                "casa": equipa_casa,
                "fora": equipa_fora,
                "mensagem": (
                    "A API não retornou uma "
                    "previsão para este confronto."
                )
            }

        jogo = encontrados[0]

        return {
            "encontrado": True,
            "casa": equipa_casa,
            "fora": equipa_fora,
            "jogo": jogo
        }

    # ========================================================
    # MELHOR OPORTUNIDADE
    # ========================================================

    def obter_melhor_oportunidade(
        self,
        jogo: Dict
    ) -> str:

        prediction = jogo.get(
            "prediction"
        )

        confidence = jogo.get(
            "confidence",
            0
        )

        if prediction:

            return (
                f"{prediction} "
                f"({confidence:.1f}%)"
            )

        return "Sem previsão disponível"

    # ========================================================
    # COMPATIBILIDADE COM O APP ANTIGO
    # ========================================================

    def get_scheduled_events(
        self,
        date_str: str
    ) -> List[Dict]:

        return self.buscar_previsoes(
            date_str
        )

    def buscar_jogos_reais_api(
        self,
        data_selecionada: str
    ) -> List[Dict]:

        return self.buscar_previsoes(
            data_selecionada
        )
