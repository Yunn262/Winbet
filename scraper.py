# ============================================================
# scraper.py
# FOOTBALL AI BOT - API-FOOTBALL + RAPIDAPI FALLBACK
# ============================================================

import requests
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any


# ============================================================
# CONFIGURAÇÕES
# ============================================================

API_FOOTBALL_URL = "https://v3.football.api-sports.io"

RAPIDAPI_URL = (
    "https://football-prediction-api.p.rapidapi.com"
    "/api/v2"
)


# ============================================================
# LER SECRETS
# ============================================================

def obter_secret(nome: str) -> str:
    """
    Lê uma chave dos Secrets do Streamlit.

    Exemplos:

    API_FOOTBALL_KEY = "..."
    RAPIDAPI_KEY = "..."
    """

    try:
        valor = st.secrets.get(nome, "")
        return str(valor).strip()
    except Exception:
        return ""


def obter_api_football_key() -> str:
    return obter_secret("API_FOOTBALL_KEY")


def obter_rapidapi_key() -> str:
    return obter_secret("RAPIDAPI_KEY")


# ============================================================
# CLASSE PRINCIPAL
# ============================================================

class FootballAIEngine:

    def __init__(
        self,
        liga_nome: str = "Premier League"
    ):

        self.liga_nome = liga_nome

        self.api_football_key = (
            obter_api_football_key()
        )

        self.rapidapi_key = (
            obter_rapidapi_key()
        )

        # IDs das ligas API-Football
        self.ligas = {

            "Premier League": 39,

            "La Liga": 140,

            "Serie A Italiana": 135,

            "Bundesliga": 78,

            "Ligue 1": 61,

            "Champions League": 2,

            "Brasileirao Serie A": 71,

            "Liga Portugal": 94,

            "Primeira Liga": 94,

            "Eredivisie": 88,

            "Noruega": 103,

            "Escócia": 179,

            "Dinamarca": 119,

            "Polônia": 106,

            "Bulgária": 172
        }

        self.league_id = self.ligas.get(
            liga_nome,
            39
        )

        self.season = self._obter_temporada()

    # ========================================================
    # TEMPORADA
    # ========================================================

    def _obter_temporada(self) -> int:

        hoje = datetime.now()

        if hoje.month >= 8:
            return hoje.year

        return hoje.year - 1

    # ========================================================
    # REQUEST API-FOOTBALL
    # ========================================================

    def _get_api_football(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict]:

        if not self.api_football_key:

            print(
                "API_FOOTBALL_KEY não configurada."
            )

            return None

        headers = {

            "x-apisports-key":
                self.api_football_key,

            "Accept":
                "application/json"
        }

        try:

            response = requests.get(

                f"{API_FOOTBALL_URL}{endpoint}",

                headers=headers,

                params=params or {},

                timeout=25
            )

            print(
                "API-Football HTTP:",
                response.status_code
            )

            if response.status_code != 200:

                print(
                    response.text[:500]
                )

                return None

            data = response.json()

            if data.get("errors"):

                print(
                    "API-Football errors:",
                    data.get("errors")
                )

            return data

        except requests.Timeout:

            print(
                "Timeout API-Football."
            )

            return None

        except requests.RequestException as e:

            print(
                f"Erro API-Football: {e}"
            )

            return None

        except Exception as e:

            print(
                f"Erro inesperado: {e}"
            )

            return None

    # ========================================================
    # REQUEST RAPIDAPI
    # ========================================================

    def _get_rapidapi(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict]:

        if not self.rapidapi_key:

            print(
                "RAPIDAPI_KEY não configurada."
            )

            return None

        headers = {

            "x-rapidapi-key":
                self.rapidapi_key,

            "x-rapidapi-host":
                "football-prediction-api.p.rapidapi.com",

            "Content-Type":
                "application/json"
        }

        try:

            response = requests.get(

                f"{RAPIDAPI_URL}{endpoint}",

                headers=headers,

                params=params or {},

                timeout=25
            )

            print(
                "RapidAPI HTTP:",
                response.status_code
            )

            if response.status_code != 200:

                print(
                    response.text[:500]
                )

                return None

            return response.json()

        except requests.Timeout:

            print(
                "Timeout RapidAPI."
            )

            return None

        except requests.RequestException as e:

            print(
                f"Erro RapidAPI: {e}"
            )

            return None

        except Exception as e:

            print(
                f"Erro inesperado RapidAPI: {e}"
            )

            return None

    # ========================================================
    # TESTAR API
    # ========================================================

    def testar_api(self) -> Dict[str, Any]:

        resultado = {

            "api_football": False,

            "rapidapi": False,

            "ok": False,

            "mensagem": ""
        }

        # ----------------------------------------------------
        # API-FOOTBALL
        # ----------------------------------------------------

        if self.api_football_key:

            data = self._get_api_football(
                "/status"
            )

            if data and not data.get("errors"):

                resultado["api_football"] = True

        # ----------------------------------------------------
        # RAPIDAPI
        # ----------------------------------------------------

        if self.rapidapi_key:

            data = self._get_rapidapi(
                "/list-markets"
            )

            if data and not data.get("errors"):

                resultado["rapidapi"] = True

        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        if resultado["api_football"]:

            resultado["ok"] = True

            resultado["mensagem"] = (
                "API-Football conectada."
            )

        elif resultado["rapidapi"]:

            resultado["ok"] = True

            resultado["mensagem"] = (
                "RapidAPI conectada."
            )

        else:

            resultado["mensagem"] = (
                "Nenhuma API conseguiu responder."
            )

        return resultado

    # ========================================================
    # JOGOS API-FOOTBALL
    # ========================================================

    def _buscar_jogos_api_football(
        self,
        data_str: str
    ) -> List[Dict]:

        params = {

            "league":
                self.league_id,

            "season":
                self.season,

            "date":
                data_str
        }

        data = self._get_api_football(
            "/fixtures",
            params
        )

        if not data:

            return []

        resposta = data.get(
            "response",
            []
        )

        jogos = []

        for item in resposta:

            fixture = item.get(
                "fixture",
                {}
            )

            teams = item.get(
                "teams",
                {}
            )

            goals = item.get(
                "goals",
                {}
            )

            league = item.get(
                "league",
                {}
            )

            status = fixture.get(
                "status",
                {}
            )

            jogos.append({

                "fixture_id":
                    fixture.get("id"),

                "event_id":
                    fixture.get("id"),

                "home_team":
                    teams.get(
                        "home",
                        {}
                    ).get(
                        "name",
                        "?"
                    ),

                "away_team":
                    teams.get(
                        "away",
                        {}
                    ).get(
                        "name",
                        "?"
                    ),

                "home_team_id":
                    teams.get(
                        "home",
                        {}
                    ).get("id"),

                "away_team_id":
                    teams.get(
                        "away",
                        {}
                    ).get("id"),

                "home_logo":
                    teams.get(
                        "home",
                        {}
                    ).get("logo"),

                "away_logo":
                    teams.get(
                        "away",
                        {}
                    ).get("logo"),

                "league":
                    league.get("name"),

                "country":
                    league.get("country"),

                "round":
                    league.get("round"),

                "date":
                    fixture.get("date"),

                "start_time":
                    fixture.get("date"),

                "status":
                    status.get("long"),

                "status_short":
                    status.get("short"),

                "venue":
                    fixture.get(
                        "venue",
                        {}
                    ).get("name"),

                "referee":
                    fixture.get("referee"),

                "home_score":
                    goals.get("home"),

                "away_score":
                    goals.get("away"),

                "fonte":
                    "API-Football",

                "raw":
                    item
            })

        return jogos

    # ========================================================
    # JOGOS RAPIDAPI
    # ========================================================

    def _buscar_jogos_rapidapi(
        self,
        data_str: str
    ) -> List[Dict]:

        params = {

            "market":
                "classic",

            "iso_date":
                data_str
        }

        data = self._get_rapidapi(
            "/predictions",
            params
        )

        if not data:

            return []

        resposta = data.get(
            "data",
            data.get(
                "response",
                []
            )
        )

        if not isinstance(
            resposta,
            list
        ):

            return []

        jogos = []

        for item in resposta:

            if not isinstance(
                item,
                dict
            ):

                continue

            home = (
                item.get("home_team")
                or item.get("home")
                or "?"
            )

            away = (
                item.get("away_team")
                or item.get("away")
                or "?"
            )

            fixture_id = (
                item.get("id")
                or item.get("fixture_id")
            )

            jogos.append({

                "fixture_id":
                    fixture_id,

                "event_id":
                    fixture_id,

                "home_team":
                    home,

                "away_team":
                    away,

                "home_team_id":
                    None,

                "away_team_id":
                    None,

                "league":
                    item.get(
                        "competition_name"
                    ),

                "country":
                    item.get(
                        "federation"
                    ),

                "round":
                    None,

                "date":
                    item.get(
                        "start_date"
                    ) or item.get(
                        "iso_date"
                    ),

                "start_time":
                    item.get(
                        "start_date"
                    ) or item.get(
                        "iso_date"
                    ),

                "status":
                    item.get("status"),

                "status_short":
                    None,

                "venue":
                    None,

                "referee":
                    None,

                "home_score":
                    None,

                "away_score":
                    None,

                "prediction":
                    item.get(
                        "prediction"
                    ),

                "probabilities":
                    item.get(
                        "probabilities",
                        {}
                    ),

                "odds":
                    item.get(
                        "odds",
                        {}
                    ),

                "fonte":
                    "RapidAPI",

                "raw":
                    item
            })

        return jogos

    # ========================================================
    # JOGOS DO DIA
    # ========================================================

    def get_scheduled_events(
        self,
        date_str: str
    ) -> List[Dict]:

        # Primeiro API-Football
        jogos = (
            self._buscar_jogos_api_football(
                date_str
            )
        )

        if jogos:

            print(
                f"API-Football encontrou "
                f"{len(jogos)} jogos."
            )

            return jogos

        # Se não encontrou, tenta RapidAPI
        print(
            "API-Football não encontrou jogos."
        )

        jogos_rapid = (
            self._buscar_jogos_rapidapi(
                date_str
            )
        )

        if jogos_rapid:

            print(
                f"RapidAPI encontrou "
                f"{len(jogos_rapid)} jogos."
            )

            return jogos_rapid

        return []

    # ========================================================
    # COMPATIBILIDADE
    # ========================================================

    def buscar_jogos_reais_api(
        self,
        data_selecionada: str
    ) -> List[Dict]:

        return self.get_scheduled_events(
            data_selecionada
        )

    # ========================================================
    # PROCURAR EQUIPA
    # ========================================================

    def procurar_equipa(
        self,
        nome: str
    ) -> Optional[Dict]:

        nome = str(
            nome
        ).strip()

        if not nome:
            return None

        data = self._get_api_football(
            "/teams",
            {
                "search":
                    nome
            }
        )

        if not data:

            return None

        equipes = data.get(
            "response",
            []
        )

        if not equipes:

            return None

        nome_lower = nome.lower()

        for item in equipes:

            team = item.get(
                "team",
                {}
            )

            nome_api = str(
                team.get(
                    "name",
                    ""
                )
            )

            if nome_lower in nome_api.lower():

                return team

        return equipes[0].get(
            "team"
        )

    # ========================================================
    # H2H
    # ========================================================

    def pesquisar_h2h(
        self,
        equipa_casa: str,
        equipa_fora: str,
        ultimos: int = 10
    ) -> List[Dict]:

        casa = self.procurar_equipa(
            equipa_casa
        )

        fora = self.procurar_equipa(
            equipa_fora
        )

        if not casa or not fora:

            return []

        casa_id = casa.get("id")
        fora_id = fora.get("id")

        if not casa_id or not fora_id:

            return []

        data = self._get_api_football(

            "/fixtures/headtohead",

            {
                "h2h":
                    f"{casa_id}-{fora_id}",

                "last":
                    ultimos
            }
        )

        if not data:

            return []

        resposta = data.get(
            "response",
            []
        )

        confrontos = []

        for item in resposta:

            fixture = item.get(
                "fixture",
                {}
            )

            teams = item.get(
                "teams",
                {}
            )

            goals = item.get(
                "goals",
                {}
            )

            confrontos.append({

                "fixture_id":
                    fixture.get("id"),

                "date":
                    fixture.get("date"),

                "home_team":
                    teams.get(
                        "home",
                        {}
                    ).get("name"),

                "away_team":
                    teams.get(
                        "away",
                        {}
                    ).get("name"),

                "home_team_id":
                    teams.get(
                        "home",
                        {}
                    ).get("id"),

                "away_team_id":
                    teams.get(
                        "away",
                        {}
                    ).get("id"),

                "home_score":
                    goals.get("home"),

                "away_score":
                    goals.get("away"),

                "placar":
                    f"{goals.get('home', 0)} - "
                    f"{goals.get('away', 0)}"
            })

        return confrontos

    # ========================================================
    # ALIAS
    # ========================================================

    def buscar_h2h(
        self,
        equipa_casa: str,
        equipa_fora: str,
        ultimos: int = 10
    ) -> List[Dict]:

        return self.pesquisar_h2h(
            equipa_casa,
            equipa_fora,
            ultimos
        )

    # ========================================================
    # ÚLTIMOS JOGOS
    # ========================================================

    def get_team_recent_matches(
        self,
        team_id: int,
        last: int = 10
    ) -> List[Dict]:

        data = self._get_api_football(

            "/fixtures",

            {
                "team":
                    team_id,

                "last":
                    last
            }
        )

        if not data:

            return []

        resposta = data.get(
            "response",
            []
        )

        jogos = []

        for item in resposta:

            fixture = item.get(
                "fixture",
                {}
            )

            teams = item.get(
                "teams",
                {}
            )

            goals = item.get(
                "goals",
                {}
            )

            jogos.append({

                "fixture_id":
                    fixture.get("id"),

                "date":
                    fixture.get("date"),

                "home_team":
                    teams.get(
                        "home",
                        {}
                    ).get("name"),

                "away_team":
                    teams.get(
                        "away",
                        {}
                    ).get("name"),

                "home_score":
                    goals.get("home"),

                "away_score":
                    goals.get("away")
            })

        return jogos

    # ========================================================
    # ESTATÍSTICAS
    # ========================================================

    def get_team_statistics(
        self,
        team_id: int
    ) -> Dict:

        data = self._get_api_football(

            "/teams/statistics",

            {
                "league":
                    self.league_id,

                "season":
                    self.season,

                "team":
                    team_id
            }
        )

        if not data:

            return {}

        return data.get(
            "response",
            {}
        )

    # ========================================================
    # ESTATÍSTICAS PARA IA
    # ========================================================

    def get_team_stats_for_ai(
        self,
        equipa_nome: str
    ) -> Dict[str, Any]:

        equipa = self.procurar_equipa(
            equipa_nome
        )

        if not equipa:

            return {
                "erro":
                    "Equipa não encontrada"
            }

        team_id = equipa.get(
            "id"
        )

        stats = self.get_team_statistics(
            team_id
        )

        if not stats:

            return {

                "team_id":
                    team_id,

                "team_name":
                    equipa.get("name"),

                "dados_disponiveis":
                    False
            }

        fixtures = stats.get(
            "fixtures",
            {}
        )

        goals = stats.get(
            "goals",
            {}
        )

        return {

            "team_id":
                team_id,

            "team_name":
                equipa.get("name"),

            "jogos":
                fixtures.get(
                    "played",
                    {}
                ),

            "vitorias":
                fixtures.get(
                    "wins",
                    {}
                ),

            "empates":
                fixtures.get(
                    "draws",
                    {}
                ),

            "derrotas":
                fixtures.get(
                    "loses",
                    {}
                ),

            "golos":
                goals,

            "dados_disponiveis":
                True,

            "raw":
                stats
        }

    # ========================================================
    # ODDS
    # ========================================================

    def get_odds(
        self,
        fixture_id: int
    ) -> Dict:

        data = self._get_api_football(

            "/odds",

            {
                "fixture":
                    fixture_id
            }
        )

        if not data:

            return {}

        resposta = data.get(
            "response",
            []
        )

        if not resposta:

            return {}

        return resposta[0]

    # ========================================================
    # ESCALAÇÕES
    # ========================================================

    def get_lineups(
        self,
        fixture_id: int
    ) -> List[Dict]:

        data = self._get_api_football(

            "/fixtures/lineups",

            {
                "fixture":
                    fixture_id
            }
        )

        if not data:

            return []

        return data.get(
            "response",
            []
        )

    # ========================================================
    # EVENTOS
    # ========================================================

    def get_fixture_events(
        self,
        fixture_id: int
    ) -> List[Dict]:

        data = self._get_api_football(

            "/fixtures/events",

            {
                "fixture":
                    fixture_id
            }
        )

        if not data:

            return []

        return data.get(
            "response",
            []
        )

    # ========================================================
    # CALCULAR MERCADOS H2H
    # ========================================================

    def calcular_mercados(
        self,
        h2h: List[Dict]
    ) -> Dict[str, float]:

        mercados = {

            "Ambas marcam":
                0.0,

            "Mais de 1,5 golos":
                0.0,

            "Mais de 2,5 golos":
                0.0,

            "Menos de 3,5 golos":
                0.0,

            "Menos de 4,5 golos":
                0.0,

            "Time 1 ganha ou empata":
                0.0,

            "Time 2 ganha ou empata":
                0.0,

            "Time 1 ganha direto":
                0.0,

            "Time 2 ganha direto":
                0.0
        }

        if not h2h:

            return mercados

        total = 0

        contadores = {

            "btts":
                0,

            "over15":
                0,

            "over25":
                0,

            "under35":
                0,

            "under45":
                0,

            "time1_x":
                0,

            "time2_x":
                0,

            "time1":
                0,

            "time2":
                0
        }

        for jogo in h2h:

            hg = jogo.get(
                "home_score"
            )

            ag = jogo.get(
                "away_score"
            )

            if hg is None or ag is None:
                continue

            try:

                hg = int(hg)

                ag = int(ag)

            except:

                continue

            total += 1

            gols = hg + ag

            if hg > 0 and ag > 0:
                contadores["btts"] += 1

            if gols >= 2:
                contadores["over15"] += 1

            if gols >= 3:
                contadores["over25"] += 1

            if gols <= 3:
                contadores["under35"] += 1

            if gols <= 4:
                contadores["under45"] += 1

            if hg >= ag:
                contadores["time1_x"] += 1

            if ag >= hg:
                contadores["time2_x"] += 1

            if hg > ag:
                contadores["time1"] += 1

            if ag > hg:
                contadores["time2"] += 1

        if total == 0:

            return mercados

        def porcentagem(valor):

            return round(
                valor / total * 100,
                1
            )

        return {

            "Ambas marcam":
                porcentagem(
                    contadores["btts"]
                ),

            "Mais de 1,5 golos":
                porcentagem(
                    contadores["over15"]
                ),

            "Mais de 2,5 golos":
                porcentagem(
                    contadores["over25"]
                ),

            "Menos de 3,5 golos":
                porcentagem(
                    contadores["under35"]
                ),

            "Menos de 4,5 golos":
                porcentagem(
                    contadores["under45"]
                ),

            "Time 1 ganha ou empata":
                porcentagem(
                    contadores["time1_x"]
                ),

            "Time 2 ganha ou empata":
                porcentagem(
                    contadores["time2_x"]
                ),

            "Time 1 ganha direto":
                porcentagem(
                    contadores["time1"]
                ),

            "Time 2 ganha direto":
                porcentagem(
                    contadores["time2"]
                )
        }

    # ========================================================
    # MELHOR MERCADO
    # ========================================================

    def obter_melhor_mercado(
        self,
        mercados: Dict[str, float]
    ) -> str:

        validos = {

            mercado:
                chance

            for mercado, chance
            in mercados.items()

            if chance > 0
        }

        if not validos:

            return "Dados insuficientes"

        return max(
            validos,
            key=validos.get
        )

    # ========================================================
    # ANÁLISE H2H COMPLETA
    # ========================================================

    def analisar_confronto_completo(
        self,
        equipa_casa: str,
        equipa_fora: str
    ) -> Dict:

        h2h = self.pesquisar_h2h(
            equipa_casa,
            equipa_fora,
            10
        )

        stats_casa = (
            self.get_team_stats_for_ai(
                equipa_casa
            )
        )

        stats_fora = (
            self.get_team_stats_for_ai(
                equipa_fora
            )
        )

        mercados = self.calcular_mercados(
            h2h
        )

        melhor = (
            self.obter_melhor_mercado(
                mercados
            )
        )

        chance = mercados.get(
            melhor,
            0
        )

        return {

            "casa":
                equipa_casa,

            "fora":
                equipa_fora,

            "h2h":
                h2h,

            "stats_casa":
                stats_casa,

            "stats_fora":
                stats_fora,

            "mercados":
                mercados,

            "melhor_mercado":
                melhor,

            "melhor_chance":
                chance,

            "combinada_1":
                melhor,

            "pct_combinada_1":
                chance,

            "combinada_2":
                "Ambas marcam",

            "pct_combinada_2":
                mercados.get(
                    "Ambas marcam",
                    0
                )
        }

    # ========================================================
    # PALPITES DO DIA
    # ========================================================

    def gerar_palpites_do_dia(
        self,
        data_str: str,
        minimo: int = 5
    ) -> List[Dict]:

        jogos = self.get_scheduled_events(
            data_str
        )

        palpites = []

        for jogo in jogos:

            casa = jogo.get(
                "home_team"
            )

            fora = jogo.get(
                "away_team"
            )

            if not casa or not fora:
                continue

            # RapidAPI já pode trazer previsão
            if jogo.get("fonte") == "RapidAPI":

                prediction = jogo.get(
                    "prediction"
                )

                probabilities = jogo.get(
                    "probabilities",
                    {}
                )

                palpites.append({

                    "fixture_id":
                        jogo.get("fixture_id"),

                    "home":
                        casa,

                    "away":
                        fora,

                    "data":
                        jogo.get("start_time"),

                    "fonte":
                        "RapidAPI",

                    "melhor_mercado":
                        prediction
                        or "Previsão disponível",

                    "melhor_chance":
                        self._extrair_chance(
                            probabilities
                        ),

                    "mercados":
                        probabilities,

                    "h2h":
                        []
                })

                continue

            # API-Football
            try:

                analise = (
                    self.analisar_confronto_completo(
                        casa,
                        fora
                    )
                )

                palpites.append({

                    "fixture_id":
                        jogo.get("fixture_id"),

                    "home":
                        casa,

                    "away":
                        fora,

                    "data":
                        jogo.get("start_time"),

                    "fonte":
                        "API-Football",

                    "melhor_mercado":
                        analise.get(
                            "melhor_mercado"
                        ),

                    "melhor_chance":
                        analise.get(
                            "melhor_chance"
                        ),

                    "mercados":
                        analise.get(
                            "mercados",
                            {}
                        ),

                    "h2h":
                        analise.get(
                            "h2h",
                            []
                        )
                })

            except Exception as e:

                print(
                    f"Erro ao analisar "
                    f"{casa} x {fora}: {e}"
                )

        # Maior confiança primeiro
        palpites.sort(

            key=lambda x:
                float(
                    x.get(
                        "melhor_chance",
                        0
                    ) or 0
                ),

            reverse=True
        )

        return palpites

    # ========================================================
    # EXTRAIR PROBABILIDADE RAPIDAPI
    # ========================================================

    def _extrair_chance(
        self,
        probabilities
    ) -> float:

        if isinstance(
            probabilities,
            (int, float)
        ):

            valor = float(
                probabilities
            )

            if valor <= 1:
                valor *= 100

            return round(
                valor,
                1
            )

        if not isinstance(
            probabilities,
            dict
        ):

            return 0.0

        valores = []

        for valor in probabilities.values():

            try:

                numero = float(valor)

                if numero <= 1:
                    numero *= 100

                valores.append(
                    numero
                )

            except:

                continue

        if not valores:

            return 0.0

        return round(
            max(valores),
            1
        )

    # ========================================================
    # TODAS AS EQUIPAS
    # ========================================================

    def obter_todas_equipas(
        self
    ) -> List[str]:

        data = self._get_api_football(

            "/teams",

            {
                "league":
                    self.league_id,

                "season":
                    self.season
            }
        )

        if not data:

            return []

        resposta = data.get(
            "response",
            []
        )

        nomes = []

        for item in resposta:

            nome = item.get(
                "team",
                {}
            ).get(
                "name"
            )

            if nome:
                nomes.append(nome)

        return sorted(
            list(
                set(nomes)
            )
        )
